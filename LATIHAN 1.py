import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import base64

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SISTEM SURVEY LOT", layout="wide")

# Fungsi untuk memproses imej ke format Base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# --- SUNTIKAN CSS UNTUK WALLPAPER & UI ---
wallpaper_data = get_base64_image("gambar juruukur.jpg")
if wallpaper_data:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), 
                              url("data:image/jpg;base64,{wallpaper_data}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stSidebar"] {{
            background-color: rgba(255, 255, 255, 0.9);
        }}
        .stButton>button {{
            border-radius: 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- FUNGSI TEKNIKAL SURVEY ---
def to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int((deg - d - m/60) * 3600)
    return f"{d}°{m}'{s}\""

def transform_coords(df, epsg_code):
    try:
        transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(df['E'].values, df['N'].values)
        return lat, lon
    except:
        return None, None

# --- PENGURUSAN SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
if 'password_db' not in st.session_state:
    st.session_state.password_db = "442006" # Kata laluan default
if 'show_forgot_pw' not in st.session_state:
    st.session_state.show_forgot_pw = False

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo_puo = get_base64_image("PUO_Logo.png")
        if logo_puo:
            st.markdown(f'<center><img src="data:image/png;base64,{logo_puo}" width="150"></center>', unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; color: #333;'>LOG MASUK SISTEM</h2>", unsafe_allow_html=True)
        
        user_id = st.text_input("ID Pengguna (farzat)") 
        password = st.text_input("Kata Laluan", type='password')
        
        if st.button("LOG MASUK", use_container_width=True):
            if user_id == "farzat" and password == st.session_state.password_db:
                st.session_state.logged_in = True
                st.session_state.login_attempts = 0
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"Salah! Percubaan: {st.session_state.login_attempts}/3")

        if st.session_state.login_attempts >= 3:
            if st.button("Lupa Kata Laluan?"):
                st.session_state.show_forgot_pw = True

        if st.session_state.show_forgot_pw:
            st.info("Soalan: Apa makanan kegemaran anda?")
            jawapan = st.text_input("Jawapan anda:")
            if jawapan.lower() == "ayam goreng":
                new_pw = st.text_input("Kata Laluan Baru", type="password")
                if st.button("Reset Kata Laluan"):
                    st.session_state.password_db = new_pw
                    st.session_state.show_forgot_pw = False
                    st.session_state.login_attempts = 0
                    st.success("Berjaya ditukar!")

# --- HALAMAN UTAMA ---
def main_app():
    with st.sidebar:
        # Profil Farzat
        profile_img = get_base64_image("WhatsApp Image 2026-03-12 at 1.42.22 AM.jpeg")
        if profile_img:
            st.markdown(f"""
                <div style='text-align: center; background: linear-gradient(135deg, #007bff, #00d4ff); padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px;'>
                    <img src='data:image/jpeg;base64,{profile_img}' width='100' style='border-radius: 50%; border: 3px solid white; height: 100px; object-fit: cover;'>
                    <h3 style='margin: 10px 0 0 0;'>Hai, FARZAT!</h3>
                    <p style='font-size: 12px; opacity: 0.9;'>ID: farzat</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.subheader("⚙️ Kawalan Paparan")
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00")
        
        st.markdown("---")
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Dashboard Header
    st.markdown("""
        <div style='background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-bottom: 20px;'>
            <h1 style='margin:0;'>SISTEM SURVEY LOT</h1>
            <p style='margin:0; color: #666;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
    """, unsafe_allow_html=True)

    col_epsg, col_file = st.columns(2)
    with col_epsg:
        kod_epsg = st.text_input("Kod EPSG:", value="4390")
    with col_file:
        uploaded_file = st.file_uploader("Muat naik fail CSV (STN, E, N)", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            e, n = df['E'].values, df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            lats, lons = transform_coords(df, kod_epsg)

            tab1, tab2 = st.tabs(["🌍 Peta Interaktif", "📋 Data Koordinat"])
            
            with tab1:
                if lats is not None:
                    m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=20)
                    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Hybrid').add_to(m)
                    
                    points = list(zip(lats, lons))
                    folium.Polygon(locations=points + [points[0]], color=warna_poli, fill=True, popup=f"Luas: {area:.3f} m²").add_to(m)
                    st_folium(m, width=1000, height=500)

            # --- EKSPORT KE QGIS ---
            st.markdown("---")
            geojson_data = {
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [list(zip(e, n)) + [(e[0], n[0])]]}, "properties": {"surveyor": "FARZAT", "area": area}}]
            }
            st.download_button("🚀 Muat Turun Fail QGIS (.geojson)", data=json.dumps(geojson_data), file_name="survey_lot_farzat.geojson", use_container_width=True)

# Jalankan App
if st.session_state.logged_in:
    main_app()
else:
    login_page()
