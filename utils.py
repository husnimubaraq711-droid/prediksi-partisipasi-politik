"""
Modul utilitas yang berisi fungsi-fungsi bantuan, 
seperti format angka (persentase, rupiah) dan perhitungan ringkasan data.
"""
import pandas as pd

from src.config import DISPLAY_NAMES, TARGET_COLUMN


def format_percent(value: float) -> str:
    return f"{value:.2f}%"


def format_rupiah(value: float) -> str:
    return "Rp{:,.0f}".format(value).replace(",", ".")


def rename_for_display(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=DISPLAY_NAMES)


def get_summary(df: pd.DataFrame) -> dict:
    sub = df.dropna(subset=[TARGET_COLUMN])
    if sub.empty:
        return {
            "rows": len(df),
            "average": 0.0,
            "highest_area": "N/A",
            "highest_value": 0.0,
            "lowest_area": "N/A",
            "lowest_value": 0.0,
        }
    average = float(sub[TARGET_COLUMN].mean())
    highest_row = sub.loc[sub[TARGET_COLUMN].idxmax()]
    lowest_row = sub.loc[sub[TARGET_COLUMN].idxmin()]
    
    # Format descriptive strings showing TPS level detail
    highest_area_desc = f"{highest_row['kelurahan']} - TPS {highest_row['no_tps']}"
    lowest_area_desc = f"{lowest_row['kelurahan']} - TPS {lowest_row['no_tps']}"
    
    return {
        "rows": len(df),
        "average": average,
        "highest_area": highest_area_desc,
        "highest_value": float(highest_row[TARGET_COLUMN]),
        "lowest_area": lowest_area_desc,
        "lowest_value": float(lowest_row[TARGET_COLUMN]),
    }
