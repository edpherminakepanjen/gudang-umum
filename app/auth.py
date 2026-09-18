from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.utils import log_audit

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active_user:
                flash("Akun Anda dinonaktifkan. Hubungi Admin Gudang.", "error")
                return render_template("login.html")
            login_user(user, remember=True)
            log_audit("login", "auth", target=user.username, detail="Login berhasil")
            next_page = request.args.get("next")
            if next_page and not next_page.startswith("/"):
                next_page = None
            flash(f"Selamat datang, {user.nama}!", "success")
            return redirect(next_page or url_for("dashboard.index"))
        flash("Username atau password salah.", "error")

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    log_audit("logout", "auth", target=current_user.username, detail="Logout")
    logout_user()
    flash("Anda telah keluar dari sistem.", "info")
    return redirect(url_for("auth.login"))
