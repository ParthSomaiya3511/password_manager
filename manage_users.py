import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

def render_manage_users():
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="font-size: 3rem;">👤</span>
            <h2 style="margin: 0; color: #1e293b; font-weight: 700;">Manage Users</h2>
            <p style="color: #64748b; font-size: 0.95rem;">Configure master user profiles and isolated vaults</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize page-level toggle states
    if 'show_add_user' not in st.session_state:
        st.session_state.show_add_user = False
    if 'show_edit_user' not in st.session_state:
        st.session_state.show_edit_user = False
    if 'show_delete_user' not in st.session_state:
        st.session_state.show_delete_user = False

    # Control Grid Row (Premium Button Layout)
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    # Retrieve Users List
    users = db.get_users()
    
    with col_btn1:
        # Action button style - Dynamic Setup
        add_label = "❌ Close Add Panel" if st.session_state.show_add_user else "➕ Add New User"
        if st.button(add_label, use_container_width=True, type="primary"):
            st.session_state.show_add_user = not st.session_state.show_add_user
            st.session_state.show_edit_user = False
            st.session_state.show_delete_user = False
            st.rerun()
            
    with col_btn2:
        edit_label = "❌ Close Edit Panel" if st.session_state.show_edit_user else "✏️ Edit User Profile"
        if st.button(edit_label, use_container_width=True):
            if not users:
                st.warning("No users available to edit.")
            else:
                st.session_state.show_edit_user = not st.session_state.show_edit_user
                st.session_state.show_add_user = False
                st.session_state.show_delete_user = False
                st.rerun()
                
    with col_btn3:
        del_label = "❌ Close Delete Panel" if st.session_state.show_delete_user else "🗑️ Delete User Profile"
        if st.button(del_label, use_container_width=True):
            if not users:
                st.warning("No users available to delete.")
            else:
                st.session_state.show_delete_user = not st.session_state.show_delete_user
                st.session_state.show_add_user = False
                st.session_state.show_edit_user = False
                st.rerun()

    # --- DYNAMIC ON-PAGE CONTAINERS ---

    # 1. ADD CONTAINER
    if st.session_state.show_add_user:
        with st.container(border=True):
            st.subheader("Add Profile")
            username = st.text_input("Username", placeholder="Enter profile username...")
            email = st.text_input("Email", placeholder="Enter email address...")
            if st.button("Save User", use_container_width=True, type="primary"):
                if username and email:
                    try:
                        with st.spinner("Registering user profile..."):
                            db.add_user(username, email)
                            time.sleep(2.0)
                        st.success(f"Added User: {username}")
                        st.session_state.show_add_user = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error registering user: {e}")
                else:
                    st.error("All user fields must be provided.")

    # 2. EDIT CONTAINER
    if st.session_state.show_edit_user and users:
        with st.container(border=True):
            st.subheader("Edit User Profile")
            selected_user_edit = st.selectbox(
                "Select Profile to Modify", 
                users, 
                format_func=lambda x: f"ID {x[0]} - {x[1]}",
                key="user_edit_selectbox"
            )
            up_username = st.text_input("Change Username", value=selected_user_edit[1])
            up_email = st.text_input("Change Email", value=selected_user_edit[2])
            
            if st.button("Save Changes", use_container_width=True, type="primary"):
                if up_username and up_email:
                    with st.spinner("Saving changes..."):
                        db.update_user(selected_user_edit[0], up_username, up_email)
                        time.sleep(2.0)
                    st.success("User updated successfully.")
                    st.session_state.show_edit_user = False
                    st.rerun()
                else:
                    st.error("Please fill in all fields.")

    # 3. DELETE CONTAINER
    if st.session_state.show_delete_user and users:
        with st.container(border=True):
            st.subheader("Delete User Profile")
            selected_user_del = st.selectbox(
                "Select Profile to Delete", 
                users, 
                format_func=lambda x: f"ID {x[0]} - {x[1]}",
                key="user_del_selectbox"
            )
            st.write(f"Are you sure you want to permanently delete user **{selected_user_del[1]}**? This will remove all associated passwords.")
            
            col_del_yes, col_del_no = st.columns(2)
            with col_del_yes:
                if st.button("Yes, Delete", use_container_width=True, type="primary"):
                    with st.spinner("Deleting user..."):
                        db.delete_user(selected_user_del[0])
                        time.sleep(2.0)
                    st.success("User deleted successfully.")
                    st.session_state.show_delete_user = False
                    st.rerun()
            with col_del_no:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_delete_user = False
                    st.rerun()

    # --- USER DIRECTORY VIEW TABLE ---
    st.markdown('<div class="section-label">Active Profiles Directory</div>', unsafe_allow_html=True)
    if not users:
        st.info("No active users present.")
    else:
        df_users = pd.DataFrame(users, columns=["User ID", "Username", "Email Address"])
        st.dataframe(df_users, use_container_width=True, hide_index=True)

        selected_user_view = st.selectbox(
            "Select User to Unlock Credentials Vault", 
            users, 
            format_func=lambda x: f"ID {x[0]} - {x[1]}",
            key="user_view_selectbox"
        )

        # "Show all passwords in user profile with container" Wireframe Integration
        st.markdown("---")
        st.subheader(f"💼 Stored Credentials Vault for {selected_user_view[1]}")
        
        # Check security access before showing unencrypted data in this master panel
        unlock = st.checkbox("🔑 Unlock View Stored Credentials", key="unlock_master_user")
        if unlock:
            correct_pin = db.get_master_pin()
            
            show_pin_confirm = st.checkbox("👁️ Show Confirm PIN Input Plaintext", value=False, key="show_pin_toggle_confirm")
            confirm_input_type = "default" if show_pin_confirm else "password"

            pin_input = st.text_input("Confirm Master PIN to Decrypt", type=confirm_input_type, key="master_user_pin")
            
            if pin_input == correct_pin:
                entries = db.get_passwords_by_user(selected_user_view[0])
                if not entries:
                    st.info(f"No credentials saved for user profile: {selected_user_view[1]}")
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

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="user_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()