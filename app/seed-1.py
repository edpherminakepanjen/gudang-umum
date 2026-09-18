from datetime import date, timedelta
from extensions import db
from app.models import (
    User, Unit, Kategori, Satuan, Barang, Supplier,
    BarangMasuk, BarangMasukDetail, Permintaan, PermintaanDetail,
)


def seed_if_empty():
    """Seed sample data only if the database is empty."""
    if User.query.first():
        return

    # ----- Units -----
    units = [
        Unit(kode="IGD", nama="Instalasi Gawat Darurat"),
        Unit(kode="NICU", nama="Neonatal Intensive Care Unit"),
        Unit(kode="OK", nama="Kamar Operasi"),
        Unit(kode="ITRS", nama="IT RS Hermina"),
        Unit(kode="ADM", nama="Administrasi & Keuangan"),
        Unit(kode="LAB", nama="Laboratorium"),
    ]
    db.session.add_all(units)
    db.session.flush()

    # ----- Kategori -----
    kategoris = [
        Kategori(kode="ATK", nama="Alat Tulis Kantor"),
        Kategori(kode="RT", nama="Rumah Tangga"),
        Kategori(kode="CET", nama="Cetakan"),
        Kategori(kode="LAIN", nama="Lain-lain"),
    ]
    db.session.add_all(kategoris)
    db.session.flush()

    # ----- Satuan -----
    satuans = [
        Satuan(kode="pcs", nama="Pieces"),
        Satuan(kode="box", nama="Box"),
        Satuan(kode="rim", nama="Rim"),
        Satuan(kode="lusin", nama="Lusin"),
        Satuan(kode="rol", nama="Rol"),
        Satuan(kode="pak", nama="Pak"),
        Satuan(kode="unit", nama="Unit"),
    ]
    db.session.add_all(satuans)
    db.session.flush()

    kat_atk = next(k for k in kategoris if k.kode == "ATK")
    kat_rt = next(k for k in kategoris if k.kode == "RT")
    kat_cet = next(k for k in kategoris if k.kode == "CET")
    kat_lain = next(k for k in kategoris if k.kode == "LAIN")
    s_pcs = next(s for s in satuans if s.kode == "pcs")
    s_box = next(s for s in satuans if s.kode == "box")
    s_rim = next(s for s in satuans if s.kode == "rim")
    s_lusin = next(s for s in satuans if s.kode == "lusin")
    s_rol = next(s for s in satuans if s.kode == "rol")
    s_pak = next(s for s in satuans if s.kode == "pak")
    s_unit = next(s for s in satuans if s.kode == "unit")

    # ----- Barang -----
    barangs = [
        Barang(kode="ATK-001", nama="Kertas A4 70gsm", kategori_id=kat_atk.id, satuan_id=s_rim.id,
               harga_satuan=45000, stok=25, stok_min=10),
        Barang(kode="ATK-002", nama="Pulpen Standard AE7", kategori_id=kat_atk.id, satuan_id=s_lusin.id,
               harga_satuan=24000, stok=8, stok_min=5),
        Barang(kode="ATK-003", nama="Tinta Printer Epson Hitam", kategori_id=kat_atk.id, satuan_id=s_pcs.id,
               harga_satuan=85000, stok=3, stok_min=5),
        Barang(kode="ATK-004", nama="Map Plastik Snelhecter", kategori_id=kat_atk.id, satuan_id=s_pak.id,
               harga_satuan=15000, stok=30, stok_min=10),
        Barang(kode="RT-001", nama="Tissue Roll 1 ply", kategori_id=kat_rt.id, satuan_id=s_box.id,
               harga_satuan=35000, stok=40, stok_min=15),
        Barang(kode="RT-002", nama="Sabun Cair Antiseptik 5L", kategori_id=kat_rt.id, satuan_id=s_pcs.id,
               harga_satuan=55000, stok=12, stok_min=8),
        Barang(kode="RT-003", nama="Sarung Tangan Lateks", kategori_id=kat_rt.id, satuan_id=s_box.id,
               harga_satuan=120000, stok=2, stok_min=6),
        Barang(kode="RT-004", nama="Plastik Sampah Hitam 60x80", kategori_id=kat_rt.id, satuan_id=s_rol.id,
               harga_satuan=28000, stok=15, stok_min=8),
        Barang(kode="CET-001", nama="Kwitansi Kosong 2 lembar", kategori_id=kat_cet.id, satuan_id=s_pak.id,
               harga_satuan=18000, stok=50, stok_min=20),
        Barang(kode="CET-002", nama="Formulir Rawat Jalan", kategori_id=kat_cet.id, satuan_id=s_pak.id,
               harga_satuan=22000, stok=35, stok_min=15),
        Barang(kode="LAIN-001", nama="Baterai AA (pack 4)", kategori_id=kat_lain.id, satuan_id=s_pcs.id,
               harga_satuan=20000, stok=0, stok_min=5),
        Barang(kode="LAIN-002", nama="Lampu LED 18W", kategori_id=kat_lain.id, satuan_id=s_pcs.id,
               harga_satuan=35000, stok=6, stok_min=4),
    ]
    db.session.add_all(barangs)
    db.session.flush()

    # ----- Supplier -----
    suppliers = [
        Supplier(kode="SUP-001", nama="PT Sumber Rezeki", kontak="Budi Santoso",
                 telepon="081234567890", alamat="Jl. Merdeka No. 12, Kepanjen"),
        Supplier(kode="SUP-002", nama="CV Maju Jaya ATK", kontak="Siti Aminah",
                 telepon="081298765432", alamat="Jl. Diponegoro No. 45, Malang"),
        Supplier(kode="SUP-003", nama="PT Bersih Sehat", kontak="Agus Widodo",
                 telepon="085711112222", alamat="Jl. Ahmad Yani No. 78, Kepanjen"),
    ]
    db.session.add_all(suppliers)
    db.session.flush()

    # ----- Users -----
    unit_igr = next(u for u in units if u.kode == "IGD")
    unit_it = next(u for u in units if u.kode == "ITRS")
    unit_adm = next(u for u in units if u.kode == "ADM")

    users = [
        User(username="admin", nama="Admin Gudang", email="admin@rsh-kepanjen.id",
             role="admin", is_active_user=True),
        User(username="kepala", nama="dr. Rina Wijaya", email="rina@rsh-kepanjen.id",
             role="kepala", is_active_user=True, unit_id=unit_igr.id),
        User(username="staff", nama="Dewi Lestari", email="dewi@rsh-kepanjen.id",
             role="staff", is_active_user=True, unit_id=unit_igr.id),
        User(username="kepala_it", nama="Budi Hartono", email="budi@rsh-kepanjen.id",
             role="kepala", is_active_user=True, unit_id=unit_it.id),
        User(username="staff_adm", nama="Nur Aini", email="nur@rsh-kepanjen.id",
             role="staff", is_active_user=True, unit_id=unit_adm.id),
    ]
    for u in users:
        u.set_password("password123")
    db.session.add_all(users)
    db.session.flush()

    admin_user = users[0]
    kepala_user = users[1]
    staff_user = users[2]

    # ----- Barang Masuk -----
    bm1 = BarangMasuk(no_faktur="PO-2026-001", tanggal=date.today() - timedelta(days=20),
                      supplier_id=suppliers[0].id, user_id=admin_user.id,
                      catatan="Pembelian rutin bulanan")
    db.session.add(bm1)
    db.session.flush()
    db.session.add_all([
        BarangMasukDetail(header_id=bm1.id, barang_id=barangs[0].id, qty=20, harga=45000),
        BarangMasukDetail(header_id=bm1.id, barang_id=barangs[4].id, qty=30, harga=35000),
        BarangMasukDetail(header_id=bm1.id, barang_id=barangs[8].id, qty=40, harga=18000),
    ])

    bm2 = BarangMasuk(no_faktur="PO-2026-002", tanggal=date.today() - timedelta(days=10),
                      supplier_id=suppliers[1].id, user_id=admin_user.id)
    db.session.add(bm2)
    db.session.flush()
    db.session.add_all([
        BarangMasukDetail(header_id=bm2.id, barang_id=barangs[1].id, qty=5, harga=24000),
        BarangMasukDetail(header_id=bm2.id, barang_id=barangs[3].id, qty=20, harga=15000),
    ])

    bm3 = BarangMasuk(no_faktur="PO-2026-003", tanggal=date.today() - timedelta(days=3),
                      supplier_id=suppliers[2].id, user_id=admin_user.id)
    db.session.add(bm3)
    db.session.flush()
    db.session.add_all([
        BarangMasukDetail(header_id=bm3.id, barang_id=barangs[5].id, qty=10, harga=55000),
        BarangMasukDetail(header_id=bm3.id, barang_id=barangs[6].id, qty=4, harga=120000),
    ])

    # ----- Permintaan -----
    # 1. Disetujui & diproses (selesai)
    p1 = Permintaan(no_permintaan="REQ/202609/0001", tanggal=date.today() - timedelta(days=15),
                    unit_id=unit_igr.id, diajukan_oleh=staff_user.id,
                    status=Permintaan.STATUS_SELESAI, catatan="Untuk operasional IGD",
                    disetujui_oleh=kepala_user.id, diproses_oleh=admin_user.id,
                    tanggal_disetujui=db.func.now() if False else None)
    db.session.add(p1)
    db.session.flush()
    db.session.add_all([
        PermintaanDetail(header_id=p1.id, barang_id=barangs[0].id, qty=3, qty_diproses=3),
        PermintaanDetail(header_id=p1.id, barang_id=barangs[4].id, qty=5, qty_diproses=5),
    ])
    # Reduce stock for processed permintaan
    barangs[0].stok -= 3
    barangs[4].stok -= 5

    # 2. Diajukan (pending)
    p2 = Permintaan(no_permintaan="REQ/202609/0002", tanggal=date.today() - timedelta(days=2),
                    unit_id=unit_adm.id, diajukan_oleh=users[4].id,
                    status=Permintaan.STATUS_DIAJUKAN, catatan="Stok habis di administrasi")
    db.session.add(p2)
    db.session.flush()
    db.session.add_all([
        PermintaanDetail(header_id=p2.id, barang_id=barangs[8].id, qty=5),
        PermintaanDetail(header_id=p2.id, barang_id=barangs[9].id, qty=3),
    ])

    # 3. Disetujui (menunggu proses)
    p3 = Permintaan(no_permintaan="REQ/202609/0003", tanggal=date.today() - timedelta(days=5),
                    unit_id=unit_igr.id, diajukan_oleh=staff_user.id,
                    status=Permintaan.STATUS_DISETUJUI, catatan="Kebutuhan emergency",
                    disetujui_oleh=kepala_user.id)
    db.session.add(p3)
    db.session.flush()
    db.session.add_all([
        PermintaanDetail(header_id=p3.id, barang_id=barangs[5].id, qty=2),
        PermintaanDetail(header_id=p3.id, barang_id=barangs[1].id, qty=2),
    ])

    db.session.commit()
