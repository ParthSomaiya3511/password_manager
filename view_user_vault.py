import streamlit as st
import database as db
import encryption as enc
import time

def render_view_user_vault():
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

    # Uses the verified session current_pin directly to decrypt (removes redundant input fields)
    entries = db.get_passwords_by_user(target_user_id)
    if not entries:
        st.info(f"No credentials saved for user profile: {target_user_name}")
    else:
        st.write("### Stored Passwords")
        
        # Divide entries into rows of 3 columns (side-by-side)
        for i in range(0, len(entries), 3):
            row_entries = entries[i:i+3]
            cols = st.columns(3)
            
            for idx, ent in enumerate(row_entries):
                ent_id, u_name, t_name, st_name, title, user_or_email, enc_pass, _, _, _ = ent
                decrypted = enc.decrypt_password(enc_pass, st.session_state.current_pin)
                
                field_label = st_name if st_name else "Username / Email"
                
                with cols[idx]:
                    # st.container(border=True) is styled globally in app.py to match your sketch card design perfectly
                    with st.container(border=True):
                        st.markdown(f"#### 📂 {title}")
                        st.write(f"**Hierarchy**: {t_name or 'None'} &rarr; {st_name or 'None'}")
                        st.write(f"**{field_label}**: {user_or_email}")
                        st.write(f"**Decrypted Password**:")
                        st.code(decrypted, language="text")
                        
                        # Row level inline delete
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