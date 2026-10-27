from fpdf import FPDF
from datetime import datetime
import io

class PolPartPDF(FPDF):
    def header(self):
        # Draw a top coral/mint header banner
        self.set_fill_color(234, 248, 248) # Mint background (#eaf8f8)
        self.rect(0, 0, 210, 20, "F")
        
        self.set_fill_color(255, 127, 102) # Coral strip (#ff7f66)
        self.rect(0, 20, 210, 2, "F")
        
        self.set_y(6)
        self.set_font("helvetica", "B", 12)
        self.set_text_color(30, 41, 59) # Slate Dark (#1e293b)
        self.cell(0, 8, "LAPORAN REKAPITULASI PREDIKSI PARTISIPASI POLITIK", align="C", ln=True)
        self.ln(10)
        
    def footer(self):
        self.set_y(-20)
        self.set_fill_color(241, 245, 249) # Light slate footer
        self.rect(0, 280, 210, 17, "F")
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139) # Slate lighter
        self.cell(0, 10, f"Halaman {self.page_no()} | Dokumen hasil analisa otomatis sistem PolPart RF", align="C")

def generate_recap_pdf(data: dict) -> bytes:
    """
    Generates a PDF recap file in-memory and returns the bytes.
    Expects data keys:
      - kecamatan
      - kelurahan
      - no_tps
      - dpt
      - rasio_dpt
      - usia_17_24
      - usia_25_44
      - usia_45_plus
      - hasil_prediksi
      - model_metrics (dict: r2, rmse)
      - printed_by
    """
    pdf = PolPartPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    
    # Title
    pdf.set_y(30)
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(255, 127, 102) # Coral
    pdf.cell(0, 10, "REKAP HASIL PREDIKSI (RANDOM FOREST REGRESSOR)", ln=True, align="L")
    
    # Metadata info (2 columns)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(71, 85, 105) # Slate grey
    
    col_width = 90
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    # Line 1
    pdf.cell(col_width, 6, f"Tanggal Cetak: {current_time}", ln=False)
    pdf.cell(col_width, 6, f"Dicetak Oleh: {data.get('printed_by', 'Guest')}", ln=True)
    
    # Line 2
    pdf.cell(col_width, 6, f"Kecamatan: {data.get('kecamatan', '-')}", ln=False)
    pdf.cell(col_width, 6, f"Kelurahan / Desa: {data.get('kelurahan', '-')}", ln=True)
    
    # Line 3
    pdf.cell(col_width, 6, f"Nomor TPS: {data.get('no_tps', '-')}", ln=False)
    pdf.cell(col_width, 6, "Metode Analisa: Random Forest Regressor", ln=True)
    
    pdf.ln(4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    # Input Variables Header
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "1. Parameter Demografi & Lokasi (Variabel Input)", ln=True)
    pdf.ln(2)
    
    # Table of inputs with soft borders
    pdf.set_draw_color(226, 232, 240) # Soft grey borders
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(234, 248, 248) # Mint header
    pdf.set_text_color(30, 41, 59)
    
    pdf.cell(100, 8, " Nama Variabel / Parameter", border=1, fill=True, align="L")
    pdf.cell(90, 8, " Nilai Input", border=1, fill=True, align="C", ln=True)
    
    pdf.set_font("helvetica", "", 10)
    
    # Rows
    pdf.cell(100, 8, " Jumlah Daftar Pemilih Tetap (DPT) TPS", border=1, align="L")
    pdf.cell(90, 8, f" {data.get('dpt', 0):,}".replace(",", "."), border=1, align="C", ln=True)
    
    pdf.cell(100, 8, " Rasio DPT Terhadap Penduduk Kelurahan", border=1, align="L")
    pdf.cell(90, 8, f" {data.get('rasio_dpt', 0.0):.4f}", border=1, align="C", ln=True)
    
    pdf.cell(100, 8, " Pendapatan Per Kapita (Rp)", border=1, align="L")
    pdf.cell(90, 8, f" Rp {data.get('pendapatan_per_kapita', 0.0):,}".replace(",", "."), border=1, align="C", ln=True)
    
    pdf.cell(100, 8, " Tingkat Pengangguran Kecamatan (%)", border=1, align="L")
    pdf.cell(90, 8, f" {data.get('tingkat_pengangguran', 0.0):.2f}%", border=1, align="C", ln=True)
    
    pdf.cell(100, 8, " Kepadatan Penduduk (jiwa/km²)", border=1, align="L")
    pdf.cell(90, 8, f" {data.get('kepadatan_penduduk', 0.0):.2f}", border=1, align="C", ln=True)
    
    pdf.cell(100, 8, " Indeks Pembangunan Manusia (IPM)", border=1, align="L")
    pdf.cell(90, 8, f" {data.get('ipm', 0.0):.2f}", border=1, align="C", ln=True)
    
    pdf.cell(100, 8, " Persentase Pemilih Usia 17 - 24 Tahun (Kecamatan)", border=1, align="L")
    pdf.cell(90, 8, f" {data.get('usia_17_24', 0.0):.2f}%", border=1, align="C", ln=True)
    
    pdf.cell(100, 8, " Persentase Pemilih Usia 25 - 44 Tahun (Kecamatan)", border=1, align="L")
    pdf.cell(90, 8, f" {data.get('usia_25_44', 0.0):.2f}%", border=1, align="C", ln=True)
    
    pdf.cell(100, 8, " Persentase Pemilih Usia 45 Tahun Keatas (Kecamatan)", border=1, align="L")
    pdf.cell(90, 8, f" {data.get('usia_45_plus', 0.0):.2f}%", border=1, align="C", ln=True)
    
    pdf.ln(8)
    
    # Prediction Results Box
    pdf.set_fill_color(255, 247, 245) # Light peach card background
    pdf.rect(10, pdf.get_y(), 190, 22, "F")
    
    pdf.set_y(pdf.get_y() + 4)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(239, 68, 68) # Coral red
    pdf.cell(0, 5, "    OUTPUT PREDIKSI MODEL:", ln=True, align="L")
    
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(255, 127, 102) # Coral accent
    hasil_str = f"{data.get('hasil_prediksi', 0.0):.2f}%"
    pdf.cell(0, 8, f"    Tingkat Partisipasi Politik Prediksi: {hasil_str}", ln=True, align="L")
    
    pdf.ln(10)
    
    # Model evaluation metrics
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "2. Performa Model Acuan (Random Forest Regressor)", ln=True)
    pdf.ln(2)
    
    metrics = data.get("model_metrics", {})
    r2 = metrics.get("r2", 0.0)
    rmse = metrics.get("rmse", 0.0)
    mae = metrics.get("mae", 0.0)
    
    # Draw a clean, borderless metric block
    pdf.set_fill_color(248, 250, 252) # Soft light slate background
    pdf.rect(10, pdf.get_y(), 190, 16, "F")
    
    pdf.set_y(pdf.get_y() + 4)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(71, 85, 105)
    
    pdf.cell(63, 8, f"   R2 Score :  {r2:.4f} ({r2*100:.1f}%)", ln=False)
    pdf.cell(63, 8, f"   RMSE :  {rmse:.4f}", ln=False)
    pdf.cell(64, 8, f"   MAE :  {mae:.4f}", ln=True)
    
    pdf.ln(6)
    pdf.set_font("helvetica", "I", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(0, 4, "* Catatan: Nilai R2 menggambarkan persentase pengaruh parameter demografi di atas terhadap variasi tingkat partisipasi politik. RMSE yang semakin mendekati 0 menunjukkan keakuratan prediksi model yang semakin tinggi.", align="L")
    
    # Return PDF bytes
    return bytes(pdf.output())


def generate_visualization_pdf(data: dict) -> bytes:
    """
    Generates a PDF report containing visualization summaries, side-by-side charts, and academic explanations.
    Expected data structure:
      - active_year (int)
      - selected_areas (list)
      - correlation_data (list of dicts with 'variabel' and 'korelasi')
      - average_data (list of dicts with 'kecamatan' and 'partisipasi_politik')
      - comparison_year1 (int)
      - comparison_year2 (int)
      - comparison_data (list of dicts with 'kecamatan', 'partisipasi_y1', 'partisipasi_y2', 'selisih')
      - path_corr (str)
      - path_area (str)
      - path_comp (str)
      - printed_by (str)
    """
    pdf = PolPartPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    
    # Title
    pdf.set_y(30)
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(255, 127, 102) # Coral
    pdf.cell(0, 10, "LAPORAN VISUALISASI DAN ANALISIS PARTISIPASI POLITIK", ln=True, align="L")
    
    # Metadata info (2 columns)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(71, 85, 105) # Slate grey
    col_width = 90
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    pdf.cell(col_width, 5, f"Tanggal Cetak: {current_time}", ln=False)
    pdf.cell(col_width, 5, f"Dicetak Oleh: {data.get('printed_by', 'Guest')}", ln=True)
    pdf.cell(col_width, 5, f"Tahun Pemilu Aktif: {data.get('active_year', '-')}", ln=False)
    
    areas_str = ", ".join(data.get("selected_areas", [])) if data.get("selected_areas") else "Semua Kecamatan"
    pdf.cell(col_width, 5, f"Filter Wilayah: {areas_str}", ln=True)
    
    pdf.ln(3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    # 1. Analisis Korelasi Demografi
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "1. Hasil Analisis Korelasi Pearson (Variabel Demografi vs Partisipasi)", ln=True)
    pdf.ln(1)
    
    start_y_corr = pdf.get_y()
    
    # Table of correlation (Left Column - 95mm wide)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(234, 248, 248)
    pdf.cell(50, 5.5, " Nama Variabel Demografi", border=1, fill=True, align="L")
    pdf.cell(20, 5.5, " Korelasi", border=1, fill=True, align="C")
    pdf.cell(25, 5.5, " Hubungan", border=1, fill=True, align="C", ln=True)
    
    pdf.set_font("helvetica", "", 8)
    
    corr_list = data.get("correlation_data", [])
    corr_list = sorted(corr_list, key=lambda x: abs(x.get("korelasi", 0.0)), reverse=True)
    
    strongest_pos = None
    strongest_neg = None
    max_pos_val = 0.0
    min_neg_val = 0.0
    
    for item in corr_list:
        var_name = item.get("variabel", "")
        val = item.get("korelasi", 0.0)
        
        # Determine strength
        abs_val = abs(val)
        if abs_val >= 0.8:
            strength = "Sangat Kuat"
        elif abs_val >= 0.6:
            strength = "Kuat"
        elif abs_val >= 0.4:
            strength = "Sedang"
        elif abs_val >= 0.2:
            strength = "Lemah"
        else:
            strength = "Sangat Lemah"
            
        # Handle nan values cleanly
        import math
        if math.isnan(val):
            val_str = "N/A"
            strength = "N/A"
        else:
            val_str = f"{val:.4f}"
            if val > 0:
                strength += " (+)"
                if val > max_pos_val:
                    max_pos_val = val
                    strongest_pos = var_name
            else:
                strength += " (-)"
                if val < min_neg_val:
                    min_neg_val = val
                    strongest_neg = var_name
                
        # Format display name
        display_name = var_name
        if var_name == "dpt": display_name = "Jumlah DPT TPS"
        elif var_name == "rasio_dpt_terhadap_penduduk_kelurahan": display_name = "Rasio DPT Kelurahan"
        elif var_name == "pendapatan_per_kapita": display_name = "Pendapatan Per Kapita"
        elif var_name == "tingkat_pengangguran": display_name = "Tingkat Pengangguran"
        elif var_name == "kepadatan_penduduk": display_name = "Kepadatan Penduduk"
        elif var_name == "ipm": display_name = "Indeks Pembangunan Manusia"
        elif var_name == "persen_usia_17_24_kec": display_name = "Proporsi Usia 17-24"
        elif var_name == "persen_usia_25_44_kec": display_name = "Proporsi Usia 25-44"
        elif var_name == "persen_usia_45_plus_kec": display_name = "Proporsi Usia 45+"
        
        pdf.cell(50, 5, f" {display_name}", border=1, align="L")
        pdf.cell(20, 5, f" {val_str}", border=1, align="C")
        pdf.cell(25, 5, f" {strength}", border=1, align="C", ln=True)
        
    table_end_y_corr = pdf.get_y()
    
    # Render Heatmap image on the Right Column (90mm wide)
    path_corr = data.get("path_corr")
    if path_corr:
        pdf.image(path_corr, x=110, y=start_y_corr, w=90, h=50)
        
    # Synchronize Y position
    pdf.set_y(max(table_end_y_corr, start_y_corr + 50) + 3)
    
    # Narrative explanation
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 4.5, "Interpretasi Akademis Korelasi:", ln=True)
    pdf.set_font("helvetica", "", 8.5)
    pdf.set_text_color(71, 85, 105)
    
    def trans(v):
        if v == "dpt": return "Jumlah DPT TPS"
        if v == "rasio_dpt_terhadap_penduduk_kelurahan": return "Rasio DPT Kelurahan"
        if v == "pendapatan_per_kapita": return "Pendapatan Per Kapita"
        if v == "tingkat_pengangguran": return "Tingkat Pengangguran"
        if v == "kepadatan_penduduk": return "Kepadatan Penduduk"
        if v == "ipm": return "Indeks Pembangunan Manusia (IPM)"
        if v == "persen_usia_17_24_kec": return "Proporsi Usia 17-24"
        if v == "persen_usia_25_44_kec": return "Proporsi Usia 25-44"
        if v == "persen_usia_45_plus_kec": return "Proporsi Usia 45+"
        return str(v)
        
    pos_desc = f"Variabel dengan korelasi positif terkuat adalah {trans(strongest_pos)} ({max_pos_val:.4f}). Hal ini menunjukkan bahwa wilayah dengan {trans(strongest_pos)} yang tinggi memiliki tingkat partisipasi pemilih yang cenderung lebih tinggi." if strongest_pos else "Tidak ditemukan variabel dengan korelasi positif yang signifikan."
    neg_desc = f"Sementara itu, variabel dengan korelasi negatif terkuat adalah {trans(strongest_neg)} ({min_neg_val:.4f}). Hal ini berarti bahwa semakin tinggi {trans(strongest_neg)} di suatu wilayah, tingkat partisipasi politik cenderung lebih rendah." if strongest_neg else "Tidak ditemukan variabel dengan korelasi negatif yang signifikan."
    
    explanation_text = f"Nilai koefisien korelasi Pearson berkisar antara -1 hingga +1. Korelasi positif (+) mengindikasikan hubungan yang searah, sedangkan korelasi negatif (-) mengindikasikan hubungan yang berlawanan arah. {pos_desc} {neg_desc}"
    pdf.multi_cell(0, 4, explanation_text, align="L")
    
    pdf.ln(4)
    
    # 2. Analisis Rata-rata Partisipasi per Kecamatan
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, f"2. Rata-rata Partisipasi Politik per Kecamatan (Tahun Pemilu {data.get('active_year')})", ln=True)
    pdf.ln(1)
    
    start_y_avg = pdf.get_y()
    
    # Table of average turnout (Left Column - 95mm wide)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(234, 248, 248)
    pdf.cell(55, 6, " Nama Kecamatan", border=1, fill=True, align="L")
    pdf.cell(40, 6, " Rata-rata Partisipasi (%)", border=1, fill=True, align="C", ln=True)
    
    pdf.set_font("helvetica", "", 8)
    avg_list = data.get("average_data", [])
    
    highest_kec = None
    highest_val = 0.0
    lowest_kec = None
    lowest_val = 100.0
    
    for item in avg_list:
        kec = item.get("kecamatan", "")
        part = item.get("partisipasi_politik", 0.0)
        
        if part > highest_val:
            highest_val = part
            highest_kec = kec
        if part < lowest_val:
            lowest_val = part
            lowest_kec = kec
            
        pdf.cell(55, 5.5, f" {kec}", border=1, align="L")
        pdf.cell(40, 5.5, f" {part:.2f}%", border=1, align="C", ln=True)
        
    table_end_y_avg = pdf.get_y()
    
    # Render Bar Chart image on the Right Column (90mm wide)
    path_area = data.get("path_area")
    if path_area:
        pdf.image(path_area, x=110, y=start_y_avg, w=90, h=40)
        
    # Synchronize Y position
    pdf.set_y(max(table_end_y_avg, start_y_avg + 40) + 3)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 4.5, "Interpretasi Tingkat Partisipasi:", ln=True)
    pdf.set_font("helvetica", "", 8.5)
    
    turnout_explanation = f"Berdasarkan sebaran wilayah di atas untuk Pemilu {data.get('active_year')}, tingkat partisipasi politik tertinggi dicapai oleh Kecamatan {highest_kec} dengan rata-rata {highest_val:.2f}%. Sebaliknya, Kecamatan {lowest_kec} mencatat tingkat partisipasi politik terendah dengan rata-rata {lowest_val:.2f}%."
    pdf.multi_cell(0, 4, turnout_explanation, align="L")
    
    # 3. Perbandingan Historis
    pdf.add_page()
    
    pdf.set_y(30)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    
    y1 = data.get("comparison_year1")
    y2 = data.get("comparison_year2")
    pdf.cell(0, 8, f"3. Analisis Perbandingan Historis (Pemilu {y1} vs Pemilu {y2})", ln=True)
    pdf.ln(1)
    
    start_y_comp = pdf.get_y()
    
    # Table of comparison (Left Column - 95mm wide)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(234, 248, 248)
    pdf.cell(45, 6, " Nama Kecamatan", border=1, fill=True, align="L")
    pdf.cell(18, 6, f" {y1} (%)", border=1, fill=True, align="C")
    pdf.cell(18, 6, f" {y2} (%)", border=1, fill=True, align="C")
    pdf.cell(14, 6, " Selisih", border=1, fill=True, align="C", ln=True)
    
    pdf.set_font("helvetica", "", 8)
    comp_list = data.get("comparison_data", [])
    
    best_grow_kec = None
    max_grow = -100.0
    
    for item in comp_list:
        kec = item.get("kecamatan", "")
        val_y1 = item.get(f"partisipasi_{y1}", 0.0)
        val_y2 = item.get(f"partisipasi_{y2}", 0.0)
        diff = item.get("selisih", val_y2 - val_y1)
        
        if diff > max_grow:
            max_grow = diff
            best_grow_kec = kec
            
        sign = "+" if diff >= 0 else ""
        pdf.cell(45, 5.5, f" {kec}", border=1, align="L")
        pdf.cell(18, 5.5, f" {val_y1:.2f}%", border=1, align="C")
        pdf.cell(18, 5.5, f" {val_y2:.2f}%", border=1, align="C")
        pdf.cell(14, 5.5, f" {sign}{diff:.2f}%", border=1, align="C", ln=True)
        
    table_end_y_comp = pdf.get_y()
    
    # Render Comparison Chart image on the Right Column (90mm wide)
    path_comp = data.get("path_comp")
    if path_comp:
        pdf.image(path_comp, x=110, y=start_y_comp, w=90, h=40)
        
    # Synchronize Y position
    pdf.set_y(max(table_end_y_comp, start_y_comp + 40) + 3)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 4.5, "Interpretasi Perbandingan Tren:", ln=True)
    pdf.set_font("helvetica", "", 8.5)
    
    growth_word = "peningkatan" if max_grow >= 0 else "penurunan terkecil"
    comp_explanation = f"Perbandingan antara pemilu tahun {y1} dan {y2} memperlihatkan fluktuasi tingkat partisipasi politik pemilih per kecamatan. Kecamatan yang mengalami tren {growth_word} partisipasi politik tertinggi adalah {best_grow_kec} dengan selisih mencapai {max_grow:+.2f}%."
    pdf.multi_cell(0, 4, comp_explanation, align="L")
    
    return bytes(pdf.output())
