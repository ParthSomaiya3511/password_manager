import streamlit as st
import database as db
import time

def render_clear_data():
    st.title("⚠️ Wipe Database Store")
    st.warning("Warning: This destroys all configuration histories (Users, Types, Sub-types, Passwords).")
    
    confirmation = st.checkbox("I confirm that I want to completely delete all stored data.")
    if st.button("Execute Storage Purge", type="primary", use_container_width=True):
        if confirmation:
            try:
                with st.spinner("Wiping local database store..."):
                    db.clear_all_tables()
                    time.sleep(2.0)
                st.success("Local storage purged successfully.")
                st.session_state.page = 'dashboard'
                st.rerun()
            except Exception as e:
                st.error(f"Failed clearing datasets: {e}")
        else:
            st.error("Please confirm your action first.")

    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="clear_data_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()