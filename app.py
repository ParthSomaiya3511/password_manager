import streamlit as st
import pandas as pd
import io
import time
import sys
import importlib

# import connection and modules
import database as db
import encryption as enc

# ૧. ઓટોમેટીક મોડ્યુલ રીલોડર - રન ટાઇમ ચેન્જીસ અપ્લાય કરવા માટે
for module_name in ['database', 'encryption', 'manage_users', 'manage_types', 'manage_subtypes', 'view_passwords', 'reset_pin', 'export_passwords', 'import_passwords', 'clear_data']:
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])

# Import multi-page files cleanly
import view_passwords
import manage_users
import manage_types as type_page
import manage_subtypes
import reset_pin
import export_passwords
import import_passwords
import clear_data

# Base Page Configuration
st.set_page_config(page_title="Password Manager", layout="centered")

# Optimize database startup by caching resources
@st.cache_resource(show_spinner=False)
def bootstrap_database():
    db.init_db()

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
        z-index: 9999999 !important; /* Sits over normal page contents */
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Dialog/Popup-Specific Spinner Override (Forces exact center lock inside st.dialog) */
    div[data-testid="stDialog"] div[data-testid="stSpinner"] {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 16px !important; /* Matches Streamlit popup card corners */
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        z-index: 99999999 !important; /* Sits directly over active popup contents */
    }
    
    /* Dialog/Popup Spacing Correction */
    div[data-testid="stDialog"] {
        padding: 24px !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15) !important;
    }
    div[data-testid="stDialog"] .stTextInput {
        margin-bottom: 14px !important;
    }
    div[data-testid="stDialog"] div[data-testid="stBlock"] {
        gap: 1.2rem !important;
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
    
    /* Sibling selector rule to prevent duplicate stacking of spinners */
    div[data-testid="stSpinner"] div[data-testid="stSpinner"],
    div[data-testid="stSpinner"] ~ div[data-testid="stSpinner"] {
        display: none !important;
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

# State Machine Management & Startup Loader Sequence
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

# First run: displays the dynamic viewport loader for 2.5 seconds
if not st.session_state.initialized:
    with st.spinner("Initializing cryptographic container..."):
        time.sleep(2.5)  
        st.session_state.initialized = True
        st.rerun()

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
    # 1. Setup Screen: If no Master PIN has ever been set in the database
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

    # 2. Verification Login Screen (Driven strictly by the database set PIN value)
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


# Page Routing Evaluation
if st.session_state.page == 'dashboard':
    render_dashboard()
elif st.session_state.page == 'view_passwords':
    view_passwords.render_view_passwords(check_pin_access)
elif st.session_state.page == 'manage_users':
    manage_users.render_manage_users()
elif st.session_state.page == 'manage_types':
    type_page.render_manage_types()
elif st.session_state.page == 'manage_subtypes':
    manage_subtypes.render_manage_subtypes(check_pin_access)
elif st.session_state.page == 'reset_pin':
    reset_pin.render_reset_pin()
elif st.session_state.page == 'export_passwords':
    export_passwords.render_export_passwords(check_pin_access)
elif st.session_state.page == 'import_passwords':
    import_passwords.render_import_passwords(check_pin_access)
elif st.session_state.page == 'clear_data':
    clear_data.render_clear_data()