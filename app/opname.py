from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from app.models import StokOpname, StokOpnameDetail, Barang, now_wib
from app.utils import admin_required, log_audit, gen_no_opname
from sqlalchemy.exc import IntegrityError

bp = Blueprint("opname", __name__)


@bp.route("/")
@login_required
@admin_required
def index():
    items = StokOpname.query.order_by(StokOpname.id.desc()).all()
    return render_template("opname/index.html", items=items)


@bp.route("/create", methods=["POST"])
@login_required
@admin_required
def create():
    existing_draft = StokOpname.query.filter_by(status=StokOpname.STATUS_DRAFT).first()
    if existing_draft:
        flash(f"Masih ada sesi opname yang belum selesai ({existing_draft.no_opname}). Selesaikan dulu sebelum membuat sesi baru.", "warning")
        return redirect(url_for("opname.form", oid=existing_draft.id))

    no_opn = None
    MAX_RETRY = 5
    barangs = Barang.query.filter_by(is_aktif=True).order_by(Barang.kode).all()

    for attempt in range(MAX_RETRY):
        no_opn = gen_no_opname()
        o = StokOpname(
            no_opname=no_opn,
            tanggal=date.today(),
            status=StokOpname.STATUS_DRAFT,
            dibuat_oleh=current_user.id,
        )
        db.session.add(o)
        try:
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            continue

        for b in barangs:
            d = StokOpnameDetail(header_id=o.id, barang_id=b.id, stok_sistem=b.stok)
            db.session.add(d)

        try:
            db.session.commit()
            break
        except IntegrityError:
            db.session.rollback()
            no_opn = None
            continue
    else:
        flash("Gagal membuat sesi opname karena tabrakan data. Coba lagi.", "error")
        return redirect(url_for("opname.index"))

    log_audit("create", "stok_opname", target=no_opn)
    flash(f"Sesi opname {no_opn} dibuat dengan {len(barangs)} barang aktif. Silakan mulai hitung fisik.", "success")
    return redirect(url_for("opname.form", oid=o.id))


@bp.route("/<int:oid>")
@login_required
@admin_required
def form(oid):
    o = StokOpname.query.get_or_404(oid)
    if o.status == StokOpname.STATUS_SELESAI:
        return redirect(url_for("opname.detail", oid=oid))
    return render_template("opname/form.html", o=o)


@bp.route("/<int:oid>/save", methods=["POST"])
@login_required
@admin_required
def save(oid):
    o = StokOpname.query.get_or_404(oid)
    if o.status != StokOpname.STATUS_DRAFT:
        flash("Sesi opname ini sudah selesai, tidak bisa diubah lagi.", "warning")
        return redirect(url_for("opname.detail", oid=oid))

    detail_ids = request.form.getlist("detail_id[]")
    stok_fisiks = request.form.getlist("stok_fisik[]")

    for did, sf in zip(detail_ids, stok_fisiks):
        d = StokOpnameDetail.query.get(int(did)) if did.isdigit() else None
        if not d or d.header_id != o.id:
            continue
        sf = (sf or "").strip()
        d.stok_fisik = int(sf) if sf.isdigit() else None

    db.session.commit()
    flash("Progress hitung fisik disimpan.", "success")
    return redirect(url_for("opname.form", oid=oid))


@bp.route("/<int:oid>/finalize", methods=["POST"])
@login_required
@admin_required
def finalize(oid):
    o = StokOpname.query.get_or_404(oid)
    if o.status != StokOpname.STATUS_DRAFT:
        flash("Sesi opname ini sudah selesai.", "warning")
        return redirect(url_for("opname.detail", oid=oid))

    belum_dihitung = [d for d in o.details if d.stok_fisik is None]
    if belum_dihitung:
        flash(f"Masih ada {len(belum_dihitung)} barang yang belum dihitung fisiknya. Lengkapi dulu sebelum menyelesaikan opname.", "error")
        return redirect(url_for("opname.form", oid=oid))

    total_selisih = 0
    for d in o.details:
        if d.selisih != 0:
            d.barang.stok = d.stok_fisik
            total_selisih += 1

    o.status = StokOpname.STATUS_SELESAI
    o.diselesaikan_oleh = current_user.id
    o.selesai_at = now_wib()
    db.session.commit()
    log_audit("complete", "stok_opname", target=o.no_opname, detail=f"{total_selisih} barang disesuaikan stoknya")
    flash(f"Opname {o.no_opname} selesai. {total_selisih} barang mengalami penyesuaian stok.", "success")
    return redirect(url_for("opname.detail", oid=oid))


@bp.route("/<int:oid>/detail")
@login_required
@admin_required
def detail(oid):
    o = StokOpname.query.get_or_404(oid)
    return render_template("opname/detail.html", o=o)