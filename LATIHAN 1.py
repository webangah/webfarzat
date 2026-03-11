import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import base64
from folium.plugins import Fullscreen

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SISTEM SURVEY LOT", layout="wide")

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# --- SUNTIKAN CSS (WALLPAPER & UI) ---
wallpaper_data = get_base64_image("gambar juruukur.jpg")
logo_puo = get_base64_image("PUO_Logo.png")
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
                    <img src='data:image/jpeg;base64,{prof_img_data}' width='120' style='border-radius: 50%; border: 4px solid #007bff; height: 120px; object-fit: cover;'>
                    <h3 style='margin-top: 10px;'>{st.session_state.current_user}</h3>
                </div>
            """, unsafe_allow_html=True)
        st.subheader("⚙️ Tetapan Paparan")
        saiz_m = st.slider("Saiz Marker Point", 5, 80, 40) # Slider dibesarkan sedikit
        saiz_t = st.slider("Saiz Teks Info", 10, 30, 20)
        warna_poly = st.color_picker("Warna Lot", "#FFFF00")
        if st.button("🚪 Keluar", use_container_width=True): st.session_state.logged_in = False; st.rerun()

    # --- HEADER ---
    l_html = f'<img src="data:image/png;base64,{logo_puo}" width="80">' if logo_puo else ""
    st.markdown(f'<div class="header-container"><div class="header-logo">{l_html}</div><div class="header-text"><h1>SISTEM SURVEY LOT</h1><p>Jabatan Kejuruteraan Awam | Politeknik Ungku Omar</p></div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1: epsg = st.text_input("EPSG", "4390")
    with col2: file = st.file_uploader("Upload CSV", type="csv")

    if file:
        df = pd.read_csv(file)
        lats, lons = transform_coords(df, epsg)
        e, n = df['E'].values, df['N'].values
        area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
        dist_list = [np.sqrt((e[(i+1)%len(df)]-e[i])**2 + (n[(i+1)%len(df)]-n[i])**2) for i in range(len(df))]

        tab1, tab2 = st.tabs(["🌍 Peta Interaktif", "📋 Jadual Data"])
        
        with tab1:
            m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=19, max_zoom=28)
            folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Satellite', max_zoom=28, max_native_zoom=20).add_to(m)
            Fullscreen().add_to(m)
            
            fg_stn = folium.FeatureGroup(name="Titik & No STN").add_to(m)
            fg_lbl = folium.FeatureGroup(name="Bearing & Jarak").add_to(m)
            fg_poly = folium.FeatureGroup(name="Sempadan").add_to(m)

            points = list(zip(lats, lons))
            folium.Polygon(locations=points + [points[0]], color=warna_poly, weight=3, fill=True, fill_opacity=0.3).add_to(fg_poly)

            for i in range(len(df)):
                stn_name = str(df['STN'].iloc[i])
                next_i = (i + 1) % len(df)
                brg = np.degrees(np.arctan2((e[next_i]-e[i]), (n[next_i]-n[i]))) % 360
                
                # --- POPUP BULAT (CIRCLE BUBBLE) ---
                popup_html = f"""
                <div style="
                    background-color: white; 
                    border: 3px solid #d9534f; 
                    border-radius: 50%; 
                    width: 140px; 
                    height: 140px; 
                    display: flex; 
                    flex-direction: column; 
                    justify-content: center; 
                    align-items: center; 
                    text-align: center; 
                    font-family: 'Arial Black', sans-serif;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                    padding: 5px;
                ">
                    <span style="color:#d9534f; font-size:16px;">STN {stn_name}</span>
                    <hr style="width: 70%; margin: 3px; border: 1px solid #eee;">
                    <span style="font-size:11px;">Ke: {df['STN'].iloc[next_i]}</span>
                    <span style="font-size:12px; color: #1a1a1a;">{to_dms(brg)}</span>
                    <span style="font-size:12px; color: #1a1a1a;">{dist_list[i]:.3f}m</span>
                </div>
                """
                
                # TITIK MERAH (Point Utama) + HITBOX BESAR
                folium.CircleMarker(
                    [lats[i], lons[i]], 
                    radius=saiz_m/4, 
                    color="red", 
                    fill=True, 
                    fill_opacity=0.9,
                    weight=15, # Ini buat hitbox sekeliling titik jadi besar gila, senang klik
                    opacity=0, # Hitbox halimunan
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=f"KLIK STN {stn_name}"
                ).add_to(fg_stn)
                
                # NOMBOR STESEN
                folium.Marker(
                    [lats[i], lons[i]], 
                    icon=folium.DivIcon(html=f'<div style="color:white; font-weight:bold; font-size:12pt; text-shadow:2px 2px black; width:30px; text-align:center;">{stn_name}</div>')
                ).add_to(fg_stn)
                
                # LABEL KUNING KAT GARISAN
                mid = [(lats[i]+lats[next_i])/2, (lons[i]+lons[next_i])/2]
                label_txt = f'<div style="color:yellow; font-size:{saiz_t}pt; font-weight:bold; text-shadow:2px 2px black; text-align:center; width:150px;">{to_dms(brg)}<br>{dist_list[i]:.3f}m</div>'
                folium.Marker(mid, icon=folium.DivIcon(html=label_txt)).add_to(fg_lbl)

            # Info Luas (Tengah)
            folium.Marker([np.mean(lats), np.mean(lons)], icon=folium.Icon(color='blue', icon='info-sign'), 
                          popup=f"Luas: {area:.3f} m²\nSurveyor: {st.session_state.current_user}").add_to(m)

            folium.LayerControl(position='topright', collapsed=False).add_to(m)
            st_folium(m, width=1100, height=600)

        # BUTTON EXPORT QGIS
        geojson_data = json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [lons[i], lats[i]]}, "properties": {"STN": str(df['STN'].iloc[i]), "E": float(e[i]), "N": float(n[i])}} for i in range(len(df))]})
        st.download_button("🚀 EXPORT KE QGIS (GEOJSON)", data=geojson_data, file_name=f"survey_{st.session_state.current_user}.geojson", use_container_width=True)

if st.session_state.logged_in: main_app()
else: login_page()
