import streamlit as st
import database as db
import time

def render_edit_type():
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

    st.title("✏️ Edit Category Type")
    st.write("Modify the Category Name and parameters below:")
    st.write("---")

    target_id = st.session_state.get('edit_type_id')
    if not target_id:
        st.warning("No category type selected for editing.")
        if st.button("⬅️ Return to Manage Categories", use_container_width=True):
            st.session_state.page = 'manage_types'
            st.rerun()
        return

    # Fetch types statically to locate matching element
    types = db.get_password_types()
    target_type = [t for t in types if t[0] == target_id]
    
    if target_type:
        curr_t = target_type[0]
        tid, uid, uname, tname = curr_t
        
        with st.container(border=True):
            st.markdown(f"""
                <div style="background-color: #f1f5f9; padding: 14px 20px; border-bottom: 3px solid #000000; margin: -24px -24px 20px -24px;">
                    <span style="font-weight: 700; font-size: 1.1rem; color: #000000;">📝 Editing Category ID: {tid}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Display Associated User Profile context (Read-Only)
            st.text_input("Associated User Profile", value=uname, disabled=True)
            
            # Mutable Category Type Name
            new_name = st.text_input("Category Type Name", value=tname, placeholder="Enter new category name...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Changes", use_container_width=True, type="primary"):
                    if new_name:
                        clean_name = new_name.strip()
                        
                        # 1. Duplicate Validation (excludes own tid)
                        type_exists = any(
                            t[1] == uid and t[0] != tid and t[3].lower() == clean_name.lower()
                            for t in types
                        )
                        
                        if type_exists:
                            st.error(f"Category '{clean_name}' already exists for user profile '{uname}'.")
                        else:
                            try:
                                with st.spinner("Saving changes in database..."):
                                    db.update_password_type(tid, clean_name)
                                    time.sleep(2.0)
                                st.success("Category updated successfully.")
                                st.session_state.page = 'manage_types'
                                st.rerun()
                            except Exception as e:
                                st.error(f"Database write error: {e}")
                    else:
                        st.error("Category name cannot be empty.")
            with col_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.page = 'manage_types'
                    st.rerun()
    else:
        st.error("Selected category type not found.")
        if st.button("⬅️ Return to Manage Categories", use_container_width=True):
            st.session_state.page = 'manage_types'
            st.rerun()