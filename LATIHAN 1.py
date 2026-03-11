# --- KEMASKINI BAHAGIAN INI SAHAJA DALAM LOOP FOR ---

for i, row in df.iterrows():
    stn_id = str(row["STN"]) if "STN" in df.columns else str(i+1)
    
    # 1. Lukis Bulatan Merah (Base)
    folium.CircleMarker(
        location=[lats[i], lons[i]],
        radius=12,  # Besarkan sedikit supaya nombor nampak jelas
        color="red",
        weight=2,
        fill=True,
        fill_color="red",
        fill_opacity=1
    ).add_to(m)
    
    # 2. Letak Nombor Putih TEPAT di Tengah
    folium.Marker(
        [lats[i], lons[i]],
        icon=folium.DivIcon(
            icon_size=(0, 0), # Paksa anchor titik tengah
            icon_anchor=(0, 0),
            html=f"""
                <div style="
                    font-family: Arial, sans-serif; 
                    color: white; 
                    font-weight: bold; 
                    font-size: 10pt; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    width: 24px; 
                    height: 24px; 
                    margin-left: -12px; 
                    margin-top: -12px;
                    pointer-events: none;
                ">
                    {stn_id}
                </div>
            """
        )
    ).add_to(m)
