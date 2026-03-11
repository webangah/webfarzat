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
st.set_page_config(page_title="SISTEM SURVEY LOT + GOOGLE MAPS", layout="wide")

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# --- SUNTIKAN CSS ---
wallpaper_data = get_base64_image("gambar juruukur.jpg")
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
        .main-header {{
            background: white; padding: 20px; border-radius: 10px; 
            border-left: 10px solid #007bff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
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

# --- PENGURUSAN SESSION & SECURITY ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = ""
if 'attempts' not in st.session_state: st.session_state.attempts = 0
if 'recovery_active' not in st.session_state: st.session_state.recovery_active = False

# Database Pengguna Awal
if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        "farzat": "442006",
        "sir fauzul": "1234",
        "123": "1234"
    }

SECRET_KEY = "progaming"

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo = get_base64_image("PUO_Logo.png")
        if logo: st.markdown(f'<center><img src="data:image/png;base64,{logo}" width="180"></center>', unsafe_allow_html=True)
        
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # --- PAPARAN PEMULIHAN AKAUN ---
        if st.session_state.recovery_active:
            st.markdown("<h3 style='text-align: center; color: #d9534f;'>🛠️ PEMULIHAN AKAUN</h3>", unsafe_allow_html=True)
            safe_word = st.text_input("Masukkan Kata Selamat", type="password", placeholder="Petunjuk: 'pro...'")
            
            if safe_word == SECRET_KEY:
                st.success("✅ Kata selamat disahkan!")
                new_id = st.text_input("ID Pengguna Baru")
                new_pass = st.text_input("Kata Laluan Baru", type="password")
                
                if st.button("KEMASKINI DATA AKAUN", use_container_width=True):
                    if new_id and new_pass:
                        st.session_state.users_db[new_id] = new_pass
                        st.session_state.recovery_active = False
                        st.session_state.attempts = 0
                        st.success(f"Berjaya! Akaun {new_id} sedia digunakan.")
                        st.rerun()
                    else:
                        st.error("Sila isi semua maklumat!")
            elif safe_word != "":
                st.error("❌ Kata selamat salah!")

            if st.button("Kembali ke Log Masuk", use_container_width=True):
                st.session_state.recovery_active = False
                st.session_state.attempts = 0
                st.rerun()

        # --- PAPARAN LOG MASUK BIASA ---
        else:
            st.markdown("<h2 style='text-align: center;'>LOG MASUK SISTEM</h2>", unsafe_allow_html=True)
            u_input = st.text_input("ID Pengguna")
            p_input = st.text_input("Kata Laluan", type="password")
            
            if st.button("MASUK", use_container_width=True):
                if u_input in st.session_state.users_db and st.session_state.users_db[u_input] == p_input:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u_input.upper()
                    st.session_state.attempts = 0
                    st.rerun()
                else:
                    st.session_state.attempts += 1
                    if st.session_state.attempts < 3:
                        st.error(f"ID atau Kata Laluan Salah! (Cubaan: {st.session_state.attempts}/3)")
            
            # Jika salah 3 kali atau lebih
            if st.session_state.attempts >= 3:
                st.error("❌ Akses Disekat: Percubaan melebihi had.")
                st.warning("⚠️ Terlupa kata laluan atau ID pengguna?")
                if st.button("KLIK UNTUK RESET AKAUN", use_container_width=True):
                    st.session_state.recovery_active = True
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- HALAMAN UTAMA (Hanya muncul jika logged_in = True) ---
def main_app():
    with st.sidebar:
        st.markdown(f"""
            <div style='text-align: center; background: linear-gradient(135deg, #00b4ff, #007bff); padding: 15px; border-radius: 10px; color: white;'>
                <h3>Hai, {st.session_state.current_user}!</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.subheader("⚙️ Kawalan Peta")
        saiz_marker = st.slider("Saiz Marker", 5, 50, 38)
        saiz_teks = st.slider("Saiz Teks", 10, 30, 23)
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00")
        
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = ""
            st.rerun()

    st.markdown(f'<div class="main-header"><h1>SISTEM SURVEY LOT + GOOGLE MAPS</h1><p>Log Masuk Sebagai: {st.session_state.current_user}</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1: epsg = st.text_input("🟢 Kod EPSG:", value="4390")
    with col2: file = st.file_uploader("📂 Muat naik fail CSV (STN, E, N)", type="csv")

    if file:
        df = pd.read_csv(file)
        if 'E' in df.columns and 'N' in df.columns:
            e, n = df['E'].values, df['N'].values
            lats, lons = transform_coords(df, epsg)
            
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            dist_list = [np.sqrt((e[(i+1)%len(df)]-e[i])**2 + (n[(i+1)%len(df)]-n[i])**2) for i in range(len(df))]

            tab1, tab2 = st.tabs(["🌍 Peta Interaktif", "📋 Jadual Data"])
            
            with tab1:
                m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=20)
                folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Satellite').add_to(m)
                
                # Feature Groups (On/Off Buttons)
                fg_stesen = folium.FeatureGroup(name="Marker Stesen").add_to(m)
                fg_label = folium.FeatureGroup(name="Bearing & Jarak").add_to(m)
                fg_sempadan = folium.FeatureGroup(name="Sempadan Lot").add_to(m)
                fg_luas = folium.FeatureGroup(name="Info Luas & Surveyor").add_to(m)

                # Lukis Sempadan
                points = list(zip(lats, lons))
                folium.Polygon(locations=points + [points[0]], color=warna_poli, weight=3, fill=True, fill_opacity=0.3).add_to(fg_sempadan)

                for i in range(len(df)):
                    stn_name = str(df['STN'].iloc[i]) if 'STN' in df.columns else str(i+1)
                    # Marker
                    folium.CircleMarker([lats[i], lons[i]], radius=saiz_marker/4, color="red", fill=True).add_to(fg_stesen)
                    # Label
                    next_i = (i + 1) % len(df)
                    brg = np.degrees(np.arctan2((e[next_i]-e[i]), (n[next_i]-n[i]))) % 360
                    label_html = f'<div style="color:#FFFF00; font-size:{saiz_teks}pt; text-shadow:2px 2px #000; font-weight:bold;">{to_dms(brg)}<br>{dist_list[i]:.3f}m</div>'
                    folium.Marker([(lats[i]+lats[next_i])/2, (lons[i]+lons[next_i])/2], icon=folium.DivIcon(html=label_html)).add_to(fg_label)

                # Center Info
                folium.Marker([np.mean(lats), np.mean(lons)], icon=folium.Icon(color='blue', icon='home'), 
                              popup=f"Luas: {area:.3f} m²\nSurveyor: {st.session_state.current_user}").add_to(fg_luas)

                folium.LayerControl(position='topright', collapsed=False).add_to(m)
                st_folium(m, width=1100, height=600)
            
            with tab2:
                st.dataframe(df, use_container_width=True)

# --- LOGIK JALANKAN APLIKASI ---
if st.session_state.logged_in:
    main_app()
else:
    login_page()
