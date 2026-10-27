import sqlite3
import os
import pandas as pd
from src.config import DB_PATH

def get_connection():
    """Returns a sqlite3 connection to the local database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def database_exists() -> bool:
    """Helper to check if the database file exists and contains TPS records."""
    if not DB_PATH.exists():
        return False
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_partisipasi_tps'")
            if not cursor.fetchone():
                return False
            cursor.execute("SELECT COUNT(*) FROM data_partisipasi_tps")
            count = cursor.fetchone()[0]
            return count >= 1000
    except Exception:
        return False

def init_database():
    """Initializes the database schema using the schema.sql file."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    schema_path = DB_PATH.parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
    with get_connection() as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()

def seed_kecamatan():
    """Seeds default kecamatan list into the kecamatan table."""
    default_kecamatan = [
        "BANJARMASIN SELATAN",
        "BANJARMASIN TIMUR",
        "BANJARMASIN BARAT",
        "BANJARMASIN TENGAH",
        "BANJARMASIN UTARA"
    ]
    with get_connection() as conn:
        cursor = conn.cursor()
        for name in default_kecamatan:
            cursor.execute("""
                INSERT OR IGNORE INTO kecamatan (nama_kecamatan) VALUES (?)
            """, (name.upper(),))
        conn.commit()

def get_kecamatan_id_by_name(conn, name: str) -> int:
    """Finds or inserts a kecamatan by name and returns its ID."""
    name_clean = name.strip().upper()
    cursor = conn.cursor()
    cursor.execute("SELECT id_kecamatan FROM kecamatan WHERE nama_kecamatan = ?", (name_clean,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    cursor.execute("INSERT INTO kecamatan (nama_kecamatan) VALUES (?)", (name_clean,))
    conn.commit()
    return cursor.lastrowid

def get_all_kecamatan() -> pd.DataFrame:
    """Retrieves all kecamatan rows from the database."""
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM kecamatan ORDER BY nama_kecamatan ASC", conn)

def get_dataset_final() -> pd.DataFrame:
    """Retrieves the full dataset from the dataset_final view."""
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM dataset_final ORDER BY tahun DESC, kecamatan ASC", conn)

def get_tps_data() -> pd.DataFrame:
    """Retrieves all raw TPS records from the database."""
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT 
                id, tahun_pemilu, level_data, kecamatan, kelurahan, no_tps, id_record,
                dpt, pengguna_hak_pilih, partisipasi_politik, dpt_total_tps,
                penduduk_total_kelurahan, penduduk_total_kecamatan, rasio_dpt_terhadap_penduduk_kelurahan,
                pendapatan_per_kapita, tingkat_pengangguran, kepadatan_penduduk, ipm,
                jumlah_usia_17_24_kec, jumlah_usia_25_44_kec, jumlah_usia_45_plus_kec,
                persen_usia_17_24_kec, persen_usia_25_44_kec, persen_usia_45_plus_kec,
                created_at
            FROM data_partisipasi_tps
            ORDER BY kecamatan ASC, kelurahan ASC, no_tps ASC
        """, conn)

def insert_or_update_tps_data(data: dict):
    """Inserts a new record or updates it in data_partisipasi_tps."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Calculate participation rate automatically if needed
        partisipasi = data.get('partisipasi_politik')
        dpt = data.get('dpt')
        pilih = data.get('pengguna_hak_pilih')
        if partisipasi is None and dpt and pilih:
            partisipasi = (float(pilih) / float(dpt)) * 100.0
            
        cursor.execute("""
            INSERT INTO data_partisipasi_tps (
                tahun_pemilu, level_data, kecamatan, kelurahan, no_tps, id_record,
                dpt, pengguna_hak_pilih, partisipasi_politik, dpt_total_tps,
                penduduk_total_kelurahan, penduduk_total_kecamatan, rasio_dpt_terhadap_penduduk_kelurahan,
                pendapatan_per_kapita, tingkat_pengangguran, kepadatan_penduduk, ipm,
                jumlah_usia_17_24_kec, jumlah_usia_25_44_kec, jumlah_usia_45_plus_kec,
                persen_usia_17_24_kec, persen_usia_25_44_kec, persen_usia_45_plus_kec
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('tahun_pemilu'),
            data.get('level_data', 'tps'),
            data.get('kecamatan', '').strip().upper(),
            data.get('kelurahan', '').strip().upper(),
            data.get('no_tps', '').strip(),
            data.get('id_record'),
            dpt,
            pilih,
            partisipasi,
            data.get('dpt_total_tps'),
            data.get('penduduk_total_kelurahan'),
            data.get('penduduk_total_kecamatan'),
            data.get('rasio_dpt_terhadap_penduduk_kelurahan'),
            data.get('pendapatan_per_kapita'),
            data.get('tingkat_pengangguran'),
            data.get('kepadatan_penduduk'),
            data.get('ipm'),
            data.get('jumlah_usia_17_24_kec'),
            data.get('jumlah_usia_25_44_kec'),
            data.get('jumlah_usia_45_plus_kec'),
            data.get('persen_usia_17_24_kec'),
            data.get('persen_usia_25_44_kec'),
            data.get('persen_usia_45_plus_kec')
        ))
        conn.commit()

def insert_data_agregat(data: dict):
    """Inserts a record into data_partisipasi_agregat."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO data_partisipasi_agregat (
                tahun_pemilu, level_data, dapil, kecamatan, dpt_total,
                pengguna_total, partisipasi_politik, sumber_data, catatan
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('tahun_pemilu'),
            data.get('level_data', 'agregat'),
            data.get('dapil'),
            data.get('kecamatan', '').strip().upper(),
            data.get('dpt_total'),
            data.get('pengguna_total'),
            data.get('partisipasi_politik'),
            data.get('sumber_data'),
            data.get('catatan')
        ))
        conn.commit()

def get_dataset_2019_agregat() -> pd.DataFrame:
    """Retrieves all 2019 aggregated records from database."""
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT * FROM data_partisipasi_agregat
            WHERE tahun_pemilu = 2019
            ORDER BY kecamatan ASC
        """, conn)

def delete_tps_data(id_tps: int):
    """Deletes a TPS record by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM data_partisipasi_tps WHERE id = ?", (id_tps,))
        conn.commit()

def save_prediction(data: dict):
    """Saves a model prediction scenario into hasil_prediksi table."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hasil_prediksi (
                kecamatan, kelurahan, no_tps, dpt, rasio_dpt_terhadap_penduduk_kelurahan,
                pendapatan_per_kapita, tingkat_pengangguran, kepadatan_penduduk, ipm,
                persen_usia_17_24_kec, persen_usia_25_44_kec, persen_usia_45_plus_kec,
                hasil_prediksi, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            data.get('kecamatan'),
            data.get('kelurahan'),
            data.get('no_tps'),
            data.get('dpt'),
            data.get('rasio_dpt_terhadap_penduduk_kelurahan'),
            data.get('pendapatan_per_kapita'),
            data.get('tingkat_pengangguran'),
            data.get('kepadatan_penduduk'),
            data.get('ipm'),
            data.get('persen_usia_17_24_kec'),
            data.get('persen_usia_25_44_kec'),
            data.get('persen_usia_45_plus_kec'),
            data.get('hasil_prediksi')
        ))
        conn.commit()

def get_prediction_history() -> pd.DataFrame:
    """Retrieves all prediction logs."""
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT 
                id_prediksi, kecamatan, kelurahan, no_tps, dpt, rasio_dpt_terhadap_penduduk_kelurahan,
                pendapatan_per_kapita, tingkat_pengangguran, kepadatan_penduduk, ipm,
                persen_usia_17_24_kec, persen_usia_25_44_kec, persen_usia_45_plus_kec,
                hasil_prediksi, created_at
            FROM hasil_prediksi
            ORDER BY created_at DESC
        """, conn)

def save_model_evaluation(data: dict):
    """Saves model evaluation scores after training."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO model_evaluasi (
                nama_model, rmse, mae, r2_score, jumlah_data, jumlah_training, jumlah_testing
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['nama_model'],
            data.get('rmse'),
            data.get('mae'),
            data.get('r2_score'),
            data.get('jumlah_data'),
            data.get('jumlah_training'),
            data.get('jumlah_testing')
        ))
        conn.commit()

def seed_admin():
    """Seeds the default admin and user credentials into database if table is empty."""
    import hashlib
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Admin default: admin / admin123
        admin_hash = hashlib.sha256(b"admin123").hexdigest()
        cursor.execute("""
            INSERT OR IGNORE INTO pengguna (username, password_hash, role) VALUES (?, ?, ?)
        """, ("admin", admin_hash, "admin"))
        
        # User default: user / user123
        user_hash = hashlib.sha256(b"user123").hexdigest()
        cursor.execute("""
            INSERT OR IGNORE INTO pengguna (username, password_hash, role) VALUES (?, ?, ?)
        """, ("user", user_hash, "user"))

        # KPU default: kpu / kpu123
        kpu_hash = hashlib.sha256(b"kpu123").hexdigest()
        cursor.execute("""
            INSERT OR IGNORE INTO pengguna (username, password_hash, role) VALUES (?, ?, ?)
        """, ("kpu", kpu_hash, "kpu"))

        # Bakesbangpol default: bakesbangpol / bakesbangpol123
        bakes_hash = hashlib.sha256(b"bakesbangpol123").hexdigest()
        cursor.execute("""
            INSERT OR IGNORE INTO pengguna (username, password_hash, role) VALUES (?, ?, ?)
        """, ("bakesbangpol", bakes_hash, "bakesbangpol"))

        # BPS default: bps / bps123
        bps_hash = hashlib.sha256(b"bps123").hexdigest()
        cursor.execute("""
            INSERT OR IGNORE INTO pengguna (username, password_hash, role) VALUES (?, ?, ?)
        """, ("bps", bps_hash, "bps"))

        # Dukcapil default: dukcapil / dukcapil123
        duk_hash = hashlib.sha256(b"dukcapil123").hexdigest()
        cursor.execute("""
            INSERT OR IGNORE INTO pengguna (username, password_hash, role) VALUES (?, ?, ?)
        """, ("dukcapil", duk_hash, "dukcapil"))
        
        conn.commit()

def check_login(username, password) -> dict or None:
    """Verifies user credentials using SHA-256 and returns role details if valid."""
    import hashlib
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, role FROM pengguna WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        row = cursor.fetchone()
        if row:
            return {"username": row[0], "role": row[1]}
        return None

def register_user(username, password, role) -> bool:
    """Registers a new user into the database."""
    import hashlib
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pengguna (username, password_hash, role) VALUES (?, ?, ?)
            """, (username.strip(), password_hash, role))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def seed_dapil():
    """Seeds default dapil list into the dapil table."""
    dapils = [
        ("BANJARMASIN 1", "Kecamatan Banjarmasin Tengah"),
        ("BANJARMASIN 2", "Kecamatan Banjarmasin Utara"),
        ("BANJARMASIN 3", "Kecamatan Banjarmasin Timur"),
        ("BANJARMASIN 4", "Kecamatan Banjarmasin Selatan"),
        ("BANJARMASIN 5", "Kecamatan Banjarmasin Barat")
    ]
    with get_connection() as conn:
        cursor = conn.cursor()
        for nama, wilayah in dapils:
            cursor.execute("""
                INSERT OR IGNORE INTO dapil (nama_dapil, wilayah_cakupan) VALUES (?, ?)
            """, (nama, wilayah))
        conn.commit()

def seed_partai():
    """Seeds major political parties into the partai table."""
    partai_list = [
        ("Partai Kebangkitan Bangsa", "PKB", 1),
        ("Partai Gerakan Indonesia Raya", "GERINDRA", 2),
        ("Partai Demokrasi Indonesia Perjuangan", "PDIP", 3),
        ("Partai Golongan Karya", "GOLKAR", 4),
        ("Partai NasDem", "NASDEM", 5),
        ("Partai Buruh", "BURUH", 6),
        ("Partai Gelombang Rakyat Indonesia", "GELORA", 7),
        ("Partai Keadilan Sejahtera", "PKS", 8),
        ("Partai Kebangkitan Nusantara", "PKN", 9),
        ("Partai Hati Nurani Rakyat", "HANURA", 10),
        ("Partai Garda Republik Indonesia", "GARUDA", 11),
        ("Partai Amanat Nasional", "PAN", 12),
        ("Partai Bulan Bintang", "PBB", 13),
        ("Partai Demokrat", "DEMOKRAT", 14),
        ("Partai Solidaritas Indonesia", "PSI", 15),
        ("Partai Perindo", "PERINDO", 16),
        ("Partai Persatuan Pembangunan", "PPP", 17),
        ("Partai Ummat", "UMMAT", 24)
    ]
    with get_connection() as conn:
        cursor = conn.cursor()
        for nama, singkatan, no_urut in partai_list:
            cursor.execute("""
                INSERT OR IGNORE INTO partai (nama_partai, singkatan, nomor_urut) VALUES (?, ?, ?)
            """, (nama, singkatan, no_urut))
        conn.commit()

def seed_pemilu():
    """Seeds election periods into the pemilu table."""
    pemilu_list = [
        (2019, "Pemilu Serentak 2019 (Pileg & Pilpres)", 0),
        (2024, "Pemilu Serentak 2024 (Pileg & Pilpres)", 1)
    ]
    with get_connection() as conn:
        cursor = conn.cursor()
        for tahun, jenis, status in pemilu_list:
            cursor.execute("""
                INSERT OR IGNORE INTO pemilu (tahun_pemilu, jenis_pemilu, status_aktif) VALUES (?, ?, ?)
            """, (tahun, jenis, status))
        conn.commit()

def seed_relational_tables_from_tps():
    """Extracts unique kelurahan and tps from data_partisipasi_tps, and inserts them into master tables."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Populate kelurahan
        cursor.execute("SELECT DISTINCT kecamatan, kelurahan FROM data_partisipasi_tps")
        rows = cursor.fetchall()
        for kec_name, kel_name in rows:
            cursor.execute("SELECT id_kecamatan FROM kecamatan WHERE nama_kecamatan = ?", (kec_name.strip().upper(),))
            kec_row = cursor.fetchone()
            kec_id = kec_row[0] if kec_row else None
            if kec_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO kelurahan (nama_kelurahan, id_kecamatan) VALUES (?, ?)
                """, (kel_name.strip().upper(), kec_id))
        conn.commit()
        
        # 2. Populate tps
        cursor.execute("SELECT DISTINCT kelurahan, no_tps FROM data_partisipasi_tps")
        tps_rows = cursor.fetchall()
        for kel_name, no_tps in tps_rows:
            cursor.execute("SELECT id_kelurahan FROM kelurahan WHERE nama_kelurahan = ?", (kel_name.strip().upper(),))
            kel_row = cursor.fetchone()
            kel_id = kel_row[0] if kel_row else None
            if kel_id:
                cursor.execute("SELECT id_tps FROM tps WHERE no_tps = ? AND id_kelurahan = ?", (no_tps.strip(), kel_id))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO tps (no_tps, id_kelurahan) VALUES (?, ?)
                    """, (no_tps.strip(), kel_id))
        conn.commit()
        
        # 3. Populate suara_partai_tps with mock votes for Indonesian political parties
        cursor.execute("SELECT id_tps FROM tps")
        tps_ids = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT id_partai FROM partai")
        partai_ids = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM suara_partai_tps")
        exist_count = cursor.fetchone()[0]
        if exist_count == 0 and tps_ids and partai_ids:
            suara_data = []
            for t_id in tps_ids[:100]: # Seed for first 100 TPS to keep it fast
                for p_id in partai_ids:
                    jumlah_suara = (t_id * p_id + 7) % 45
                    suara_data.append((t_id, p_id, jumlah_suara))
            
            cursor.executemany("""
                INSERT INTO suara_partai_tps (id_tps, id_partai, jumlah_suara) VALUES (?, ?, ?)
            """, suara_data)
            conn.commit()

def add_partai(nama_partai: str, singkatan: str, nomor_urut: int) -> bool:
    """Adds a new political party into the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO partai (nama_partai, singkatan, nomor_urut) VALUES (?, ?, ?)
            """, (nama_partai.strip(), singkatan.strip().upper(), int(nomor_urut)))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def delete_partai(id_partai: int) -> bool:
    """Deletes a political party by ID from the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM partai WHERE id_partai = ?", (int(id_partai),))
            conn.commit()
            return True
    except Exception:
        return False

def get_kelurahannya_by_kecamatan(kecamatan_name: str, tahun_pemilu: int = 2024) -> list[str]:
    """Retrieves list of kelurahan names for a given kecamatan and election year."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT kelurahan FROM data_partisipasi_tps 
            WHERE kecamatan = ? AND tahun_pemilu = ?
            ORDER BY kelurahan ASC
        """, (kecamatan_name.strip().upper(), int(tahun_pemilu)))
        return [r[0] for r in cursor.fetchall()]

def get_tps_by_kelurahan(kecamatan_name: str, kelurahan_name: str, tahun_pemilu: int = 2024) -> list[str]:
    """Retrieves list of TPS numbers for a given kelurahan, kecamatan, and election year."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT no_tps FROM data_partisipasi_tps 
            WHERE kecamatan = ? AND kelurahan = ? AND tahun_pemilu = ?
            ORDER BY CAST(no_tps AS INTEGER), no_tps ASC
        """, (kecamatan_name.strip().upper(), kelurahan_name.strip().upper(), int(tahun_pemilu)))
        return [r[0] for r in cursor.fetchall()]

def get_tps_demographics(kecamatan: str, kelurahan: str, no_tps: str, tahun_pemilu: int = 2024) -> dict or None:
    """Retrieves variables / demographics for a single specific TPS and election year."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM data_partisipasi_tps 
            WHERE kecamatan = ? AND kelurahan = ? AND no_tps = ? AND tahun_pemilu = ?
            LIMIT 1
        """, (kecamatan.strip().upper(), kelurahan.strip().upper(), no_tps.strip(), int(tahun_pemilu)))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def update_partai(id_partai: int, nama_partai: str, singkatan: str, nomor_urut: int) -> bool:
    """Updates a political party's details in the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE partai 
                SET nama_partai = ?, singkatan = ?, nomor_urut = ?
                WHERE id_partai = ?
            """, (nama_partai.strip(), singkatan.strip().upper(), int(nomor_urut), int(id_partai)))
            conn.commit()
            return True
    except Exception:
        return False

def add_tps_record(data: dict) -> bool:
    """Inserts a new TPS record into the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            dpt = int(data.get('dpt', 0))
            pilih = int(data.get('pengguna_hak_pilih', 0))
            partisipasi = (float(pilih) / float(dpt) * 100.0) if dpt > 0 else 0.0
            
            cursor.execute("""
                INSERT INTO data_partisipasi_tps (
                    tahun_pemilu, level_data, kecamatan, kelurahan, no_tps, id_record,
                    dpt, pengguna_hak_pilih, partisipasi_politik, dpt_total_tps,
                    penduduk_total_kelurahan, penduduk_total_kecamatan, rasio_dpt_terhadap_penduduk_kelurahan,
                    pendapatan_per_kapita, tingkat_pengangguran, kepadatan_penduduk, ipm,
                    jumlah_usia_17_24_kec, jumlah_usia_25_44_kec, jumlah_usia_45_plus_kec,
                    persen_usia_17_24_kec, persen_usia_25_44_kec, persen_usia_45_plus_kec
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(data.get('tahun_pemilu', 2024)),
                'tps',
                str(data.get('kecamatan', '')).strip().upper(),
                str(data.get('kelurahan', '')).strip().upper(),
                str(data.get('no_tps', '')).strip(),
                f"{data.get('tahun_pemilu')}-{data.get('kecamatan')}-{data.get('kelurahan')}-{data.get('no_tps')}".strip().upper(),
                dpt,
                pilih,
                partisipasi,
                int(data.get('dpt_total_tps', dpt)),
                str(data.get('penduduk_total_kelurahan', '')),
                int(data.get('penduduk_total_kecamatan', 0)),
                float(data.get('rasio_dpt_terhadap_penduduk_kelurahan', 0.0)),
                float(data.get('pendapatan_per_kapita', 0.0)),
                float(data.get('tingkat_pengangguran', 0.0)),
                float(data.get('kepadatan_penduduk', 0.0)),
                float(data.get('ipm', 0.0)),
                int(data.get('jumlah_usia_17_24_kec', 0)),
                int(data.get('jumlah_usia_25_44_kec', 0)),
                int(data.get('jumlah_usia_45_plus_kec', 0)),
                float(data.get('persen_usia_17_24_kec', 0.0)),
                float(data.get('persen_usia_25_44_kec', 0.0)),
                float(data.get('persen_usia_45_plus_kec', 0.0))
            ))
            conn.commit()
            
            # Sync relational tables
            seed_relational_tables_from_tps()
            return True
    except Exception as e:
        import sys
        print(f"Error add_tps_record: {e}", file=sys.stderr)
        return False

def update_tps_record(tps_id: int, data: dict) -> bool:
    """Updates an existing TPS record in the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            dpt = int(data.get('dpt', 0))
            pilih = int(data.get('pengguna_hak_pilih', 0))
            partisipasi = (float(pilih) / float(dpt) * 100.0) if dpt > 0 else 0.0
            
            cursor.execute("""
                UPDATE data_partisipasi_tps SET
                    tahun_pemilu = ?,
                    kecamatan = ?,
                    kelurahan = ?,
                    no_tps = ?,
                    id_record = ?,
                    dpt = ?,
                    pengguna_hak_pilih = ?,
                    partisipasi_politik = ?,
                    dpt_total_tps = ?,
                    penduduk_total_kelurahan = ?,
                    penduduk_total_kecamatan = ?,
                    rasio_dpt_terhadap_penduduk_kelurahan = ?,
                    pendapatan_per_kapita = ?,
                    tingkat_pengangguran = ?,
                    kepadatan_penduduk = ?,
                    ipm = ?,
                    jumlah_usia_17_24_kec = ?,
                    jumlah_usia_25_44_kec = ?,
                    jumlah_usia_45_plus_kec = ?,
                    persen_usia_17_24_kec = ?,
                    persen_usia_25_44_kec = ?,
                    persen_usia_45_plus_kec = ?
                WHERE id = ?
            """, (
                int(data.get('tahun_pemilu', 2024)),
                str(data.get('kecamatan', '')).strip().upper(),
                str(data.get('kelurahan', '')).strip().upper(),
                str(data.get('no_tps', '')).strip(),
                f"{data.get('tahun_pemilu')}-{data.get('kecamatan')}-{data.get('kelurahan')}-{data.get('no_tps')}".strip().upper(),
                dpt,
                pilih,
                partisipasi,
                int(data.get('dpt_total_tps', dpt)),
                str(data.get('penduduk_total_kelurahan', '')),
                int(data.get('penduduk_total_kecamatan', 0)),
                float(data.get('rasio_dpt_terhadap_penduduk_kelurahan', 0.0)),
                float(data.get('pendapatan_per_kapita', 0.0)),
                float(data.get('tingkat_pengangguran', 0.0)),
                float(data.get('kepadatan_penduduk', 0.0)),
                float(data.get('ipm', 0.0)),
                int(data.get('jumlah_usia_17_24_kec', 0)),
                int(data.get('jumlah_usia_25_44_kec', 0)),
                int(data.get('jumlah_usia_45_plus_kec', 0)),
                float(data.get('persen_usia_17_24_kec', 0.0)),
                float(data.get('persen_usia_25_44_kec', 0.0)),
                float(data.get('persen_usia_45_plus_kec', 0.0)),
                int(tps_id)
            ))
            conn.commit()
            
            # Sync relational tables
            seed_relational_tables_from_tps()
            return True
    except Exception as e:
        import sys
        print(f"Error update_tps_record: {e}", file=sys.stderr)
        return False

def delete_tps_record(tps_id: int) -> bool:
    """Deletes a TPS record from the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM data_partisipasi_tps WHERE id = ?", (int(tps_id),))
            conn.commit()
            
            # Sync relational tables
            seed_relational_tables_from_tps()
            return True
    except Exception as e:
        import sys
        print(f"Error delete_tps_record: {e}", file=sys.stderr)
        return False

# ====================================================================
# MASTER DATA CRUD FUNCTIONS
# ====================================================================

def add_kecamatan(nama_kecamatan: str) -> bool:
    """Inserts a new kecamatan."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO kecamatan (nama_kecamatan) VALUES (?)", (nama_kecamatan.strip().upper(),))
            conn.commit()
            return True
    except Exception:
        return False

def update_kecamatan(id_kecamatan: int, nama_kecamatan: str) -> bool:
    """Updates a kecamatan's name."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE kecamatan SET nama_kecamatan = ? WHERE id_kecamatan = ?", (nama_kecamatan.strip().upper(), int(id_kecamatan)))
            conn.commit()
            return True
    except Exception:
        return False

def delete_kecamatan(id_kecamatan: int) -> bool:
    """Deletes a kecamatan by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kecamatan WHERE id_kecamatan = ?", (int(id_kecamatan),))
            conn.commit()
            return True
    except Exception:
        return False

def get_all_kelurahan() -> pd.DataFrame:
    """Retrieves all kelurahan with their kecamatan name."""
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT 
                k.id_kelurahan,
                k.nama_kelurahan,
                k.id_kecamatan,
                kc.nama_kecamatan
            FROM kelurahan k
            LEFT JOIN kecamatan kc ON k.id_kecamatan = kc.id_kecamatan
            ORDER BY kc.nama_kecamatan ASC, k.nama_kelurahan ASC
        """, conn)

def add_kelurahan(nama_kelurahan: str, id_kecamatan: int) -> bool:
    """Inserts a new kelurahan linked to a kecamatan."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO kelurahan (nama_kelurahan, id_kecamatan) VALUES (?, ?)", (nama_kelurahan.strip().upper(), int(id_kecamatan)))
            conn.commit()
            return True
    except Exception:
        return False

def update_kelurahan(id_kelurahan: int, nama_kelurahan: str, id_kecamatan: int) -> bool:
    """Updates a kelurahan's name and associated kecamatan."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE kelurahan SET nama_kelurahan = ?, id_kecamatan = ? WHERE id_kelurahan = ?", (nama_kelurahan.strip().upper(), int(id_kecamatan), int(id_kelurahan)))
            conn.commit()
            return True
    except Exception:
        return False

def delete_kelurahan(id_kelurahan: int) -> bool:
    """Deletes a kelurahan by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kelurahan WHERE id_kelurahan = ?", (int(id_kelurahan),))
            conn.commit()
            return True
    except Exception:
        return False

def get_all_master_tps() -> pd.DataFrame:
    """Retrieves all registered master TPS rows with kelurahan and kecamatan."""
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT 
                t.id_tps,
                t.no_tps,
                t.id_kelurahan,
                k.nama_kelurahan,
                kc.nama_kecamatan
            FROM tps t
            LEFT JOIN kelurahan k ON t.id_kelurahan = k.id_kelurahan
            LEFT JOIN kecamatan kc ON k.id_kecamatan = kc.id_kecamatan
            ORDER BY kc.nama_kecamatan ASC, k.nama_kelurahan ASC, CAST(t.no_tps AS INTEGER), t.no_tps ASC
        """, conn)

def add_master_tps(no_tps: str, id_kelurahan: int) -> bool:
    """Inserts a new master TPS under a kelurahan."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tps (no_tps, id_kelurahan) VALUES (?, ?)", (str(no_tps).strip(), int(id_kelurahan)))
            conn.commit()
            return True
    except Exception:
        return False

def update_master_tps(id_tps: int, no_tps: str, id_kelurahan: int) -> bool:
    """Updates master TPS details."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tps SET no_tps = ?, id_kelurahan = ? WHERE id_tps = ?", (str(no_tps).strip(), int(id_kelurahan), int(id_tps)))
            conn.commit()
            return True
    except Exception:
        return False

def delete_master_tps(id_tps: int) -> bool:
    """Deletes master TPS by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tps WHERE id_tps = ?", (int(id_tps),))
            conn.commit()
            return True
    except Exception:
        return False

def get_all_dapil() -> pd.DataFrame:
    """Retrieves all dapil."""
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM dapil ORDER BY id_dapil ASC", conn)

def add_dapil(nama_dapil: str, wilayah_cakupan: str) -> bool:
    """Inserts a new dapil."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO dapil (nama_dapil, wilayah_cakupan) VALUES (?, ?)", (nama_dapil.strip().upper(), wilayah_cakupan.strip()))
            conn.commit()
            return True
    except Exception:
        return False

def update_dapil(id_dapil: int, nama_dapil: str, wilayah_cakupan: str) -> bool:
    """Updates a dapil record."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dapil SET nama_dapil = ?, wilayah_cakupan = ? WHERE id_dapil = ?", (nama_dapil.strip().upper(), wilayah_cakupan.strip(), int(id_dapil)))
            conn.commit()
            return True
    except Exception:
        return False

def delete_dapil(id_dapil: int) -> bool:
    """Deletes a dapil record."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dapil WHERE id_dapil = ?", (int(id_dapil),))
            conn.commit()
            return True
    except Exception:
        return False

def get_all_pemilu() -> pd.DataFrame:
    """Retrieves all pemilu periods."""
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM pemilu ORDER BY tahun_pemilu ASC", conn)

def add_pemilu(tahun_pemilu: int, jenis_pemilu: str, status_aktif: int = 0) -> bool:
    """Inserts a new pemilu period."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO pemilu (tahun_pemilu, jenis_pemilu, status_aktif) VALUES (?, ?, ?)", (int(tahun_pemilu), jenis_pemilu.strip(), int(status_aktif)))
            conn.commit()
            return True
    except Exception:
        return False

def update_pemilu(id_pemilu: int, tahun_pemilu: int, jenis_pemilu: str, status_aktif: int) -> bool:
    """Updates a pemilu period."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE pemilu SET tahun_pemilu = ?, jenis_pemilu = ?, status_aktif = ? WHERE id_pemilu = ?", (int(tahun_pemilu), jenis_pemilu.strip(), int(status_aktif), int(id_pemilu)))
            conn.commit()
            return True
    except Exception:
        return False

def delete_pemilu(id_pemilu: int) -> bool:
    """Deletes a pemilu period."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pemilu WHERE id_pemilu = ?", (int(id_pemilu),))
            conn.commit()
            return True
    except Exception:
        return False

def get_all_pengguna() -> pd.DataFrame:
    """Retrieves all users without exposing full password hash."""
    with get_connection() as conn:
        return pd.read_sql_query("SELECT id_pengguna, username, role, created_at FROM pengguna ORDER BY role ASC, username ASC", conn)

def add_pengguna(username: str, password: str, role: str) -> bool:
    """Adds a new user account."""
    return register_user(username, password, role)

def update_pengguna(id_pengguna: int, role: str, new_password: str = None) -> bool:
    """Updates user role and optionally password."""
    import hashlib
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if new_password and new_password.strip():
                pwd_hash = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
                cursor.execute("UPDATE pengguna SET role = ?, password_hash = ? WHERE id_pengguna = ?", (role.strip().lower(), pwd_hash, int(id_pengguna)))
            else:
                cursor.execute("UPDATE pengguna SET role = ? WHERE id_pengguna = ?", (role.strip().lower(), int(id_pengguna)))
            conn.commit()
            return True
    except Exception:
        return False

def delete_pengguna(id_pengguna: int) -> bool:
    """Deletes a user account by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pengguna WHERE id_pengguna = ?", (int(id_pengguna),))
            conn.commit()
            return True
    except Exception:
        return False


# ====================================================================
# DATA TRANSAKSI CRUD FUNCTIONS
# ====================================================================

def get_all_data_agregat() -> pd.DataFrame:
    """Retrieves all aggregate participation records."""
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM data_partisipasi_agregat ORDER BY tahun_pemilu DESC, kecamatan ASC", conn)

def add_data_agregat(data: dict) -> bool:
    """Inserts a record into data_partisipasi_agregat."""
    try:
        insert_data_agregat(data)
        return True
    except Exception:
        return False

def update_data_agregat(id_agregat: int, data: dict) -> bool:
    """Updates a record in data_partisipasi_agregat."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE data_partisipasi_agregat SET
                    tahun_pemilu = ?,
                    dapil = ?,
                    kecamatan = ?,
                    dpt_total = ?,
                    pengguna_total = ?,
                    partisipasi_politik = ?,
                    sumber_data = ?,
                    catatan = ?
                WHERE id = ?
            """, (
                int(data.get('tahun_pemilu', 2024)),
                data.get('dapil'),
                str(data.get('kecamatan', '')).strip().upper(),
                int(data.get('dpt_total', 0)),
                int(data.get('pengguna_total', 0)),
                float(data.get('partisipasi_politik', 0.0)),
                data.get('sumber_data'),
                data.get('catatan'),
                int(id_agregat)
            ))
            conn.commit()
            return True
    except Exception:
        return False

def delete_data_agregat(id_agregat: int) -> bool:
    """Deletes an aggregate participation record by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM data_partisipasi_agregat WHERE id = ?", (int(id_agregat),))
            conn.commit()
            return True
    except Exception:
        return False

def delete_prediction(id_prediksi: int) -> bool:
    """Deletes a prediction record by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hasil_prediksi WHERE id_prediksi = ?", (int(id_prediksi),))
            conn.commit()
            return True
    except Exception:
        return False

def clear_all_predictions() -> bool:
    """Clears all prediction logs."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hasil_prediksi")
            conn.commit()
            return True
    except Exception:
        return False

def get_all_model_evaluations() -> pd.DataFrame:
    """Retrieves all model training evaluations."""
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM model_evaluasi ORDER BY tanggal_evaluasi DESC", conn)

def delete_model_evaluation(id_evaluasi: int) -> bool:
    """Deletes a model evaluation log."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM model_evaluasi WHERE id_evaluasi = ?", (int(id_evaluasi),))
            conn.commit()
            return True
    except Exception:
        return False

def get_database_summary_stats() -> dict:
    """Retrieves summary row counts for Master Data and Transaksi tables."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Master tables
        def get_count(tbl):
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                return cursor.fetchone()[0]
            except Exception:
                return 0
                
        return {
            # Master Data
            "master_kecamatan": get_count("kecamatan"),
            "master_kelurahan": get_count("kelurahan"),
            "master_tps": get_count("tps"),
            "master_dapil": get_count("dapil"),
            "master_partai": get_count("partai"),
            "master_pemilu": get_count("pemilu"),
            "master_pengguna": get_count("pengguna"),
            # Transaksi Data
            "transaksi_tps": get_count("data_partisipasi_tps"),
            "transaksi_suara_partai": get_count("suara_partai_tps"),
            "transaksi_agregat": get_count("data_partisipasi_agregat"),
            "transaksi_log_prediksi": get_count("hasil_prediksi"),
            "transaksi_evaluasi_model": get_count("model_evaluasi"),
        }


def check_database_integrity() -> dict:
    """Performs integrity and relational foreign key diagnostic check across tables."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
        except Exception:
            fk_violations = []

        try:
            cursor.execute("""
                SELECT COUNT(*) FROM kelurahan k 
                LEFT JOIN kecamatan c ON k.id_kecamatan = c.id_kecamatan 
                WHERE c.id_kecamatan IS NULL
            """)
            orphan_kel = cursor.fetchone()[0]
        except Exception:
            orphan_kel = 0

        try:
            cursor.execute("""
                SELECT COUNT(*) FROM tps t 
                LEFT JOIN kelurahan k ON t.id_kelurahan = k.id_kelurahan 
                WHERE k.id_kelurahan IS NULL
            """)
            orphan_tps = cursor.fetchone()[0]
        except Exception:
            orphan_tps = 0

        is_healthy = (len(fk_violations) == 0 and orphan_kel == 0 and orphan_tps == 0)
        return {
            "fk_violations": len(fk_violations),
            "orphan_kelurahan": orphan_kel,
            "orphan_tps": orphan_tps,
            "is_healthy": is_healthy,
            "status": "100% Terintegrasi & Sinkron" if is_healthy else "Perlu Penyelarasan Relasi"
        }




