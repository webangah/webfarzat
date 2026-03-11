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

# --- SUNTIKAN CSS (WALLPAPER & UI) ---
wallpaper_data = get_base64_image("gambar juruukur.jpg")
if wallpaper_data:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255,255,255,0.6), rgba(255,255,255,0.6)), 
                              url("data:image/jpg;base64,{wallpaper_data}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        [data-testid="stSidebar"] {{ background-color: rgba(255, 255, 255, 0.95); }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.8); padding: 15px; border-radius: 10px;
            border-top: 4px solid #007bff; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
if 'current_password' not in st.session_state: st.session_state.current_password = "442006"
if 'login_attempts' not in st.session_state: st.session_state.login_attempts = 0

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo = get_base64_image("PUO_Logo.png")
        if logo: st.markdown(f'<center><img src="data:image/png;base64,{logo}" width="180"></center>', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>LOG MASUK SISTEM</h2>", unsafe_allow_html=True)
        user_id = st.text_input("ID Pengguna", value="farzat")
        password = st.text_input("Kata Laluan", type='password')
        if st.button("MASUK", use_container_width=True):
            if user_id == "farzat" and password == st.session_state.current_password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"Salah! Cuba lagi.")
        
        if st.session_state.login_attempts >= 3:
            st.info("Soalan: Apa makanan kegemaran anda?")
            jawapan = st.text_input("Jawapan (ayam goreng):")
            if jawapan.lower() == "ayam goreng" and st.button("Reset PWD"):
                st.success("Sila masukkan kata laluan baru di bahagian atas.")

# --- HALAMAN UTAMA ---
def main_app():
    with st.sidebar:
        prof_img = get_base64_image("WhatsApp Image 2026-03-12 at 1.42.22 AM.jpeg")
        if prof_img:
            st.markdown(f"""
                <div style='text-align: center; background: #007bff; padding: 20px; border-radius: 15px; color: white;'>
                    <img src='data:image/jpeg;base64,{prof_img}' width='100' style='border-radius: 50%; border: 3px solid white; height: 110px; object-fit: cover;'>
                    <h3>FARZAT</h3>
                </div>
            """, unsafe_allow_html=True)
        st.subheader("⚙️ Kawalan Paparan")
        saiz_marker = st.slider("Saiz Marker", 5, 50, 38)
        saiz_teks = st.slider("Saiz Bearing/Jarak", 10, 30, 23)
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00")
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<h1>SISTEM SURVEY LOT + INFO</h1>", unsafe_allow_html=True)
    epsg = st.text_input("Kod EPSG:", value="4390")
    file = st.file_uploader("Muat naik CSV (STN, E, N)", type="csv")

    if file:
        df = pd.read_csv(file)
        if 'E' in df.columns and 'N' in df.columns:
            e, n = df['E'].values, df['N'].values
            lats, lons = transform_coords(df, epsg)
            
            # Pengiraan Luas & Perimeter
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            dist_list = [np.sqrt((e[(i+1)%len(df)]-e[i])**2 + (n[(i+1)%len(df)]-n[i])**2) for i in range(len(df))]
            perimeter = sum(dist_list)

            tab1, tab2, tab3 = st.tabs(["🌍 Peta Interaktif", "📊 Lukisan Teknikal", "📋 Senarai Koordinat"])
            
            with tab1:
                m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=24)
                folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Hybrid', max_zoom=24).add_to(m)
                
                points = list(zip(lats, lons))
                folium.Polygon(locations=points + [points[0]], color=warna_poli, weight=3, fill=True, fill_opacity=0.3).add_to(m)

                # --- BEARING & JARAK ---
                for i in range(len(df)):
                    p1, p2 = [lats[i], lons[i]], [lats[(i+1)%len(df)], lons[(i+1)%len(df)]]
                    dist = dist_list[i]
                    brg = np.degrees(np.arctan2((e[(i+1)%len(df)]-e[i]), (n[(i+1)%len(df)]-n[i]))) % 360
                    m_lat, m_lon = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
                    
                    label_html = f'<div style="color:#FFFF00; font-size:{saiz_teks}pt; text-shadow:2px 2px #000; font-weight:bold; text-align:center;">{to_dms(brg)}<br>{dist:.3f}m</div>'
                    folium.Marker([m_lat, m_lon], icon=folium.DivIcon(html=label_html)).add_to(m)
                    
                    stn_id = str(df['STN'].iloc[i]) if 'STN' in df.columns else str(i+1)
                    folium.CircleMarker(p1, radius=saiz_marker/2, color="red", fill=True, fill_opacity=1).add_to(m)
                    folium.Marker(p1, icon=folium.DivIcon(html=f"<div style='color:white;font-weight:bold;'>{stn_id}</div>")).add_to(m)

                st_folium(m, width=1100, height=600)

            with tab2:
                # --- LUKISAN TEKNIKAL (PLOT) ---
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.plot(list(e) + [e[0]], list(n) + [n[0]], color='blue', marker='o', mfc='red')
                ax.set_aspect('equal')
                ax.set_title("Lukisan Teknikal Plot Lot")
                for i, txt in enumerate(df['STN'] if 'STN' in df.columns else range(1, len(df)+1)):
                    ax.annotate(txt, (e[i], n[i]), textcoords="offset points", xytext=(0,10), ha='center')
                st.pyplot(fig)

            with tab3:
                st.dataframe(df, use_container_width=True)

            # --- LOT INFO SECTION ---
            st.markdown("---")
            st.subheader("📍 Maklumat Lot Survey")
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="metric-card"><b>LUAS</b><br><h2>{area:.3f} m²</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><b>PERIMETER</b><br><h2>{perimeter:.3f} m</h2></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><b>LUAS (EKAR)</b><br><h2>{area*0.000247:.4f}</h2></div>', unsafe_allow_html=True)

            # EXPORT
            geojson = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [list(zip(e, n)) + [(e[0], n[0])]]}}]}
            st.download_button("🚀 Export QGIS", data=json.dumps(geojson), file_name="survey_farzat.geojson", use_container_width=True)

if st.session_state.logged_in: main_app()
else: login_page()
