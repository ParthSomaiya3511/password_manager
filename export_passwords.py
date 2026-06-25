import streamlit as st
import pandas as pd
import io
import database as db
import encryption as enc
import time

def render_export_passwords(check_pin_access):
    st.title("📥 Export Credentials")
    if not check_pin_access():
        return

    st.info("Compiles and decrypts stored database passwords into a downloadable CSV file.")
    
    # Initialize session state variables to track export compilation
    if 'export_ready' not in st.session_state:
        st.session_state.export_ready = False
    if 'csv_data' not in st.session_state:
        st.session_state.csv_data = None

    # Stage 1: Display the "Generate" button only if compilation hasn't occurred yet
    if not st.session_state.export_ready:
        if st.button("Generate Export Document", use_container_width=True, type="primary"):
            entries = db.get_passwords()
            if not entries:
                st.warning("No records present to compile.")
            else:
                # Triggers the custom centered circular loading screen
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
                    
                    # Store data in session state and update active view state
                    st.session_state.csv_data = csv_buffer.getvalue()
                    st.session_state.export_ready = True
                    time.sleep(2.0)
                st.success("Export document generated successfully!")
                st.rerun()
                
    # Stage 2: Hide the "Generate" button, show only the "Download" actions
    else:
        st.success("Your decrypted credentials export is ready for secure download.")
        st.download_button(
            label="💾 Download CSV Export",
            data=st.session_state.csv_data,
            file_name="passwords_vault_export.csv",
            mime="text/csv",
            use_container_width=True
        )
        
       

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Dashboard", key="exp_back", use_container_width=True):
        # Reset variables on return to dashboard
        st.session_state.export_ready = False
        st.session_state.csv_data = None
        st.session_state.page = 'dashboard'
        st.rerun()