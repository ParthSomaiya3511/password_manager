import streamlit as st
import pandas as pd
import io
import database as db
import encryption as enc
import time

# Base Configuration
st.set_page_config(page_title="Password Manager", layout="centered")

# Optimize database startup by caching resources (eliminates the page-refresh blank screen)
@st.cache_resource(show_spinner=False)
def bootstrap_database():
    db.init_db()

# Run the cached boostrap with a clean inline visual loader
try:
    with st.spinner("Establishing secure connection to database..."):
        bootstrap_database()
except Exception as e:
    st.error(f"PostgreSQL database connection failed: {e}")
    st.stop()

# Visual Styling Setup
st.markdown("""
<style>
    /* Full-screen Centered Frosted Backdrop Spinner Overlay */
    div[data-testid="stSpinner"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        background-color: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        z-index: 999999 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Hide Streamlit's default bouncing ball loader */
    div[data-testid="stSpinner"] svg {
        display: none !important;
    }
    
    /* Borderless, Transparent Loader Container */
    div[data-testid="stSpinner"] > div {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 18px !important;
        font-weight: 500 !important;
        color: #0f172a !important;
        font-size: 1.15rem !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* Premium Minimalistic Circular Rotating Spinner */
    div[data-testid="stSpinner"] > div::before {
        content: "" !important;
        display: block !important;
        width: 64px !important;
        height: 64px !important;
        border: 4px solid rgba(59, 130, 246, 0.1) !important; /* Soft guiding base ring */
        border-top: 4px solid #3b82f6 !important;           /* Premium Blue rotating arc */
        border-radius: 50% !important;
        animation: spinner-rotate 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite !important;
    }
    
    @keyframes spinner-rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

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
    .cred-container {
        border: 1px solid #cbd5e1;
        background-color: #f8fafc;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# State Machine Management
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def navigate_to(page_name):
    # Triggers the dynamic full-screen spinner on click
    with st.spinner("Transitioning interface. Please wait..."):
        st.session_state.page = page_name
        time.sleep(2.0)  
        st.rerun()

def check_pin_access():
    """Renders dynamic first-run PIN setup and secure login gates."""
    # 1. Dynamic Setup Screen: If no Master PIN has ever been set in the database
    if not db.is_pin_configured():
        st.subheader("🛠️ Setup Your Custom Master PIN")
        st.write("No Master PIN has been configured. Please define a custom PIN to secure this application database.")
        
        show_setup_pin = st.checkbox("👁️ Show PIN Input Plaintext", value=False, key="show_setup_pin_toggle")
        setup_input_type = "default" if show_setup_pin else "password"
        
        new_pin = st.text_input("Enter New Master PIN:", type=setup_input_type, key="setup_new_pin")
        confirm_new_pin = st.text_input("Confirm New Master PIN:", type=setup_input_type, key="setup_confirm_pin")
        
        if st.button("Set Master PIN", use_container_width=True, type="primary"):
            if len(new_pin) < 4:
                st.error("PIN must be at least 4 characters long.")
            elif new_pin != confirm_new_pin:
                st.error("PIN confirmations do not match.")
            else:
                with st.spinner("Setting Master PIN in database..."):
                    db.set_initial_pin(new_pin)
                    time.sleep(2.0)
                st.success("Master PIN successfully set! Please log in now.")
                st.rerun()
        return False

    # 2. Dynamic Verification Login Screen (Driven strictly by the database set PIN value)
    if not st.session_state.authenticated:
        st.subheader("🔑 Access Security Verification")
        
        # Checking this box disables browser autocompletion popups
        show_pin = st.checkbox("👁️ Show PIN Input Plaintext (Prevents Autocomplete Overrides)", value=False, key="show_pin_toggle_gate")
        input_type = "default" if show_pin else "password"

        input_pin = st.text_input(
            "Enter Security Code:", 
            type=input_type, 
            key="login_pin_input_field"
        )
        
        col_sub, col_back = st.columns(2)
        with col_sub:
            if st.button("Submit PIN", use_container_width=True, key="submit_pin_btn_gate"):
                with st.spinner("Authenticating security code..."):
                    correct_pin = db.get_master_pin()
                    time.sleep(2.0)
                    if input_pin == correct_pin:
                        st.session_state.authenticated = True
                        st.session_state.current_pin = input_pin
                        st.session_state.pin_failed = False
                        st.success("Access Granted")
                        st.rerun()
                    else:
                        st.session_state.pin_failed = True
        with col_back:
            if st.button("Back to Menu", use_container_width=True, key="back_pin_btn_gate"):
                navigate_to('dashboard')
        
        # If the PIN fails, show an emergency recovery option to reset the database PIN back to '1234'
        if st.session_state.get("pin_failed", False):
            st.error("Incorrect PIN entered.")
            st.info("💡 Stuck? If you have forgotten your PIN, use the recovery button below to force-reset your database Master PIN back to '1234'.")
            if st.button("⚠️ Reset Database PIN to Default (1234)", use_container_width=True, key="emergency_pin_reset_button"):
                with st.spinner("Force resetting database PIN..."):
                    db.update_master_pin("1234")
                    st.session_state.pin_failed = False
                    time.sleep(2.0)
                st.success("The database Master PIN has been reset to '1234'. Enter '1234' to access.")
                st.rerun()
        return False
    return True


# Screen: Dashboard Homepage
def render_dashboard():
    st.markdown("""
        <div class="app-header">
            <span style="font-size: 3.2rem;">🔒</span>
            <div class="app-title">Password Manager</div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("👁️ VIEW PASSWORD", use_container_width=True, type="primary"):
        navigate_to('view_passwords')

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
    
    if st.button("⚠️ CLEAR DATA", use_container_width=True):
        navigate_to('clear_data')


# Screen: Isolated View Password Vault Directory
def render_view_passwords():
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
            for ent in entries:
                ent_id, u_name, t_name, st_name, title, user_or_email, enc_pass, u_id, t_id, st_id = ent
                decrypted = enc.decrypt_password(enc_pass, st.session_state.current_pin)
                
                # Containerized UI
                field_label = st_name if st_name else "Username / Email"
                st.markdown(f"""
                <div class="cred-container">
                    <h4>📂 {title}</h4>
                    <p style="margin: 4px 0;"><b>Classification</b>: {t_name or 'None'} &rarr; {st_name or 'None'}</p>
                    <p style="margin: 4px 0;"><b>{field_label}</b>: {user_or_email}</p>
                    <p style="margin: 4px 0;"><b>Decrypted Password</b>: <code style="color: #0284c7;">{decrypted}</code></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Delete option
                if st.button(f"🗑️ Delete Account Entry - {title}", key=f"del_dir_{ent_id}"):
                    with st.spinner("Deleting credential record..."):
                        db.delete_password(ent_id)
                        time.sleep(2.0)
                    st.success("Entry removed.")
                    st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)

    if st.button("⬅️ Back to Dashboard", key="v_back", use_container_width=True):
        navigate_to('dashboard')


# Screen: Manage Users (Add, Update, Delete & Show Stored Passwords in Container)
def render_manage_users():
    st.title("👤 Manage Users")
    
    # 1. Add User Form
    with st.form("Add User Form"):
        st.subheader("Add Profile")
        username = st.text_input("Username")
        email = st.text_input("Email")
        if st.form_submit_button("Save User"):
            if username and email:
                try:
                    with st.spinner("Registering user profile..."):
                        db.add_user(username, email)
                        time.sleep(2.0)
                    st.success(f"Added User: {username}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error registering user: {e}")
            else:
                st.error("All user fields must be provided.")

    st.subheader("Update / Delete User Profiles")
    users = db.get_users()
    if not users:
        st.info("No active users present.")
    else:
        # Selector for edits
        selected_user_id = st.selectbox("Select Profile to Modify", [u[0] for u in users], format_func=lambda x: f"ID: {x} - {[u[1] for u in users if u[0] == x][0]}")
        curr_u = [u for u in users if u[0] == selected_user_id][0]
        
        up_username = st.text_input("Change Username", value=curr_u[1])
        up_email = st.text_input("Change Email", value=curr_u[2])
        
        col_up, col_del = st.columns(2)
        with col_up:
            if st.button("Update Profile", use_container_width=True):
                with st.spinner("Updating profile details..."):
                    db.update_user(selected_user_id, up_username, up_email)
                    time.sleep(2.0)
                st.success("User updated.")
                st.rerun()
        with col_del:
            if st.button("Delete Profile", use_container_width=True):
                with st.spinner("Purging profile details..."):
                    db.delete_user(selected_user_id)
                    time.sleep(2.0)
                st.success("User purged.")
                st.rerun()

        # "Show all passwords in user profile with container" Wireframe Integration
        st.markdown("---")
        st.subheader(f"💼 Stored Credentials Vault for {curr_u[1]}")
        
        # Check security access before showing unencrypted data in this master panel
        unlock = st.checkbox("🔑 Unlock View Stored Credentials", key="unlock_master_user")
        if unlock:
            correct_pin = db.get_master_pin()
            
            show_pin_confirm = st.checkbox("👁️ Show Confirm PIN Input Plaintext", value=False, key="show_pin_toggle_confirm")
            confirm_input_type = "default" if show_pin_confirm else "password"

            pin_input = st.text_input("Confirm Master PIN to Decrypt", type=confirm_input_type, key="master_user_pin")
            
            if pin_input == correct_pin:
                entries = db.get_passwords_by_user(selected_user_id)
                if not entries:
                    st.info(f"No credentials saved for user profile: {curr_u[1]}")
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

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Screen: Manage Types (Show User with Dropdown and Select Password Type)
def render_manage_types():
    st.title("📁 Manage Categories (Types)")
    
    users = db.get_users()
    if not users:
        st.warning("Please configure at least one active User Profile first.")
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            navigate_to('dashboard')
        return

    # 1. "Show user with dropdown" Integration
    user_opts = {u[1]: u[0] for u in users}
    selected_user = st.selectbox("Select User Profile to Manage Types For", list(user_opts.keys()), key="type_user_scope")
    active_user_id = user_opts[selected_user]

    # 2. Select, create, update, or delete types scoped directly to the selected User
    with st.form("Add Type Form"):
        st.subheader(f"Create New Category Type under {selected_user}")
        name = st.text_input("Category Type Name (e.g. Enterprise, Personal)")
        if st.form_submit_button("Save Category Type"):
            if name:
                try:
                    with st.spinner("Saving Category Type..."):
                        db.add_password_type(active_user_id, name)
                        time.sleep(2.0)
                    st.success(f"Category added: {name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add: {e}")
            else:
                st.error("Please enter a category name.")

    st.subheader(f"Active Category Types belonging to: {selected_user}")
    types = db.get_password_types_by_user(active_user_id)
    if not types:
        st.info(f"No custom category types defined for {selected_user}.")
    else:
        df_types = pd.DataFrame(types, columns=["Type ID", "Category Label"])
        st.dataframe(df_types, use_container_width=True, hide_index=True)

        selected_type_id = st.selectbox("Select Type to Modify", [t[0] for t in types], format_func=lambda x: f"ID: {x} - {[t[1] for t in types if t[0] == x][0]}")
        curr_t = [t for t in types if t[0] == selected_type_id][0]
        
        up_name = st.text_input("Edit Category Label", value=curr_t[1])
        
        col_up, col_del = st.columns(2)
        with col_up:
            if st.button("Update Label", use_container_width=True):
                with st.spinner("Updating Category Type..."):
                    db.update_password_type(selected_type_id, up_name)
                    time.sleep(2.0)
                st.success("Category updated.")
                st.rerun()
        with col_del:
            if st.button("Delete Label", use_container_width=True):
                with st.spinner("Deleting Category Type..."):
                    db.delete_password_type(selected_type_id)
                    time.sleep(2.0)
                st.success("Category purged.")
                st.rerun()

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Screen: Manage Sub-types (Show user with dropdown, select type, sub-type, and save account password)
def render_manage_subtypes():
    st.title("🏷️ Manage Sub-Categories (Sub-types)")
    
    users = db.get_users()
    if not users:
        st.warning("Please configure at least one active User Profile first.")
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            navigate_to('dashboard')
        return

    # 1. "Show user with dropdown" Integration
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
        
        # CRUD for Sub-types scoped under Type
        with st.form("Add Subtype Form"):
            st.subheader(f"Add New Sub-Category under '{selected_type}' for '{selected_user}'")
            sub_name = st.text_input("Sub-Category Label (e.g. AWS, Steam)")
            if st.form_submit_button("Save Sub-Category"):
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

        st.subheader(f"Active Sub-Categories under '{selected_type}'")
        sub_list = db.get_subtypes_by_type(active_type_id)
        if not sub_list:
            st.info("No sub-categories configured yet.")
        else:
            df_subtypes = pd.DataFrame(sub_list, columns=["Subtype ID", "Sub-Category Label"])
            st.dataframe(df_subtypes, use_container_width=True, hide_index=True)

            selected_sub_id = st.selectbox("Select Sub-Category to Modify", [s[0] for s in sub_list], format_func=lambda x: f"ID: {x} - {[s[1] for s in sub_list if s[0] == x][0]}")
            curr_st = [s for s in sub_list if s[0] == selected_sub_id][0]
            
            up_subname = st.text_input("Change Sub-Category Name", value=curr_st[1])
            
            col_up, col_del = st.columns(2)
            with col_up:
                if st.button("Update Mapping", use_container_width=True):
                    with st.spinner("Updating Sub-Category..."):
                        db.update_password_subtype(selected_sub_id, active_type_id, up_subname)
                        time.sleep(2.0)
                    st.success("Mapping updated.")
                    st.rerun()
            with col_del:
                if st.button("Delete Mapping", use_container_width=True):
                    with st.spinner("Deleting Sub-Category..."):
                        db.delete_password_subtype(selected_sub_id)
                        time.sleep(2.0)
                    st.success("Mapping removed.")
                    st.rerun()

        # 2. "and save any account password" Direct Panel Wireframe Integration
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
        
        # 3. Form-level Pin verification
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

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Screen: Reset PIN (set Reset PIN of app)
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
            st.session_state.authenticated = False
            st.success("PIN changed successfully.")
            navigate_to('dashboard')

    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')


# Screen: Export Password (click this button and save all password with file download)
def render_export_passwords():
    st.title("📥 Export Credentials")
    if not check_pin_access():
        return

    st.info("Compiles and decrypts stored database passwords into a downloadable CSV file.")
    
    if st.button("Generate Export Document", use_container_width=True):
        entries = db.get_passwords()
        if not entries:
            st.warning("No records present to compile.")
        else:
            with st.spinner("Compiling and decrypting your credentials vault..."):
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
                time.sleep(2.0)

            st.download_button(
                label="💾 Download CSV Export",
                data=csv_data,
                file_name="passwords_vault_export.csv",
                mime="text/csv",
                use_container_width=True
            )

    if st.button("⬅️ Back to Dashboard", key="exp_back", use_container_width=True):
        # Preservation change: st.session_state.authenticated = False is removed
        navigate_to('dashboard')


# Screen: Import Password (click this button and save all password file save in this app)
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
                with st.spinner("Parsing and importing credentials..."):
                    for _, row in df.iterrows():
                        username_val = row.get("Profile Username")
                        cat_type = row.get("Category Type")
                        subtype_val = row.get("Subtype")
                        title = row.get("Record Title")
                        acc_user = row.get("Account Username/Email")
                        raw_pass = row.get("Decrypted Password")

                        if pd.isna(username_val) or pd.isna(title) or pd.isna(acc_user) or pd.isna(raw_pass):
                            continue

                        u_id = db.add_user(str(username_val).strip(), f"{str(username_val).strip().lower()}@example.com")

                        t_id = None
                        if not pd.isna(cat_type) and str(cat_type).strip() != "":
                            t_id = db.add_password_type(u_id, str(cat_type).strip())

                        st_id = None
                        if t_id and not pd.isna(subtype_val) and str(subtype_val).strip() != "":
                            st_id = db.add_password_subtype(u_id, t_id, str(subtype_val).strip())

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
                    time.sleep(2.0)
                st.success(f"Processing Complete: {imported_records} credentials loaded.")
        except Exception as e:
            st.error(f"Error compiling CSV payload: {e}")

    if st.button("⬅️ Back to Dashboard", key="imp_back", use_container_width=True):
        # Preservation change: st.session_state.authenticated = False is removed
        navigate_to('dashboard')


# Screen: Clear Data (clear data)
def render_clear_data():
    st.title("⚠️ Wipe Database Store")
    st.warning("Warning: This destroys all configuration histories (Users, Types, Sub-types, Passwords).")
    
    confirmation = st.checkbox("I confirm that I want to completely delete all stored data.")
    if st.button("Execute Storage Purge", type="primary", use_container_width=True):
        if confirmation:
            try:
                with st.spinner("Wiping local database store..."):
                    db.clear_all_tables()
                    time.sleep(2.0)
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