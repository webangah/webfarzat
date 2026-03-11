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
        [data-testid="stSidebar"] {{ background-color: rgba(240, 242, 246, 0.95); }}
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

# --- PENGURUSAN SESSION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'password_db' not in st.session_state: st.session_state.password_db = "442006"

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
            if user_id == "farzat" and password == st.session_state.password_db:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("ID atau Kata Laluan Salah!")

# --- HALAMAN UTAMA ---
def main_app():
    with st.sidebar:
        prof_img = get_base64_image("WhatsApp Image 2026-03-12 at 1.42.22 AM.jpeg")
        if prof_img:
            st.markdown(f"""
                <div style='text-align: center; background: linear-gradient(135deg, #00b4ff, #007bff); padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px;'>
                    <img src='data:image/jpeg;base64,{prof_img}' width='100' style='border-radius: 50%; border: 3px solid white; height: 100px; object-fit: cover;'>
                    <h3 style='margin:10px 0 0 0;'>Hai, FARZAT!</h3>
                </div>
            """, unsafe_allow_html=True)
        
        st.subheader("⚙️ Kawalan Paparan")
        saiz_marker = st.slider("Saiz Marker Stesen", 5, 50, 38)
        saiz_teks = st.slider("Saiz Bearing/Jarak", 10, 30, 23)
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00")
        
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown(f'<div class="main-header"><h1>SISTEM SURVEY LOT + GOOGLE MAPS</h1><p>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p></div>', unsafe_allow_html=True)

    col_epsg, col_file = st.columns(2)
    with col_epsg:
        epsg = st.text_input("🟢 Kod EPSG (RSO: 4390):", value="4390")
    with col_file:
        file = st.file_uploader("📂 Muat naik fail CSV (STN, E, N)", type="csv")

    if file:
        df = pd.read_csv(file)
        if 'E' in df.columns and 'N' in df.columns:
            e, n = df['E'].values, df['N'].values
            lats, lons = transform_coords(df, epsg)
            
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            dist_list = [np.sqrt((e[(i+1)%len(df)]-e[i])**2 + (n[(i+1)%len(df)]-n[i])**2) for i in range(len(df))]
            perimeter = sum(dist_list)

            tab1, tab2, tab3 = st.tabs(["🌍 Peta Interaktif", "📊 Lukisan Teknikal", "📋 Senarai Koordinat"])
            
            with tab1:
                # 1. Inisialisasi Peta
                m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=20, control_scale=True)
                
                # 2. Base Layers
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                    attr='Google', name='Google Satellite', max_zoom=24
                ).add_to(m)
                folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)

                # 3. Create Feature Groups (Buttons)
                fg_sempadan = folium.FeatureGroup(name="Sempadan Lot").add_to(m)
                fg_labels = folium.FeatureGroup(name="Bearing & Jarak").add_to(m)
                fg_stesen = folium.FeatureGroup(name="Marker Stesen").add_to(m)
                fg_luas = folium.FeatureGroup(name="Info Luas & Surveyor").add_to(m)

                # Poligon (Sempadan)
                points = list(zip(lats, lons))
                folium.Polygon(
                    locations=points + [points[0]], 
                    color=warna_poli, weight=3, fill=True, fill_opacity=0.3
                ).add_to(fg_sempadan)

                # Loop Stesen & Label
                for i in range(len(df)):
                    p_lat, p_lon = lats[i], lons[i]
                    stn_name = str(df['STN'].iloc[i]) if 'STN' in df.columns else str(i+1)
                    val_e, val_n = df['E'].iloc[i], df['N'].iloc[i]

                    # Marker Stesen
                    stn_popup_html = f'<div style="min-width:140px;"><b>STN {stn_name}</b><br>E: {val_e:.3f}<br>N: {val_n:.3f}</div>'
                    folium.CircleMarker(
                        [p_lat, p_lon], radius=saiz_marker/4, color="red", fill=True, fill_opacity=1,
                        popup=folium.Popup(stn_popup_html, max_width=250)
                    ).add_to(fg_stesen)
                    
                    folium.Marker(
                        [p_lat, p_lon], 
                        icon=folium.DivIcon(html=f"<div style='color:white; font-weight:bold; font-size:10pt; transform:translate(-3px,-7px);'>{stn_name}</div>")
                    ).add_to(fg_stesen)

                    # Label Bearing & Jarak
                    next_i = (i + 1) % len(df)
                    dist = dist_list[i]
                    brg = np.degrees(np.arctan2((e[next_i]-e[i]), (n[next_i]-n[i]))) % 360
                    m_lat, m_lon = (lats[i]+lats[next_i])/2, (lons[i]+lons[next_i])/2
                    
                    label_html = f'<div style="color:#FFFF00; font-size:{saiz_teks}pt; text-shadow:2px 2px #000; font-weight:bold; text-align:center;">{to_dms(brg)}<br>{dist:.3f}m</div>'
                    folium.Marker([m_lat, m_lon], icon=folium.DivIcon(html=label_html)).add_to(fg_labels)

                # Info Luas (Center Marker)
                lot_info_html = f"<div style='width:160px;'><b>📍 Info Lot</b><br>Surveyor: FARZAT<br>Luas: {area:.3f} m²<br>Perimeter: {perimeter:.3f} m</div>"
                folium.Marker(
                    [np.mean(lats), np.mean(lons)], 
                    icon=folium.Icon(color='blue', icon='home'), 
                    popup=folium.Popup(lot_info_html)
                ).add_to(fg_luas)

                # --- LAYER CONTROL (BUTANG ON/OFF) ---
                folium.LayerControl(position='topright', collapsed=False).add_to(m)

                st_folium(m, width=1100, height=600)

            with tab2:
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.plot(list(e) + [e[0]], list(n) + [n[0]], color='blue', marker='o', mfc='red')
                ax.set_aspect('equal')
                ax.grid(True, linestyle='--', alpha=0.6)
                st.pyplot(fig)
            
            with tab3:
                st.dataframe(df, use_container_width=True)

            st.download_button("🚀 EXPORT KE QGIS (GEOJSON)", data=json.dumps({"type": "FeatureCollection", "features": []}), file_name="survey_farzat.geojson", use_container_width=True)

if st.session_state.logged_in: main_app()
else: login_page()
