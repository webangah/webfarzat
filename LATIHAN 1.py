import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PUO Survey Lot Visualizer", layout="centered")

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
    st.image("https://www.puo.edu.my/wp-content/uploads/2021/08/cropped-LOGO-PUO-1.png", width=150)
    st.title("Sistem Lot Ukur PUO")
    
    tab1, tab2 = st.tabs(["Log Masuk", "Lupa Kata Laluan"])
    
    with tab1:
        st.info("ID: 1 | Kata Laluan: admin123")
        user_id = st.text_input("ID Pengguna")
        password = st.text_input("Kata Laluan", type='password')
        
        if st.button("Log Masuk"):
            if user_id == "1" and password == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("ID atau Kata Laluan salah!")

    with tab2:
        st.subheader("Pemulihan Akaun")
        soalan = st.text_input("Apakah makanan kesukaan anda?")
        if st.button("Tunjukkan Kata Laluan"):
            if soalan.lower() == "ayam":
                st.success("Kata laluan anda adalah: **admin123**")
            else:
                st.error("Jawapan salah!")

# --- HALAMAN UTAMA (APLIKASI) ---
def main_app():
    # Sidebar: Info & Log Keluar
    st.sidebar.image("https://www.puo.edu.my/wp-content/uploads/2021/08/cropped-LOGO-PUO-1.png", width=100)
    st.sidebar.title("Politeknik Ungku Omar")
    st.sidebar.write("Jabatan Kejuruteraan Awam")
    if st.sidebar.button("Log Keluar"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("Visualisasi Poligon Data Ukur")
    st.write("Sila muat naik fail CSV untuk menjana pelan dan fail GeoJSON.")

    uploaded_file = st.file_uploader("Pilih fail CSV anda", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("### Pratinjau Data:")
        st.dataframe(df)

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
            st.pyplot(fig)
            
            # Metrik Luas
            col1, col2 = st.columns(2)
            col1.metric("Luas (m²)", f"{area:.3f}")
            col2.metric("Luas (Ekar)", f"{area * 0.000247105:.4f}")

            # --- KEMUDAHAN KE QGIS ---
            st.markdown("---")
            st.subheader("📥 Integrasi QGIS")
            st.write("Muat turun fail GeoJSON di bawah dan masukkan ke dalam QGIS untuk melihat pelan di atas peta.")
            
            features = []
            # Feature Poligon
            features.append({
                "type": "Feature",
                "properties": {"Jenis": "Lot Tanah", "Luas": round(area, 2)},
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
                mime="application/json"
            )
        else:
            st.error("Kolum 'E' dan 'N' tidak dijumpai.")

# --- RUN LOGIC ---
if st.session_state.logged_in:
    main_app()
else:
    login_page()