from datetime import datetime, date
from functools import wraps
from flask import abort, request
from flask_login import current_user


# ---------------------------------------------------------------------------
# Date / time formatting (WIB)
# ---------------------------------------------------------------------------
def fmt_date(d=None):
    if d is None:
        d = date.today()
    if isinstance(d, datetime):
        d = d.date()
    if not d:
        return "-"
    bulan = [
        "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
        "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
    ]
    return f"{d.day:02d} {bulan[d.month - 1]} {d.year}"


def fmt_date_full(d=None):
    if d is None:
        d = date.today()
    if isinstance(d, datetime):
        d = d.date()
    if not d:
        return "-"
    bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    return f"{d.day:02d} {bulan[d.month - 1]} {d.year}"


def fmt_datetime(dt=None):
    if dt is None:
        dt = datetime.now()
    if not dt:
        return "-"
    return f"{fmt_date(dt)} {dt.strftime('%H:%M')} WIB"


def fmt_rupiah(n):
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        n = 0
    return "Rp " + f"{n:,.0f}".replace(",", ".")


def fmt_number(n):
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        n = 0
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def admin_required(f):
    return role_required("admin")(f)


def admin_or_kepala_required(f):
    return role_required("admin", "kepala")(f)


# ---------------------------------------------------------------------------
# Audit logging helper
# ---------------------------------------------------------------------------
def log_audit(aksi, modul, target="", detail=""):
    from extensions import db
    from app.models import AuditLog
    uname = current_user.username if current_user.is_authenticated else "system"
    uid = current_user.id if current_user.is_authenticated else None
    entry = AuditLog(
        user_id=uid,
        username=uname,
        aksi=aksi,
        modul=modul,
        target=str(target)[:160] if target else "",
        detail=detail,
    )
    db.session.add(entry)
    db.session.commit()


# ---------------------------------------------------------------------------
# Generate sequential numbers
# ---------------------------------------------------------------------------
def gen_no_permintaan():
    from extensions import db
    from app.models import Permintaan
    today = date.today()
    prefix = f"REQ/{today.strftime('%Y%m')}/"
    last = (
        db.session.query(Permintaan)
        .filter(Permintaan.no_permintaan.like(prefix + "%"))
        .order_by(Permintaan.id.desc())
        .first()
    )
    seq = 1
    if last and last.no_permintaan.startswith(prefix):
        try:
            seq = int(last.no_permintaan.rsplit("/", 1)[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:04d}"

def gen_no_opname():
    from extensions import db
    from app.models import StokOpname
    today = date.today()
    prefix = f"OPN/{today.strftime('%Y%m')}/"
    last = (
        db.session.query(StokOpname)
        .filter(StokOpname.no_opname.like(prefix + "%"))
        .order_by(StokOpname.id.desc())
        .first()
    )
    seq = 1
    if last and last.no_opname.startswith(prefix):
        try:
            seq = int(last.no_opname.rsplit("/", 1)[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:04d}"