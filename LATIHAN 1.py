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

def transform_coords(df, epsg_code):
    try:
        # Menukar koordinat RSO/Tempatan ke WGS84 untuk paparan peta
        transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(df['E'].values, df['N'].values)
        return lat, lon
    except Exception as e:
        st.error(f"Ralat Transform: {e}")
        return None, None

# --- PENGURUSAN SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
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
        saiz_marker = st.slider("Saiz Marker Stesen", 5, 30, 12)
        saiz_teks = st.slider("Saiz Bearing/Jarak", 5, 20, 10)
        warna_poli = st.color_picker("Warna Isi Poligon", "#FFFF00")
        
        st.markdown("---")
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("""
        <div style='border-left: 5px solid #007bff; padding-left: 20px;'>
            <h1 style='margin-bottom: 0px;'>SISTEM SURVEY LOT + GOOGLE MAPS</h1>
            <p style='color: #6c757d;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
    """, unsafe_allow_html=True)

    col_epsg, col_upload = st.columns(2)
    with col_epsg:
        kod_epsg = st.text_input("🟢 Kod EPSG (Contoh: 4390 untuk RSO):", value="4390")
    with col_upload:
        uploaded_file = st.file_uploader("📁 Muat naik fail CSV (STN, E, N)", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        if 'E' in df.columns and 'N' in df.columns:
            e, n = df['E'].values, df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            
            tab_map, tab_plot = st.tabs(["🌍 Peta Interaktif", "📊 Lukisan Teknikal"])

            with tab_map:
                lats, lons = transform_coords(df, kod_epsg)
                
                if lats is not None:
                    # Mulakan peta tanpa tiles default
                    m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=19, tiles=None)
                    
                    # --- PILIHAN LAPISAN GOOGLE ---
                    google_sat = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
                    google_streets = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
                    google_hybrid = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'

                    folium.TileLayer(tiles=google_streets, attr='Google', name='Google Street Map', overlay=False).add_to(m)
                    folium.TileLayer(tiles=google_sat, attr='Google', name='Google Satellite', overlay=False).add_to(m)
                    folium.TileLayer(tiles=google_hybrid, attr='Google', name='Google Hybrid', overlay=False).add_to(m)
                    
                    # 1. Lukis Poligon
                    points = list(zip(lats, lons))
                    points_closed = points + [points[0]]
                    
                    folium.Polygon(
                        locations=points_closed, 
                        color="yellow", 
                        weight=3, 
                        fill=True, 
                        fill_color=warna_poli, 
                        fill_opacity=0.4
                    ).add_to(m)
                    
                    # 2. Tambah Label Bering & Jarak
                    for i in range(len(df)):
                        p1 = [lats[i], lons[i]]
                        next_idx = (i + 1) % len(df)
                        p2 = [lats[next_idx], lons[next_idx]]
                        
                        dist = np.sqrt((e[next_idx]-e[i])**2 + (n[next_idx]-n[i])**2)
                        brg = np.degrees(np.arctan2((e[next_idx]-e[i]), (n[next_idx]-n[i]))) % 360
                        
                        mid_lat = (p1[0] + p2[0]) / 2
                        mid_lon = (p1[1] + p2[1]) / 2
                        
                        folium.Marker(
                            [mid_lat, mid_lon],
                            icon=folium.DivIcon(
                                html=f"""<div style="font-family: Arial; color: #00FF00; font-weight: bold; font-size: {saiz_teks}pt; 
                                white-space: nowrap; text-shadow: 2px 2px #000; text-align: center; transform: translate(-50%, -50%);">
                                {to_dms(brg)}<br>{dist:.2f}m</div>"""
                            )
                        ).add_to(m)

                    # 3. Tambah Marker Stesen
                    for i, row in df.iterrows():
                        stn_id = str(row["STN"]) if "STN" in df.columns else str(i+1)
                        
                        folium.CircleMarker(
                            location=[lats[i], lons[i]],
                            radius=saiz_marker, 
                            color="red", 
                            fill=True, 
                            fill_color="red", 
                            fill_opacity=1
                        ).add_to(m)
                        
                        folium.Marker(
                            [lats[i], lons[i]],
                            icon=folium.DivIcon(
                                icon_anchor=(0,0),
                                html=f"""<div style="font-family: Arial; color: white; font-weight: bold; font-size: 10pt; 
                                display: flex; align-items: center; justify-content: center; width: {saiz_marker*2}px; 
                                height: {saiz_marker*2}px; margin-left: -{saiz_marker}px; margin-top: -{saiz_marker}px;">
                                {stn_id}</div>"""
                            )
                        ).add_to(m)

                    # Tambah Layer Control di penjuru kanan atas
                    folium.LayerControl(position='topright').add_to(m)

                    m.fit_bounds(points)
                    st_folium(m, width=1100, height=600, returned_objects=[])

            with tab_plot:
                fig, ax = plt.subplots(figsize=(10, 8))
                e_plot = list(e) + [e[0]]
                n_plot = list(n) + [n[0]]
                ax.plot(e_plot, n_plot, marker='o', color='black', linewidth=2)
                ax.fill(e_plot, n_plot, color=warna_poli, alpha=0.3)
                
                # Label stesen pada plot Matplotlib
                for i, txt in enumerate(df['STN'] if 'STN' in df.columns else range(len(df))):
                    ax.annotate(txt, (e[i], n[i]), textcoords="offset points", xytext=(0,10), ha='center', fontweight='bold')
                
                ax.set_aspect('equal')
                ax.set_title("Lukisan Teknikal Lot", fontsize=14)
                ax.grid(True, linestyle='--', alpha=0.6)
                st.pyplot(fig)

            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Luas (m²)", f"{area:.3f}")
            c2.metric("Luas (Ekar)", f"{area * 0.000247105:.4f}")
            
            # GeoJSON Export
            geojson_data = json.dumps({
                "type": "FeatureCollection", 
                "features": [{
                    "type": "Feature", 
                    "geometry": {
                        "type": "Polygon", 
                        "coordinates": [list(zip(e, n))]
                    },
                    "properties": {"area_m2": area}
                }]
            })
            c3.download_button("📥 Download GeoJSON", data=geojson_data, file_name="survey_export.geojson", use_container_width=True)
        else:
            st.error("Fail CSV mesti mempunyai kolum 'E' dan 'N'!")

# JALANKAN APP
if st.session_state.logged_in:
    main_app()
else:
    login_page()
