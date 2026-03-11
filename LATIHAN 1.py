import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PUO Survey Lot Visualizer", layout="wide") # Tukar ke 'wide' supaya lebih cantik

# --- FUNGSI PEMBANTU ---
def to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int((deg - d - m/60) * 3600)
    return f"{d}°{m}'{s}\""

# --- PENGURUSAN SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- HALAMAN LOG MASUK & LUPA PASSWORD ---
def login_page():
    # Guna lajur untuk letak login di tengah
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://www.puo.edu.my/wp-content/uploads/2021/08/cropped-LOGO-PUO-1.png", width=150)
        st.title("Sistem Lot Ukur PUO")
        
        tab1, tab2 = st.tabs(["Log Masuk", "Lupa Kata Laluan"])
        
        with tab1:
            st.info("ID: 1 | Kata Laluan: admin123")
            user_id = st.text_input("ID Pengguna")
            password = st.text_input("Kata Laluan", type='password')
            
            if st.button("Log Masuk", use_container_width=True):
                if user_id == "1" and password == "admin123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan salah!")

        with tab2:
            st.subheader("Pemulihan Akaun")
            soalan = st.text_input("Apakah makanan kesukaan anda?")
            if st.button("Tunjukkan Kata Laluan", use_container_width=True):
                if soalan.lower() == "ayam":
                    st.success("Kata laluan anda adalah: **admin123**")
                else:
                    st.error("Jawapan salah!")

# --- HALAMAN UTAMA (APLIKASI) ---
def main_app():
    # --- SIDEBAR ---
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True) # Jarak sedikit dari atas
    if st.sidebar.button("🔑 Tukar Kata Laluan", use_container_width=True):
        st.sidebar.info("Fungsi tukar kata laluan belum diaktifkan.")
    
    if st.sidebar.button("🚪 Log Keluar", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    # --- HEADER UTAMA ---
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        st.image("https://www.puo.edu.my/wp-content/uploads/2021/08/cropped-LOGO-PUO-1.png", use_column_width=True)
        
    with col_title:
        # Kod HTML untuk hasilkan garisan biru di tepi tajuk
        st.markdown("""
        <div style='border-left: 5px solid #007bff; padding-left: 20px; margin-top: 10px;'>
            <h1 style='margin-bottom: 0px; font-size: 40px;'>SISTEM SURVEY LOT</h1>
            <p style='color: #6c757d; font-size: 16px; margin-top: 5px;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---") # Garisan pemisah

    # --- BAHAGIAN INPUT (EPSG & MUAT NAIK CSV) ---
    col_epsg, col_upload = st.columns(2)
    
    with col_epsg:
        kod_epsg = st.text_input("🟢 Kod EPSG:", value="4390")
        
    with col_upload:
        uploaded_file = st.file_uploader("📁 Muat naik fail CSV (STN, E, N)", type="csv")

    # --- LOGIK PEMPROSESAN DATA ---
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        st.markdown("---")
        st.write("### Pratinjau Data:")
        st.dataframe(df, use_container_width=True)

        if 'E' in df.columns and 'N' in df.columns:
            # 1. Pengiraan LUAS
            e = df['E'].values
            n = df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))

            coords_list = [[df['E'][i], df['N'][i]] for i in range(len(df))]
            poly_coords = coords_list + [coords_list[0]]

            # Plotting
            fig, ax = plt.subplots(figsize=(10, 10))
            e_plot = [c[0] for c in poly_coords]
            n_plot = [c[1] for c in poly_coords]
            ax.plot(e_plot, n_plot, marker='o', color='b', linewidth=2)
            ax.fill(e_plot, n_plot, alpha=0.1, color='skyblue')
            
            # Label Jarak & Bearing
            for i in range(len(df)):
                x1, y1 = df['E'][i], df['N'][i]
                next_idx = (i + 1) % len(df)
                x2, y2 = df['E'][next_idx], df['N'][next_idx]
                
                dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                brg = np.degrees(np.arctan2((x2-x1), (y2-y1))) % 360
                
                mid_x, mid_y = (x1+x2)/2, (y1+y2)/2
                ax.text(mid_x, mid_y, f"{to_dms(brg)}\n{dist:.3f}m", fontsize=8, color='red', ha='center')

            ax.set_aspect('equal')
            
            # Papar hasil
            col_plot, col_metric = st.columns([2, 1])
            with col_plot:
                st.pyplot(fig)
            with col_metric:
                st.metric("Luas (m²)", f"{area:.3f}")
                st.metric("Luas (Ekar)", f"{area * 0.000247105:.4f}")
                st.info(f"Kod EPSG digunakan: **{kod_epsg}**")

            # --- KEMUDAHAN KE QGIS ---
            st.markdown("---")
            st.subheader("📥 Integrasi QGIS")
            st.write("Muat turun fail GeoJSON di bawah dan masukkan ke dalam QGIS untuk melihat pelan di atas peta.")
            
            features = []
            # Feature Poligon
            features.append({
                "type": "Feature",
                "properties": {"Jenis": "Lot Tanah", "Luas": round(area, 2), "EPSG": kod_epsg},
                "geometry": {"type": "Polygon", "coordinates": [poly_coords]}
            })
            # Feature Point (Batu Sempadan)
            for i in range(len(df)):
                features.append({
                    "type": "Feature",
                    "properties": {"STN": str(df['STN'][i]) if 'STN' in df.columns else i+1},
                    "geometry": {"type": "Point", "coordinates": [df['E'][i], df['N'][i]]}
                })

            geojson_data = json.dumps({"type": "FeatureCollection", "features": features})
            st.download_button(
                label="Download GeoJSON untuk QGIS",
                data=geojson_data,
                file_name="puo_lot_qgis.geojson",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.error("Kolum 'E' dan 'N' tidak dijumpai dalam fail CSV anda.")

# --- RUN LOGIC ---
if st.session_state.logged_in:
    main_app()
else:
    login_page()
