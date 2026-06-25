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
    
    users = db.get_users()
    if not users:
        st.warning("Please configure at least one active User Profile first.")
    else:
        view_user_opts = {u[1]: u[0] for u in users}
        view_user_name = st.selectbox("Select User Profile context to view decrypted accounts", list(view_user_opts.keys()))
        view_user_id = view_user_opts[view_user_name]
        
        st.markdown(f"### Vault Directory for **{view_user_name}**")
        entries = db.get_passwords_by_user(view_user_id)
        
        if not entries:
            st.info(f"No password entries recorded for user profile: {view_user_name}")
        else:
            # Build database table pattern cleanly
            table_rows = []
            for ent in entries:
                ent_id, u_name, t_name, st_name, title, user_or_email, enc_pass, u_id, t_id, st_id = ent
                decrypted = enc.decrypt_password(enc_pass, st.session_state.current_pin)
                
                # Dynamic field label mapping based on Sub-category context
                field_label = st_name if st_name else "Username/Email"
                
                table_rows.append({
                    "Title": title,
                    "Category": t_name or "None",
                    "Sub-Category": st_name or "None",
                    "Account Username/Email": user_or_email,
                    "Decrypted Password": decrypted
                })
            
            # Display decrypted records inside a professional interactive dataframe
            df_entries = pd.DataFrame(table_rows)
            st.dataframe(df_entries[["Title", "Category", "Sub-Category", "Account Username/Email", "Decrypted Password"]], use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Dashboard", key="v_back", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()