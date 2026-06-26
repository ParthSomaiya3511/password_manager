import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

def render_view_passwords(check_pin_access):
    st.title("🔑 Stored Credentials Directory")
    if not check_pin_access():
        return

    st.write("---")
    
    # Fetch all passwords globally across all user profiles
    entries = db.get_passwords()
    
    if not entries:
        st.info("No credentials stored in the database yet.")
    else:
        st.markdown("### Master Vault Directory (All Profiles)")
        
        # Build master database table pattern cleanly
        table_rows = []
        for ent in entries:
            ent_id, u_name, t_name, st_name, title, user_or_email, enc_pass, u_id, t_id, st_id = ent
            decrypted = enc.decrypt_password(enc_pass, st.session_state.current_pin)
            
            table_rows.append({
                "User Profile": u_name,
                "Title": title,
                "Category": t_name or "None",
                "Sub-Category": st_name or "None",
                "Account Username/Email": user_or_email,
                "Decrypted Password": decrypted
            })
        
        # Display all decrypted records inside a single combined master table
        df_entries = pd.DataFrame(table_rows)
        st.dataframe(
            df_entries[["User Profile", "Title", "Category", "Sub-Category", "Account Username/Email", "Decrypted Password"]], 
            use_container_width=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Dashboard", key="v_back", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()