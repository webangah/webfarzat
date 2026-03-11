import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import base64
import matplotlib.pyplot as plt

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SISTEM SURVEY LOT", layout="wide")

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# --- SUNTIKAN CSS ---
wallpaper_data = get_base64_image("gambar juruukur.jpg")
logo_puo = get_base64_image("PUO_Logo.png")
# Pastikan nama fail gambar profil anda betul
prof_img_data = get_base64_image("WhatsApp Image 2026-03-12 at 1.42.22 AM.jpeg")

if wallpaper_data:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255,255,255,0.6), rgba(255,255,255,0.6)), 
                              url("data:image/jpg;base64,{wallpaper_data}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        .login-box {{
            background: white; padding: 30px; border-radius: 15px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); color: #333;
        }}
        .header-container {{
            display: flex; align-items: center; background: white; padding: 15px;
            border-radius: 12px; border-left: 10px solid #007bff;
            margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header-logo {{ margin-right: 20px; }}
        .header-text h1 {{ margin: 0; font-size: 28px; color: #1a1a1a; }}
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

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = ""
if 'attempts' not in st.session_state: st.session_state.attempts = 0
if 'recovery_active' not in st.session_state: st.session_state.recovery_active = False
if 'users_db' not in st.session_state:
    st.session_state.users_db = {"farzat": "442006", "sir fauzul": "1234", "123": "1234"}

SECRET_KEY = "progaming"

# --- LOGIN PAGE ---
def login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if logo_puo: st.markdown(f'<center><img src="data:image/png;base64,{logo_puo}" width="180"></center>', unsafe_allow_html=True)
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        if st.session_state.recovery_active:
            st.subheader("🛠️ PEMULIHAN AKAUN")
            safe_word = st.text_input("Masukkan Kata Selamat", type="password")
            if safe_word == SECRET_KEY:
                st.success("Akses Diterima")
                new_id = st.text_input("ID Baru")
                new_pass = st.text_input("Pass Baru", type="password")
                if st.button("RESET AKAUN"):
                    st.session_state.users_db[new_id] = new_pass
                    st.session_state.recovery_active = False
                    st.rerun()
        else:
            st.markdown("<h2 style='text-align: center;'>LOG MASUK</h2>", unsafe_allow_html=True)
            u = st.text_input("ID")
            p = st.text_input("Password", type="password")
            if st.button("MASUK", use_container_width=True):
                if u in st.session_state.users_db and st.session_state.users_db[u] == p:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u.upper()
                    st.rerun()
                else: st.session_state.attempts += 1
            if st.session_state.attempts >= 3:
                if st.button("LUPA ID/PASSWORD?"): st.session_state.recovery_active = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN APP ---
def main_app():
    with st.sidebar:
        if prof_img_data:
            st.markdown(f"""
                <div style='text-align: center; margin-bottom: 20px;'>
                    <img src='data:image/jpeg;base64,{prof_img_data}' width='120' style='border-radius: 50%; border: 4px solid #007bff;'>
                    <h3 style='margin-top: 10px;'>{st.session_state.current_user}</h3>
                </div>
            """, unsafe_allow_html=True)
        st.subheader("⚙️ Tetapan")
        saiz_m = st.slider("Marker", 5, 50, 30)
        saiz_t = st.slider("Teks", 10, 30, 20)
        if st.button("🚪 Keluar", use_container_width=True): st.session_state.logged_in = False; st.rerun()

    # --- HEADER ---
    l_html = f'<img src="data:image/png;base64,{logo_puo}" width="80">' if logo_puo else ""
    st.markdown(f'<div class="header-container"><div class="header-logo">{l_html}</div><div class="header-text"><h1>SISTEM SURVEY LOT</h1><p>Politeknik Ungku Omar</p></div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1: epsg = st.text_input("EPSG", "4390")
    with col2: file = st.file_uploader("Upload CSV", type="csv")

    if file:
        df = pd.read_csv(file)
        lats, lons = transform_coords(df, epsg)
        
        # Pengiraan Luas & Data GeoJSON
        e, n = df['E'].values, df['N'].values
        area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
        
        tab1, tab2 = st.tabs(["🌍 Peta", "📋 Data"])
        with tab1:
            m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=19)
            folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Satellite').add_to(m)
            
            # Kumpulan On/Off
            fg_stn = folium.FeatureGroup(name="Marker Stesen").add_to(m)
            fg_lbl = folium.FeatureGroup(name="Bearing & Jarak").add_to(m)

            points = list(zip(lats, lons))
            folium.Polygon(locations=points + [points[0]], color="yellow", fill=True, fill_opacity=0.2).add_to(m)

            for i in range(len(df)):
                folium.CircleMarker([lats[i], lons[i]], radius=saiz_m/4, color="red", fill=True).add_to(fg_stn)
                next_i = (i + 1) % len(df)
                dist = np.sqrt((e[next_i]-e[i])**2 + (n[next_i]-n[i])**2)
                brg = np.degrees(np.arctan2((e[next_i]-e[i]), (n[next_i]-n[i]))) % 360
                label = f'<div style="color:yellow; font-size:{saiz_t}pt; font-weight:bold; text-shadow:1px 1px black;">{to_dms(brg)}<br>{dist:.2f}m</div>'
                folium.Marker([(lats[i]+lats[next_i])/2, (lons[i]+lons[next_i])/2], icon=folium.DivIcon(html=label)).add_to(fg_lbl)

            folium.LayerControl().add_to(m)
            st_folium(m, width=1100, height=600)

        # --- BUTANG EXPORT KE QGIS ---
        features = []
        for i in range(len(df)):
            features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lons[i], lats[i]]}, "properties": {"STN": str(df['STN'].iloc[i])}})
        
        geojson_data = json.dumps({"type": "FeatureCollection", "features": features})
        st.download_button(label="🚀 EXPORT KE QGIS (GEOJSON)", data=geojson_data, file_name="survey_output.geojson", mime="application/json", use_container_width=True)

if st.session_state.logged_in: main_app()
else: login_page()
