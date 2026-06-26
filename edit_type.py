import streamlit as st
import database as db
import time

def render_edit_type():
    st.title("✏️ Edit Category Type")
    st.write("Modify the Category Name below:")
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
        new_name = st.text_input("Category Type Name", value=curr_t[3])
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("Save Changes", use_container_width=True, type="primary"):
                if new_name:
                    with st.spinner("Saving changes in database..."):
                        db.update_password_type(curr_t[0], new_name.strip())
                        time.sleep(2.0)
                    st.success("Category updated successfully.")
                    st.session_state.page = 'manage_types'
                    st.rerun()
                else:
                    st.error("Please fill in all fields.")
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.page = 'manage_types'
                st.rerun()
    else:
        st.error("Selected category type not found.")
        if st.button("⬅️ Return to Manage Categories", use_container_width=True):
            st.session_state.page = 'manage_types'
            st.rerun()