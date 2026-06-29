import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

# Modal: Delete Sub-Category Popup (સેન્ટ્રલ ડાયલોગ પોપઅપ તરીકે - ઇન્સ્ટન્ટ ડીલીટ ફ્લો)
@st.dialog("⚠️ Delete Sub-Category")
def show_delete_popup(subtype_id, name):
    st.write(f"Are you sure you want to permanently delete sub-category **{name}**? This will remove all associated credentials.")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", use_container_width=True, type="primary"):
            # Instant database execution without loader
            db.delete_password_subtype(subtype_id)
            st.success("Sub-category deleted successfully.")
            st.rerun()
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_manage_subtypes(check_pin_access):
    st.title("🏷️ Manage Sub-Categories (Sub-types)")
    
    # Secure session pin verification check before loading page
    if not check_pin_access():
        return

    users = db.get_users()

    # Initialize page-level toggle states
    if 'show_add_subtype' not in st.session_state:
        st.session_state.show_add_subtype = False
        
    # State-driven trigger for Delete Popup
    if 'delete_subtype_triggered' not in st.session_state:
        st.session_state.delete_subtype_triggered = False
    if 'delete_subtype_id' not in st.session_state:
        st.session_state.delete_subtype_id = None
    if 'delete_subtype_name' not in st.session_state:
        st.session_state.delete_subtype_name = None

    # ➕ Add Toggle Button
    add_label = "❌ Close Add Panel" if st.session_state.show_add_subtype else "➕ Add New Sub-Category"
    if st.button(add_label, use_container_width=True, type="primary"):
        st.session_state.show_add_subtype = not st.session_state.show_add_subtype
        st.rerun()

    # --- DYNAMIC ON-PAGE ADD CONTAINER ---
    if st.session_state.show_add_subtype:
        with st.container(border=True):
            st.subheader("➕ Create New Sub-Category")
            
            if not users:
                st.warning("Please configure at least one active User Profile first.")
            else:
                user_opts = {u[1]: u[0] for u in users}
                selected_user = st.selectbox("👤 Select User Profile context", list(user_opts.keys()), key="subtype_add_user_scope")
                active_user_id = user_opts[selected_user]

                types = db.get_password_types_by_user(active_user_id)
                if not types:
                    st.warning(f"Please configure at least one Category Type for {selected_user} first.")
                else:
                    type_opts = {t[1]: t[0] for t in types}
                    selected_type = st.selectbox(f"Select Category Type (Belonging to {selected_user})", list(type_opts.keys()))
                    active_type_id = type_opts[selected_type]

                    sub_name = st.text_input("Sub-Category Label (e.g. AWS, Steam)", placeholder="Enter sub-category name...")
                    if st.button("Save Sub-Category", use_container_width=True, type="primary"):
                        if sub_name:
                            clean_sub_name = sub_name.strip()
                            
                            # Validate if the sub-category already exists under this parent context
                            existing_subtypes = db.get_password_subtypes()
                            subtype_exists = any(
                                s[1] == active_user_id and s[3] == active_type_id and s[5].lower() == clean_sub_name.lower()
                                for s in existing_subtypes
                            )
                            
                            if subtype_exists:
                                st.error(f"Sub-category '{clean_sub_name}' already exists under the '{selected_type}' category context.")
                            else:
                                try:
                                    with st.spinner("Saving Sub-Category..."):
                                        db.add_password_subtype(active_user_id, active_type_id, clean_sub_name)
                                        time.sleep(2.0)
                                    st.success(f"Added {sub_name} under category '{selected_type}'")
                                    st.session_state.show_add_subtype = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error writing: {e}")
                        else:
                            st.error("Please enter a sub-category label.")

    # Fetch all subtypes globally across all users for the Master action-grid
    sub_list = db.get_password_subtypes()

    # --- SUB-CATEGORY ACTION-GRID DIRECTORY ---
    st.markdown('<div class="section-label">Active Sub-Categories (All Profiles)</div>', unsafe_allow_html=True)
    if not sub_list:
        st.info("No sub-categories configured yet.")
    else:
        # Header Row
        st.markdown("""
            <div style="font-weight: 700; color: #475569; padding-bottom: 8px; border-bottom: 1px solid #cbd5e1; margin-bottom: 12px;">
                <div style="display: flex;">
                    <div style="width: 25%;">User Profile</div>
                    <div style="width: 25%;">Parent Category</div>
                    <div style="width: 35%;">Sub-Category Label</div>
                    <div style="width: 15%; text-align: center;">Access</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Grid rows
        for s in sub_list:
            sid, uid, uname, tid, tname, sname = s
            col_row, col_act = st.columns([80, 20])
            with col_row:
                st.markdown(f"""
                    <div style="display: flex; padding: 6px 0; border-bottom: 1px solid #f1f5f9;">
                        <div style="width: 29%; font-weight: 600; color: #475569;">{uname}</div>
                        <div style="width: 29%; color: #334155;">{tname}</div>
                        <div style="width: 42%; font-weight: 600; color: #0f172a;">{sname}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col_act:
                col_e, col_d = st.columns(2)
                
                with col_e:
                    # Redirects cleanly to standalone edit_subtype.py on click
                    if st.button("✏️", key=f"edit_s_{sid}", help=f"Edit {sname}"):
                        st.session_state.edit_subtype_id = sid
                        st.session_state.page = 'edit_subtype'
                        st.rerun()
                with col_d:
                    # Triggers state-driven modal popup cleanly
                    if st.button("🗑️", key=f"del_s_{sid}", help=f"Delete {sname}"):
                        st.session_state.delete_subtype_id = sid
                        st.session_state.delete_subtype_name = sname
                        st.session_state.delete_subtype_triggered = True
                        st.session_state.show_add_subtype = False
                        st.rerun()

    # Execute State-driven delete modal popup cleanly outside page loops
    if st.session_state.delete_subtype_triggered:
        st.session_state.delete_subtype_triggered = False # resets trigger
        show_delete_popup(st.session_state.delete_subtype_id, st.session_state.delete_subtype_name)

    # --- DIRECT PASSWORD SAVING FORM ---
    st.markdown("---")
    st.subheader("🔒 Directly Save New Account Password")
    st.write("Save a password securely linked to any User, Category, and Sub-category:")

    if users:
        direct_users = {u[1]: u[0] for u in users}
        selected_direct_user = st.selectbox("👤 Select User Profile", list(direct_users.keys()), key="direct_save_user_select")
        direct_user_id = direct_users[selected_direct_user]
        
        direct_types = db.get_password_types_by_user(direct_user_id)
        if not direct_types:
            st.info(f"Please configure at least one active Category Type for {selected_direct_user} first.")
        else:
            direct_type_opts = {t[1]: t[0] for t in direct_types}
            selected_direct_type = st.selectbox("📁 Select Category Type", list(direct_type_opts.keys()), key="direct_save_type_select")
            direct_type_id = direct_type_opts[selected_direct_type]
            
            direct_sub_list = db.get_subtypes_by_type(direct_type_id)
            sub_options = ["None"] + [s[1] for s in direct_sub_list] if direct_sub_list else ["None"]
            save_sub_opt = st.selectbox("Assign Sub-Category for Saved Password", sub_options, key="direct_save_sub_opt")
            
            # Account Specific Details
            title = st.text_input("Account/Service Title (e.g. Gmail)")
            acc_user = st.text_input("Account Username/Email")
            
            show_pin_direct = st.checkbox("👁️ Show Password Confirm PIN Input Plaintext", value=False, key="show_pin_toggle_direct")
            direct_input_type = "default" if show_pin_direct else "password"
            acc_pass = st.text_input("Account Password (Plaintext)", type=direct_input_type)

            if st.button("Encrypt & Save Credentials to Vault", use_container_width=True, type="primary"):
                if title and acc_user and acc_pass:
                    resolved_subtype_id = None
                    if save_sub_opt != "None" and direct_sub_list:
                        sub_opts_dict = {s[1]: s[0] for s in direct_sub_list}
                        resolved_subtype_id = sub_opts_dict.get(save_sub_opt)

                    # Uses the verified session current_pin directly
                    with st.spinner("Encrypting and saving credentials securely..."):
                        encrypted_val = enc.encrypt_password(acc_pass, st.session_state.current_pin)
                        db.add_password(
                            user_id=direct_user_id,
                            type_id=direct_type_id,
                            subtype_id=resolved_subtype_id,
                            title=title.strip(),
                            username_or_email=acc_user.strip(),
                            encrypted_val=encrypted_val
                        )
                        time.sleep(2.0)
                    st.success("Credentials saved to vault successfully.")
                    st.rerun()
                else:
                    st.error("Platform title, account username, and password fields are required.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="subtypes_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()