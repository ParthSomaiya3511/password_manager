import streamlit as st
import database as db
import time

def render_edit_user():
    st.title("✏️ Edit User Profile")
    st.write("Modify the user parameters below:")
    st.write("---")

    target_id = st.session_state.get('edit_user_id')
    if not target_id:
        st.warning("No user selected for editing.")
        if st.button("⬅️ Return to Manage Users", use_container_width=True):
            st.session_state.page = 'manage_users'
            st.rerun()
        return

    users = db.get_users()
    target_user = [u for u in users if u[0] == target_id]
    
    if target_user:
        curr_u = target_user[0]
        new_username = st.text_input("Username", value=curr_u[1])
        new_email = st.text_input("Email Address", value=curr_u[2])
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("Save Changes", use_container_width=True, type="primary"):
                if new_username and new_email:
                    with st.spinner("Saving changes in database..."):
                        db.update_user(curr_u[0], new_username, new_email)
                        time.sleep(2.0)
                    st.success("User updated successfully.")
                    st.session_state.page = 'manage_users'
                    st.rerun()
                else:
                    st.error("Please fill in all fields.")
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.page = 'manage_users'
                st.rerun()
    else:
        st.error("Selected user profile not found.")
        if st.button("⬅️ Return to Manage Users", use_container_width=True):
            st.session_state.page = 'manage_users'
            st.rerun()