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
        .login-box {{
            background: white; padding: 30px; border-radius: 15px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); color: #333;
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

# --- PENGURUSAN SESSION & SECURITY ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = ""
if 'attempts' not in st.session_state: st.session_state.attempts = 0
if 'recovery_mode' not in st.session_state: st.session_state.recovery_mode = False

# Database Pengguna (Simpan dalam Session supaya boleh diubah)
if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        "farzat": "442006",
        "sir fauzul": "1234",
        "123": "1234"
    }

SECRET_KEY = "progaming"

# --- HALAMAN LOG MASUK ---
def login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo = get_base64_image("PUO_Logo.png")
        if logo: st.markdown(f'<center><img src="data:image/png;base64,{logo}" width="180"></center>', unsafe_allow_html=True)
        
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # JIKA MOD PEMULIHAN AKTIF
        if st.session_state.recovery_mode:
            st.subheader("🛠️ Pemulihan Akaun")
            safe_word = st.text_input("Masukkan Kata Selamat", type="password")
            
            if safe_word == SECRET_KEY:
                st.success("Kata selamat betul!")
                new_user = st.text_input("ID Pengguna Baru")
                new_pass = st.text_input("Kata Laluan Baru", type="password")
                
                if st.button("SAHKAN PERUBAHAN"):
                    if new_user and new_pass:
                        st.session_state.users_db[new_user] = new_pass
                        st.session_state.recovery_mode = False
                        st.session_state.attempts = 0
                        st.success("Berjaya! Sila Log Masuk dengan ID baru.")
                        st.rerun()
                    else:
                        st.error("Sila isi semua ruangan!")
            elif safe_word != "":
                st.error("Kata Selamat Salah!")
                
            if st.button("Batal"):
                st.session_state.recovery_mode = False
                st.rerun()

        # JIKA LOG MASUK BIASA
        else:
            st.markdown("<h2 style='text-align: center;'>LOG MASUK SISTEM</h2>", unsafe_allow_html=True)
            user_in = st.text_input("ID Pengguna")
            pass_in = st.text_input("Kata Laluan", type="password")
            
            if st.button("MASUK"):
                if user_in in st.session_state.users_db and st.session_state.users_db[user_in] == pass_in:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_in.upper()
                    st.rerun()
                else:
                    st.session_state.attempts += 1
                    if st.session_state.attempts >= 3:
                        st.error("⚠️ ID atau Kata Laluan Salah 3 Kali!")
                        st.info("Terlupa kata laluan atau ID pengguna?")
                        if st.button("KLIK UNTUK RESET"):
                            st.session_state.recovery_mode = True
                            st.rerun()
                    else:
                        st.error(f"Salah! Cubaan: {st.session_state.attempts}/3")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- HALAMAN UTAMA ---
def main_app():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.current_user}")
        if st.button("🚪 Log Keluar"):
            st.session_state.logged_in = False
            st.session_state.attempts = 0
            st.rerun()

    st.markdown(f'<div class="main-header"><h1>SISTEM SURVEY LOT</h1><p>Selamat Datang, {st.session_state.current_user}</p></div>', unsafe_allow_html=True)

    # (Bahagian muat naik CSV dan peta kekal sama seperti sebelum ini)
    file = st.file_uploader("📂 Muat naik fail CSV", type="csv")
    if file:
        st.success("Fail berjaya dimuat naik!")
        # ... (kod peta anda di sini)

if st.session_state.logged_in:
    main_app()
else:
    login_page()
