from collections import defaultdict
from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import db
from app.models import Barang, Permintaan, PermintaanDetail, BarangMasuk, BarangMasukDetail, Unit
from app.utils import admin_required

bp = Blueprint("monitoring", __name__)


@bp.route("/")
@login_required
@admin_required
def index():
    all_barang = Barang.query.order_by(Barang.kode).all()

    below_min = [b for b in all_barang if b.stok <= b.stok_min]
    aman = [b for b in all_barang if b.stok > b.stok_min]

    # Usage trend: last 6 months qty keluar per month
    today = date.today()
    bulan_nama = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    trend_labels = []
    trend_keluar = []
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
        qty = db.session.query(db.func.coalesce(db.func.sum(PermintaanDetail.qty_diproses), 0)).join(
            Permintaan
        ).filter(
            Permintaan.tanggal >= start,
            Permintaan.tanggal < end,
            Permintaan.status.in_([Permintaan.STATUS_SELESAI, Permintaan.STATUS_DIPROSES]),
        ).scalar() or 0
        trend_keluar.append(int(qty))

    # Top per unit (qty)
    top_unit = (
        db.session.query(
            Unit.nama.label("unit"),
            db.func.coalesce(db.func.sum(PermintaanDetail.qty_diproses), 0).label("total"),
        )
        .select_from(Permintaan)
        .join(PermintaanDetail, PermintaanDetail.header_id == Permintaan.id)
        .join(Unit, Permintaan.unit_id == Unit.id)
        .group_by(Unit.id, Unit.nama)
        .order_by(db.desc("total"))
        .limit(6)
        .all()
    )

    return render_template(
        "monitoring.html",
        below_min=below_min,
        aman_count=len(aman),
        below_min_count=len(below_min),
        trend_labels=trend_labels,
        trend_keluar=trend_keluar,
        top_unit=top_unit,
    )
