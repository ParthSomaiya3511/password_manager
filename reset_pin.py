import streamlit as st
import database as db
import time

def render_reset_pin():
    st.title("🔑 Reset Master PIN")
    
    current_pin_input = st.text_input("Enter Current PIN", type="password")
    new_pin_input = st.text_input("Enter New PIN", type="password")
    confirm_new_pin = st.text_input("Confirm New PIN", type="password")
    
    if st.button("Update PIN", use_container_width=True):
        real_pin = db.get_master_pin()
        if current_pin_input != real_pin:
            st.error("Incorrect current Master PIN.")
        elif new_pin_input != confirm_new_pin:
            st.error("PIN mismatch on verification.")
        elif len(new_pin_input) < 4:
            st.error("PIN must be at least 4 characters.")
        else:
            with st.spinner("Updating Master PIN..."):
                db.update_master_pin(new_pin_input)
                time.sleep(2.0)
            st.success("PIN changed successfully.")
            st.session_state.authenticated = False
            st.session_state.page = 'dashboard'
            st.rerun()

    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="reset_pin_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()