# --- LAYER POLYGON DENGAN POPUP ---
            points = list(zip(lats, lons))
            
            # Bina kandungan Popup HTML untuk Lot
            lot_popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 200px;">
                <h4 style="margin-bottom:10px; color:#007bff;">INFO LOT</h4>
                <table style="width:100%; border-collapse: collapse;">
                    <tr><td><b>Luas (m²):</b></td><td>{area:.3f}</td></tr>
                    <tr><td><b>Luas (Ekar):</b></td><td>{area/4046.856:.4f}</td></tr>
                    <tr><td><b>Luas (kp):</b></td><td>{area*10.7639:.2f}</td></tr>
                    <tr><td><b>Juruukur:</b></td><td>{st.session_state.current_user}</td></tr>
                </table>
            </div>
            """
            
            folium.Polygon(
                locations=points + [points[0]], 
                color=warna_poly, 
                weight=3, 
                fill=True, 
                fill_opacity=0.3,
                popup=folium.Popup(lot_popup_html, max_width=250),
                tooltip="Klik untuk Info Lot"
            ).add_to(fg_poly)
