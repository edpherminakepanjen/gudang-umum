from datetime import datetime, date, timedelta
from collections import defaultdict
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import db
from app.models import (
    Barang, Permintaan, PermintaanDetail, BarangMasuk, BarangMasukDetail,
    AuditLog, Unit,
)

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    # KPIs
    total_jenis = db.session.query(db.func.count(Barang.id)).scalar() or 0
    total_nilai = db.session.query(
        db.func.coalesce(db.func.sum(Barang.stok * Barang.harga_satuan), 0)
    ).scalar() or 0

    if current_user.is_admin:
        pending_count = db.session.query(db.func.count(Permintaan.id)).filter(
            Permintaan.status == Permintaan.STATUS_DIAJUKAN
        ).scalar() or 0
        below_min = db.session.query(db.func.count(Barang.id)).filter(
            Barang.stok <= Barang.stok_min
        ).scalar() or 0
    else:
        pending_count = db.session.query(db.func.count(Permintaan.id)).filter(
            Permintaan.diajukan_oleh == current_user.id,
            Permintaan.status.in_([Permintaan.STATUS_DIAJUKAN, Permintaan.STATUS_DISETUJUI]),
        ).scalar() or 0
        below_min = 0

    # Monthly trend (masuk vs keluar) — last 6 months
    today = date.today()
    trend_labels = []
    masuk_data = []
    keluar_data = []
    bulan_nama = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

    for i in range(6):
        y = today.year
        m = today.month - 5 + i
        while m <= 0:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        start = date(y, m, 1)
        end = date(y + (1 if m == 12 else 0), (m % 12) + 1, 1)
        trend_labels.append(f"{bulan_nama[m-1]} {str(y)[-2:]}")

        qty_masuk = db.session.query(db.func.coalesce(db.func.sum(BarangMasukDetail.qty), 0)).join(
            BarangMasuk
        ).filter(BarangMasuk.tanggal >= start, BarangMasuk.tanggal < end).scalar() or 0
        masuk_data.append(int(qty_masuk))

        qty_keluar = db.session.query(db.func.coalesce(db.func.sum(PermintaanDetail.qty_diproses), 0)).join(
            Permintaan
        ).filter(
            Permintaan.tanggal >= start,
            Permintaan.tanggal < end,
            Permintaan.status.in_([Permintaan.STATUS_SELESAI, Permintaan.STATUS_DIPROSES]),
        ).scalar() or 0
        keluar_data.append(int(qty_keluar))

    # Top requested items (admin) or recent activity
    # Filtered to diproses/selesai only, consistent with the trend chart below —
    # so this reflects barang yang benar-benar sudah keluar, bukan yang masih diajukan/ditolak
    if current_user.is_admin:
        top_items = (
            db.session.query(
                Barang.nama,
                db.func.coalesce(db.func.sum(PermintaanDetail.qty_diproses), 0).label("total"),
            )
            .join(PermintaanDetail, PermintaanDetail.barang_id == Barang.id)
            .join(Permintaan, PermintaanDetail.header_id == Permintaan.id)
            .filter(Permintaan.status.in_([Permintaan.STATUS_DIPROSES, Permintaan.STATUS_SELESAI]))
            .group_by(Barang.id, Barang.nama)
            .order_by(db.desc("total"))
            .limit(7)
            .all()
        )
    else:
        top_items = []

    # Recent activity feed
    if current_user.is_admin:
        recent_permintaan = Permintaan.query.order_by(Permintaan.id.desc()).limit(5).all()
        recent_masuk = BarangMasuk.query.order_by(BarangMasuk.id.desc()).limit(5).all()
    else:
        recent_permintaan = (
            Permintaan.query.filter_by(diajukan_oleh=current_user.id)
            .order_by(Permintaan.id.desc()).limit(5).all()
        )
        recent_masuk = []

    # Low stock items (admin)
    low_stock = []
    if current_user.is_admin:
        low_stock = Barang.query.filter(Barang.stok <= Barang.stok_min).order_by(Barang.stok.asc()).limit(8).all()

    return render_template(
        "dashboard.html",
        total_jenis=total_jenis,
        total_nilai=total_nilai,
        pending_count=pending_count,
        below_min=below_min,
        trend_labels=trend_labels,
        masuk_data=masuk_data,
        keluar_data=keluar_data,
        top_items=top_items,
        recent_permintaan=recent_permintaan,
        recent_masuk=recent_masuk,
        low_stock=low_stock,
    )
