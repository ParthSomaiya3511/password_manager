import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

def render_manage_subtypes(check_pin_access):
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="font-size: 3rem;">🏷️</span>
            <h2 style="margin: 0; color: #1e293b; font-weight: 700;">Manage Sub-Categories (Sub-types)</h2>
            <p style="color: #64748b; font-size: 0.95rem;">Configure user-specific password sub-category groups</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Secure session pin verification check before loading page
    if not check_pin_access():
        return

    users = db.get_users()
    if not users:
        st.warning("Please configure at least one active User Profile first.")
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="subtypes_no_users_back"):
            st.session_state.page = 'dashboard'
            st.rerun()
        return

    # "Show user with dropdown" Integration
    user_opts = {u[1]: u[0] for u in users}
    selected_user = st.selectbox("Select User Profile context", list(user_opts.keys()), key="subtype_user_scope")
    
    # Dynamically resolve User ID from database to prevent cached-state ForeignKeyViolation
    active_user_id = db.get_user_id_by_name(selected_user)

    types = db.get_password_types_by_user(active_user_id) if active_user_id else []
    if not types:
        st.warning(f"Please configure at least one active Category Type for {selected_user} first.")
    else:
        type_opts = {t[1]: t[0] for t in types}
        selected_type = st.selectbox(f"Select Category Type (Belonging to {selected_user})", list(type_opts.keys()))
        active_type_id = type_opts[selected_type]

        # Initialize page-level toggle states
        if 'show_add_subtype' not in st.session_state:
            st.session_state.show_add_subtype = False
        if 'show_edit_subtype' not in st.session_state:
            st.session_state.show_edit_subtype = False
        if 'show_delete_subtype' not in st.session_state:
            st.session_state.show_delete_subtype = False

        sub_list = db.get_subtypes_by_type(active_type_id)

        # Control Grid Row (Premium Button Layout)
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            add_label = "❌ Close Add Panel" if st.session_state.show_add_subtype else "➕ Add New Sub-Category"
            if st.button(add_label, use_container_width=True, type="primary"):
                st.session_state.show_add_subtype = not st.session_state.show_add_subtype
                st.session_state.show_edit_subtype = False
                st.session_state.show_delete_subtype = False
                st.rerun()
                
        with col_btn2:
            edit_label = "❌ Close Edit Panel" if st.session_state.show_edit_subtype else "✏️ Edit Sub-Category"
            if st.button(edit_label, use_container_width=True):
                if not sub_list:
                    st.warning("No sub-categories available to edit.")
                else:
                    st.session_state.show_edit_subtype = not st.session_state.show_edit_subtype
                    st.session_state.show_add_subtype = False
                    st.session_state.show_delete_subtype = False
                    st.rerun()
                    
        with col_btn3:
            del_label = "❌ Close Delete Panel" if st.session_state.show_delete_subtype else "🗑️ Delete Sub-Category"
            if st.button(del_label, use_container_width=True):
                if not sub_list:
                    st.warning("No sub-categories available to delete.")
                else:
                    st.session_state.show_delete_subtype = not st.session_state.show_delete_subtype
                    st.session_state.show_add_subtype = False
                    st.session_state.show_edit_subtype = False
                    st.rerun()

        # --- DYNAMIC ON-PAGE CONTAINERS ---

        # 1. ADD CONTAINER
        if st.session_state.show_add_subtype:
            with st.container(border=True):
                st.subheader(f"Add New Sub-Category under '{selected_type}' for '{selected_user}'")
                sub_name = st.text_input("Sub-Category Label (e.g. AWS, Steam)")
                if st.button("Save Sub-Category", use_container_width=True, type="primary"):
                    if sub_name and active_user_id:
                        try:
                            with st.spinner("Saving Sub-Category..."):
                                db.add_password_subtype(active_user_id, active_type_id, sub_name)
                                time.sleep(2.0)
                            st.success(f"Added {sub_name} under category '{selected_type}'")
                            st.session_state.show_add_subtype = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error writing: {e}")
                    else:
                        st.error("Please enter a sub-category label.")

        # 2. EDIT CONTAINER
        if st.session_state.show_edit_subtype and sub_list:
            with st.container(border=True):
                st.subheader(f"Edit Sub-Category (Belonging to {selected_type})")
                selected_sub_edit = st.selectbox(
                    "Select Sub-Category to Modify", 
                    sub_list, 
                    format_func=lambda x: f"ID {x[0]} - {x[1]}",
                    key="subtype_edit_selectbox"
                )
                up_subname = st.text_input("Change Sub-Category Name", value=selected_sub_edit[1])
                if st.button("Save Changes", use_container_width=True, type="primary"):
                    if up_subname:
                        with st.spinner("Saving changes..."):
                            db.update_password_subtype(selected_sub_edit[0], active_type_id, up_subname)
                            time.sleep(2.0)
                        st.success("Sub-category updated successfully.")
                        st.session_state.show_edit_subtype = False
                        st.rerun()
                    else:
                        st.error("Please fill in all fields.")

        # 3. DELETE CONTAINER
        if st.session_state.show_delete_subtype and sub_list:
            with st.container(border=True):
                st.subheader(f"Delete Sub-Category (Belonging to {selected_type})")
                selected_sub_del = st.selectbox(
                    "Select Sub-Category to Delete", 
                    sub_list, 
                    format_func=lambda x: f"ID {x[0]} - {x[1]}",
                    key="subtype_del_selectbox"
                )
                st.write(f"Are you sure you want to permanently delete sub-category **{selected_sub_del[1]}**? This will remove all associated credentials.")
                
                col_del_yes, col_del_no = st.columns(2)
                with col_del_yes:
                    if st.button("Yes, Delete", use_container_width=True, type="primary"):
                        with st.spinner("Deleting sub-category..."):
                            db.delete_password_subtype(selected_sub_del[0])
                            time.sleep(2.0)
                        st.success("Sub-category deleted successfully.")
                        st.session_state.show_delete_subtype = False
                        st.rerun()
                with col_del_no:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.show_delete_subtype = False
                        st.rerun()

        # --- SUB-CATEGORY DIRECTORY TABLE ---
        st.markdown(f"**Active Sub-Categories under '{selected_type}'**")
        if not sub_list:
            st.info("No sub-categories configured yet.")
        else:
            df_subtypes = pd.DataFrame(sub_list, columns=["Subtype ID", "Sub-Category Label"])
            st.dataframe(df_subtypes, use_container_width=True, hide_index=True)

        # "and save any account password" Direct Panel Wireframe Integration
        st.markdown("---")
        st.subheader(f"🔒 Directly Save New Account Password for {selected_user}")
        st.write(f"Save a password securely linked to **{selected_user}** &rarr; **{selected_type}**")
        
        # Sub-type dropdown
        sub_options = ["None"] + [s[1] for s in sub_list] if sub_list else ["None"]
        save_sub_opt = st.selectbox("Assign Sub-Category for Saved Password", sub_options, key="direct_save_sub_opt")
        
        # Account Specific Details
        title = st.text_input("Account/Service Title (e.g. Gmail)")
        acc_user = st.text_input("Account Username/Email")
        
        show_pin_direct = st.checkbox("👁️ Show Password Confirm PIN Input Plaintext", value=False, key="show_pin_toggle_direct")
        direct_input_type = "default" if show_pin_direct else "password"
        acc_pass = st.text_input("Account Password (Plaintext)", type=direct_input_type)

        if st.button("Encrypt & Save Credentials to Vault", use_container_width=True, type="primary"):
            if title and acc_user and acc_pass:
                # Dynamically resolve fresh, valid IDs to avoid KeyForeignKeyViolation
                resolved_user_id = db.get_user_id_by_name(selected_user)
                resolved_type_id = db.get_type_id_by_name(resolved_user_id, selected_type)
                
                resolved_subtype_id = None
                if save_sub_opt != "None" and sub_list:
                    resolved_subtype_id = db.get_subtype_id_by_name(resolved_type_id, save_sub_opt)

                if resolved_user_id is None:
                    st.error("Error: Selected user profile no longer exists. Please refresh.")
                elif resolved_type_id is None:
                    st.error("Error: Selected category type no longer exists. Please refresh.")
                else:
                    # Uses the verified session current_pin directly (removes redundant inputs)
                    with st.spinner("Encrypting and saving credentials securely..."):
                        encrypted_val = enc.encrypt_password(acc_pass, st.session_state.current_pin)
                        db.add_password(
                            user_id=resolved_user_id,
                            type_id=resolved_type_id,
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