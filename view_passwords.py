import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

# Modal: Edit Password popup
@st.dialog("✏️ Edit Credentials")
def show_edit_popup(ent_id, current_title, current_email, decrypted_password, view_user_id, t_id, st_id):
    st.write("Modify the record parameters below:")
    
    # Category dropdown context
    user_ptypes = db.get_password_types_by_user(view_user_id)
    edit_types_opts = {t[1]: t[0] for t in user_ptypes}
    
    type_index = list(edit_types_opts.values()).index(t_id) if t_id in edit_types_opts.values() else 0
    up_type_name = st.selectbox("Category Type", list(edit_types_opts.keys()), index=type_index)
    new_type_id = edit_types_opts[up_type_name]
    
    # Sub-category dropdown context
    up_sub_list = db.get_subtypes_by_type(new_type_id)
    up_sub_id = None
    if up_sub_list:
        edit_sub_opts = {s[1]: s[0] for s in up_sub_list}
        sub_index = list(edit_sub_opts.values()).index(st_id) + 1 if (st_id and st_id in edit_sub_opts.values()) else 0
        up_sub_name = st.selectbox("Sub-Type", ["None"] + list(edit_sub_opts.keys()), index=sub_index)
        if up_sub_name != "None":
            up_sub_id = edit_sub_opts[up_sub_name]

    new_title = st.text_input("Title", value=current_title)
    new_email = st.text_input("Username/Email", value=current_email)
    new_pass = st.text_input("Password (Plaintext)", value=decrypted_password, type="password")
    
    if st.button("Save Changes", use_container_width=True):
        if new_title and new_email and new_pass:
            with st.spinner("Saving changes..."):
                new_enc = enc.encrypt_password(new_pass, st.session_state.current_pin)
                db.update_password(ent_id, view_user_id, new_type_id, up_sub_id, new_title, new_email, new_enc)
                time.sleep(2.0)
            st.success("Record updated successfully.")
            st.rerun()
        else:
            st.error("Please fill in all fields.")

# Modal: Delete Password popup
@st.dialog("⚠️ Delete Record")
def show_delete_popup(ent_id, title):
    st.write(f"Are you sure you want to permanently delete **{title}**?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", use_container_width=True):
            with st.spinner("Deleting record..."):
                db.delete_password(ent_id)
                time.sleep(2.0)
            st.success("Record deleted successfully.")
            st.rerun()
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_view_passwords(check_pin_access):
    st.title("🔑 Stored Credentials Directory")
    if not check_pin_access():
        return

    st.write("---")
    
    users = db.get_users()
    if not users:
        st.warning("Please configure at least one active User Profile first.")
    else:
        view_user_opts = {u[1]: u[0] for u in users}
        view_user_name = st.selectbox("Select User Profile context to view decrypted accounts", list(view_user_opts.keys()))
        view_user_id = view_user_opts[view_user_name]
        
        st.markdown(f"### Vault Directory for **{view_user_name}**")
        entries = db.get_passwords_by_user(view_user_id)
        
        if not entries:
            st.info(f"No password entries recorded for user profile: {view_user_name}")
        else:
            # Build database table pattern
            table_rows = []
            for ent in entries:
                ent_id, u_name, t_name, st_name, title, user_or_email, enc_pass, u_id, t_id, st_id = ent
                decrypted = enc.decrypt_password(enc_pass, st.session_state.current_pin)
                table_rows.append({
                    "id": ent_id,
                    "Title": title,
                    "Category": t_name or "None",
                    "Sub-Category": st_name or "None",
                    "Username/Email": user_or_email,
                    "Password": decrypted,
                    "type_id": t_id,
                    "subtype_id": st_id
                })
            
            df_entries = pd.DataFrame(table_rows)
            st.dataframe(df_entries[["Title", "Category", "Sub-Category", "Username/Email", "Password"]], use_container_width=True)

            # Interactive CRUD Selection Panel
            st.write("#### Select Row to Edit / Delete")
            selected_row = st.selectbox(
                "Choose Record", 
                table_rows, 
                format_func=lambda x: f"{x['Title']} ({x['Username/Email']})"
            )
            
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("✏️ Edit Selected", use_container_width=True):
                    show_edit_popup(
                        selected_row["id"], selected_row["Title"], 
                        selected_row["Username/Email"], selected_row["Password"],
                        view_user_id, selected_row["type_id"], selected_row["subtype_id"]
                    )
            with col_del:
                if st.button("🗑️ Delete Selected", use_container_width=True):
                    show_delete_popup(selected_row["id"], selected_row["Title"])

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Dashboard", key="v_back", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()