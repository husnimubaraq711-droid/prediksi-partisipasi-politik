"""
File konfigurasi utama untuk aplikasi polpart.
Berisi definisi path file, pengaturan kolom dataset, dan hyperparameter model.
"""
from pathlib import Path

# Mendefinisikan direktori dasar (root project)
BASE_DIR = Path(__file__).resolve().parents[1]

# Path untuk data, model, database, dan aset
DATA_DIR = BASE_DIR / "data"
DATA_2024_PATH = DATA_DIR / "raw" / "dataset_2024_tps_model_final.csv"
DATA_2019_PATH = DATA_DIR / "raw" / "dataset_2019_agregat_historis.csv"
GEOJSON_PATH = DATA_DIR / "geo" / "kecamatan_5.geojson"
MODEL_DIR = BASE_DIR / "models"
DB_PATH = BASE_DIR / "database" / "polpart.db"
ASSETS_DIR = BASE_DIR / "assets"
STYLE_PATH = ASSETS_DIR / "style.css"

APP_TITLE = "Prediksi Partisipasi Politik"
APP_SUBTITLE = "Dashboard dan prediksi tingkat partisipasi politik berbasis Random Forest"

TARGET_COLUMN = "partisipasi_politik"
YEAR_COLUMN = "tahun"
AREA_COLUMN = "kecamatan"

FEATURE_COLUMNS = [
    "dpt",
    "rasio_dpt_terhadap_penduduk_kelurahan",
    "pendapatan_per_kapita",
    "tingkat_pengangguran",
    "kepadatan_penduduk",
    "ipm",
    "persen_usia_17_24_kec",
    "persen_usia_25_44_kec",
    "persen_usia_45_plus_kec",
]

REQUIRED_COLUMNS = [YEAR_COLUMN, AREA_COLUMN, "kelurahan", "no_tps", *FEATURE_COLUMNS, TARGET_COLUMN]

DISPLAY_NAMES = {
    "tahun": "Tahun",
    "kecamatan": "Kecamatan",
    "kelurahan": "Kelurahan",
    "no_tps": "No TPS",
    "dpt": "Jumlah DPT",
    "rasio_dpt_terhadap_penduduk_kelurahan": "Rasio DPT Kelurahan",
    "pendapatan_per_kapita": "Pendapatan Per Kapita",
    "tingkat_pengangguran": "Tingkat Pengangguran (%)",
    "kepadatan_penduduk": "Kepadatan Penduduk (jiwa/km²)",
    "ipm": "IPM",
    "persen_usia_17_24_kec": "Usia 17-24 Tahun (%)",
    "persen_usia_25_44_kec": "Usia 25-44 Tahun (%)",
    "persen_usia_45_plus_kec": "Usia 45+ Tahun (%)",
    "partisipasi_politik": "Partisipasi Politik (%)",
}

MODEL_PARAMS = {
    "n_estimators": 300,
    "max_depth": 8,
    "random_state": 42,
    "min_samples_leaf": 1,
}
