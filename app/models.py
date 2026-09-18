from datetime import datetime, date
from zoneinfo import ZoneInfo
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager

WIB = ZoneInfo("Asia/Jakarta")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def now_wib():
    """Return the current datetime in WIB (Asia/Jakarta), regardless of the server's own timezone."""
    return datetime.now(WIB).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# User / Auth
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    nama = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")  # admin, kepala, staff
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=now_wib)

    unit = db.relationship("Unit", backref="users")

    # Role helpers
    ROLE_ADMIN = "admin"
    ROLE_KEPALA = "kepala"
    ROLE_STAFF = "staff"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_kepala(self):
        return self.role == self.ROLE_KEPALA

    @property
    def is_staff(self):
        return self.role == self.ROLE_STAFF

    @property
    def role_label(self):
        return {
            self.ROLE_ADMIN: "Admin Gudang",
            self.ROLE_KEPALA: "Kepala Unit",
            self.ROLE_STAFF: "Staff Unit",
        }.get(self.role, self.role)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    @property
    def is_active(self):
        return self.is_active_user

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


@login_manager.user_loader
def load_user(uid):
    try:
        return db.session.get(User, int(uid))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Master: Unit
# ---------------------------------------------------------------------------
class Unit(db.Model):
    __tablename__ = "units"

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(120), nullable=False)
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_wib)

    def __repr__(self):
        return f"<Unit {self.kode} {self.nama}>"


# ---------------------------------------------------------------------------
# Master: Kategori
# ---------------------------------------------------------------------------
class Kategori(db.Model):
    __tablename__ = "kategoris"

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(80), nullable=False)
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_wib)

    def __repr__(self):
        return f"<Kategori {self.kode} {self.nama}>"


# ---------------------------------------------------------------------------
# Master: Satuan
# ---------------------------------------------------------------------------
class Satuan(db.Model):
    __tablename__ = "satuans"

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, default=now_wib)

    def __repr__(self):
        return f"<Satuan {self.kode} {self.nama}>"


# ---------------------------------------------------------------------------
# Master: Barang
# ---------------------------------------------------------------------------
class Barang(db.Model):
    __tablename__ = "barangs"

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(30), unique=True, nullable=False, index=True)
    nama = db.Column(db.String(160), nullable=False, index=True)
    kategori_id = db.Column(db.Integer, db.ForeignKey("kategoris.id"), nullable=False)
    satuan_id = db.Column(db.Integer, db.ForeignKey("satuans.id"), nullable=False)
    harga_satuan = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    stok = db.Column(db.Integer, default=0, nullable=False)
    stok_min = db.Column(db.Integer, default=0, nullable=False)  # reorder point
    keterangan = db.Column(db.Text)
    is_aktif = db.Column(db.Boolean, default=True, nullable=False)  # <-- BARU
    created_at = db.Column(db.DateTime, default=now_wib)
    updated_at = db.Column(db.DateTime, default=now_wib, onupdate=now_wib)

    kategori = db.relationship("Kategori", backref="barangs")
    satuan = db.relationship("Satuan", backref="barangs")

    @property
    def nilai_stok(self):
        return (self.stok or 0) * (self.harga_satuan or 0)

    @property
    def status_stok(self):
        if self.stok <= 0:
            return "habis"
        if self.stok <= self.stok_min:
            return "minimum"
        return "aman"

    def __repr__(self):
        return f"<Barang {self.kode} {self.nama} stok={self.stok}>"
    
# ---------------------------------------------------------------------------
# Master: Supplier
# ---------------------------------------------------------------------------
class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(160), nullable=False)
    kontak = db.Column(db.String(120))
    alamat = db.Column(db.Text)
    telepon = db.Column(db.String(40))
    email = db.Column(db.String(120))
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_wib)

    def __repr__(self):
        return f"<Supplier {self.kode} {self.nama}>"


# ---------------------------------------------------------------------------
# Transaksi: Barang Masuk
# ---------------------------------------------------------------------------
class BarangMasuk(db.Model):
    __tablename__ = "barang_masuk"

    id = db.Column(db.Integer, primary_key=True)
    no_faktur = db.Column(db.String(60), nullable=False)
    tanggal = db.Column(db.Date, nullable=False, default=date.today, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    catatan = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=now_wib)

    supplier = db.relationship("Supplier", backref="barang_masuk_list")
    user = db.relationship("User", backref="barang_masuk_list")
    details = db.relationship(
        "BarangMasukDetail", backref="header", cascade="all, delete-orphan"
    )

    @property
    def total_nilai(self):
        return sum((d.qty or 0) * (d.harga or 0) for d in self.details)


class BarangMasukDetail(db.Model):
    __tablename__ = "barang_masuk_detail"

    id = db.Column(db.Integer, primary_key=True)
    header_id = db.Column(db.Integer, db.ForeignKey("barang_masuk.id"), nullable=False)
    barang_id = db.Column(db.Integer, db.ForeignKey("barangs.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    harga = db.Column(db.Numeric(14, 2), default=0, nullable=False)

    barang = db.relationship("Barang")


# ---------------------------------------------------------------------------
# Transaksi: Permintaan & Distribusi (Barang Keluar)
# ---------------------------------------------------------------------------
class Permintaan(db.Model):
    __tablename__ = "permintaan"

    STATUS_DIAJUKAN = "diajukan"
    STATUS_DISETUJUI = "disetujui"
    STATUS_DITOLAK = "ditolak"
    STATUS_DIPROSES = "diproses"
    STATUS_SELESAI = "selesai"

    STATUS_ORDER = [
        STATUS_DIAJUKAN,
        STATUS_DISETUJUI,
        STATUS_DIPROSES,
        STATUS_SELESAI,
        STATUS_DITOLAK,
    ]

    id = db.Column(db.Integer, primary_key=True)
    no_permintaan = db.Column(db.String(40), unique=True, nullable=False, index=True)
    tanggal = db.Column(db.Date, nullable=False, default=date.today, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False)
    diajukan_oleh = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_DIAJUKAN)
    catatan = db.Column(db.Text)
    alasan_tolak = db.Column(db.Text)
    disetujui_oleh = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    diproses_oleh = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    tanggal_disetujui = db.Column(db.DateTime, nullable=True)
    tanggal_diproses = db.Column(db.DateTime, nullable=True)
    tanggal_selesai = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=now_wib)

    unit = db.relationship("Unit")
    pengaju = db.relationship("User", foreign_keys=[diajukan_oleh])
    approver = db.relationship("User", foreign_keys=[disetujui_oleh])
    processor = db.relationship("User", foreign_keys=[diproses_oleh])
    details = db.relationship(
        "PermintaanDetail", backref="header", cascade="all, delete-orphan"
    )

    @property
    def status_label(self):
        return {
            self.STATUS_DIAJUKAN: "Diajukan",
            self.STATUS_DISETUJUI: "Disetujui",
            self.STATUS_DITOLAK: "Ditolak",
            self.STATUS_DIPROSES: "Diproses",
            self.STATUS_SELESAI: "Selesai",
        }.get(self.status, self.status)

    @property
    def status_color(self):
        return {
            self.STATUS_DIAJUKAN: "amber",
            self.STATUS_DISETUJUI: "blue",
            self.STATUS_DITOLAK: "rose",
            self.STATUS_DIPROSES: "violet",
            self.STATUS_SELESAI: "emerald",
        }.get(self.status, "slate")

class PermintaanDetail(db.Model):
    __tablename__ = "permintaan_detail"

    id = db.Column(db.Integer, primary_key=True)
    header_id = db.Column(db.Integer, db.ForeignKey("permintaan.id"), nullable=False)
    barang_id = db.Column(db.Integer, db.ForeignKey("barangs.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    qty_disetujui = db.Column(db.Integer, nullable=True)  # <-- BARU: diisi saat approval, None = belum diproses
    qty_diproses = db.Column(db.Integer, default=0, nullable=False)
    catatan = db.Column(db.Text)

    barang = db.relationship("Barang")

    @property
    def qty_efektif(self):
        """Qty yang jadi acuan distribusi: qty_disetujui kalau sudah diisi, kalau belum fallback ke qty diminta."""
        return self.qty_disetujui if self.qty_disetujui is not None else self.qty
    
# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------
class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=now_wib, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username = db.Column(db.String(64))
    aksi = db.Column(db.String(40), nullable=False)  # create/update/delete/approve/reject/process
    modul = db.Column(db.String(40), nullable=False)  # barang/supplier/permintaan/barang_masuk/user
    target = db.Column(db.String(160))
    detail = db.Column(db.Text)

    user = db.relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AuditLog {self.timestamp} {self.username} {self.aksi} {self.modul}>"

# ---------------------------------------------------------------------------
# Stok Opname
# ---------------------------------------------------------------------------
class StokOpname(db.Model):
    __tablename__ = "stok_opname"

    STATUS_DRAFT = "draft"
    STATUS_SELESAI = "selesai"

    id = db.Column(db.Integer, primary_key=True)
    no_opname = db.Column(db.String(40), unique=True, nullable=False, index=True)
    tanggal = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default=STATUS_DRAFT)
    dibuat_oleh = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    diselesaikan_oleh = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=now_wib)
    selesai_at = db.Column(db.DateTime, nullable=True)

    pembuat = db.relationship("User", foreign_keys=[dibuat_oleh])
    penyelesai = db.relationship("User", foreign_keys=[diselesaikan_oleh])
    details = db.relationship("StokOpnameDetail", backref="header", cascade="all, delete-orphan")

    @property
    def jumlah_selisih(self):
        return sum(1 for d in self.details if d.stok_fisik is not None and d.selisih != 0)

    @property
    def jumlah_belum_dihitung(self):
        return sum(1 for d in self.details if d.stok_fisik is None)


class StokOpnameDetail(db.Model):
    __tablename__ = "stok_opname_detail"

    id = db.Column(db.Integer, primary_key=True)
    header_id = db.Column(db.Integer, db.ForeignKey("stok_opname.id"), nullable=False)
    barang_id = db.Column(db.Integer, db.ForeignKey("barangs.id"), nullable=False)
    stok_sistem = db.Column(db.Integer, nullable=False)  # snapshot saat opname dibuat
    stok_fisik = db.Column(db.Integer, nullable=True)    # diisi user, None = belum dihitung

    barang = db.relationship("Barang")

    @property
    def selisih(self):
        if self.stok_fisik is None:
            return 0
        return self.stok_fisik - self.stok_sistem