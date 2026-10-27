import streamlit as st
from pathlib import Path
from src.config import STYLE_PATH
from streamlit_option_menu import option_menu

# Mengatur konfigurasi halaman secara global (Hanya boleh dipanggil sekali di file utama ini!)
# page_title: Judul yang muncul di tab browser
# layout="wide": Menggunakan lebar layar penuh
# initial_sidebar_state="expanded": Membiarkan menu samping (sidebar) terbuka sejak awal
st.set_page_config(
    page_title="Sistem Prediksi Partisipasi Politik",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Mengambil status login dari session state
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.html("""
        <style>
        /* Sembunyikan sidebar sepenuhnya saat belum login */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        .stApp {
            background-color: #eaf8f8 !important;
        }
        .login-card {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            max-width: 450px;
            margin: 80px auto 0 auto;
            border-top: 5px solid #ff7f66;
        }
        .login-title {
            color: #1e293b;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 800;
            text-align: center;
            margin-bottom: 20px;
        }
        div[data-baseweb="tab-list"] {
            justify-content: center;
        }
        </style>
    """)
    
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="login-title">Masuk PolPart RF</h2>', unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["Masuk", "Daftar Akun"])
        
        with tab_login:
            with st.form("login_form_main"):
                user_val = st.text_input("Username", key="login_username")
                pass_val = st.text_input("Password", type="password", key="login_password")
                submit_login = st.form_submit_button("Masuk", use_container_width=True)
                if submit_login:
                    from src.database import check_login, seed_admin
                    seed_admin()
                    res = check_login(user_val, pass_val)
                    if res:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = res["username"]
                        st.session_state["role"] = res["role"]
                        st.success(f"Selamat datang {res['username']}!")
                        st.rerun()
                    else:
                        st.error("Gagal: Username atau Password salah.")
                        
        with tab_register:
            with st.form("register_form_main"):
                reg_user = st.text_input("Username Baru", key="reg_username")
                reg_pass = st.text_input("Password Baru", type="password", key="reg_password")
                reg_pass_conf = st.text_input("Konfirmasi Password", type="password", key="reg_password_conf")
                reg_actor = st.selectbox(
                    "Pilih Instansi / Role",
                    ["Masyarakat", "Operator KPU", "Bakesbangpol", "BPS", "Dukcapil"],
                    key="reg_role_actor"
                )
                submit_reg = st.form_submit_button("Daftar Sekarang", use_container_width=True)
                if submit_reg:
                    if not reg_user.strip() or not reg_pass.strip():
                        st.error("Username dan password tidak boleh kosong.")
                    elif reg_pass != reg_pass_conf:
                        st.error("Konfirmasi password tidak cocok.")
                    else:
                        from src.database import register_user
                        role_map = {
                            "Masyarakat": "user",
                            "Operator KPU": "kpu",
                            "Bakesbangpol": "bakesbangpol",
                            "BPS": "bps",
                            "Dukcapil": "dukcapil"
                        }
                        db_role = role_map.get(reg_actor, "user")
                        if register_user(reg_user, reg_pass, db_role):
                            st.success("Registrasi berhasil! Silakan masuk di tab Login.")
                        else:
                            st.error("Username sudah terdaftar. Silakan pilih username lain.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Memasukkan kode CSS kustom untuk mempercantik tampilan agar lebih rapi
if STYLE_PATH.exists():
    st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Mendefinisikan halaman-halaman yang ada di sistem
dashboard = st.Page("pages/1_Dashboard.py", title="Dashboard", default=True)
data_historis = st.Page("pages/2_Data_Historis.py", title="Data Historis")
prediksi = st.Page("pages/3_Prediksi.py", title="Prediksi RF")
visualisasi = st.Page("pages/4_Visualisasi.py", title="Visualisasi & Peta")
tentang = st.Page("pages/5_Tentang.py", title="Tentang Aplikasi")
kelola_data = st.Page("pages/6_Kelola_Data.py", title="Kelola Data")

# Membuat menu navigasi kustom menggunakan library streamlit-option-menu
page_names = ["Dashboard", "Data Historis", "Prediksi", "Visualisasi", "Tentang"]
page_files = [
    "pages/1_Dashboard.py",
    "pages/2_Data_Historis.py",
    "pages/3_Prediksi.py",
    "pages/4_Visualisasi.py",
    "pages/5_Tentang.py"
]
page_icons = ["grid-fill", "table", "cpu", "map-fill", "info-circle-fill"]

if st.session_state.get("role") in ["admin", "kpu"]:
    page_names.insert(4, "Kelola Data")
    page_files.insert(4, "pages/6_Kelola_Data.py")
    page_icons.insert(4, "database-fill")

current_page = st.session_state.get("current_page", "Dashboard")
try:
    default_index = page_names.index(current_page)
except ValueError:
    default_index = 0

# Menggambar menu sidebar di sebelah kiri layar
with st.sidebar:
    # Profil Pengguna
    role_db = st.session_state.get("role", "user")
    role_label_map = {
        "admin": "Operator KPU",
        "kpu": "Operator KPU",
        "bakesbangpol": "Bakesbangpol",
        "bps": "BPS",
        "dukcapil": "Dukcapil",
        "user": "Masyarakat"
    }
    role_label = role_label_map.get(role_db, "Masyarakat")
    st.markdown(f"""
        <div style="padding: 10px; background-color: #eaf8f8; border-radius: 8px; border-left: 5px solid #ff7f66; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 11px; color: #64748b; font-weight: bold;">PENGGUNA AKTIF</p>
            <p style="margin: 0; font-size: 14px; font-weight: 800; color: #1e293b;">{st.session_state.get('username', 'Guest')}</p>
            <span style="font-size: 10px; padding: 2px 6px; background-color: #ff7f66; color: white; border-radius: 4px; font-weight: bold; text-transform: uppercase;">{role_label}</span>
        </div>
    """, unsafe_allow_html=True)

    selected = option_menu(
        "PolPart RF",
        options=page_names,
        icons=page_icons,
        menu_icon="activity",
        default_index=default_index,
        styles={
            "container": {"background-color": "#ffffff", "padding": "5px 0px"},
            "icon": {"color": "#475569", "font-size": "15px"},
            "menu-title": {"color": "#1E293B", "font-family": "Plus Jakarta Sans", "font-weight": "800"},
            "nav-link": {
                "color": "#475569",
                "font-family": "Plus Jakarta Sans",
                "font-weight": "600",
                "font-size": "13px",
                "text-align": "left",
                "margin": "0px",
            },
            "nav-link-selected": {"background-color": "#ff7f66", "color": "#FFFFFF"},
        }
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Keluar (Logout)", use_container_width=True, key="logout_btn_main"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None
        st.rerun()

# Jika pengguna mengklik menu lain, pindahkan halamannya (switch_page)
if selected != current_page:
    st.session_state["current_page"] = selected
    st.switch_page(page_files[page_names.index(selected)])

# Membuat navigasi bawaan streamlit dan menjalankannya secara tersembunyi
# position="hidden" digunakan agar menu default Streamlit tidak muncul (tidak dobel dengan menu kustom kita)
pages_to_register = [dashboard, data_historis, prediksi, visualisasi]
if st.session_state.get("role") in ["admin", "kpu"]:
    pages_to_register.append(kelola_data)
pages_to_register.append(tentang)

pg = st.navigation(pages_to_register, position="hidden")
pg.run()
