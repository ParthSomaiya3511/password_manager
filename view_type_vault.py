import streamlit as st
import database as db

def render_view_type_vault():
    st.markdown("""
    <style>
        /* Force outer container to have solid sharp rectangular styling */
        div[data-testid="stVerticalBlockBorder"] {
            border: 3px solid #000000 !important;
            border-radius: 0px !important;
            background-color: #ffffff !important;
            box-shadow: none !important;
            overflow: hidden !important;
            padding: 20px !important;
        }
        
        .record-header-band {
            padding: 14px 20px;
            border-bottom: 3px solid #000000;
            background-color: #f1f5f9;
            margin: -20px -20px 16px -20px;
            width: calc(100% + 40px);
        }
        
        .record-field-group {
            margin-bottom: 16px;
        }
        
        .record-field-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            font-weight: 700;
            margin-bottom: 2px;
        }
        
        .record-field-value {
            font-size: 1.05rem;
            font-weight: 600;
            color: #000000;
        }
        
        /* Directory Back Button */
        div[data-testid="stVerticalBlockBorder"] button {
            border: 2px solid #000000 !important;
            border-radius: 0px !important;
            font-weight: 700 !important;
            background-color: #ffffff !important;
            color: #000000 !important;
            box-shadow: none !important;
            transition: all 0.1s ease-in-out !important;
        }
        
        div[data-testid="stVerticalBlockBorder"] button:hover {
            background-color: #000000 !important;
            color: #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)

    target_type_id = st.session_state.get('view_type_id')
    
    if not target_type_id:
        st.warning("No category profile selected.")
        if st.button("⬅️ Return to Category Directory", use_container_width=True):
            st.session_state.page = 'manage_types'
            st.rerun()
        return

    types = db.get_password_types()
    target_type = next((t for t in types if t[0] == target_type_id), None)
    
    if not target_type:
        st.error("Category record not found.")
        if st.button("⬅️ Return to Category Directory", use_container_width=True):
            st.session_state.page = 'manage_types'
            st.rerun()
        return

    tid, uid, uname, tname = target_type

    st.subheader("📁 Category Record Details")
    
    with st.container(border=True):
        st.markdown(f"""
            <div class="record-header-band">
                <div style="font-weight: 700; font-size: 1.15rem; color: #000000;">📂 Category ID: {tid}</div>
            </div>
            
            <div class="record-field-group">
                <div class="record-field-label">User Profile</div>
                <div class="record-field-value">{uname}</div>
            </div>
            
            <div class="record-field-group">
                <div class="record-field-label">Type ID</div>
                <div class="record-field-value" style="font-family: monospace;">{tid}</div>
            </div>
            
            <div class="record-field-group">
                <div class="record-field-label">Category Label</div>
                <div class="record-field-value">{tname}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("⬅️ Return to Category Directory", use_container_width=True):
            st.session_state.page = 'manage_types'
            st.rerun()