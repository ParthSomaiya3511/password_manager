import streamlit as st
import database as db
import time

def render_edit_subtype():
    # Inject sharp rectangular form styling
    st.markdown("""
    <style>
        div[data-testid="stVerticalBlockBorder"] {
            border: 3px solid #000000 !important;
            border-radius: 0px !important;
            background-color: #ffffff !important;
            box-shadow: none !important;
            padding: 24px !important;
        }
        div.stButton > button {
            border-radius: 0px !important;
            border: 2px solid #000000 !important;
            font-weight: 700 !important;
            transition: all 0.1s ease-in-out !important;
        }
        div.stButton > button:hover {
            background-color: #000000 !important;
            color: #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("✏️ Edit Sub-Category")
    st.write("Modify the Sub-Category parameters below:")
    st.write("---")

    target_id = st.session_state.get('edit_subtype_id')
    if not target_id:
        st.warning("No sub-category selected for editing.")
        if st.button("⬅️ Return to Manage Sub-categories", use_container_width=True):
            st.session_state.page = 'manage_subtypes'
            st.rerun()
        return

    # Fetch subtypes statically to find the targeting record
    subtypes = db.get_password_subtypes()
    target_sub = [s for s in subtypes if s[0] == target_id]
    
    if target_sub:
        curr_s = target_sub[0]
        sid, uid, uname, tid, tname, sname = curr_s
        
        with st.container(border=True):
            st.markdown(f"""
                <div style="background-color: #f1f5f9; padding: 14px 20px; border-bottom: 3px solid #000000; margin: -24px -24px 20px -24px;">
                    <span style="font-weight: 700; font-size: 1.1rem; color: #000000;">📝 Editing Sub-Category ID: {sid}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Display Associated User Profile context (Read-Only)
            st.text_input("Associated User Profile", value=uname, disabled=True)
            
            # Fetch and dynamically select Category Types belonging to this user
            user_types = db.get_password_types_by_user(uid)
            if not user_types:
                st.error("No Parent Category Types configured for this User.")
                new_type_id = tid
            else:
                type_opts = {t[1]: t[0] for t in user_types}
                # Align default index to current parent category name
                default_idx = list(type_opts.keys()).index(tname) if tname in type_opts else 0
                
                selected_type_name = st.selectbox(
                    "Parent Category Type", 
                    options=list(type_opts.keys()), 
                    index=default_idx
                )
                new_type_id = type_opts[selected_type_name]
            
            # Mutable Sub-Category label name
            new_name = st.text_input("Sub-Category Name", value=sname, placeholder="Enter sub-category name...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Changes", use_container_width=True, type="primary"):
                    if new_name:
                        clean_name = new_name.strip()
                        
                        # 1. Duplicate Validation (excludes own sid)
                        subtype_exists = any(
                            s[1] == uid and s[3] == new_type_id and s[0] != sid and s[5].lower() == clean_name.lower()
                            for s in subtypes
                        )
                        
                        if subtype_exists:
                            st.error(f"Sub-category '{clean_name}' already exists under the selected parent category type.")
                        else:
                            try:
                                with st.spinner("Saving changes in database..."):
                                    # Update parameters in database safely
                                    db.update_password_subtype(sid, new_type_id, clean_name)
                                    time.sleep(2.0)
                                st.success("Sub-category updated successfully.")
                                st.session_state.page = 'manage_subtypes'
                                st.rerun()
                            except Exception as e:
                                st.error(f"Database write error: {e}")
                    else:
                        st.error("Sub-category name cannot be empty.")
            with col_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.page = 'manage_subtypes'
                    st.rerun()
    else:
        st.error("Selected sub-category profile not found.")
        if st.button("⬅️ Return to Manage Sub-categories", use_container_width=True):
            st.session_state.page = 'manage_subtypes'
            st.rerun()