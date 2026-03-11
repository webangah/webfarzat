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

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# --- SUNTIKAN CSS (WALLPAPER & UI) ---
wallpaper_data = get_base64_image("gambar juruukur.jpg") #
if wallpaper_data:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255,255,255,0.6), rgba(255,255,255,0.6)), 
                              url("data:image/jpg;base64,{wallpaper_data}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        [data-testid="stSidebar"] {{ background-color: rgba(255, 255, 255, 0.95); border-right: 2px solid #007bff; }}
        .main-header {{
            background: white; padding: 20px; border-radius: 10px; 
            border-left: 10px solid #007bff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        </style>
        """, unsafe_allow_html=True)

# --- FUNGSI TEKNIKAL ---
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
    except: return None, None

# --- PENGURUSAN SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'login_attempts' not in st.session_state: st.session_state.login_attempts = 0
if 'password_db' not in st.session_state: st.session_state.password_db = "442006" #
if 'show_forgot_pw' not in st.session_state: st.session_state.show_forgot_pw = False

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo = get_base64_image("PUO_Logo.png")
        if logo: st.markdown(f'<center><img src="data:image/png;base64,{logo}" width="180"></center>', unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; color: #111;'>LOG MASUK SISTEM</h2>", unsafe_allow_html=True)
        user_id = st.text_input("ID Pengguna", value="farzat") #
        password = st.text_input("Kata Laluan", type='password')
        
        if st.button("MASUK", use_container_width=True):
            if user_id == "farzat" and password == st.session_state.password_db:
                st.session_state.logged_in = True
                st.session_state.login_attempts = 0
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"Salah! Percubaan: {st.session_state.login_attempts}/3")

        if st.session_state.login_attempts >= 3: #
            if st.button("Lupa Kata Laluan?"):
                st.session_state.show_forgot_pw = True

        if st.session_state.show_forgot_pw:
            st.warning("Soalan: Apa makanan kegemaran anda?") #
            jawapan = st.text_input("Jawapan (ayam goreng):")
            if jawapan.lower() == "ayam goreng": #
                new_pw = st.text_input("Kata Laluan Baru", type="password")
                if st.button("Reset Sekarang"):
                    st.session_state.password_db = new_pw
                    st.session_state.show_forgot_pw = False
                    st.session_state.login_attempts = 0
                    st.success("Berjaya! Sila log masuk semula.")

# --- HALAMAN UTAMA ---
def main_app():
    with st.sidebar:
        # Profil Farzat
        prof_img = get_base64_image("WhatsApp Image 2026-03-12 at 1.42.22 AM.jpeg")
        if prof_img:
            st.markdown(f"""
                <div style='text-align: center; background: linear-gradient(135deg, #007bff, #00d4ff); padding: 25px; border-radius: 20px; color: white; margin-bottom: 25px;'>
                    <img src='data:image/jpeg;base64,{prof_img}' width='110' style='border-radius: 50%; border: 4px solid white; height: 110px; object-fit: cover;'>
                    <h2 style='margin: 10px 0 0 0;'>FARZAT</h2>
                    <p style='font-size: 14px; opacity: 0.9;'>ID: farzat</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.subheader("⚙️ Kawalan Paparan")
        saiz_marker = st.slider("Saiz Marker", 5, 50, 38)
        saiz_teks = st.slider("Saiz Bearing/Jarak", 10, 30, 23)
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00")
        
        st.markdown("---")
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Header Dashboard
    st.markdown("""
        <div class="main-header">
            <h1 style='margin:0; font-size: 40px;'>SISTEM SURVEY LOT</h1>
            <p style='margin:0; color: #555;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
    """, unsafe_allow_html=True)

    col_epsg, col_file = st.columns(2)
    with col_epsg:
        epsg = st.text_input("🟢 Kod EPSG (RSO: 4390):", value="4390") #
    with col_file:
        file = st.file_uploader("📂 Muat naik fail CSV (STN, E, N)", type="csv")

    if file:
        df = pd.read_csv(file)
        if 'E' in df.columns and 'N' in df.columns:
            e, n = df['E'].values, df['N'].values
            lats, lons = transform_coords(df, epsg)
            
            if lats is not None:
                # Tab Menu
                tab1, tab2, tab3 = st.tabs(["🌍 Peta Interaktif", "📊 Lukisan Teknikal", "📋 Senarai Koordinat"])
                
                with tab1:
                    m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=24)
                    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                                     attr='Google', name='Google Hybrid (Satelit)', max_zoom=24).add_to(m)
                    
                    points = list(zip(lats, lons))
                    folium.Polygon(locations=points + [points[0]], color=warna_poli, weight=3, fill=True, fill_opacity=0.3).add_to(m)

                    # --- LOGIK LABEL BEARING & JARAK (KUNING) ---
                    for i in range(len(df)):
                        p1 = [lats[i], lons[i]]
                        next_i = (i + 1) % len(df)
                        p2 = [lats[next_i], lons[next_i]]
                        
                        # Hitung Jarak & Bearing
                        dist = np.sqrt((e[next_i]-e[i])**2 + (n[next_i]-n[i])**2)
                        brg = np.degrees(np.arctan2((e[next_i]-e[i]), (n[next_i]-n[i]))) % 360
                        
                        # Titik Tengah untuk Label
                        m_lat, m_lon = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
                        
                        # Label Kuning Terapung
                        label_html = f"""
                        <div style="font-family: 'Arial Black'; color: #FFFF00; font-size: {saiz_teks}pt; 
                                    text-shadow: 2px 2px #000; white-space: nowrap; text-align: center;">
                            {to_dms(brg)}<br>{dist:.3f}m
                        </div>"""
                        folium.Marker([m_lat, m_lon], icon=folium.DivIcon(html=label_html)).add_to(m)

                        # Marker Stesen (Bulatan Merah Berombor)
                        stn_id = str(df['STN'].iloc[i]) if 'STN' in df.columns else str(i+1)
                        folium.CircleMarker(p1, radius=saiz_marker/2, color="red", fill=True, fill_color="red", fill_opacity=1).add_to(m)
                        folium.Marker(p1, icon=folium.DivIcon(icon_anchor=(7,7), 
                                      html=f"<div style='color:white; font-weight:bold; font-size:10pt;'>{stn_id}</div>")).add_to(m)

                    st_folium(m, width=1100, height=600)
                
                with tab3:
                    st.dataframe(df, use_container_width=True)

                # --- EXPORT TO QGIS ---
                area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
                geojson = {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "geometry": {"type": "Polygon", "coordinates": [list(zip(e, n)) + [(e[0], n[0])]]},
                        "properties": {"surveyor": "FARZAT", "area_sqm": area}
                    }]
                }
                st.download_button("🚀 EXPORT KE QGIS (.geojson)", data=json.dumps(geojson), 
                                   file_name="survey_farzat.geojson", use_container_width=True)

# JALANKAN PROGRAM
if st.session_state.logged_in: main_app()
else: login_page()
