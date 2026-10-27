"""
Modul ini bertanggung jawab untuk memuat dan memproses data awal 
sebelum digunakan oleh aplikasi (seperti membaca data dari database atau membersihkan data).
"""
import json
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

from src.config import GEOJSON_PATH, DATA_2024_PATH, DATA_2019_PATH, REQUIRED_COLUMNS


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names so CSV from Excel does not explode instantly."""
    clean = df.copy()
    clean.columns = (
        clean.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return clean


def validate_columns(df: pd.DataFrame, required_columns: Iterable[str] = REQUIRED_COLUMNS) -> list[str]:
    return [col for col in required_columns if col not in df.columns]


def coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    non_numeric = ["kecamatan", "kelurahan", "no_tps", "id_record", "penduduk_total_kelurahan", "level_data", "dapil", "sumber_data", "catatan"]
    for column in clean.columns:
        if column not in non_numeric:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")
    return clean


def load_dataset_2024() -> pd.DataFrame:
    """Reads 2024 TPS dataset from database view dataset_final."""
    from src.database import get_dataset_final, database_exists
    if not database_exists():
        return pd.DataFrame()
    try:
        return get_dataset_final()
    except Exception:
        return pd.DataFrame()


def load_dataset_2019() -> pd.DataFrame:
    """Reads 2019 agregat dataset from database."""
    from src.database import get_dataset_2019_agregat, database_exists
    if not database_exists():
        return pd.DataFrame()
    try:
        return get_dataset_2019_agregat()
    except Exception:
        return pd.DataFrame()


def load_dataset() -> pd.DataFrame:
    """Loads all raw TPS records from the database (all years) and standardizes columns."""
    from src.database import get_tps_data
    df = get_tps_data()
    if not df.empty and "tahun_pemilu" in df.columns and "tahun" not in df.columns:
        df["tahun"] = df["tahun_pemilu"]
    return df


def get_training_dataset_2024() -> pd.DataFrame:
    """Retrieves dataset_final (which is 2024 TPS only) and drops rows with missing target or features."""
    from src.config import FEATURE_COLUMNS, TARGET_COLUMN
    df = load_dataset_2024()
    if df.empty:
        return pd.DataFrame()
    cols = list(FEATURE_COLUMNS) + [TARGET_COLUMN]
    return df.dropna(subset=cols).reset_index(drop=True)


def get_training_dataset() -> pd.DataFrame:
    """Fallback alias to retrieve training dataset."""
    return get_training_dataset_2024()


def get_summary_2024(df: pd.DataFrame) -> dict:
    """Calculates statistics summary for 2024 TPS data."""
    if df.empty:
        return {
            "total_tps": 0,
            "total_dpt": 0,
            "total_pengguna": 0,
            "average_partisipasi": 0.0,
            "highest_area": "N/A",
            "highest_value": 0.0,
            "lowest_area": "N/A",
            "lowest_value": 0.0,
        }
    
    # Calculate unique TPS count
    if all(c in df.columns for c in ["kecamatan", "kelurahan", "no_tps"]):
        total_tps = int(df[["kecamatan", "kelurahan", "no_tps"]].drop_duplicates().shape[0])
    else:
        total_tps = len(df)
    total_dpt = int(df["dpt"].sum())
    total_pengguna = int(df["pengguna_hak_pilih"].sum())
    avg_part = (total_pengguna / total_dpt * 100.0) if total_dpt > 0 else 0.0
    
    # Find highest and lowest participation rows
    valid_part = df.dropna(subset=["partisipasi_politik"])
    if not valid_part.empty:
        highest_row = valid_part.loc[valid_part["partisipasi_politik"].idxmax()]
        lowest_row = valid_part.loc[valid_part["partisipasi_politik"].idxmin()]
        
        highest_area = f"{highest_row['kecamatan']} ({highest_row['kelurahan']} - TPS {highest_row['no_tps']})"
        highest_val = float(highest_row["partisipasi_politik"])
        
        lowest_area = f"{lowest_row['kecamatan']} ({lowest_row['kelurahan']} - TPS {lowest_row['no_tps']})"
        lowest_val = float(lowest_row["partisipasi_politik"])
    else:
        highest_area = "N/A"
        highest_val = 0.0
        lowest_area = "N/A"
        lowest_val = 0.0
        
    return {
        "total_tps": total_tps,
        "total_dpt": total_dpt,
        "total_pengguna": total_pengguna,
        "average_partisipasi": avg_part,
        "highest_area": highest_area,
        "highest_value": highest_val,
        "lowest_area": lowest_area,
        "lowest_value": lowest_val,
    }


def get_summary_2019(df: pd.DataFrame) -> dict:
    """Calculates statistics summary for 2019 aggregated data."""
    if df.empty:
        return {
            "total_dpt": 0,
            "total_pengguna": 0,
            "average_partisipasi": 0.0,
        }
    total_dpt = int(df["dpt_total"].sum())
    total_pengguna = int(df["pengguna_total"].sum())
    avg_part = (total_pengguna / total_dpt * 100.0) if total_dpt > 0 else 0.0
    return {
        "total_dpt": total_dpt,
        "total_pengguna": total_pengguna,
        "average_partisipasi": avg_part,
    }


def get_comparison_2019_2024() -> pd.DataFrame:
    """Aggregates 2024 and 2019 TPS data from data_partisipasi_tps to kecamatan level and merges them."""
    from src.database import get_connection
    try:
        with get_connection() as conn:
            df_2024 = pd.read_sql_query("""
                SELECT kecamatan, SUM(dpt) as dpt, SUM(pengguna_hak_pilih) as pengguna
                FROM data_partisipasi_tps
                WHERE tahun_pemilu = 2024
                GROUP BY kecamatan
            """, conn)
            df_2019 = pd.read_sql_query("""
                SELECT kecamatan, SUM(dpt) as dpt, SUM(pengguna_hak_pilih) as pengguna
                FROM data_partisipasi_tps
                WHERE tahun_pemilu = 2019
                GROUP BY kecamatan
            """, conn)
            
        if df_2024.empty or df_2019.empty:
            return pd.DataFrame()
            
        df_2024["partisipasi_2024"] = (df_2024["pengguna"] / df_2024["dpt"]) * 100.0
        df_24_clean = df_2024[["kecamatan", "partisipasi_2024"]]
        
        df_2019["partisipasi_2019"] = (df_2019["pengguna"] / df_2019["dpt"]) * 100.0
        df_19_clean = df_2019[["kecamatan", "partisipasi_2019"]]
        
        merged = pd.merge(df_19_clean, df_24_clean, on="kecamatan", how="outer")
        return merged
    except Exception as e:
        import sys
        print(f"Error in get_comparison_2019_2024: {e}", file=sys.stderr)
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_geojson(path: str | Path = GEOJSON_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def filter_dataset(df: pd.DataFrame, selected_years: list[int], selected_areas: list[str]) -> pd.DataFrame:
    filtered = df.copy()
    if selected_years and "tahun" in filtered.columns:
        filtered = filtered[filtered["tahun"].isin(selected_years)]
    elif selected_years and "tahun_pemilu" in filtered.columns:
        filtered = filtered[filtered["tahun_pemilu"].isin(selected_years)]
        
    if selected_areas and "kecamatan" in filtered.columns:
        filtered = filtered[filtered["kecamatan"].isin(selected_areas)]
    return filtered.reset_index(drop=True)
