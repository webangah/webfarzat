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

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

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
    except Exception as e:
        return None, None

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try:
            st.image("PUO_Logo.png", width=150)
        except:
            st.image("https://www.puo.edu.my/wp-content/uploads/2021/08/cropped-LOGO-PUO-1.png", width=150)
        st.title("Log Masuk")
        user_id = st.text_input("ID Pengguna")
        password = st.text_input("Kata Laluan", type='password')
        if st.button("Log Masuk", use_container_width=True):
            if user_id == "1" and password == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("ID atau Kata Laluan salah!")

# --- HALAMAN UTAMA ---
def main_app():
    with st.sidebar:
        st.subheader("⚙️ Kawalan Paparan")
        saiz_marker = st.slider("Saiz Marker Stesen", 5, 50, 38)
        saiz_teks = st.slider("Saiz Bearing/Jarak", 5, 30, 23)
        tahap_zoom = st.slider("Tahap Zoom", 10, 24, 24)
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00")
        
        st.markdown("---")
        st.subheader("💾 Eksport Data")
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- HEADER ---
    encoded_logo = get_base64_image("PUO_Logo.png")
    logo_html = f"<img src='data:image/png;base64,{encoded_logo}' width='120'>" if encoded_logo else "LOGO"
    
    st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 30px; margin-bottom: 20px;'>
            {logo_html}
            <div style='border-left: 4px solid #007bff; padding-left: 20px;'>
                <h1 style='margin: 0; font-size: 48px; color: #212529; font-weight: 800; font-family: sans-serif;'>SISTEM SURVEY LOT</h1>
                <p style='color: #6c757d; margin: 0; font-size: 18px;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_epsg, col_upload = st.columns(2)
    with col_epsg:
        kod_epsg = st.text_input("🟢 Kod EPSG:", value="4390")
    with col_upload:
        uploaded_file = st.file_uploader("📁 Muat naik fail CSV (STN, E, N)", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            e, n = df['E'].values, df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            distances = [np.sqrt((e[(i+1)%len(df)]-e[i])**2 + (n[(i+1)%len(df)]-n[i])**2) for i in range(len(df))]
            perimeter = sum(distances)
            lats, lons = transform_coords(df, kod_epsg)

            tab1, tab2, tab3 = st.tabs(["🌍 Peta Interaktif", "📊 Lukisan Teknikal", "📋 Senarai Koordinat"])

            with tab1:
                if lats is not None:
                    m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=tahap_zoom, tiles=None)
                    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Hybrid (Satelit)', max_zoom=24).add_to(m)
                    folium.TileLayer('openstreetmap', name='openstreetmap').add_to(m)
                    
                    points = list(zip(lats, lons))
                    popup_html = f"<div style='font-family: Arial; width: 200px;'><b>📍 Info Lot</b><br><b>Surveyor:</b> MUHAMMAD FARZAT<br><b>Luas:</b> {area:.3f} m²<br><b>Perimeter:</b> {perimeter:.3f} m</div>"
                    
                    folium.Polygon(locations=points + [points[0]], color="yellow", weight=3, fill=True, fill_color=warna_poli, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=300)).add_to(m)
                    
                    for i in range(len(df)):
                        p1, p2 = [lats[i], lons[i]], [lats[(i+1)%len(df)], lons[(i+1)%len(df)]]
                        dist, brg = distances[i], np.degrees(np.arctan2((e[(i+1)%len(df)]-e[i]), (n[(i+1)%len(df)]-n[i]))) % 360
                        folium.Marker([(p1[0]+p2[0])/2, (p1[1]+p2[1])/2], icon=folium.DivIcon(html=f"<div style='font-family: Arial; color: #FFFF00; font-weight: bold; font-size: {saiz_teks}pt; text-shadow: 1px 1px #000; white-space: nowrap;'>{to_dms(brg)}<br>{dist:.3f}m</div>")).add_to(m)

                    for i, row in df.iterrows():
                        stn_id = str(row["STN"]) if "STN" in df.columns else str(i+1)
                        folium.CircleMarker(location=[lats[i], lons[i]], radius=saiz_marker/2, color="red", fill=True, fill_color="red", fill_opacity=1).add_to(m)
                        folium.Marker([lats[i], lons[i]], icon=folium.DivIcon(icon_anchor=(0,0), html=f"<div style='color: white; font-weight: bold; font-size: 10pt; text-align: center; width: 20px;'>{stn_id}</div>")).add_to(m)

                    folium.LayerControl().add_to(m)
                    st_folium(m, width=1100, height=600)

            with tab3:
                st.dataframe(df, use_container_width=True)

            with st.sidebar:
                 geojson_data = json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [list(zip(e, n))]}}]})
                 st.download_button("🚀 Export to QGIS (.geojson)", data=geojson_data, file_name="survey_lot.geojson", use_container_width=True)

if st.session_state.logged_in:
    main_app()
else:
    login_page()
