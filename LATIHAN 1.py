# --- KEMASKINI FUNGSI TRANSFORM ---
def transform_coords(df, epsg_code):
    try:
        # Kita guna pyproj untuk tukar koordinat meter (RSO/Cassini) ke Lat/Lon
        # 'always_xy=True' memastikan E=X dan N=Y
        transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
        
        # Ambil data E dan N
        e_vals = df['E'].values
        n_vals = df['N'].values
        
        # Tukar koordinat
        lon, lat = transformer.transform(e_vals, n_vals)
        
        # Semak jika hasil penukaran adalah munasabah (Lat Malaysia antara 1 hingga 7)
        if np.isnan(lat).any() or np.mean(lat) < -90 or np.mean(lat) > 90:
            return None, None
            
        return lat, lon
    except Exception as e:
        st.error(f"Ralat Transform: {e}")
        return None, None

# --- DALAM main_app() BAHAGIAN tab_map ---
with tab_map:
    st.subheader("Paparan Google Satellite")
    lats, lons = transform_coords(df, kod_epsg)
    
    if lats is not None and not np.isnan(lats).any():
        # Setup Folium Map - Zoom ke purata koordinat
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=18, control_scale=True)
        
        # Tambah Layer Google Satellite
        google_sat = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
        folium.TileLayer(
            tiles=google_sat, 
            attr='Google', 
            name='Google Satellite', 
            overlay=False, 
            control=True
        ).add_to(m)
        
        # Lukis Poligon
        points = list(zip(lats, lons))
        points.append(points[0]) # Tutup poligon
        
        folium.Polygon(
            locations=points, 
            color="white", 
            weight=3, 
            fill=True, 
            fill_color=warna_poli, 
            fill_opacity=0.5
        ).add_to(m)
        
        # Tambah Marker & Label Nombor Stesen
        for i, row in df.iterrows():
            folium.CircleMarker(
                location=[lats[i], lons[i]], 
                radius=4, 
                color="red", 
                fill=True,
                fill_color="yellow"
            ).add_to(m)
            
            # Label nombor stesen yang lebih jelas
            stn_label = str(row["STN"]) if "STN" in df.columns else str(i+1)
            folium.Marker(
                [lats[i], lons[i]], 
                icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; font-weight: bold; background-color: rgba(0,0,0,0.5); padding: 2px; border-radius: 3px; font-size: 9pt;">{stn_label}</div>""")
            ).add_to(m)

        # Autozoom ke poligon
        m.fit_bounds(points)
        
        st_folium(m, width=1100, height=600, returned_objects=[])
    else:
        st.error("❌ Peta tidak dapat dipaparkan. Kod EPSG mungkin salah atau koordinat CSV tidak sah.")
        st.info("Tip: Untuk Semenanjung Malaysia, cuba gunakan EPSG:3168 atau 3375.")
