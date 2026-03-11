import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PUO Survey Lot Visualizer", layout="wide")

# --- FUNGSI PEMBANTU ---
def to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int((deg - d - m/60) * 3600)
    return f"{d}°{m}'{s}\""

# --- PENGURUSAN SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://www.puo.edu.my/wp-content/uploads/2021/08/cropped-LOGO-PUO-1.png", width=150)
        st.title("Sistem Lot Ukur PUO")
        st.info("ID: 1 | Kata Laluan: admin123")
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
    # --- SIDEBAR (PROFIL & KAWALAN) ---
    with st.sidebar:
        # 1. Kad Profil Pengguna
        st.markdown("""
        <div style='background-color: #0099ff; padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px;'>
            <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' width='80' style='filter: brightness(0) invert(1);'>
            <h2 style='margin: 10px 0 0 0;'>Hai, FARZAT!</h2>
            <p style='font-size: 14px; opacity: 0.8;'>MUHAMMAD FARZAT</p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("⚙️ Kawalan Paparan")
        
        # 2. Slider Kawalan
        saiz_marker = st.slider("Saiz Marker Stesen", 5, 50, 22)
        saiz_teks = st.slider("Saiz Bearing/Jarak", 5, 20, 12)
        tahap_zoom = st.slider("Tahap Zoom (Padding)", 0, 50, 19)
        
        # 3. Warna Poligon
        warna_poli = st.color_picker("Warna Poligon", "#FFFF00") # Default Kuning
        
        st.markdown("---")
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- HEADER UTAMA ---
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.image("https://www.puo.edu.my/wp-content/uploads/2021/08/cropped-LOGO-PUO-1.png", use_column_width=True)
    with col_title:
        st.markdown("""
        <div style='border-left: 5px solid #007bff; padding-left: 20px;'>
            <h1 style='margin-bottom: 0px;'>SISTEM SURVEY LOT</h1>
            <p style='color: #6c757d;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- BAHAGIAN INPUT ---
    col_epsg, col_upload = st.columns(2)
    with col_epsg:
        kod_epsg = st.text_input("🟢 Kod EPSG:", value="4390")
    with col_upload:
        uploaded_file = st.file_uploader("📁 Muat naik fail CSV (STN, E, N)", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        if 'E' in df.columns and 'N' in df.columns:
            # Pengiraan Luas
            e = df['E'].values
            n = df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            
            coords_list = [[df['E'][i], df['N'][i]] for i in range(len(df))]
            poly_coords = coords_list + [coords_list[0]]

            # Plotting menggunakan Matplotlib
            fig, ax = plt.subplots(figsize=(10, 8))
            e_plot = [c[0] for c in poly_coords]
            n_plot = [c[1] for c in poly_coords]
            
            # Lukis Poligon (Guna warna dari color picker)
            ax.plot(e_plot, n_plot, marker='o', color='black', markersize=saiz_marker/4, linewidth=2)
            ax.fill(e_plot, n_plot, color=warna_poli, alpha=0.5)
            
            # Label Bearing & Jarak
            for i in range(len(df)):
                x1, y1 = df['E'][i], df['N'][i]
                next_idx = (i + 1) % len(df)
                x2, y2 = df['E'][next_idx], df['N'][next_idx]
                
                dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                brg = np.degrees(np.arctan2((x2-x1), (y2-y1))) % 360
                
                mid_x, mid_y = (x1+x2)/2, (y1+y2)/2
                ax.text(mid_x, mid_y, f"{to_dms(brg)}\n{dist:.3f}m", 
                        fontsize=saiz_teks, color='red', ha='center', fontweight='bold')
                
                # Label Nombor Stesen
                ax.text(x1, y1, str(df['STN'][i] if 'STN' in df.columns else i+1), 
                        fontsize=saiz_teks+2, color='blue', ha='right')

            ax.set_aspect('equal')
            
            # Adjust Zoom (Padding)
            padding = tahap_zoom * 2
            ax.set_xlim(min(e_plot) - padding, max(e_plot) + padding)
            ax.set_ylim(min(n_plot) - padding, max(n_plot) + padding)

            # Paparan Hasil
            col_graph, col_info = st.columns([3, 1])
            with col_graph:
                st.pyplot(fig)
            with col_info:
                st.metric("Luas (m²)", f"{area:.3f}")
                st.metric("Luas (Ekar)", f"{area * 0.000247105:.4f}")
                
                # Download Button
                geojson_data = json.dumps({"type": "FeatureCollection", "features": [{
                    "type": "Feature",
                    "properties": {"Luas": area},
                    "geometry": {"type": "Polygon", "coordinates": [poly_coords]}
                }]})
                st.download_button("📥 Download GeoJSON", data=geojson_data, file_name="survey.geojson", use_container_width=True)

        else:
            st.error("Pastikan CSV anda mempunyai kolum 'E' dan 'N'.")

# --- JALANKAN APP ---
if st.session_state.logged_in:
    main_app()
else:
    login_page()
