"""
Modul untuk mengatur elemen antarmuka pengguna (UI) menggunakan Streamlit.
Berisi fungsi-fungsi untuk menampilkan header, kartu metrik (metric card),
dan sidebar untuk filter serta unggah data.
"""
import streamlit as st

from src.config import APP_SUBTITLE, APP_TITLE, STYLE_PATH
from src.data_loader import load_dataset


def setup_page(title: str = APP_TITLE):
    # Map title to navigation option
    title_mapping = {
        "Dashboard": "Dashboard",
        "Data Historis": "Data Historis",
        "Prediksi": "Prediksi",
        "Visualisasi": "Visualisasi",
        "Tentang": "Tentang",
        "Kelola Data": "Kelola Data"
    }
    st.session_state["current_page"] = title_mapping.get(title, "Dashboard")
    inject_css()


def inject_css():
    if STYLE_PATH.exists():
        st.html(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>")


def render_header(title: str, subtitle: str | None = None):
    html_content = f"""<div class="hero-container">
<div class="breadcrumb">BERANDA &nbsp;&rsaquo;&nbsp; {title}</div>
<h1 class="hero-title">{title}</h1>
<p class="hero-subtitle">{subtitle or ""}</p>
</div>"""
    st.html(html_content.replace("\n", " ").strip())


def custom_metric_card(header: str, value: str, icon: str = "", trend_text: str = "", trend_type: str = "up") -> str:
    if trend_type == "up":
        trend_class = "trend-up"
        badge_class = "badge-green"
    elif trend_type == "down":
        trend_class = "trend-down"
        badge_class = "badge-purple"
    else:
        trend_class = "trend-neutral"
        badge_class = "badge-orange"
        
    icon_html = f'<span class="card-badge {badge_class}">{icon}</span>' if icon else ''
    html_content = f"""<div class="dashboard-card">
<div class="card-header">{header}</div>
<div class="card-body">
<div class="card-row">
<span class="card-value">{value}</span>
{icon_html}
</div>
<div class="card-trend {trend_class}">{trend_text}</div>
</div>
</div>"""
    return html_content.replace("\n", " ").strip()


def load_data_from_sidebar():
    """Loads dataset from database without displaying any sidebar widgets."""
    from src.data_loader import load_dataset
    return load_dataset()


def metric_card(label: str, value: str, help_text: str | None = None):
    st.metric(label=label, value=value, help=help_text)
