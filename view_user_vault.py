import streamlit as st
import database as db
import encryption as enc
import time

def render_view_user_vault():
    # Targeted CSS to force sharp corners and alignment on all elements in this view
    st.markdown("""
    <style>
        /* Force outer container to have sharp rectangular corners and 3px black borders */
        div[data-testid="stVerticalBlockBorder"] {
            border: 3px solid #000000 !important;
            border-radius: 0px !important;
            background-color: #ffffff !important;
            box-shadow: none !important;
            padding: 20px !important;
            overflow: hidden !important; /* Clips inner header band perfectly to the card's sharp edges */
        }

        /* Remove potential inner container rounding in newer Streamlit versions */
        div[data-testid="stVerticalBlockBorder"] > div {
            border-radius: 0px !important;
        }

        /* Header Band Styling matching the sharp rectangle container layout */
        .card-header-band {
            padding: 14px 20px;
            border-bottom: 3px solid #000000;
            background-color: #f1f5f9;
            /* Extends negative margins to touch the outer border lines perfectly */
            margin: -20px -20px 16px -20px; 
            width: calc(100% + 40px);
        }
        
        .card-title-text {
            font-size: 13px;
            font-weight: 700;
            color: #000000;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .card-field-group {
            margin-bottom: 12px;
        }
        
        .card-field-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            font-weight: 700;
            margin-bottom: 2px;
        }
        
        .card-field-value {
            font-size: 0.95rem;
            font-weight: 600;
            color: #000000;
            word-break: break-all;
        }
        
        .card-field-value-mono {
            font-family: monospace;
            font-size: 0.95rem;
            font-weight: 600;
            color: #0f172a;
            word-break: break-all;
        }

        /* Force Code Block wrapper elements to lose rounded corners and use solid borders */
        div[data-testid="stVerticalBlockBorder"] div[data-testid="stCodeBlock"],
        div[data-testid="stVerticalBlockBorder"] div[data-testid="stCodeBlock"] pre,
        div[data-testid="stVerticalBlockBorder"] div[data-testid="stCodeBlock"] code {
            border: 2px solid #000000 !important;
            border-radius: 0px !important;
            background-color: #f8fafc !important;
            box-shadow: none !important;
        }

        /* Button design: Sharp corners and high contrast borders */
        div[data-testid="stVerticalBlockBorder"] button {
            border: 2px solid #000000 !important;
            border-radius: 0px !important;
            background-color: #ffffff !important;
            color: #000000 !important;
            font-weight: 700 !important;
            box-shadow: none !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            transition: all 0.1s ease-in-out !important;
        }

        div[data-testid="stVerticalBlockBorder"] button:hover {
            background-color: #000000 !important;
            color: #ffffff !important;
            border-color: #000000 !important;
        }
        .st-emotion-cache-1ne20ew {
            display: flex;
            gap: 1rem;
            width: 150%;
            height: auto;
            flex-flow: column;
            flex: 1 1 0%;
            -webkit-box-align: start;
            align-items: start;
            -webkit-box-pack: start;
            justify-content: start;
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 0.5rem;
            padding: calc(-1px + 1rem);
            overflow: visible;
        }
       
    </style>
    """, unsafe_allow_html=True)

    target_user_id = st.session_state.get('view_user_id')
    target_user_name = st.session_state.get('view_user_name')
    
    if not target_user_id:
        st.warning("No user profile selected.")
        if st.button("⬅️ Return to Manage Users", use_container_width=True):
            st.session_state.page = 'manage_users'
            st.rerun()
        return

    st.title(f"💼 Decrypted Vault for {target_user_name}")
    st.write("---")

    # Uses the verified session current_pin directly to decrypt
    entries = db.get_passwords_by_user(target_user_id)
    if not entries:
        st.info(f"No credentials saved for user profile: {target_user_name}")
    else:
        st.write("### Stored Passwords")
        
        # Divide entries into rows of 3 columns
        for i in range(0, len(entries), 3):
            row_entries = entries[i:i+3]
            cols = st.columns(3)
            
            for idx, ent in enumerate(row_entries):
                ent_id, u_name, t_name, st_name, title, user_or_email, enc_pass, _, _, _ = ent
                decrypted = enc.decrypt_password(enc_pass, st.session_state.current_pin)
                
                field_label = st_name if st_name else "Username / Email"
                
                with cols[idx]:
                    with st.container(border=True):
                        # Structured top header band spanning edge-to-edge
                        st.markdown(f"""
                            <div class="card-header-band">
                                <div class="card-title-text">
                                    <span>📂</span> {title}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Hierarchy details
                        st.markdown(f"""
                            <div class="card-field-group">
                                <div class="card-field-label">Hierarchy</div>
                                <div class="card-field-value">{t_name or 'None'} &rarr; {st_name or 'None'}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Credential Username / Email
                        st.markdown(f"""
                            <div class="card-field-group">
                                <div class="card-field-label">{field_label}</div>
                                <div class="card-field-value-mono">{user_or_email}</div>
                            </div>
                            <div class="card-field-label" style="margin-bottom: 4px;">Decrypted Password</div>
                        """, unsafe_allow_html=True)
                        
                        # Decrypted Password output code block
                        st.code(decrypted, language="text")
                        
                        # Row Level Delete Action
                        if st.button("🗑️ Delete", key=f"del_v_ent_{ent_id}", use_container_width=True):
                            with st.spinner("Deleting record..."):
                                db.delete_password(ent_id)
                                time.sleep(1.0)
                            st.success("Record deleted.")
                            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Return to Manage Users", use_container_width=True, key="return_users_vault"):
        st.session_state.page = 'manage_users'
        st.rerun()