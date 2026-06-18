import streamlit as st
import pandas as pd
import io
import database as db
import encryption as enc

# Base Configuration
st.set_page_config(page_title="Password Manager", layout="centered")

# Ensure tables are built
try:
    db.init_db()
except Exception as e:
    st.error(f"PostgreSQL database connection failed: {e}")
    st.stop()

# Visual Styling Setup (Dashboard theme)
st.markdown("""
<style>
    .app-header {
        text-align: center;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .app-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #1e293b;
    }
    .section-label {
        font-size: 1.3rem;
        font-weight: 600;
        color: #475569;
        margin-top: 25px;
        margin-bottom: 12px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 4px;
    }
    div.stButton > button {
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 500;
        padding: 10px 16px;
    }
</style>
""", unsafe_allow_html=True)

# State Machine Management
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def navigate_to(page_name):
    st.session_state.page = page_name
    st.rerun()

def check_pin_access():
    if not st.session_state.authenticated:
        st.subheader("🔑 Access Security Verification")
        input_pin = st.text_input("Enter Master PIN to continue:", type="password")
        col_sub, col_back = st.columns(2)
        with col_sub:
            if st.button("Submit PIN", use_container_width=True):
                correct_pin = db.get_master_pin()
                if input_pin == correct_pin:
                    st.session_state.authenticated = True
                    st.session_state.current_pin = input_pin
                    st.success("Access Granted")
                    st.rerun()
                else:
                    st.error("Incorrect PIN entered.")
        with col_back:
            if st.button("Back to Menu", use_container_width=True):
                navigate_to('dashboard')
        return False
    return True

# --- VIEWS ---

# Screen: Dashboard Homepage
def render_dashboard():
    st.markdown("""
        <div class="app-header">
            <span style="font-size: 3.2rem;">🔒</span>
            <div class="app-title">Password Manager</div>
        </div>
    """, unsafe_allow_html=True)

    # View Passwords (Primary Action Button)
    if st.button("👁️ VIEW PASSWORD", use_container_width=True, type="primary"):
        navigate_to('view_passwords')

    # Master Tables Section
    st.markdown('<div class="section-label">Master</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👤 User", use_container_width=True):
            navigate_to('manage_users')
    with col2:
        if st.button("📁 Type", use_container_width=True):
            navigate_to('manage_types')
    with col3:
        if st.button("🏷️ Sub-Type", use_container_width=True):
            navigate_to('manage_subtypes')

    # General Configuration Actions
    st.markdown('<div class="section-label">General</div>', unsafe_allow_html=True)
    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button("🔑 Reset PIN", use_container_width=True):
            navigate_to('reset_pin')
    with col5:
        if st.button("📥 Export", use_container_width=True):
            navigate_to('export_passwords')
    with col6:
        if st.button("📤 Import", use_container_width=True):
            navigate_to('import_passwords')

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Bottom Utility Action
    if st.button("⚠️ CLEAR DATA", use_container_width=True):
        navigate_to('clear_data')


# Screen: Dynamic Unified Password Form & Multi-User Viewer
def render_view_passwords():
    st.title("🔑 Credentials Storage Engine")
    if not check_pin_access():
        return

    st.write("---")
    
    # ------------------ STABLE UNIFIED RECORD FORM ------------------
    st.subheader("📝 Save Password Profile")
    st.write("Fill in the fields below. You can select existing master records or dynamically define new ones in a single step.")

    # Retrieve current configurations
    users = db.get_users()
    ptypes = db.get_password_types()

    # Dropdown Options Lists
    user_options = [u[1] for u in users] + ["➕ [Create New User Profile]"]
    type_options = [t[1] for t in ptypes] + ["➕ [Create New Category Type]"]

    # Form Fields
    selected_user_opt = st.selectbox("Select User Profile", user_options)
    
    # If adding a user dynamically
    new_user_name = ""
    new_user_email = ""
    if selected_user_opt == "➕ [Create New User Profile]":
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            new_user_name = st.text_input("New Username (e.g. User A)")
        with col_u2:
            new_user_email = st.text_input("New User Email")

    # Category Type Selector
    selected_type_opt = st.selectbox("Select Category Type", type_options)
    
    # If adding a Type dynamically
    new_type_name = ""
    if selected_type_opt == "➕ [Create New Category Type]":
        new_type_name = st.text_input("New Category Type Name (e.g. Personal, Work)")

    # Dynamic Sub-Type selector depending on Type Option
    selected_subtype_opt = "None"
    new_subtype_name = ""
    
    if selected_type_opt != "➕ [Create New Category Type]":
        type_opts_dict = {t[1]: t[0] for t in ptypes}
        curr_type_id = type_opts_dict.get(selected_type_opt)
        
        if curr_type_id:
            sub_list = db.get_subtypes_by_type(curr_type_id)
            sub_options = ["None"] + [s[1] for s in sub_list] + ["➕ [Create New Sub-Category]"]
            selected_subtype_opt = st.selectbox("Select Sub-Category", sub_options)
            
            if selected_subtype_opt == "➕ [Create New Sub-Category]":
                new_subtype_name = st.text_input("New Sub-Category Name (e.g. Google, GitHub)")
    else:
        # If user is creating a new Category Type, they can enter a new Sub-Type directly too
        new_subtype_name = st.text_input("Optional New Sub-Category Name (under the new Type)")

    # Account Specific Details
    st.write("#### Platform Login Details")
    title = st.text_input("Account Platform Name (e.g. Gmail)")
    acc_user = st.text_input("Account Login ID (Username/Email)")
    acc_pass = st.text_input("Account Password (Plaintext)", type="password")

    # Single Submit Button executing transaction cleanly
    if st.button("🔒 Save Password Profile Securely", type="primary", use_container_width=True):
        if title and acc_user and acc_pass:
            # 1. Resolve User
            final_user_id = None
            if selected_user_opt == "➕ [Create New User Profile]":
                if new_user_name and new_user_email:
                    final_user_id = db.add_user(new_user_name.strip(), new_user_email.strip())
                else:
                    st.error("Please fill out both Username and Email for the new profile.")
                    st.stop()
            else:
                user_opts_dict = {u[1]: u[0] for u in users}
                final_user_id = user_opts_dict.get(selected_user_opt)

            # 2. Resolve Category Type
            final_type_id = None
            if selected_type_opt == "➕ [Create New Category Type]":
                if new_type_name:
                    final_type_id = db.add_password_type(new_type_name.strip())
                else:
                    st.error("Please specify a Name for the new Category Type.")
                    st.stop()
            else:
                type_opts_dict = {t[1]: t[0] for t in ptypes}
                final_type_id = type_opts_dict.get(selected_type_opt)

            # 3. Resolve Sub-Category (Subtype)
            final_subtype_id = None
            if final_type_id:
                if selected_subtype_opt == "➕ [Create New Sub-Category]" or (selected_type_opt == "➕ [Create New Category Type]" and new_subtype_name):
                    if new_subtype_name:
                        final_subtype_id = db.add_password_subtype(final_type_id, new_subtype_name.strip())
                elif selected_subtype_opt != "None":
                    sub_list = db.get_subtypes_by_type(final_type_id)
                    sub_opts_dict = {s[1]: s[0] for s in sub_list}
                    final_subtype_id = sub_opts_dict.get(selected_subtype_opt)

            # 4. Encrypt and save account credentials
            encrypted_val = enc.encrypt_password(acc_pass, st.session_state.current_pin)
            db.add_password(
                user_id=final_user_id,
                type_id=final_type_id,
                subtype_id=final_subtype_id,
                title=title.strip(),
                username_or_email=acc_user.strip(),
                encrypted_val=encrypted_val
            )
            st.success("Credentials stored successfully.")
            st.rerun()
        else:
            st.error("Please complete Platform Name, Login ID, and Password to save.")

    # ------------------ ISOLATED USER PROFILE VAULT VIEWER ------------------
    st.markdown("---")
    st.subheader("🔍 Filter Credentials View by User Profile")
    
    updated_users = db.get_users()
    if updated_users:
        view_user_opts = {u[1]: u[0] for u in updated_users}
        view_user_name = st.selectbox("Select User Vault Profile to Display Below", list(view_user_opts.keys()), key="vault_user_filter")
        view_user_id = view_user_opts[view_user_name]
        
        st.markdown(f"Displaying stored credentials belonging to: **{view_user_name}**")
        entries = db.get_passwords_by_user(view_user_id)
        
        if not entries:
            st.info(f"No password records stored for User: {view_user_name}")
        else:
            for ent in entries:
                ent_id, u_name, t_name, st_name, title, user_or_email, enc_pass, u_id, t_id, st_id = ent
                decrypted = enc.decrypt_password(enc_pass, st.session_state.current_pin)
                
                with st.container():
                    st.markdown(f"#### {title}")
                    st.text(f"Hierarchy Classification: {t_name or 'None'} -> {st_name or 'None'}")
                    st.text(f"Login Username/Email: {user_or_email}")
                    st.text(f"Decrypted Password: {decrypted}")
                    
                    # Update & Delete functionality for stored passwords
                    col_up, col_del = st.columns(2)
                    with col_up:
                        with st.expander("✏️ Edit Record"):
                            types_list = db.get_password_types()
                            edit_types_opts = {t[1]: t[0] for t in types_list}
                            type_index = list(edit_types_opts.values()).index(t_id) if t_id in edit_types_opts.values() else 0
                            
                            up_type_name = st.selectbox("Update Category Type", list(edit_types_opts.keys()), index=type_index, key=f"up_typ_{ent_id}")
                            new_type_id = edit_types_opts[up_type_name]
                            
                            up_sub_list = db.get_subtypes_by_type(new_type_id)
                            up_sub_id = None
                            if up_sub_list:
                                edit_sub_opts = {s[1]: s[0] for s in up_sub_list}
                                sub_index = list(edit_sub_opts.values()).index(st_id) + 1 if (st_id and st_id in edit_sub_opts.values()) else 0
                                up_sub_name = st.selectbox("Update Sub-Type", ["None"] + list(edit_sub_opts.keys()), index=sub_index, key=f"up_sub_{ent_id}")
                                if up_sub_name != "None":
                                    up_sub_id = edit_sub_opts[up_sub_name]
                            
                            new_title = st.text_input("Update Title", value=title, key=f"title_{ent_id}")
                            new_user_or_email = st.text_input("Update Username", value=user_or_email, key=f"login_{ent_id}")
                            new_raw_pass = st.text_input("Update Password", value=decrypted if not decrypted.startswith("[Decryption") else "", type="password", key=f"pass_{ent_id}")
                            
                            if st.button("Commit Changes", key=f"save_{ent_id}", use_container_width=True):
                                new_enc = enc.encrypt_password(new_raw_pass, st.session_state.current_pin)
                                db.update_password(
                                    pass_id=ent_id,
                                    user_id=view_user_id,
                                    type_id=new_type_id,
                                    subtype_id=up_sub_id,
                                    title=new_title,
                                    username_or_email=new_user_or_email,
                                    encrypted_val=new_enc
                                )
                                st.success("Record updated successfully.")
                                st.rerun()
                    with col_del:
                        if st.button("🗑️ Purge Record", key=f"del_{ent_id}", use_container_width=True):
                            db.delete_password(ent_id)
                            st.success("Record deleted successfully.")
                            st.rerun()
                st.markdown("---")
    else:
        st.info("No users registered in master database yet.")

    if st.button("⬅️ Back to Dashboard", key="v_back", use_container_width=True):
        st.session_state.authenticated = False
        navigate_to('dashboard')


# Screen: Manage Users (Add, Update, Delete)
def render_manage_users():
    st.title("👤 Manage Users")
    
    with st.form("Add User Form"):
        st.subheader("Create New User")
        username = st.text_input("Username")
        email = st.text_input("Email")
        if st.form_submit_button("Save User"):
            if username and email:
                try:
                    db.add_user(username, email)
                    st.success(f"Added User: {username}")
                except Exception as e:
                    st.error(f"Error registering user: {e}")
            else:
                st.error("All user fields must be provided.")

    st.subheader("Manage Active Profiles")
    users = db.get_users()
    if not users:
        st.info("No active users present.")
    else:
        df_users = pd.DataFrame(users, columns=["User ID", "Username", "Email Address"])
        st.dataframe(df_users, use_container_width=True, hide_index=True)

        selected_user_id = st.selectbox("Select Profile to Modify", [u[0] for u in users], format_func=lambda x: f"ID: {x} - {[u[1] for u in users if u[0] == x][0]}")
        curr_u = [u for u in users if u[0] == selected_user_id][0]
        
        up_username = st.text_input("Change Username", value=curr_u[1])
        up_email = st.text_input("Change Email", value=curr_u[2])
        
        col_up, col_del = st.columns(2)
        with col_up:
            if st.button("Update Profile", use_container_width=True):
                db.update_user(selected_user_id, up_username, up_email)
                st.success("User updated.")
                st.rerun()
        with col_del:
            if st.button("Delete Profile", use_container_width=True):
                db.delete_user(selected_user_id)
                st.success("User purged.")
                st.rerun()

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Screen: Manage Types (Add, Update, Delete)
def render_manage_types():
    st.title("📁 Manage Categories (Types)")
    
    with st.form("Add Type Form"):
        st.subheader("Create New Category Type")
        name = st.text_input("Type Name (e.g., Enterprise, Personal)")
        if st.form_submit_button("Save Type"):
            if name:
                try:
                    db.add_password_type(name)
                    st.success(f"Category added: {name}")
                except Exception as e:
                    st.error(f"Failed to add: {e}")
            else:
                st.error("Please enter a category name.")

    st.subheader("Active Category Types")
    types = db.get_password_types()
    if not types:
        st.info("No types found.")
    else:
        df_types = pd.DataFrame(types, columns=["Type ID", "Category Label"])
        st.dataframe(df_types, use_container_width=True, hide_index=True)

        selected_type_id = st.selectbox("Select Type to Modify", [t[0] for t in types], format_func=lambda x: f"ID: {x} - {[t[1] for t in types if t[0] == x][0]}")
        curr_t = [t for t in types if t[0] == selected_type_id][0]
        
        up_name = st.text_input("Edit Category Label", value=curr_t[1])
        
        col_up, col_del = st.columns(2)
        with col_up:
            if st.button("Update Label", use_container_width=True):
                db.update_password_type(selected_type_id, up_name)
                st.success("Category updated.")
                st.rerun()
        with col_del:
            if st.button("Delete Label", use_container_width=True):
                db.delete_password_type(selected_type_id)
                st.success("Category purged.")
                st.rerun()

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Screen: Manage Sub-types (Add, Update, Delete)
def render_manage_subtypes():
    st.title("🏷️ Manage Sub-Categories (Sub-types)")
    
    types = db.get_password_types()
    if not types:
        st.warning("Please configure at least one active Category Type first.")
    else:
        type_opts = {t[1]: t[0] for t in types}
        
        with st.form("Add Subtype Form"):
            st.subheader("Create New Sub-Category")
            parent_type = st.selectbox("Select Parent Category", list(type_opts.keys()))
            sub_name = st.text_input("Sub-Category Label (e.g., Slack, GitHub)")
            if st.form_submit_button("Save Sub-Category"):
                if sub_name:
                    try:
                        db.add_password_subtype(type_opts[parent_type], sub_name)
                        st.success(f"Added {sub_name} to category {parent_type}")
                    except Exception as e:
                        st.error(f"Database error writing structure: {e}")
                else:
                    st.error("Please enter a sub-category label.")

    st.subheader("Active Sub-Category Hierarchies")
    subtypes = db.get_password_subtypes()
    if not subtypes:
        st.info("No sub-category relationships found.")
    else:
        df_subtypes = pd.DataFrame(subtypes, columns=["Subtype ID", "Type ID", "Parent Category", "Sub-Category Label"])
        st.dataframe(df_subtypes[["Subtype ID", "Parent Category", "Sub-Category Label"]], use_container_width=True, hide_index=True)

        selected_sub_id = st.selectbox("Select Sub-Category to Modify", [s[0] for s in subtypes], format_func=lambda x: f"ID: {x} - {[f'{s[2]} -> {s[3]}' for s in subtypes if s[0] == x][0]}")
        curr_st = [s for s in subtypes if s[0] == selected_sub_id][0]
        
        type_keys = list(type_opts.keys())
        type_index = type_keys.index(curr_st[2]) if curr_st[2] in type_keys else 0
        
        up_parent = st.selectbox("Change Parent Category", type_keys, index=type_index)
        up_subname = st.text_input("Change Sub-Category Name", value=curr_st[3])

        col_up, col_del = st.columns(2)
        with col_up:
            if st.button("Update Mapping", use_container_width=True):
                db.update_password_subtype(selected_sub_id, type_opts[up_parent], up_subname)
                st.success("Mapping updated.")
                st.rerun()
        with col_del:
            if st.button("Delete Mapping", use_container_width=True):
                db.delete_password_subtype(selected_sub_id)
                st.success("Mapping removed.")
                st.rerun()

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Screen: Reset PIN
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
            db.update_master_pin(new_pin_input)
            st.success("PIN changed successfully.")
            st.session_state.authenticated = False
            navigate_to('dashboard')

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Screen: Export Password
def render_export_passwords():
    st.title("📥 Export Credentials")
    if not check_pin_access():
        return

    st.info("Compiles and decrypts stored database passwords into a plain CSV file.")
    
    if st.button("Generate Export Document", use_container_width=True):
        entries = db.get_passwords()
        if not entries:
            st.warning("No records present to compile.")
        else:
            export_list = []
            for ent in entries:
                _, u_name, t_name, st_name, title, user_or_email, enc_pass, _, _, _ = ent
                decrypted = enc.decrypt_password(enc_pass, st.session_state.current_pin)
                
                export_list.append({
                    "Profile Username": u_name,
                    "Category Type": t_name or "",
                    "Subtype": st_name or "",
                    "Record Title": title,
                    "Account Username/Email": user_or_email,
                    "Decrypted Password": decrypted
                })
            
            df_export = pd.DataFrame(export_list)
            csv_buffer = io.StringIO()
            df_export.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="💾 Download CSV Export",
                data=csv_data,
                file_name="passwords_vault_export.csv",
                mime="text/csv",
                use_container_width=True
            )

    if st.button("⬅️ Back to Dashboard", key="exp_back", use_container_width=True):
        st.session_state.authenticated = False
        navigate_to('dashboard')


# Screen: Import Password
def render_import_passwords():
    st.title("📤 Import Credentials")
    if not check_pin_access():
        return

    st.write("Import external records via a structured CSV file.")
    st.caption("Standard Header Template: `Profile Username`, `Category Type`, `Subtype`, `Record Title`, `Account Username/Email`, `Decrypted Password`")

    uploaded_file = st.file_uploader("Upload CSV Source", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("Import Data Preview:", df.head())

            if st.button("Validate and Commit Imports", use_container_width=True):
                imported_records = 0
                for _, row in df.iterrows():
                    username_val = row.get("Profile Username")
                    cat_type = row.get("Category Type")
                    subtype_val = row.get("Subtype")
                    title = row.get("Record Title")
                    acc_user = row.get("Account Username/Email")
                    raw_pass = row.get("Decrypted Password")

                    if pd.isna(username_val) or pd.isna(title) or pd.isna(acc_user) or pd.isna(raw_pass):
                        continue

                    # Insert missing Users automatically
                    u_id = db.add_user(str(username_val).strip(), f"{str(username_val).strip().lower()}@example.com")

                    # Handle Category Type mapping
                    t_id = None
                    if not pd.isna(cat_type) and str(cat_type).strip() != "":
                        t_id = db.add_password_type(str(cat_type).strip())

                    # Handle Sub-Category mapping
                    st_id = None
                    if t_id and not pd.isna(subtype_val) and str(subtype_val).strip() != "":
                        st_id = db.add_password_subtype(t_id, str(subtype_val).strip())

                    # Encrypt the incoming password
                    enc_val = enc.encrypt_password(str(raw_pass).strip(), st.session_state.current_pin)
                    
                    db.add_password(
                        user_id=u_id,
                        type_id=t_id,
                        subtype_id=st_id,
                        title=str(title).strip(),
                        username_or_email=str(acc_user).strip(),
                        encrypted_val=enc_val
                    )
                    imported_records += 1
                
                st.success(f"Processing Complete: {imported_records} credentials loaded.")
        except Exception as e:
            st.error(f"Error compiling CSV payload: {e}")

    if st.button("⬅️ Back to Dashboard", key="imp_back", use_container_width=True):
        st.session_state.authenticated = False
        navigate_to('dashboard')


# Screen: Clear Data
def render_clear_data():
    st.title("⚠️ Wipe Database Store")
    st.warning("Warning: This destroys all configuration histories (Users, Types, Sub-types, Passwords).")
    
    confirmation = st.checkbox("I confirm that I want to completely delete all stored data.")
    if st.button("Execute Storage Purge", type="primary", use_container_width=True):
        if confirmation:
            try:
                db.clear_all_tables()
                st.success("Local storage purged successfully.")
                navigate_to('dashboard')
            except Exception as e:
                st.error(f"Failed clearing datasets: {e}")
        else:
            st.error("Please confirm your action first.")

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Page Routing Evaluation
if st.session_state.page == 'dashboard':
    render_dashboard()
elif st.session_state.page == 'view_passwords':
    render_view_passwords()
elif st.session_state.page == 'manage_users':
    render_manage_users()
elif st.session_state.page == 'manage_types':
    render_manage_types()
elif st.session_state.page == 'manage_subtypes':
    render_manage_subtypes()
elif st.session_state.page == 'reset_pin':
    render_reset_pin()
elif st.session_state.page == 'export_passwords':
    render_export_passwords()
elif st.session_state.page == 'import_passwords':
    render_import_passwords()
elif st.session_state.page == 'clear_data':
    render_clear_data()