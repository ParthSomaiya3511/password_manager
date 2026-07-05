import streamlit as st
import database as db
import time

def render_edit_user():
    # Inject sharp rectangular form card styling
    st.markdown("""
    <style>
        div[data-testid="stVerticalBlockBorder"] {
            border: 3px solid #000000 !important;
            border-radius: 0px !important;
            background-color: #ffffff !important;
            box-shadow: none !important;
            padding: 24px !important;
        }
        div.stButton > button {
            border-radius: 0px !important;
            border: 2px solid #000000 !important;
            font-weight: 700 !important;
            transition: all 0.1s ease-in-out !important;
        }
        div.stButton > button:hover {
            background-color: #000000 !important;
            color: #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("✏️ Edit User Profile")
    st.write("Modify the User parameters below:")
    st.write("---")

    target_id = st.session_state.get('edit_user_id')
    if not target_id:
        st.warning("No user profile selected for editing.")
        if st.button("⬅️ Return to Manage Users", use_container_width=True):
            st.session_state.page = 'manage_users'
            st.rerun()
        return

    # Fetch users statically to find matching record
    users = db.get_users()
    target_user = [u for u in users if u[0] == target_id]
    
    if target_user:
        curr_u = target_user[0]
        uid, uname, uemail = curr_u
        
        with st.container(border=True):
            st.markdown(f"""
                <div style="background-color: #f1f5f9; padding: 14px 20px; border-bottom: 3px solid #000000; margin: -24px -24px 20px -24px;">
                    <span style="font-weight: 700; font-size: 1.1rem; color: #000000;">📝 Editing User ID: {uid}</span>
                </div>
            """, unsafe_allow_html=True)
            
            new_username = st.text_input("Username", value=uname, placeholder="Enter username...")
            new_email = st.text_input("Email Address", value=uemail, placeholder="Enter email address...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Changes", use_container_width=True, type="primary"):
                    if new_username and new_email:
                        clean_username = new_username.strip()
                        clean_email = new_email.strip()
                        
                        # 1. Format validation: Check for @ and .
                        if "@" not in clean_email or "." not in clean_email:
                            st.error("Please enter a valid email address containing both '@' and '.' characters.")
                        elif len(clean_username) < 3:
                            st.error("Username must be at least 3 characters long.")
                        else:
                            # 2. Duplicate validation (excludes own record)
                            username_exists = any(u[1].lower() == clean_username.lower() and u[0] != uid for u in users)
                            email_exists = any(u[2].lower() == clean_email.lower() and u[0] != uid for u in users)
                            
                            if username_exists:
                                st.error(f"A user profile with the username '{clean_username}' already exists.")
                            elif email_exists:
                                st.error(f"A user profile with the email address '{clean_email}' already exists.")
                            else:
                                try:
                                    with st.spinner("Saving changes in database..."):
                                        db.update_user(uid, clean_username, clean_email)
                                        time.sleep(2.0)
                                    st.success("User profile updated successfully.")
                                    st.session_state.page = 'manage_users'
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to update profile: {e}")
                    else:
                        st.error("All user fields must be provided.")
            with col_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.page = 'manage_users'
                    st.rerun()
    else:
        st.error("Selected user profile not found.")
        if st.button("⬅️ Return to Manage Users", use_container_width=True):
            st.session_state.page = 'manage_users'
            st.rerun()