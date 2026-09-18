from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from extensions import db
from app.models import AuditLog
from app.utils import admin_required

bp = Blueprint("audit", __name__)


@bp.route("/")
@login_required
@admin_required
def index():
    modul = (request.args.get("modul") or "").strip()
    aksi = (request.args.get("aksi") or "").strip()
    query = AuditLog.query
    if modul:
        query = query.filter_by(modul=modul)
    if aksi:
        query = query.filter_by(aksi=aksi)
    items = query.order_by(AuditLog.id.desc()).limit(200).all()
    modul_list = ["barang", "kategori", "satuan", "supplier", "unit", "barang_masuk", "permintaan", "user", "auth", "stok_opname"]
    aksi_list = ["create", "update", "delete", "approve", "reject", "process", "complete", "cancel", "activate", "deactivate", "import", "login", "logout"]
    return render_template("audit.html", items=items, modul_list=modul_list, aksi_list=aksi_list,
                           mf=modul, af=aksi)
