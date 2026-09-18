from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from app.models import User, Unit
from app.utils import admin_required, log_audit

bp = Blueprint("users", __name__)


@bp.route("/")
@login_required
@admin_required
def index():
    items = User.query.order_by(User.role, User.nama).all()
    units = Unit.query.order_by(Unit.nama).all()
    return render_template("users.html", items=items, units=units)


@bp.route("/create", methods=["POST"])
@login_required
@admin_required
def create():
    username = (request.form.get("username") or "").strip().lower()
    nama = (request.form.get("nama") or "").strip()
    email = (request.form.get("email") or "").strip()
    role = (request.form.get("role") or "staff").strip()
    unit_id = request.form.get("unit_id", type=int)
    password = (request.form.get("password") or "").strip()

    if not username or not nama or not password:
        flash("Username, nama, dan password wajib diisi.", "error")
        return redirect(url_for("users.index"))
    if len(password) < 6:
        flash("Password minimal 6 karakter.", "error")
        return redirect(url_for("users.index"))
    if role not in ("admin", "kepala", "staff"):
        flash("Role tidak valid.", "error")
        return redirect(url_for("users.index"))
    if role in ("kepala", "staff") and not unit_id:
        flash("Role Kepala Unit dan Staff Unit wajib memilih unit.", "error")
        return redirect(url_for("users.index"))
    if User.query.filter_by(username=username).first():
        flash("Username sudah dipakai.", "error")
        return redirect(url_for("users.index"))

    u = User(username=username, nama=nama, email=email, role=role,
             unit_id=unit_id if unit_id else None)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    log_audit("create", "user", target=f"{username} ({role})")
    flash("User ditambahkan.", "success")
    return redirect(url_for("users.index"))


@bp.route("/<int:uid>/edit", methods=["POST"])
@login_required
@admin_required
def edit(uid):
    u = User.query.get_or_404(uid)

    role = (request.form.get("role") or u.role).strip()
    if role not in ("admin", "kepala", "staff"):
        flash("Role tidak valid.", "error")
        return redirect(url_for("users.index"))

    unit_id = request.form.get("unit_id", type=int) or None
    if role in ("kepala", "staff") and not unit_id:
        flash("Role Kepala Unit dan Staff Unit wajib memilih unit.", "error")
        return redirect(url_for("users.index"))

    new_pw = (request.form.get("password") or "").strip()
    if new_pw and len(new_pw) < 6:
        flash("Password baru minimal 6 karakter.", "error")
        return redirect(url_for("users.index"))

    u.nama = (request.form.get("nama") or "").strip() or u.nama
    u.email = (request.form.get("email") or "").strip()
    u.role = role
    u.unit_id = unit_id
    u.is_active_user = request.form.get("is_active") == "on"
    if new_pw:
        u.set_password(new_pw)
    db.session.commit()
    log_audit("update", "user", target=u.username)
    flash("User diperbarui.", "success")
    return redirect(url_for("users.index"))


@bp.route("/<int:uid>/delete", methods=["POST"])
@login_required
@admin_required
def delete(uid):
    u = User.query.get_or_404(uid)
    if u.id == current_user.id:
        flash("Anda tidak bisa menghapus akun sendiri.", "error")
        return redirect(url_for("users.index"))
    db.session.delete(u)
    db.session.commit()
    log_audit("delete", "user", target=u.username)
    flash("User dihapus.", "info")
    return redirect(url_for("users.index"))
