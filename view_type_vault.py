import streamlit as st
import database as db
import encryption as enc
import time

def render_view_type_vault():
    target_user_id = st.session_state.get('view_user_id')
    target_user_name = st.session_state.get('view_user_name')
    target_type_id = st.session_state.get('view_type_id')
    target_type_name = st.session_state.get('view_type_name')
    
    if not target_user_id or not target_type_id:
        st.warning("No category context selected.")
        if st.button("⬅️ Return to Manage Categories", use_container_width=True):
            st.session_state.page = 'manage_types'
            st.rerun()
        return

    st.title(f"💼 Vault: {target_type_name} ({target_user_name})")
    st.write("---")

    # Uses the verified session current_pin directly to decrypt (removes redundant input fields)
    entries = db.get_passwords_by_type(target_user_id, target_type_id)
    if not entries:
        st.info(f"No credentials saved under category **{target_type_name}** for {target_user_name}")
    else:
        # Render decrypted passwords in groups of 3 columns (side-by-side)
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
                        st.markdown(f"#### 📂 {title}")
                        st.write(f"**Sub-Category**: {st_name or 'None'}")
                        st.write(f"**{field_label}**: {user_or_email}")
                        st.write(f"**Decrypted Password**:")
                        st.code(decrypted, language="text")
                        
                        # Row level inline delete
                        if st.button("🗑️ Delete", key=f"del_v_t_ent_{ent_id}", use_container_width=True):
                            with st.spinner("Deleting record..."):
                                db.delete_password(ent_id)
                                time.sleep(1.0)
                            st.success("Record deleted.")
                            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Return to Manage Categories", use_container_width=True, key="return_types_vault"):
        st.session_state.page = 'manage_types'
        st.rerun()