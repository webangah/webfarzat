import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import folium
from folium.plugins import MiniMap
from streamlit_folium import st_folium
from pyproj import Transformer
import base64

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SISTEM SURVEY LOT", layout="wide")

# Fungsi untuk memproses imej ke Base64 (untuk paparan logo/profil)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Fungsi Matematik Survey
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

# --- PENGURUSAN SESSION STATE (KESELAMATAN) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
if 'current_password' not in st.session_state:
    st.session_state.current_password = "442006"
if 'forgot_pw_mode' not in st.session_state:
    st.session_state.forgot_pw_mode = False

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Logo PUO
        logo_data = get_base64_image("PUO_Logo.png")
        if logo_data:
            st.markdown(f'<center><img src="data:image/png;base64,{logo_data}" width="150"></center>', unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center;'>SISTEM SURVEY LOT</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Sila masukkan kredential anda</p>", unsafe_allow_html=True)

        # Form Input
        user_id = st.text_input("ID Pengguna", placeholder="Masukkan ID")
        password = st.text_input("Kata Laluan", type='password', placeholder="Masukkan Kata Laluan")
        
        btn_login = st.button("LOG MASUK", use_container_width=True)

        if btn_login:
            if user_id == "farzat" and password == st.session_state.current_password:
                st.session_state.logged_in = True
                st.session_state.login_attempts = 0
                st.success("Log masuk berjaya!")
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"ID atau Kata Laluan Salah! (Percubaan: {st.session_state.login_attempts}/3)")

        # Logik Lupa Kata Laluan (Selepas 3 kali gagal)
        if st.session_state.login_attempts >= 3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Lupa Kata Laluan?", type="secondary", use_container_width=True):
                st.session_state.forgot_pw_mode = True

        if st.session_state.forgot_pw_mode:
            st.markdown("---")
            st.info("Sila jawab soalan keselamatan untuk menukar kata laluan.")
            jawapan = st.text_input("Soalan: Apa makanan kegemaran anda?")
            
            if jawapan.lower() == "ayam goreng":
                new_pw = st.text_input("Kata Laluan Baru", type="password")
                confirm_new_pw = st.text_input("Sahkan Kata Laluan Baru", type="password")
                
                if st.button("Tukar Kata Laluan"):
                    if new_pw == confirm_new_pw and new_pw != "":
                        st.session_state.current_password = new_pw
                        st.session_state.login_attempts = 0
                        st.session_state.forgot_pw_mode = False
                        st.success("Berjaya! Sila log masuk dengan kata laluan baru.")
                    else:
                        st.error("Kata laluan tidak sepadan.")
            elif jawapan != "":
                st.error("Jawapan salah! Cuba lagi.")

# --- HALAMAN UTAMA APLIKASI ---
def main_app():
    # Sidebar
    with st.sidebar:
        # Foto Profil User
        user_img = get_base64_image("WhatsApp Image 2026-03-12 at 1.42.22 AM.jpeg")
        if user_img:
            st.markdown(f"""
                <div style='text-align: center; background: #007bff; padding: 20px; border-radius: 15px; color: white;'>
                    <img src='data:image/jpeg;base64,{user_img}' width='100' style='border-radius: 50%; border: 3px solid white;'>
                    <h3>FARZAT</h3>
                    <p>ID: farzat</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("⚙️ Tetapan Paparan")
        saiz_marker = st.slider("Saiz Stesen", 5, 50, 30)
        saiz_teks = st.slider("Saiz Teks Data", 10, 30, 20)
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00")
        
        st.markdown("---")
        if st.button("🚪 LOG KELUAR", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Layout Atas
    st.title("🌍 Dashboard Visualisasi Lot")
    col_epsg, col_file = st.columns([1, 2])
    
    with col_epsg:
        kod_epsg = st.text_input("Kod EPSG (cth: 4326/4390):", value="4390")
    with col_file:
        uploaded_file = st.file_uploader("Muat naik data ukur (.csv)", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            e, n = df['E'].values, df['N'].values
            
            # Pengiraan Luas & Perimeter
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            dist = [np.sqrt((e[(i+1)%len(df)]-e[i])**2 + (n[(i+1)%len(df)]-n[i])**2) for i in range(len(df))]
            
            # Koordinat GPS untuk Folium
            lats, lons = transform_coords(df, kod_epsg)

            tab1, tab2 = st.tabs(["🗺️ Peta Interaktif", "📊 Data Teknikal"])

            with tab1:
                if lats is not None:
                    m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=20)
                    # Google Satellite Layer
                    folium.TileLayer(
                        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                        attr='Google',
                        name='Satelit',
                        overlay=False,
                        control=True
                    ).add_to(m)
                    
                    points = list(zip(lats, lons))
                    folium.Polygon(
                        locations=points + [points[0]],
                        color=warna_poli,
                        weight=4,
                        fill=True,
                        fill_opacity=0.3
                    ).add_to(m)

                    for i, row in df.iterrows():
                        folium.CircleMarker(
                            [lats[i], lons[i]], 
                            radius=saiz_marker/5, 
                            color="red", 
                            fill=True
                        ).add_to(m)
                    
                    st_folium(m, width=1000, height=500)

            with tab2:
                st.write(f"**Luas:** {area:.3f} m²")
                st.write(f"**Perimeter:** {sum(dist):.3f} m")
                st.dataframe(df)

            # EPORT TO QGIS SECTION
            st.markdown("---")
            st.subheader("📦 Eksport Data ke QGIS")
            
            # Bina GeoJSON
            features = []
            polygon_coords = [list(zip(e, n))]
            polygon_coords[0].append((e[0], n[0])) # Tutup poligon
            
            feature = {
                "type": "Feature",
                "properties": {"Name": "Lot Survey Farzat", "Area": area},
                "geometry": {"type": "Polygon", "coordinates": polygon_coords}
            }
            features.append(feature)
            
            geojson_output = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": f"urn:ogc:def:crs:EPSG::{kod_epsg}"}},
                "features": features
            }
            
            st.download_button(
                label="📥 MUAT TURUN FAIL GEOJSON (QGIS)",
                data=json.dumps(geojson_output),
                file_name="survey_farzat.geojson",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.error("Sila pastikan fail CSV mempunyai kolum 'E' dan 'N'.")

# --- MAIN LOGIC ---
if st.session_state.logged_in:
    main_app()
else:
    login_page()
