import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

# Modal: Add Sub-Category Popup
@st.dialog("➕ Add Sub-Category Type")
def show_add_subtype_popup(active_user_id, active_type_id, selected_type, selected_user):
    st.write(f"Add a new Sub-Category under **{selected_type}** for user: **{selected_user}**")
    sub_name = st.text_input("Sub-Category Label (e.g. AWS, Steam)")
    if st.button("Save Sub-Category", use_container_width=True):
        if sub_name and active_user_id:
            try:
                with st.spinner("Saving Sub-Category..."):
                    db.add_password_subtype(active_user_id, active_type_id, sub_name)
                    time.sleep(2.0)
                st.success(f"Added {sub_name} under category '{selected_type}'")
                st.rerun()
            except Exception as e:
                st.error(f"Error writing: {e}")
        else:
            st.error("Please enter a sub-category label.")

# Modal: Edit Sub-Category Popup
@st.dialog("✏️ Edit Sub-Category")
def show_edit_popup(subtype_id, active_type_id, current_name):
    st.markdown("#### Modify the Sub-Category parameter below:")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    new_name = st.text_input("Sub-Category Name", value=current_name)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    if st.button("Save Changes", use_container_width=True):
        if new_name:
            with st.spinner("Saving changes..."):
                db.update_password_subtype(subtype_id, active_type_id, new_name)
                time.sleep(2.0)
            st.success("Sub-category updated successfully.")
            st.rerun()
        else:
            st.error("Please fill in all fields.")

# Modal: Delete Sub-Category Popup
@st.dialog("⚠️ Delete Sub-Category")
def show_delete_popup(subtype_id, name):
    st.write(f"Are you sure you want to permanently delete sub-category **{name}**? This will remove all associated credentials.")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", use_container_width=True):
            with st.spinner("Deleting sub-category..."):
                db.delete_password_subtype(subtype_id)
                time.sleep(2.0)
            st.success("Sub-category deleted successfully.")
            st.rerun()
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_manage_subtypes():
    st.title("🏷️ Manage Sub-Categories (Sub-types)")
    
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
        
        # Trigger Add Sub-category Modal
        if st.button("➕ Add New Sub-Category", use_container_width=True, type="primary"):
            show_add_subtype_popup(active_user_id, active_type_id, selected_type, selected_user)

        st.subheader(f"Active Sub-Categories under '{selected_type}'")
        sub_list = db.get_subtypes_by_type(active_type_id)
        if not sub_list:
            st.info("No sub-categories configured yet.")
        else:
            df_subtypes = pd.DataFrame(sub_list, columns=["Subtype ID", "Sub-Category Label"])
            st.dataframe(df_subtypes, use_container_width=True, hide_index=True)

            selected_sub = st.selectbox(
                "Select Sub-Category to Update/Delete", 
                sub_list, 
                format_func=lambda x: f"ID {x[0]} - {x[1]}"
            )
            
            col_up, col_del = st.columns(2)
            with col_up:
                if st.button("✏️ Edit Selected Sub-category", use_container_width=True):
                    show_edit_popup(selected_sub[0], active_type_id, selected_sub[1])
            with col_del:
                if st.button("🗑️ Delete Selected Sub-category", use_container_width=True):
                    show_delete_popup(selected_sub[0], selected_sub[1])

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
        
        # Form-level Pin verification
        pin_verify = st.text_input("Enter Master PIN to Authorize Encryption:", type=direct_input_type, key="direct_save_pin_verify_field")

        if st.button("Encrypt & Save Credentials to Vault", use_container_width=True):
            if title and acc_user and acc_pass and pin_verify:
                pin_val = db.get_master_pin()
                if pin_verify == pin_val:
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
                        # Encrypt and write cleanly to passwords table referencing the fresh IDs with loader
                        with st.spinner("Encrypting and saving credentials securely..."):
                            encrypted_val = enc.encrypt_password(acc_pass, pin_verify)
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
                    st.error("Incorrect PIN confirmation.")
            else:
                st.error("Platform title, account username, and password fields are required.")

    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="subtypes_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()