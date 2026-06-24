import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

# Modal: Add User Popup
@st.dialog("➕ Add New User Profile")
def show_add_user_popup():
    st.write("Register a new master profile:")
    username = st.text_input("Username")
    email = st.text_input("Email")
    if st.button("Save User", use_container_width=True):
        if username and email:
            try:
                # Custom CSS targets this and centers it within the modal window
                with st.spinner("Registering user profile..."):
                    db.add_user(username, email)
                    time.sleep(2.0)
                st.success(f"Added User: {username}")
                st.rerun()
            except Exception as e:
                st.error(f"Error registering user: {e}")
        else:
            st.error("All user fields must be provided.")

# Modal: Edit User Popup
@st.dialog("✏️ Edit User Profile")
def show_edit_popup(user_id, current_username, current_email):
    st.markdown("#### Modify the user parameters below:")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    new_username = st.text_input("Username", value=current_username)
    new_email = st.text_input("Email", value=current_email)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    if st.button("Save Changes", use_container_width=True):
        if new_username and new_email:
            with st.spinner("Saving changes..."):
                db.update_user(user_id, new_username, new_email)
                time.sleep(2.0)
            st.success("User updated successfully.")
            st.rerun()
        else:
            st.error("Please fill in all fields.")

# Modal: Delete User Popup
@st.dialog("⚠️ Delete User Profile")
def show_delete_popup(user_id, username):
    st.write(f"Are you sure you want to permanently delete user **{username}**? This will remove all associated passwords.")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", use_container_width=True):
            with st.spinner("Deleting user..."):
                db.delete_user(user_id)
                time.sleep(2.0)
            st.success("User deleted successfully.")
            st.rerun()
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_manage_users():
    st.title("👤 Manage Users")
    
    # Trigger Add User Popup Button
    if st.button("➕ Add New User", use_container_width=True, type="primary"):
        show_add_user_popup()

    st.subheader("Manage Active Profiles")
    users = db.get_users()
    if not users:
        st.info("No active users present.")
    else:
        df_users = pd.DataFrame(users, columns=["User ID", "Username", "Email Address"])
        st.dataframe(df_users, use_container_width=True, hide_index=True)

        selected_user = st.selectbox(
            "Select User to Update/Delete", 
            users, 
            format_func=lambda x: f"ID {x[0]} - {x[1]}"
        )
        
        col_up, col_del = st.columns(2)
        with col_up:
            if st.button("✏️ Edit Selected User", use_container_width=True):
                show_edit_popup(selected_user[0], selected_user[1], selected_user[2])
        with col_del:
            if st.button("🗑️ Delete Selected User", use_container_width=True):
                show_delete_popup(selected_user[0], selected_user[1])

        # "Show all passwords in user profile with container" Wireframe Integration
        st.markdown("---")
        st.subheader(f"💼 Stored Credentials Vault for {selected_user[1]}")
        
        # Check security access before showing unencrypted data in this master panel
        unlock = st.checkbox("🔑 Unlock View Stored Credentials", key="unlock_master_user")
        if unlock:
            correct_pin = db.get_master_pin()
            
            show_pin_confirm = st.checkbox("👁️ Show Confirm PIN Input Plaintext", value=False, key="show_pin_toggle_confirm")
            confirm_input_type = "default" if show_pin_confirm else "password"

            pin_input = st.text_input("Confirm Master PIN to Decrypt", type=confirm_input_type, key="master_user_pin")
            
            if pin_input == correct_pin:
                entries = db.get_passwords_by_user(selected_user[0])
                if not entries:
                    st.info(f"No credentials saved for user profile: {selected_user[1]}")
                else:
                    for ent in entries:
                        ent_id, u_name, t_name, st_name, title, user_or_email, enc_pass, _, _, _ = ent
                        decrypted = enc.decrypt_password(enc_pass, pin_input)
                        
                        # Container Box
                        st.markdown(f"**Platform Title: {title}**")
                        field_label = st_name if st_name else "Username / Email"
                        st.markdown(f"""
                        <div class="cred-container">
                            <h5>📂 Platform: {title}</h5>
                            <p style="margin: 2px 0;"><b>Type Hierarchy</b>: {t_name or 'None'} &rarr; {st_name or 'None'}</p>
                            <p style="margin: 2px 0;"><b>{field_label}</b>: {user_or_email}</p>
                            <p style="margin: 2px 0;"><b>Decrypted Password</b>: <code style="color: #0284c7;">{decrypted}</code></p>
                        </div>
                        """, unsafe_allow_html=True)
            elif pin_input:
                st.error("Invalid Master PIN.")

    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="user_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()