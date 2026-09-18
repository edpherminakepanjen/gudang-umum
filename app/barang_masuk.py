from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from app.models import BarangMasuk, BarangMasukDetail, Barang, Supplier
from app.utils import admin_required, log_audit

bp = Blueprint("barang_masuk", __name__)


@bp.route("/")
@login_required
@admin_required
def index():
    q = (request.args.get("q") or "").strip()
    query = BarangMasuk.query
    if q:
        query = query.filter(
            db.or_(BarangMasuk.no_faktur.ilike(f"%{q}%"),)
        )
    items = query.order_by(BarangMasuk.id.desc()).all()
    return render_template("barang_masuk/index.html", items=items, q=q)


@bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    suppliers = Supplier.query.order_by(Supplier.nama).all()
    barangs = Barang.query.filter_by(is_aktif=True).order_by(Barang.nama).all()
    if request.method == "POST":
        no_faktur = (request.form.get("no_faktur") or "").strip()
        tanggal = request.form.get("tanggal") or date.today().isoformat()
        supplier_id = request.form.get("supplier_id", type=int)
        catatan = (request.form.get("catatan") or "").strip()
        if not no_faktur or not supplier_id:
            flash("Nomor faktur dan supplier wajib diisi.", "error")
            return redirect(url_for("barang_masuk.create"))

        # Parse detail rows
        barang_ids = request.form.getlist("barang_id[]")
        qtys = request.form.getlist("qty[]")
        hargas = request.form.getlist("harga[]")
        if not barang_ids or not any(int(q) > 0 for q in qtys if q.isdigit()):
            flash("Minimal satu item barang harus diisi.", "error")
            return redirect(url_for("barang_masuk.create"))

        bm = BarangMasuk(
            no_faktur=no_faktur,
            tanggal=date.fromisoformat(tanggal) if isinstance(tanggal, str) else tanggal,
            supplier_id=supplier_id,
            catatan=catatan,
            user_id=current_user.id,
        )
        db.session.add(bm)
        db.session.flush()  # get bm.id

        for bid, q, h in zip(barang_ids, qtys, hargas):
            if not bid:
                continue
            qty = int(q) if q.isdigit() else 0
            if qty <= 0:
                continue
            harga = float(h) if h else 0
            detail = BarangMasukDetail(
                header_id=bm.id, barang_id=int(bid),
                qty=qty, harga=harga,
            )
            db.session.add(detail)
            # increase stock
            b = db.session.get(Barang, int(bid))
            if b:
                b.stok += qty

        db.session.commit()
        log_audit("create", "barang_masuk", target=f"{no_faktur} ({len(barang_ids)} item)")
        flash("Barang masuk berhasil dicatat. Stok otomatis bertambah.", "success")
        return redirect(url_for("barang_masuk.index"))

    return render_template("barang_masuk/form.html", suppliers=suppliers,
                           barangs=barangs, today=date.today().isoformat())


@bp.route("/<int:bid>")
@login_required
@admin_required
def detail(bid):
    bm = BarangMasuk.query.get_or_404(bid)
    return render_template("barang_masuk/detail.html", bm=bm)
