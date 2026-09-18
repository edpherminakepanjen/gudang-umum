from flask import Flask
from config import Config
from extensions import init_extensions, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    init_extensions(app)

    # Jinja globals
    from app.utils import (
        fmt_date, fmt_date_full, fmt_datetime, fmt_rupiah, fmt_number,
    )
    app.jinja_env.globals.update(
        fmt_date=fmt_date,
        fmt_date_full=fmt_date_full,
        fmt_datetime=fmt_datetime,
        fmt_rupiah=fmt_rupiah,
        fmt_number=fmt_number,
        app_name=app.config["APP_NAME"],
        app_full_name=app.config["APP_FULL_NAME"],
        app_short=app.config["APP_SHORT"],
        hospital=app.config["HOSPITAL"],
        footer_line=app.config["FOOTER_LINE"],
        powered_by=app.config["POWERED_BY"],
    )

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.master import bp as master_bp
    app.register_blueprint(master_bp, url_prefix="/master")

    from app.barang_masuk import bp as bm_bp
    app.register_blueprint(bm_bp, url_prefix="/barang-masuk")

    from app.permintaan import bp as permintaan_bp
    app.register_blueprint(permintaan_bp, url_prefix="/permintaan")

    from app.monitoring import bp as monitoring_bp
    app.register_blueprint(monitoring_bp, url_prefix="/monitoring")

    from app.laporan import bp as laporan_bp
    app.register_blueprint(laporan_bp, url_prefix="/laporan")

    from app.audit import bp as audit_bp
    app.register_blueprint(audit_bp, url_prefix="/audit")

    from app.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix="/users")

    from app.opname import bp as opname_bp
    app.register_blueprint(opname_bp, url_prefix="/opname")

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("error.html", code=403,
                               message="Anda tidak memiliki akses ke halaman ini."), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("error.html", code=404,
                               message="Halaman yang Anda cari tidak ditemukan."), 404

    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        if not current_user.is_authenticated:
            return {"notif_count": 0, "notif_items": []}

        from app.models import Permintaan

        if current_user.is_admin:
            q = Permintaan.query.filter(
                Permintaan.status.in_([Permintaan.STATUS_DIAJUKAN, Permintaan.STATUS_DISETUJUI])
            )
        elif current_user.is_kepala:
            q = Permintaan.query.filter(
                Permintaan.status == Permintaan.STATUS_DIAJUKAN,
                Permintaan.unit_id == current_user.unit_id,
                Permintaan.diajukan_oleh != current_user.id,
            )
        else:
            q = None

        if q is None:
            return {"notif_count": 0, "notif_items": []}

        items = q.order_by(Permintaan.id.desc()).limit(5).all()
        count = q.count()

        notif_items = []
        for p in items:
            if p.status == Permintaan.STATUS_DIAJUKAN:
                pesan = f"Menunggu persetujuan — {p.unit.nama}"
            else:
                pesan = f"Disetujui, menunggu diproses — {p.unit.nama}"
            notif_items.append({"id": p.id, "no_permintaan": p.no_permintaan, "pesan": pesan})

        return {"notif_count": count, "notif_items": notif_items}

    with app.app_context():
        db.create_all()
        from app.seed import seed_if_empty
        seed_if_empty()

    return app


app = create_app()
