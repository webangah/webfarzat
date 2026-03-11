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
        # EPSG:4390 ke EPSG:4326 (WGS84 Lat/Lon)
        # always_xy=True memastikan E=X dan N=Y
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

# --- HALAMAN UTAMA ---
def main_app():
    with st.sidebar:
        st.markdown("""
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

    st.markdown("""
        <div style='border-left: 5px solid #007bff; padding-left: 20px;'>
            <h1 style='margin-bottom: 0px;'>SISTEM SURVEY LOT</h1>
            <p style='color: #6c757d;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
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
