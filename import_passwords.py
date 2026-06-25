import streamlit as st
import pandas as pd
import database as db
import encryption as enc
import time

def render_import_passwords(check_pin_access):
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

                        # Lookup or insert User dynamically to bypass stale state and ForeignKey constraints
                        user_name_clean = str(username_val).strip()
                        u_id = db.get_user_id_by_name(user_name_clean)
                        if not u_id:
                            u_id = db.add_user(user_name_clean, f"{user_name_clean.lower().replace(' ', '')}@example.com")

                        # Lookup or insert Category Type dynamically under active user scope
                        t_id = None
                        if not pd.isna(cat_type) and str(cat_type).strip() != "":
                            cat_type_clean = str(cat_type).strip()
                            t_id = db.get_type_id_by_name(u_id, cat_type_clean)
                            if not t_id:
                                t_id = db.add_password_type(u_id, cat_type_clean)

                        # Lookup or insert Sub-Category Type dynamically under active user and type scope
                        st_id = None
                        if t_id and not pd.isna(subtype_val) and str(subtype_val).strip() != "":
                            sub_type_clean = str(subtype_val).strip()
                            st_id = db.get_subtype_id_by_name(t_id, sub_type_clean)
                            if not st_id:
                                st_id = db.add_password_subtype(u_id, t_id, sub_type_clean)

                        # Encrypt and save credential cleanly
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
        st.session_state.page = 'dashboard'
        st.rerun()