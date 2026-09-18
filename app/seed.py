from extensions import db
from app.models import User


def seed_if_empty():
    """
    Seed AWAL untuk production: cuma bikin 1 akun admin, supaya bisa login
    pertama kali. TIDAK ada data contoh (unit/kategori/satuan/barang/supplier/
    transaksi dummy) -- semua data operasional diisi manual lewat aplikasi
    setelah login.

    Hanya jalan kalau tabel users masih benar-benar kosong (aman dipanggil
    berkali-kali setiap aplikasi start -- lihat app/__init__.py).
    """
    if User.query.first():
        return

    admin = User(
        username="admin",
        nama="Administrator",
        email="",
        role=User.ROLE_ADMIN,
        is_active_user=True,
    )
    # ⚠️ GANTI PASSWORD INI SEGERA setelah berhasil login pertama kali.
    admin.set_password("ganti_password_ini")
    db.session.add(admin)
    db.session.commit()