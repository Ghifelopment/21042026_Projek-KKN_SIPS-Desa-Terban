import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import time
from streamlit_cookies_manager import EncryptedCookieManager
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIG & AUTH SETTINGS (Password dikunci di sini) ---
PASSWORD_BENAR = "klitihandbandit"
TIMEOUT_SECONDS = 3600  # 1 Jam (3600 detik)
COOKIE_PASSWORD = "sips_kkn_gondokusuman_2026"  # kunci enkripsi cookie

# --- FUNGSI BACKGROUND & DECODER ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

def set_png_as_page_bg(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.8)), 
        url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-attachment: fixed;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Pengelolaan Sampah", page_icon="🗑️", layout="wide")

# --- 2. SESSION & TIMEOUT MANAGEMENT ---
# Setup cookie manager — harus dipanggil sebelum widget apapun
cookies = EncryptedCookieManager(prefix="sips_", password=COOKIE_PASSWORD)
if not cookies.ready():
    st.stop()  # tunggu cookie siap

# Inisialisasi session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'last_activity' not in st.session_state:
    st.session_state.last_activity = time.time()

# Cek cookie: kalau ada cookie login_time yang valid, langsung autentikasi
# Hanya pakai 1 cookie: "login_time" berisi timestamp saat login/aktivitas terakhir
if not st.session_state.authenticated:
    cookie_time = cookies.get("login_time")
    if cookie_time:
        try:
            last_t = float(cookie_time)
            if time.time() - last_t <= TIMEOUT_SECONDS:
                st.session_state.authenticated = True
                st.session_state.last_activity = last_t
        except:
            pass

# Cek timeout: kalau sudah 1 jam tidak aktif, hapus cookie & logout
if st.session_state.authenticated:
    durasi_aktif = time.time() - st.session_state.last_activity
    if durasi_aktif > TIMEOUT_SECONDS:
        st.session_state.authenticated = False
        cookies["login_time"] = ""
        cookies.save()
        st.rerun()

# Update waktu aktivitas di session state & cookie setiap interaksi
st.session_state.last_activity = time.time()
if st.session_state.authenticated:
    cookies["login_time"] = str(st.session_state.last_activity)
    cookies.save()

# --- 3. INTRO PAGE --- (TIDAK DIUBAH)
if 'animated' not in st.session_state:
    img_base64 = get_base64_of_bin_file("background.png") if os.path.exists("background.png") else ""
    bg_css = f'url("data:image/png;base64,{img_base64}")' if img_base64 else "none"

    splash = st.empty()
    with splash.container():
        st.markdown(f"""
            <style>
            header, footer, [data-testid="stSidebar"] {{ display: none !important; }}

            #splash-overlay {{
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background: black;
                z-index: 10001;
                pointer-events: none;
                animation: overlayFadeIn 1.0s ease forwards;
            }}
            @keyframes overlayFadeIn {{
                0%   {{ opacity: 1; }}
                100% {{ opacity: 0; }}
            }}

            #splash-screen {{
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background-image: 
                    linear-gradient(rgba(15, 23, 42, 0.75), rgba(15, 23, 42, 0.75)), 
                    {bg_css};
                background-size: cover;
                background-position: center;
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                animation: bgBlurAnim 6.5s ease forwards;
            }}
            @keyframes bgBlurAnim {{
                0%   {{ filter: blur(0px); }}
                76%  {{ filter: blur(0px); }}
                100% {{ filter: blur(20px); }}
            }}

            .splash-content {{
                text-align: center;
                animation: textAnim 6.5s ease forwards;
            }}
            @keyframes textAnim {{
                0%   {{ opacity: 0; transform: translateY(8px); }}
                15%  {{ opacity: 0; transform: translateY(8px); }}
                30%  {{ opacity: 1; transform: translateY(0px); }}
                69%  {{ opacity: 1; transform: translateY(0px); }}
                77%  {{ opacity: 0; transform: translateY(-5px); }}
                100% {{ opacity: 0; }}
            }}

            .splash-logo {{
                font-size: 3.5rem;
                font-weight: 800;
                background: linear-gradient(90deg, #FFFFFF 0%, #FFD700 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: 2px;
                line-height: 1.2;
                margin-bottom: 25px;
            }}

            .splash-loading {{
                font-size: 1.4rem !important;
                font-weight: 600 !important;
                color: #94A3B8;
                letter-spacing: 6px;
                margin-top: 0px;
                animation: blinkAnim 0.8s step-start infinite;
                animation-delay: 2s;
            }}
            @keyframes blinkAnim {{
                0%, 100% {{ opacity: 1; }}
                50%       {{ opacity: 0; }}
            }}
            </style>

            <div id="splash-overlay"></div>
            <div id="splash-screen">
                <div class="splash-content">
                    <div class="splash-logo">KKN KEMANTREN<br>GONDOKUSUMAN</div>
                    <p class="splash-loading">LOADING SYSTEM...</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        time.sleep(6.8)

    splash.empty()
    st.session_state.animated = True

# --- 4. LOGIN PAGE --- (TIDAK DIUBAH)
if not st.session_state.authenticated:
    img_base64 = get_base64_of_bin_file("background.png") if os.path.exists("background.png") else ""
    bg_css = f'url("data:image/png;base64,{img_base64}")' if img_base64 else "none"

    st.markdown(f"""
        <style>
        header {{ visibility: hidden; }}

        .stApp {{
            background-image: 
                linear-gradient(rgba(15, 23, 42, 0.7), rgba(15, 23, 42, 0.7)), 
                {bg_css};
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        #root > div:nth-child(1) > div.withScreencast > div > div {{
            backdrop-filter: blur(25px) !important;
            -webkit-backdrop-filter: blur(25px) !important;
            background: rgba(15, 23, 42, 0.4);
        }}

        div[data-testid="stForm"] {{
            background: rgba(30, 41, 59, 0.6) !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 15px !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            padding: 30px !important;
            opacity: 0;
            animation: boxFadeIn 1.0s ease forwards;
            animation-delay: 1.5s;
        }}
        @keyframes boxFadeIn {{
            0%   {{ opacity: 0; transform: translateY(12px); }}
            100% {{ opacity: 1; transform: translateY(0px); }}
        }}
        </style>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("""
                <div style='text-align: center; background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                    <h2 style='color: white; margin: 0; font-size: 1.8rem; letter-spacing: 2px;'>🔐 Admin Access</h2>
                    <p style='color: #94A3B8; font-size: 0.85rem; margin-top: 5px; opacity: 0.8; letter-spacing: 1px;'>
                        SISTEM INFORMASI PENGELOLAAN SAMPAH
                    </p>
                </div>
            """, unsafe_allow_html=True)

            st.text_input("Username", value="Admin", disabled=True)
            pwd_input = st.text_input("Password", type="password", placeholder="Ketik password...")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Masuk", use_container_width=True):
                if pwd_input == PASSWORD_BENAR:
                    st.session_state.authenticated = True
                    st.session_state.just_logged_in = True  # flag untuk transisi
                    st.rerun()
                else:
                    st.error("Password Salah!")
    st.stop()

# --- 5. THEME & CSS FIX (DASHBOARD UTAMA) --- (TIDAK DIUBAH)
if os.path.exists("background.png"):
    set_png_as_page_bg('background.png')
else:
    st.markdown("<style>.stApp { background-color: #121212; }</style>", unsafe_allow_html=True)

st.markdown("""
    <style>
    .stApp { color: #FFFFFF; }
    .metric-box { 
        background-color: rgba(30, 30, 30, 0.6); 
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 10px; text-align: center; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
    }
    [data-testid="stSidebar"] { background-color: rgba(30, 30, 30, 0.9); }
    button[step] { visibility: visible !important; }
    [data-testid="stButton"] button div::after, 
    [data-testid="stDownloadButton"] button div::after {
        content: none !important;
        display: none !important;
    }

    /* Expander header: samakan persis dengan tombol Ekspor CSV */
    [data-testid="stExpander"] details summary {
        background-color: rgb(19, 23, 32) !important;
        border: 1px solid rgba(250, 250, 250, 0.2) !important;
        border-radius: 8px !important;
        color: white !important;
    }
    [data-testid="stExpander"] details summary:hover {
        background-color: rgb(30, 35, 48) !important;
        border-color: rgba(250, 250, 250, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TRANSISI LOGIN → MAIN PAGE (fade + zoom in, hanya saat baru login) ---
# Cara kerja: saat login berhasil, set flag just_logged_in = True
# Saat Main Page pertama kali render, CSS animasi diinjeksi lalu flag di-reset
if st.session_state.get("just_logged_in", False):
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] > .main {
            animation: mainPageEnter 1.2s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        @keyframes mainPageEnter {
            0%   { opacity: 0; transform: scale(0.97); }
            100% { opacity: 1; transform: scale(1.0); }
        }
        </style>
    """, unsafe_allow_html=True)
    st.session_state.just_logged_in = False  # reset agar tidak animasi terus

# --- 6. DATABASE SETUP & HARGA ---
MASTER_FILE = "master_sampah.csv"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1HMb1NVh8uWgtuUtdrO_s_MNhc14jbYFqTdBOalyYKms"
SHEET_NAME = "Sheet1"

# Harga & jenis default
HARGA_ANORGANIK_DEFAULT = {
    "Botol PET Bening": 3000, "Botol PET Warna": 1500, "Plastik Keras (Ember/Kursi)": 2250,
    "Plastik Kresek/LDPE": 1750, "Gelas Plastik": 4500, "Kardus": 2000,
    "Kertas Putih (HVS/Buku)": 1500, "Koran/Majalah": 1250, "Aluminium (Kaleng Minuman)": 11500,
    "Besi/Logam Campuran": 3000, "Tembaga": 65000, "Botol Kaca/Bening": 350
}
JENIS_ORGANIK_DEFAULT = ["Sisa Makanan", "Daun Kering", "Sisa Buah", "Sisa Sayuran"]
JENIS_B3_DEFAULT = ["Baterai Bekas", "Lampu Neon", "Limbah Medis"]

COLS_URUTAN = ["Nomor", "Waktu Setoran", "Nama", "Klasifikasi Sampah", "Jenis Sampah", "Berat (Kg)", "Estimasi Saldo"]

@st.cache_resource
def get_gsheet_client():
    """Koneksi ke Google Sheets — di-cache permanen, tidak dibuat ulang setiap rerun."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    except:
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    return gspread.authorize(creds)

def get_worksheet():
    """Ambil worksheet — pakai client yang sudah di-cache."""
    client = get_gsheet_client()
    sheet = client.open_by_url(SHEET_URL)
    return sheet.worksheet(SHEET_NAME)

@st.cache_data(ttl=30)
def load_data():
    """Load data dari Google Sheets. Cache 10 detik untuk hindari quota exceeded."""
    try:
        ws = get_worksheet()
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLS_URUTAN)
        df = pd.DataFrame(data)
        for col in COLS_URUTAN:
            if col not in df.columns:
                df[col] = ""
        return df[COLS_URUTAN]
    except Exception as e:
        st.error(f"❌ Gagal load data dari Google Sheets: {e}")
        return pd.DataFrame(columns=COLS_URUTAN)

def save_data(df):
    """Simpan seluruh dataframe ke Google Sheets (overwrite)."""
    try:
        ws = get_worksheet()
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())
        load_data.clear()  # clear cache supaya data langsung fresh
    except Exception as e:
        st.error(f"❌ Gagal simpan data ke Google Sheets: {e}")

def load_master():
    """Load data master dari CSV lokal. Jika belum ada, buat dari default."""
    if os.path.exists(MASTER_FILE):
        try:
            return pd.read_csv(MASTER_FILE)
        except:
            pass
    rows = []
    for nama, harga in HARGA_ANORGANIK_DEFAULT.items():
        rows.append({"Klasifikasi": "Anorganik", "Jenis": nama, "Harga": harga})
    for nama in JENIS_ORGANIK_DEFAULT:
        rows.append({"Klasifikasi": "Organik", "Jenis": nama, "Harga": 0})
    for nama in JENIS_B3_DEFAULT:
        rows.append({"Klasifikasi": "B3 (Bahan Berbahaya)", "Jenis": nama, "Harga": 0})
    df_m = pd.DataFrame(rows)
    df_m.to_csv(MASTER_FILE, index=False)
    return df_m

def get_harga_dict(df_m):
    df_anorg = df_m[df_m["Klasifikasi"] == "Anorganik"]
    return dict(zip(df_anorg["Jenis"], df_anorg["Harga"].astype(int)))

def get_jenis_by_klasifikasi(df_m, klasifikasi):
    return df_m[df_m["Klasifikasi"] == klasifikasi]["Jenis"].tolist()

# Load master
df_master = load_master()
HARGA_ANORGANIK = get_harga_dict(df_master)
JENIS_ORGANIK = get_jenis_by_klasifikasi(df_master, "Organik")
JENIS_B3 = get_jenis_by_klasifikasi(df_master, "B3 (Bahan Berbahaya)")

# --- 7. SIDEBAR: INPUT DATA --- (TIDAK DIUBAH, hanya list jenis dari master)
with st.sidebar:
    st.markdown("## 📥 Form Setoran")
    nama_raw = st.text_input("Nama Pengumpul", key="nama_reset")
    klasifikasi = st.selectbox("Pilih Klasifikasi Sampah",
                               ["-- Pilih --", "Anorganik", "Organik", "B3 (Bahan Berbahaya)"], key="klas_reset")

    jenis_final = ""
    if klasifikasi == "Anorganik":
        pilihan = st.selectbox("Daftar Sampah Anorganik", list(HARGA_ANORGANIK.keys()) + ["Lainnya"], key="jenis_anorg")
        jenis_final = st.text_input("Ketik Jenis Lainnya:", key="man_anorg") if pilihan == "Lainnya" else pilihan
    elif klasifikasi == "Organik":
        pilihan = st.selectbox("Daftar Sampah Organik", JENIS_ORGANIK + ["Lainnya"], key="jenis_org")
        jenis_final = st.text_input("Ketik Jenis Lainnya:", key="man_org") if pilihan == "Lainnya" else pilihan
    elif klasifikasi == "B3 (Bahan Berbahaya)":
        pilihan = st.selectbox("Daftar Sampah B3", JENIS_B3 + ["Lainnya"], key="jenis_b3")
        jenis_final = st.text_input("Ketik Jenis Lainnya:", key="man_b3") if pilihan == "Lainnya" else pilihan

    berat_gram = st.number_input("Berat (Gram)", min_value=0, step=1, key="berat_reset")

    st.markdown("<div style='margin-top: 75px;'></div>", unsafe_allow_html=True)

    if st.button("Simpan Data ✅", key="btn_simpan", use_container_width=True):
        if nama_raw and klasifikasi != "-- Pilih --" and jenis_final and berat_gram > 0:
            df_existing = load_data()
            nama_fix = nama_raw.strip().title()
            waktu_setoran = datetime.now().strftime("%d/%m/%Y %H:%M")
            berat_kg = round(berat_gram / 1000, 2)
            saldo_val = str(int(berat_kg * HARGA_ANORGANIK.get(jenis_final, 0))) if klasifikasi == "Anorganik" else "0"

            new_row = pd.DataFrame([[len(df_existing) + 1, waktu_setoran, nama_fix, klasifikasi, jenis_final, berat_kg, saldo_val]], columns=COLS_URUTAN)
            save_data(pd.concat([df_existing, new_row], ignore_index=True))
            st.rerun()

# --- 8. DASHBOARD UTAMA --- (TIDAK DIUBAH)
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='background: linear-gradient(90deg, #FFFFFF 0%, #FFD700 100%); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        font-size: 3.5rem; font-weight: 800; margin-bottom: 0px; filter: drop-shadow(0px 4px 8px rgba(255, 215, 0, 0.3));'>
        ♻️ PENGELOLAAN SAMPAH
        </h1>
        <p style='color: #E2E8F0; font-size: 1.2rem; font-weight: 500; margin-top: -10px; letter-spacing: 1px;'>
        KKN Kemantren Gondokusuman - Periode 1 Tahun 2026
        </p>
    </div>
    <br>
""", unsafe_allow_html=True)

df = load_data()

if not df.empty:
    df["Berat (Kg)"] = pd.to_numeric(df["Berat (Kg)"], errors='coerce').fillna(0)

    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='metric-box'><h3>Anorganik</h3><h2 style='color:#29b6f6;'>{df[df['Klasifikasi Sampah']=='Anorganik']['Berat (Kg)'].sum():.2f} kg</h2></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-box'><h3>Organik</h3><h2 style='color:#00c853;'>{df[df['Klasifikasi Sampah']=='Organik']['Berat (Kg)'].sum():.2f} kg</h2></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='metric-box'><h3>B3</h3><h2 style='color:#ff5252;'>{df[df['Klasifikasi Sampah']=='B3 (Bahan Berbahaya)']['Berat (Kg)'].sum():.2f} kg</h2></div>", unsafe_allow_html=True)

    t_saldo = df["Estimasi Saldo"].apply(lambda x: int(x) if str(str(x)).isdigit() else 0).sum()
    st.markdown(f"<div class='metric-box' style='margin-top:20px;'><h3>Total Saldo Akumulasi</h3><h1 style='color:#ffd700;'>Rp {t_saldo:,.0f}</h1></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    col_kiri, col_tengah, col_kanan = st.columns([2, 5, 2])

    with col_kiri:
        st.download_button("📥 Ekspor CSV", df.to_csv(index=False).encode('utf-8'), "SIPS_Terban.csv", "text/csv")

    with col_kanan:
        with st.expander("🛠️ Koreksi Data"):
            n_pilih = st.selectbox("Nomor Data:", df["Nomor"].tolist(), key="pilih_kor")
            idx = df[df["Nomor"] == n_pilih].index[0]

            klas_ed = st.selectbox("Koreksi Klasifikasi:", ["Anorganik", "Organik", "B3 (Bahan Berbahaya)"],
                                   index=["Anorganik", "Organik", "B3 (Bahan Berbahaya)"].index(df.at[idx, "Klasifikasi Sampah"]), key="klas_kor")

            jenis_ed = ""
            if klas_ed == "Anorganik":
                p_ed = st.selectbox("Koreksi Jenis Anorganik:", list(HARGA_ANORGANIK.keys()) + ["Lainnya"], key="j_an_kor")
                jenis_ed = st.text_input("Sebutkan:", key="m_an_kor") if p_ed == "Lainnya" else p_ed
            elif klas_ed == "Organik":
                p_ed = st.selectbox("Koreksi Jenis Organik:", JENIS_ORGANIK + ["Lainnya"], key="j_or_kor")
                jenis_ed = st.text_input("Sebutkan:", key="m_or_kor") if p_ed == "Lainnya" else p_ed
            elif klas_ed == "B3 (Bahan Berbahaya)":
                p_ed = st.selectbox("Koreksi Jenis B3:", JENIS_B3 + ["Lainnya"], key="j_b3_kor")
                jenis_ed = st.text_input("Sebutkan:", key="m_b3_kor") if p_ed == "Lainnya" else p_ed

            b_ed = st.number_input("Koreksi Berat (Kg):", value=float(df.at[idx, "Berat (Kg)"]), step=0.01, key="br_kor")
            h_ed = st.checkbox("Hapus baris ini", key="hp_kor")

            if st.button("Simpan Perubahan", key="btn_upd_final", use_container_width=True):
                if h_ed:
                    df = df.drop(idx).reset_index(drop=True)
                    df["Nomor"] = range(1, len(df) + 1)
                else:
                    df.at[idx, "Klasifikasi Sampah"] = klas_ed
                    df.at[idx, "Jenis Sampah"] = jenis_ed
                    df.at[idx, "Berat (Kg)"] = round(b_ed, 2)
                    df.at[idx, "Estimasi Saldo"] = str(int(b_ed * HARGA_ANORGANIK.get(jenis_ed, 0))) if klas_ed == "Anorganik" else "0"
                save_data(df)
                st.rerun()

else:
    st.info("👋 Belum ada data. Silakan isi form di samping.")

# --- 9. KELOLA DATA MASTER (BARU) ---
st.markdown("---")
with st.expander("🗂️ Kelola Data Master"):
    tab_harga, tab_jenis, tab_reset = st.tabs(["💰 Update Harga", "📋 Kelola Jenis Sampah", "🗑️ Reset Data"])

    # === TAB 1: UPDATE HARGA ===
    with tab_harga:
        st.markdown("#### Update Harga Sampah Anorganik")
        st.caption("Harga satuan dalam Rp/Kg")

        df_anorg = df_master[df_master["Klasifikasi"] == "Anorganik"].copy()

        if df_anorg.empty:
            st.info("Belum ada jenis sampah Anorganik.")
        else:
            jenis_pilih_harga = st.selectbox("Pilih Jenis Sampah:", df_anorg["Jenis"].tolist(), key="harga_pilih_jenis")
            harga_sekarang = int(df_anorg[df_anorg["Jenis"] == jenis_pilih_harga]["Harga"].values[0])
            st.markdown(f"Harga saat ini: **Rp {harga_sekarang:,}/Kg**")

            harga_baru = st.number_input("Harga Baru (Rp/Kg):", min_value=0, value=harga_sekarang, step=50, key="harga_baru_input")

            if st.button("💾 Simpan Harga", key="btn_simpan_harga", use_container_width=True):
                df_master.loc[
                    (df_master["Klasifikasi"] == "Anorganik") & (df_master["Jenis"] == jenis_pilih_harga),
                    "Harga"
                ] = harga_baru
                df_master.to_csv(MASTER_FILE, index=False)
                st.success(f"✅ Harga '{jenis_pilih_harga}' diupdate menjadi Rp {harga_baru:,}/Kg")
                st.rerun()

    # === TAB 2: KELOLA JENIS SAMPAH ===
    with tab_jenis:
        st.markdown("#### Tambah Jenis Sampah Baru")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            klas_baru = st.selectbox("Klasifikasi:", ["Anorganik", "Organik", "B3 (Bahan Berbahaya)"], key="jenis_baru_klas")
        with col_t2:
            nama_baru = st.text_input("Nama Jenis Sampah:", key="jenis_baru_nama", placeholder="contoh: Styrofoam")

        harga_jenis_baru = 0
        if klas_baru == "Anorganik":
            harga_jenis_baru = st.number_input("Harga (Rp/Kg):", min_value=0, step=50, key="jenis_baru_harga")

        if st.button("➕ Tambah Jenis", key="btn_tambah_jenis", use_container_width=True):
            if nama_baru.strip() == "":
                st.warning("⚠️ Nama jenis sampah tidak boleh kosong.")
            elif nama_baru.strip().title() in df_master["Jenis"].tolist():
                st.warning("⚠️ Jenis sampah ini sudah ada.")
            else:
                new_jenis = pd.DataFrame([[klas_baru, nama_baru.strip().title(), harga_jenis_baru]],
                                         columns=["Klasifikasi", "Jenis", "Harga"])
                df_master = pd.concat([df_master, new_jenis], ignore_index=True)
                df_master.to_csv(MASTER_FILE, index=False)
                st.success(f"✅ '{nama_baru.strip().title()}' berhasil ditambahkan ke {klas_baru}.")
                st.rerun()

        st.markdown("---")
        st.markdown("#### Hapus Jenis Sampah")

        klas_hapus = st.selectbox("Klasifikasi:", ["Anorganik", "Organik", "B3 (Bahan Berbahaya)"], key="hapus_klas")
        jenis_di_klas = df_master[df_master["Klasifikasi"] == klas_hapus]["Jenis"].tolist()

        if not jenis_di_klas:
            st.info("Tidak ada jenis sampah untuk klasifikasi ini.")
        else:
            jenis_hapus = st.selectbox("Pilih Jenis yang Dihapus:", jenis_di_klas, key="hapus_jenis")
            konfirmasi = st.checkbox(f"Saya yakin ingin menghapus '{jenis_hapus}'", key="hapus_konfirmasi")

            if st.button("🗑️ Hapus Jenis", key="btn_hapus_jenis", use_container_width=True):
                if not konfirmasi:
                    st.warning("⚠️ Centang konfirmasi terlebih dahulu.")
                else:
                    df_master = df_master[
                        ~((df_master["Klasifikasi"] == klas_hapus) & (df_master["Jenis"] == jenis_hapus))
                    ].reset_index(drop=True)
                    df_master.to_csv(MASTER_FILE, index=False)
                    st.success(f"✅ '{jenis_hapus}' berhasil dihapus.")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Daftar Jenis Sampah Saat Ini")
        st.dataframe(
            df_master[["Klasifikasi", "Jenis", "Harga"]].rename(columns={"Harga": "Harga (Rp/Kg)"}),
            use_container_width=True, hide_index=True
        )

    # === TAB 3: RESET DATA ===
    with tab_reset:
        st.markdown("#### 🗑️ Reset Tabel Data Setoran")

        df_reset_preview = load_data()
        jumlah_data = len(df_reset_preview)

        if jumlah_data == 0:
            st.info("Tabel sudah kosong, tidak ada data yang perlu direset.")
        else:
            st.warning(f"⚠️ Tabel saat ini berisi **{jumlah_data} data setoran**. Reset akan menghapus semua data secara permanen.")

            st.markdown("---")
            st.markdown("**Langkah reset:**")
            st.markdown("1. Download arsip CSV otomatis saat tombol Reset ditekan")
            st.markdown("2. Tabel dikosongkan")

            st.markdown("---")
            konfirmasi_reset = st.checkbox("Saya sudah memahami bahwa data akan dihapus permanen", key="konfirmasi_reset_cb")
            ketik_reset = st.text_input("Ketik **RESET** untuk konfirmasi:", key="ketik_reset_input", placeholder="RESET")

            reset_siap = konfirmasi_reset and ketik_reset.strip() == "RESET"

            # Siapkan CSV arsip untuk didownload sebelum reset
            arsip_csv = df_reset_preview.to_csv(index=False).encode("utf-8")
            arsip_nama = f"ARSIP_SIPS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            if reset_siap:
                st.download_button(
                    label="📥 Download Arsip & Reset Data",
                    data=arsip_csv,
                    file_name=arsip_nama,
                    mime="text/csv",
                    key="btn_download_arsip"
                )
                st.caption("⬆️ Klik tombol di atas untuk download arsip CSV sekaligus mereset tabel.")

                if st.button("🗑️ Reset Tabel Sekarang (tanpa download arsip)", key="btn_reset_langsung"):
                    save_data(pd.DataFrame(columns=COLS_URUTAN))
                    st.success("✅ Tabel berhasil direset!")
                    st.rerun()
            else:
                st.button("📥 Download Arsip & Reset Data", disabled=True, key="btn_download_arsip_disabled")
                st.caption("Centang konfirmasi dan ketik RESET untuk mengaktifkan tombol reset.")

st.markdown("<br><hr><center><small>SIPS v5.0 | Ghifelopment - KKN Kemantren Gondokusuman 2026</small></center>", unsafe_allow_html=True)
