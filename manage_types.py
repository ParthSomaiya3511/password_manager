import streamlit as st
import pandas as pd
import database as db
import time

# Modal: Add Category Popup
@st.dialog("➕ Add Category Type")
def show_add_type_popup(active_user_id, selected_user):
    st.write(f"Add a new category type under user context: **{selected_user}**")
    name = st.text_input("Category Type Name (e.g. Enterprise, Personal)")
    if st.button("Save Category", use_container_width=True):
        if name:
            try:
                with st.spinner("Saving Category Type..."):
                    db.add_password_type(active_user_id, name)
                    time.sleep(2.0)
                st.success(f"Category added: {name}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add: {e}")
        else:
            st.error("Please enter a category name.")

# Modal: Edit Category Popup
@st.dialog("✏️ Edit Category Type")
def show_edit_popup(type_id, current_name):
    st.markdown("#### Modify the Category parameters below:")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    new_name = st.text_input("Category Type Name", value=current_name)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    if st.button("Save Changes", use_container_width=True):
        if new_name:
            with st.spinner("Saving changes..."):
                db.update_password_type(type_id, new_name)
                time.sleep(2.0)
            st.success("Category updated successfully.")
            st.rerun()
        else:
            st.error("Please fill in all fields.")

# Modal: Delete Category Popup
@st.dialog("⚠️ Delete Category Type")
def show_delete_popup(type_id, name):
    st.write(f"Are you sure you want to permanently delete category **{name}**? This will remove all associated sub-types and credentials.")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", use_container_width=True):
            with st.spinner("Deleting category..."):
                db.delete_password_type(type_id)
                time.sleep(2.0)
            st.success("Category deleted successfully.")
            st.rerun()
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_manage_types():
    st.title("📁 Manage Categories (Types)")
    
    users = db.get_users()
    if not users:
        st.warning("Please configure at least one active User Profile first.")
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="types_no_users_back"):
            st.session_state.page = 'dashboard'
            st.rerun()
        return

    # "Show user with dropdown" Integration
    user_opts = {u[1]: u[0] for u in users}
    selected_user = st.selectbox("Select User Profile to Manage Types For", list(user_opts.keys()), key="type_user_scope")
    active_user_id = user_opts[selected_user]

    # Trigger Add Category Modal
    if st.button("➕ Add New Category Type", use_container_width=True, type="primary"):
        show_add_type_popup(active_user_id, selected_user)

    st.subheader(f"Active Category Types belonging to: {selected_user}")
    types = db.get_password_types_by_user(active_user_id)
    if not types:
        st.info(f"No custom category types defined for {selected_user}.")
    else:
        df_types = pd.DataFrame(types, columns=["Type ID", "Category Label"])
        st.dataframe(df_types, use_container_width=True, hide_index=True)

        selected_type = st.selectbox(
            "Select Type to Update/Delete", 
            types, 
            format_func=lambda x: f"ID {x[0]} - {x[1]}"
        )
        
        col_up, col_del = st.columns(2)
        with col_up:
            if st.button("✏️ Edit Selected Category", use_container_width=True):
                show_edit_popup(selected_type[0], selected_type[1])
        with col_del:
            if st.button("🗑️ Delete Selected Category", use_container_width=True):
                show_delete_popup(selected_type[0], selected_type[1])

    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="types_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()