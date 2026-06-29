import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

# Modal: Delete User Popup (સેન્ટ્રલ ડાયલોગ પોપઅપ - લોડર વગર ઇન્સ્ટન્ટ ડીલીટ ફ્લો)
@st.dialog("⚠️ Delete User Profile")
def show_delete_popup(user_id, username):
    st.write(f"Are you sure you want to permanently delete user **{username}**? This will remove all associated passwords.")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", use_container_width=True, type="primary"):
            # ઇન્સ્ટન્ટ ડેટાબેઝ ડીલીટ ક્વેરી એક્ઝિક્યુશન (લોડર વગર)
            db.delete_user(user_id)
            st.success("User deleted successfully.")
            st.rerun()
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_manage_users():
    st.title("👤 Manage Users")
    
    # Initialize page-level states
    if 'show_add_user' not in st.session_state:
        st.session_state.show_add_user = False
        
    # State-driven trigger for Delete Popup
    if 'delete_user_triggered' not in st.session_state:
        st.session_state.delete_user_triggered = False
    if 'delete_user_id' not in st.session_state:
        st.session_state.delete_user_id = None
    if 'delete_user_name' not in st.session_state:
        st.session_state.delete_user_name = None

    # ➕ Rectangular Add Button (Toggles on-page container directly below)
    add_label = "❌ Close Add Panel" if st.session_state.show_add_user else "➕ Add New User Profile"
    if st.button(add_label, use_container_width=True, type="primary"):
        st.session_state.show_add_user = not st.session_state.show_add_user
        st.rerun()

    # --- DYNAMIC ON-PAGE ADD CONTAINER ---
    if st.session_state.show_add_user:
        with st.container(border=True):
            st.subheader("Register New User Profile")
            username = st.text_input("Username", placeholder="Enter username...")
            email = st.text_input("Email Address", placeholder="Enter email address...")
            if st.button("Save New User", use_container_width=True, type="primary"):
                if username and email:
                    clean_username = username.strip()
                    clean_email = email.strip()
                    
                    # Fetch existing users to validate duplicates
                    existing_users = db.get_users()
                    username_exists = any(u[1].lower() == clean_username.lower() for u in existing_users)
                    email_exists = any(u[2].lower() == clean_email.lower() for u in existing_users)
                    
                    if username_exists:
                        st.error("A user profile with this username already exists.")
                    elif email_exists:
                        st.error("A user profile with this email address already exists.")
                    else:
                        try:
                            with st.spinner("Registering user profile..."):
                                db.add_user(clean_username, clean_email)
                                time.sleep(2.0)
                            st.success(f"Added User: {username}")
                            st.session_state.show_add_user = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error registering user: {e}")
                else:
                    st.error("All user fields must be provided.")

    users = db.get_users()

    # --- USER DIRECTORY VIEW TABLE (In-Line Action Grid) ---
    st.markdown('<div class="section-label">Active Profiles Directory</div>', unsafe_allow_html=True)
    if not users:
        st.info("No active users present.")
    else:
        # Header Row
        st.markdown("""
            <div style="font-weight: 700; color: #475569; padding-bottom: 8px; border-bottom: 1px solid #cbd5e1; margin-bottom: 12px;">
                <div style="display: flex;">
                    <div style="width: 15%;">User ID</div>
                    <div style="width: 35%;">Username</div>
                    <div style="width: 35%;">Email Address</div>
                    <div style="width: 15%; text-align: center;">Access</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Grid Record Rows
        for u in users:
            uid, uname, uemail = u
            col_row, col_act = st.columns([80, 20])
            with col_row:
                st.markdown(f"""
                    <div style="display: flex; padding: 6px 0; border-bottom: 1px solid #f1f5f9;">
                        <div style="width: 18%; color: #64748b; font-family: monospace;">{uid}</div>
                        <div style="width: 41%; font-weight: 600; color: #0f172a;">{uname}</div>
                        <div style="width: 41%; color: #334155;">{uemail}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col_act:
                col_v, col_e, col_d = st.columns(3)
                with col_v:
                    # Redirects cleanly to standalone view_user_vault.py on click
                    if st.button("👁️", key=f"view_u_{uid}", help=f"View decrypted credentials for {uname}"):
                        st.session_state.view_user_id = uid
                        st.session_state.view_user_name = uname
                        st.session_state.page = 'view_user_vault'
                        st.rerun()
                with col_e:
                    # Redirects cleanly to standalone edit_user.py on click
                    if st.button("✏️", key=f"edit_u_{uid}", help=f"Edit {uname}"):
                        st.session_state.edit_user_id = uid
                        st.session_state.page = 'edit_user'
                        st.rerun()
                with col_d:
                    # Triggers state-driven modal popup cleanly while hiding Add container
                    if st.button("🗑️", key=f"del_u_{uid}", help=f"Delete {uname}"):
                        st.session_state.delete_user_id = uid
                        st.session_state.delete_user_name = uname
                        st.session_state.delete_user_triggered = True
                        st.session_state.show_add_user = False # Hides add container safely
                        st.rerun()

    # Execute State-driven delete modal popup cleanly outside page loops
    if st.session_state.delete_user_triggered:
        st.session_state.delete_user_triggered = False # resets trigger
        show_delete_popup(st.session_state.delete_user_id, st.session_state.delete_user_name)

    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="user_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()