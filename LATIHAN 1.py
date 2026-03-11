# --- DALAM BAHAGIAN tab_map DI main_app() ---

with tab_map:
    st.subheader("Paparan Google Satellite")
    lats, lons = transform_coords(df, kod_epsg)
    
    if lats is not None:
        # Setup Folium Map
        m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=19)
        
        # Tambah Google Satellite Layer
        google_sat = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
        folium.TileLayer(tiles=google_sat, attr='Google', name='Google Satellite', overlay=False, control=True).add_to(m)
        
        # Lukis Poligon (Garis kuning mengikut gambar anda)
        points = list(zip(lats, lons))
        points.append(points[0]) 
        folium.Polygon(
            locations=points, 
            color="yellow", # Tukar ke kuning supaya sama macam gambar
            weight=3, 
            fill=True, 
            fill_color=warna_poli, 
            fill_opacity=0.3
        ).add_to(m)
        
        # --- KEMASKINI MARKER STESEN (SAMA MACAM GAMBAR) ---
        for i, row in df.iterrows():
            stn_id = str(row["STN"]) if "STN" in df.columns else str(i+1)
            
            # 1. Lukis Bulatan Merah (Base)
            folium.CircleMarker(
                location=[lats[i], lons[i]],
                radius=10, # Saiz bulatan
                color="red",
                weight=2,
                fill=True,
                fill_color="red",
                fill_opacity=1
            ).add_to(m)
            
            # 2. Letak Nombor Putih di Tengah Bulatan
            folium.Marker(
                [lats[i], lons[i]],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-family: sans-serif; 
                        color: white; 
                        font-weight: bold; 
                        font-size: 9pt; 
                        width: 20px; 
                        height: 20px; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center;
                        transform: translate(-10px, -10px);
                    ">
                        {stn_id}
                    </div>
                    """
                )
            ).add_to(m)

        # Auto Zoom
        m.fit_bounds(points)
        st_folium(m, width=1100, height=500, returned_objects=[])
