from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split

from src.config import FEATURE_COLUMNS, MODEL_PARAMS, TARGET_COLUMN


@dataclass
class ModelResult:
    # Kelas penyimpan data (blueprint) untuk menampung seluruh hasil dari model setelah belajar
    model: RandomForestRegressor
    rmse: float
    mae: float
    r2: float
    feature_importance: pd.DataFrame
    prediction_result: pd.DataFrame
    train_size: int
    test_size: int


def train_random_forest(df: pd.DataFrame) -> ModelResult:
    """Fungsi utama untuk melatih algoritma Random Forest menggunakan data yang diberikan."""
    

    # 1. Menghapus baris data yang kosong (NaN) pada kolom Fitur (Soal) dan Target (Kunci Jawaban)
    data = df.dropna(subset=[*FEATURE_COLUMNS, TARGET_COLUMN]).copy()

    # Jika jumlah data kurang dari 8, model tidak akan bisa belajar dengan baik
    if len(data) < 8:
        raise ValueError("Data terlalu sedikit. Diperlukan minimal 8 baris data untuk evaluasi model yang valid.")

    # 2. Menyiapkan Fitur (Variabel Bebas / X) dan Target (Variabel Terikat / Y)
    x = data[FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]

    # 3. Membagi data menjadi porsi untuk Belajar (Train) dan Ujian (Test)
    # Jika data >= 12, maka 25% dipakai ujian, sisanya 75% belajar.
    test_size = 0.25 if len(data) >= 12 else 0.3
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=42, # Angka 42 digunakan agar hasil pengacakan data selalu konsisten jika dijalankan ulang
    )

    # 4. Membuat "Otak" Mesin Random Forest
    model = RandomForestRegressor(**MODEL_PARAMS)
    
    # 5. Proses Belajar: Mesin mempelajari pola dari data X_train untuk bisa menjawab Y_train
    model.fit(x_train, y_train)

    # 6. Proses Ujian (Prediksi): Mesin disuruh menebak jawaban dari soal ujian (x_test)
    y_pred = model.predict(x_test)
    
    # 7. Evaluasi (Menghitung Nilai Raport Model)
    # RMSE = Root Mean Squared Error (Seberapa besar simpangan/error dari tebakan, makin kecil makin bagus)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    # MAE = Mean Absolute Error
    mae = float(mean_absolute_error(y_test, y_pred))
    # R2 Score = Persentase kesesuaian prediksi dengan data asli (Sempurna jika nilainya 1.0)
    r2 = float(r2_score(y_test, y_pred)) if len(y_test) > 1 else 0.0

    # 8. Mengecek faktor/fitur mana (misal IPM, Kepadatan) yang paling berpengaruh pada partisipasi
    importance = pd.DataFrame(
        {
            "variabel": FEATURE_COLUMNS,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False) # Urutkan dari yang paling penting

    # 9. Menyimpan hasil prediksi ke dalam format tabel agar mudah dibaca
    prediction_result = pd.DataFrame(
        {
            "aktual": y_test.to_numpy(),      # Kunci Jawaban Asli
            "prediksi": y_pred,               # Jawaban Tebakan Mesin
            "selisih": y_test.to_numpy() - y_pred, # Bedanya Asli dan Tebakan (Error)
        }
    )

    # 10. Menyimpan nilai raport model (RMSE, MAE, R2) ke dalam database secara otomatis
    try:
        from src.database import save_model_evaluation
        save_model_evaluation({
            "nama_model": "Random Forest",
            "rmse": rmse,
            "mae": mae,
            "r2_score": r2,
            "jumlah_data": len(data),
            "jumlah_training": len(x_train),
            "jumlah_testing": len(x_test)
        })
    except Exception as e:
        # Jika gagal simpan ke database, tampilkan peringatan tanpa membuat aplikasi crash
        import sys
        print(f"Warning: Gagal menyimpan evaluasi model ke database: {e}", file=sys.stderr)

    # Mengembalikan semua hasil dan model di dalam keranjang kelas ModelResult
    return ModelResult(
        model=model,
        rmse=rmse,
        mae=mae,
        r2=r2,
        feature_importance=importance,
        prediction_result=prediction_result,
        train_size=len(x_train),
        test_size=len(x_test),
    )


def predict_participation(model: RandomForestRegressor, input_values: dict) -> float:
    """Fungsi pembantu: Digunakan oleh halaman Prediksi untuk menebak nilai 1 kecamatan secara instan"""
    # Mengubah data input dari pengguna di halaman web menjadi format tabel 1 baris
    row = pd.DataFrame([input_values], columns=FEATURE_COLUMNS)
    # Menyuruh model untuk menebak angka partisipasi berdasarkan input tersebut
    return float(model.predict(row)[0])
