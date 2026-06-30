import streamlit as st
import database as db

def render_view_subtype_vault():
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

    target_subtype_id = st.session_state.get('view_subtype_id')
    
    if not target_subtype_id:
        st.warning("No sub-category profile selected.")
        if st.button("⬅️ Return to Sub-Category Directory", use_container_width=True):
            st.session_state.page = 'manage_subtypes'
            st.rerun()
        return

    sub_list = db.get_password_subtypes()
    target_sub = next((s for s in sub_list if s[0] == target_subtype_id), None)
    
    if not target_sub:
        st.error("Sub-category record not found.")
        if st.button("⬅️ Return to Sub-Category Directory", use_container_width=True):
            st.session_state.page = 'manage_subtypes'
            st.rerun()
        return

    sid, uid, uname, tid, tname, sname = target_sub

    st.subheader("🏷️ Sub-Category Record Details")
    
    with st.container(border=True):
        st.markdown(f"""
            <div class="record-header-band">
                <div style="font-weight: 700; font-size: 1.15rem; color: #000000;">🏷️ Sub-Category ID: {sid}</div>
            </div>
            
            <div class="record-field-group">
                <div class="record-field-label">User Profile</div>
                <div class="record-field-value">{uname}</div>
            </div>
            
            <div class="record-field-group">
                <div class="record-field-label">Parent Category</div>
                <div class="record-field-value">{tname}</div>
            </div>
            
            <div class="record-field-group">
                <div class="record-field-label">Sub-Category Label</div>
                <div class="record-field-value">{sname}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("⬅️ Return to Sub-Category Directory", use_container_width=True):
            st.session_state.page = 'manage_subtypes'
            st.rerun()