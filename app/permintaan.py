from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from app.models import Permintaan, PermintaanDetail, Barang, Unit, now_wib
from app.utils import gen_no_permintaan, log_audit
from sqlalchemy.exc import IntegrityError

bp = Blueprint("permintaan", __name__)


@bp.route("/")
@login_required
def index():
    status_filter = (request.args.get("status") or "").strip()

    if current_user.is_admin:
        query = Permintaan.query
    elif current_user.is_kepala:
        query = Permintaan.query.filter_by(unit_id=current_user.unit_id)
    else:
        query = Permintaan.query.filter_by(diajukan_oleh=current_user.id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    items = query.order_by(Permintaan.id.desc()).all()
    status_list = [
        ("diajukan", "Diajukan"), ("disetujui", "Disetujui"), ("diproses", "Diproses"),
        ("selesai", "Selesai"), ("ditolak", "Ditolak"),
    ]
    return render_template("permintaan/index.html", items=items, status_list=status_list,
                           sf=status_filter)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if not current_user.unit_id:
        flash("Akun Anda belum terhubung ke unit mana pun. Hubungi Admin Gudang.", "error")
        return redirect(url_for("permintaan.index"))
    barangs = Barang.query.filter_by(is_aktif=True).order_by(Barang.nama).all()

    if request.method == "POST":
        catatan = (request.form.get("catatan") or "").strip()
        barang_ids = request.form.getlist("barang_id[]")
        qtys = request.form.getlist("qty[]")
        catatans = request.form.getlist("catatan_item[]")

        if not barang_ids or not any(int(q) > 0 for q in qtys if q.isdigit()):
            flash("Minimal satu barang harus diminta.", "error")
            return redirect(url_for("permintaan.create"))

        no_p = None
        MAX_RETRY = 5

        for attempt in range(MAX_RETRY):
            no_p = gen_no_permintaan()
            p = Permintaan(
                no_permintaan=no_p,
                tanggal=date.today(),
                unit_id=current_user.unit_id,
                diajukan_oleh=current_user.id,
                status=Permintaan.STATUS_DIAJUKAN,
                catatan=catatan,
            )
            db.session.add(p)
            try:
                db.session.flush()
            except IntegrityError:
                db.session.rollback()
                continue  # nomor bentrok, coba lagi dengan nomor berikutnya

            for bid, q, c in zip(barang_ids, qtys, catatans):
                if not bid:
                    continue
                qty = int(q) if q.isdigit() else 0
                if qty <= 0:
                    continue
                d = PermintaanDetail(
                    header_id=p.id, barang_id=int(bid), qty=qty,
                    catatan=(c or "").strip(),
                )
                db.session.add(d)

            try:
                db.session.commit()
                break  # berhasil, keluar dari retry loop
            except IntegrityError:
                db.session.rollback()
                no_p = None
                continue
        else:
            # Loop habis tanpa "break" -> semua percobaan gagal
            flash("Gagal membuat nomor permintaan karena ada tabrakan data. Silakan coba submit sekali lagi.", "error")
            return redirect(url_for("permintaan.create"))

        log_audit("create", "permintaan", target=no_p)
        flash(f"Permintaan {no_p} berhasil diajukan.", "success")
        return redirect(url_for("permintaan.index"))

    return render_template("permintaan/form.html", barangs=barangs)


@bp.route("/<int:pid>")
@login_required
def detail(pid):
    p = Permintaan.query.get_or_404(pid)
    # Access control
    if not current_user.is_admin and p.unit_id != current_user.unit_id:
        if not (current_user.is_kepala and p.unit_id == current_user.unit_id):
            flash("Anda tidak dapat melihat permintaan ini.", "error")
            return redirect(url_for("permintaan.index"))
    return render_template("permintaan/detail.html", p=p)


@bp.route("/<int:pid>/approve", methods=["POST"])
@login_required
def approve(pid):
    p = Permintaan.query.get_or_404(pid)
    if p.status != Permintaan.STATUS_DIAJUKAN:
        flash("Permintaan ini tidak bisa disetujui (status sudah berubah).", "warning")
        return redirect(url_for("permintaan.detail", pid=pid))

    can_approve = False
    if current_user.is_admin:
        can_approve = True
    elif current_user.is_kepala and p.unit_id == current_user.unit_id:
        if p.diajukan_oleh == current_user.id:
            flash("Anda tidak dapat menyetujui permintaan yang Anda ajukan sendiri. Permintaan ini menunggu diproses langsung oleh Admin Gudang.", "error")
            return redirect(url_for("permintaan.detail", pid=pid))
        can_approve = True

    if not can_approve:
        flash("Anda tidak berhak menyetujui permintaan ini.", "error")
        return redirect(url_for("permintaan.detail", pid=pid))

    # Ambil qty yang disetujui per baris dari form
    detail_ids = request.form.getlist("detail_id[]")
    qtys_disetujui = request.form.getlist("qty_disetujui[]")

    total_disetujui = 0
    for did, qd in zip(detail_ids, qtys_disetujui):
        detail_row = PermintaanDetail.query.get(int(did)) if did.isdigit() else None
        if not detail_row or detail_row.header_id != p.id:
            continue  # lewati kalau detail_id tidak valid atau bukan milik permintaan ini
        qty_input = int(qd) if qd.isdigit() else 0
        qty_final = max(0, min(qty_input, detail_row.qty))  # tidak boleh < 0 atau > qty diminta
        detail_row.qty_disetujui = qty_final
        total_disetujui += qty_final

    if total_disetujui == 0:
        db.session.rollback()
        flash("Total qty yang disetujui tidak boleh 0 untuk semua barang. Gunakan tombol Tolak kalau memang tidak ada yang bisa dipenuhi.", "error")
        return redirect(url_for("permintaan.detail", pid=pid))

    p.status = Permintaan.STATUS_DISETUJUI
    p.disetujui_oleh = current_user.id
    p.tanggal_disetujui = now_wib()
    db.session.commit()
    log_audit("approve", "permintaan", target=p.no_permintaan, detail=f"total disetujui: {total_disetujui}")
    flash(f"Permintaan {p.no_permintaan} disetujui.", "success")
    return redirect(url_for("permintaan.detail", pid=pid))


@bp.route("/<int:pid>/reject", methods=["POST"])
@login_required
def reject(pid):
    p = Permintaan.query.get_or_404(pid)
    if p.status != Permintaan.STATUS_DIAJUKAN:
        flash("Permintaan ini tidak bisa ditolak (status sudah berubah).", "warning")
        return redirect(url_for("permintaan.detail", pid=pid))

    can_reject = False
    if current_user.is_admin:
        can_reject = True
    elif current_user.is_kepala and p.unit_id == current_user.unit_id:
        if p.diajukan_oleh == current_user.id:
            flash("Anda tidak dapat menolak permintaan yang Anda ajukan sendiri. Permintaan ini menunggu diproses langsung oleh Admin Gudang.", "error")
            return redirect(url_for("permintaan.detail", pid=pid))
        can_reject = True

    if not can_reject:
        flash("Anda tidak berhak menolak permintaan ini.", "error")
        return redirect(url_for("permintaan.detail", pid=pid))

    alasan = (request.form.get("alasan_tolak") or "").strip()
    p.status = Permintaan.STATUS_DITOLAK
    p.alasan_tolak = alasan
    p.disetujui_oleh = current_user.id
    p.tanggal_disetujui = now_wib()
    db.session.commit()
    log_audit("reject", "permintaan", target=p.no_permintaan, detail=alasan)
    flash(f"Permintaan {p.no_permintaan} ditolak.", "info")
    return redirect(url_for("permintaan.detail", pid=pid))

@bp.route("/<int:pid>/proses", methods=["POST"])
@login_required
def proses(pid):
    p = Permintaan.query.get_or_404(pid)
    if not current_user.is_admin:
        flash("Hanya Admin Gudang yang memproses permintaan.", "error")
        return redirect(url_for("permintaan.detail", pid=pid))
    if p.status != Permintaan.STATUS_DISETUJUI:
        flash("Hanya permintaan berstatus Disetujui yang bisa diproses.", "warning")
        return redirect(url_for("permintaan.detail", pid=pid))

    # Ambil qty final dari form (Admin bisa mengurangi lagi dari qty yang disetujui Kepala Unit,
    # tapi TIDAK BOLEH menaikkan melebihi qty_efektif -- itu batas atas yang sah)
    detail_ids = request.form.getlist("detail_id[]")
    qtys_final = request.form.getlist("qty_final[]")

    qty_final_map = {}
    for did, qf in zip(detail_ids, qtys_final):
        detail_row = PermintaanDetail.query.get(int(did)) if did.isdigit() else None
        if not detail_row or detail_row.header_id != p.id:
            continue
        qty_input = int(qf) if qf.isdigit() else 0
        # Clamp: tidak boleh < 0, dan tidak boleh > qty yang sudah disetujui Kepala Unit
        qty_final_map[detail_row.id] = max(0, min(qty_input, detail_row.qty_efektif))

    # Check stock availability berdasarkan qty final yang mau dikeluarkan Admin
    insufficient = []
    for d in p.details:
        qty_final = qty_final_map.get(d.id, d.qty_efektif)
        if qty_final > d.barang.stok:
            insufficient.append(f"{d.barang.nama} (mau dikeluarkan {qty_final}, stok {d.barang.stok})")
    if insufficient:
        flash("Stok tidak mencukupi: " + "; ".join(insufficient), "error")
        return redirect(url_for("permintaan.detail", pid=pid))

    total_keluar = 0
    for d in p.details:
        qty_final = qty_final_map.get(d.id, d.qty_efektif)
        d.barang.stok -= qty_final
        d.qty_diproses = qty_final
        total_keluar += qty_final

    if total_keluar == 0:
        db.session.rollback()
        flash("Total qty yang diproses tidak boleh 0 untuk semua barang.", "error")
        return redirect(url_for("permintaan.detail", pid=pid))

    p.status = Permintaan.STATUS_DIPROSES
    p.diproses_oleh = current_user.id
    p.tanggal_diproses = now_wib()
    db.session.commit()
    log_audit("process", "permintaan", target=p.no_permintaan, detail=f"total dikeluarkan: {total_keluar}")
    flash(f"Permintaan {p.no_permintaan} diproses. Stok barang dikurangi.", "success")
    return redirect(url_for("permintaan.detail", pid=pid))

@bp.route("/<int:pid>/selesai", methods=["POST"])
@login_required
def selesai(pid):
    p = Permintaan.query.get_or_404(pid)
    if not current_user.is_admin:
        flash("Hanya Admin Gudang yang menyelesaikan permintaan.", "error")
        return redirect(url_for("permintaan.detail", pid=pid))
    if p.status != Permintaan.STATUS_DIPROSES:
        flash("Hanya permintaan berstatus Diproses yang bisa diselesaikan.", "warning")
        return redirect(url_for("permintaan.detail", pid=pid))

    p.status = Permintaan.STATUS_SELESAI
    p.tanggal_selesai = now_wib()
    db.session.commit()
    log_audit("complete", "permintaan", target=p.no_permintaan)
    flash(f"Permintaan {p.no_permintaan} selesai.", "success")
    return redirect(url_for("permintaan.detail", pid=pid))


@bp.route("/<int:pid>/cancel", methods=["POST"])
@login_required
def cancel(pid):
    p = Permintaan.query.get_or_404(pid)
    if p.diajukan_oleh != current_user.id and not current_user.is_admin:
        flash("Anda hanya bisa membatalkan permintaan sendiri.", "error")
        return redirect(url_for("permintaan.detail", pid=pid))
    if p.status not in (Permintaan.STATUS_DIAJUKAN,):
        flash("Permintaan yang sudah diproses tidak bisa dibatalkan.", "warning")
        return redirect(url_for("permintaan.detail", pid=pid))
    db.session.delete(p)
    db.session.commit()
    log_audit("cancel", "permintaan", target=p.no_permintaan)
    flash("Permintaan dibatalkan.", "info")
    return redirect(url_for("permintaan.index"))