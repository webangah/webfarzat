import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PUO Survey Lot Visualizer", layout="wide")

# --- FUNGSI PEMBANTU ---
def to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int((deg - d - m/60) * 3600)
    return f"{d}°{m}'{s}\""

# Fungsi tukar koordinat ke Lat/Lon untuk Google Maps
def transform_coords(df, epsg_code):
    try:
        # Tukar dari EPSG pilihan (cth: 3168 untuk RSO) ke WGS84 (Lat/Lon)
        transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(df['E'].values, df['N'].values)
        return lat, lon
    except:
        return None, None

# --- PENGURUSAN SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://www.puo.edu.my/wp-content/uploads/2021/08/cropped-LOGO-PUO-1.png", width=150)
        st.title("Sistem Lot Ukur PUO")
        user_id = st.text_input("ID Pengguna")
        password = st.text_input("Kata Laluan", type='password')
        if st.button("Log Masuk", use_container_width=True):
            if user_id == "1" and password == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("ID atau Kata Laluan salah!")

# --- HALAMAN UTAMA (APLIKASI) ---
def main_app():
    with st.sidebar:
        st.markdown(f"""
        <div style='background-color: #0099ff; padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px;'>
            <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' width='80' style='filter: brightness(0) invert(1);'>
            <h2 style='margin: 10px 0 0 0;'>Hai, FARZAT!</h2>
            <p style='font-size: 14px; opacity: 0.8;'>MUHAMMAD FARZAT</p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("⚙️ Kawalan Paparan")
        saiz_marker = st.slider("Saiz Marker Stesen", 5, 50, 22)
        saiz_teks = st.slider("Saiz Bearing/Jarak", 5, 20, 12)
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00")
        
        st.markdown("---")
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- HEADER ---
    st.markdown("""
        <div style='border-left: 5px solid #007bff; padding-left: 20px;'>
            <h1 style='margin-bottom: 0px;'>SISTEM SURVEY LOT + GOOGLE SATELLITE</h1>
            <p style='color: #6c757d;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
    """, unsafe_allow_html=True)

    col_epsg, col_upload = st.columns(2)
    with col_epsg:
        kod_epsg = st.text_input("🟢 Kod EPSG (Contoh: 3168 untuk RSO Semenanjung):", value="3168")
    with col_upload:
        uploaded_file = st.file_uploader("📁 Muat naik fail CSV (STN, E, N)", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        if 'E' in df.columns and 'N' in df.columns:
            # Pengiraan Luas
            e, n = df['E'].values, df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            
            # --- TAB PAPARAN ---
            tab_map, tab_plot = st.tabs(["🌍 Peta Satelit (Google)", "📊 Lukisan Teknikal (Matplotlib)"])

            with tab_map:
                st.subheader("Paparan Google Satellite")
                lats, lons = transform_coords(df, kod_epsg)
                
                if lats is not None:
                    # Setup Folium Map
                    m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=18)
                    
                    # Tambah Google Satellite Layer
                    google_sat = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
                    folium.TileLayer(tiles=google_sat, attr='Google', name='Google Satellite', overlay=False, control=True).add_to(m)
                    
                    # Lukis Poligon
                    points = list(zip(lats, lons))
                    points.append(points[0]) # Tutup poligon
                    folium.Polygon(locations=points, color="white", weight=2, fill=True, fill_color=warna_poli, fill_opacity=0.4).add_to(m)
                    
                    # Tambah Marker Stesen
                    for i, row in df.iterrows():
                        folium.CircleMarker(location=[lats[i], lons[i]], radius=5, color="red", fill=True).add_to(m)
                        folium.Marker([lats[i], lons[i]], icon=folium.DivIcon(html=f'<div style="font-size: 10pt; color: white; font-weight: bold;">{row["STN"] if "STN" in df.columns else i+1}</div>')).add_to(m)

                    st_folium(m, width=1000, height=500)
                else:
                    st.warning("Gagal menukar koordinat. Sila pastikan Kod EPSG betul.")

            with tab_plot:
                # (Kod Matplotlib asal anda dikekalkan di sini)
                fig, ax = plt.subplots(figsize=(10, 8))
                coords = list(zip(e, n))
                coords.append(coords[0])
                e_p, n_p = zip(*coords)
                ax.plot(e_p, n_p, marker='o', color='black', markersize=saiz_marker/4)
                ax.fill(e_p, n_p, color=warna_poli, alpha=0.5)
                st.pyplot(fig)

            # Info Luas di bawah
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Luas (m²)", f"{area:.3f}")
            c2.metric("Luas (Ekar)", f"{area * 0.000247105:.4f}")
            
            geojson_data = json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [list(zip(e, n))]}}]})
            c3.download_button("📥 Download GeoJSON", data=geojson_data, file_name="survey_farzat.geojson", use_container_width=True)

# JALANKAN APP
if st.session_state.logged_in:
    main_app()
else:
    login_page()
