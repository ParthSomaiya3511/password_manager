import streamlit as st
import database as db
import time

def render_edit_subtype():
    st.title("✏️ Edit Sub-Category")
    st.write("Modify the Sub-Category parameter below:")
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
        new_name = st.text_input("Sub-Category Name", value=curr_s[5])
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("Save Changes", use_container_width=True, type="primary"):
                if new_name:
                    with st.spinner("Saving changes in database..."):
                        db.update_password_subtype(curr_s[0], curr_s[3], new_name.strip())
                        time.sleep(2.0)
                    st.success("Sub-category updated successfully.")
                    st.session_state.page = 'manage_subtypes'
                    st.rerun()
                else:
                    st.error("Please fill in all fields.")
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.page = 'manage_subtypes'
                st.rerun()
    else:
        st.error("Selected sub-category profile not found.")
        if st.button("⬅️ Return to Manage Sub-categories", use_container_width=True):
            st.session_state.page = 'manage_subtypes'
            st.rerun()