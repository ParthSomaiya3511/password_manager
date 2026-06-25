import streamlit as st
import pandas as pd
import database as db
import time

def render_manage_types():
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="font-size: 3rem;">📁</span>
            <h2 style="margin: 0; color: #1e293b; font-weight: 700;">Manage Categories (Types)</h2>
            <p style="color: #64748b; font-size: 0.95rem;">Configure user-specific password category groups</p>
        </div>
    """, unsafe_allow_html=True)
    
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

    # Initialize page-level toggle states
    if 'show_add_type' not in st.session_state:
        st.session_state.show_add_type = False
    if 'show_edit_type' not in st.session_state:
        st.session_state.show_edit_type = False
    if 'show_delete_type' not in st.session_state:
        st.session_state.show_delete_type = False

    types = db.get_password_types_by_user(active_user_id)

    # Control Grid Row (Premium Button Layout)
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        add_label = "❌ Close Add Panel" if st.session_state.show_add_type else "➕ Add New Category"
        if st.button(add_label, use_container_width=True, type="primary"):
            st.session_state.show_add_type = not st.session_state.show_add_type
            st.session_state.show_edit_type = False
            st.session_state.show_delete_type = False
            st.rerun()
            
    with col_btn2:
        edit_label = "❌ Close Edit Panel" if st.session_state.show_edit_type else "✏️ Edit Category Type"
        if st.button(edit_label, use_container_width=True):
            if not types:
                st.warning("No category types available to edit.")
            else:
                st.session_state.show_edit_type = not st.session_state.show_edit_type
                st.session_state.show_add_type = False
                st.session_state.show_delete_type = False
                st.rerun()
                
    with col_btn3:
        del_label = "❌ Close Delete Panel" if st.session_state.show_delete_type else "🗑️ Delete Category Type"
        if st.button(del_label, use_container_width=True):
            if not types:
                st.warning("No category types available to delete.")
            else:
                st.session_state.show_delete_type = not st.session_state.show_delete_type
                st.session_state.show_add_type = False
                st.session_state.show_edit_type = False
                st.rerun()

    # --- DYNAMIC ON-PAGE CONTAINERS ---

    # 1. ADD CONTAINER
    if st.session_state.show_add_type:
        with st.container(border=True):
            st.subheader(f"Create New Category Type under {selected_user}")
            name = st.text_input("Category Type Name (e.g. Enterprise, Personal)")
            if st.button("Save Category Type", use_container_width=True, type="primary"):
                if name:
                    try:
                        with st.spinner("Saving Category Type..."):
                            db.add_password_type(active_user_id, name)
                            time.sleep(2.0)
                        st.success(f"Category added: {name}")
                        st.session_state.show_add_type = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add: {e}")
                else:
                    st.error("Please enter a category name.")

    # 2. EDIT CONTAINER
    if st.session_state.show_edit_type and types:
        with st.container(border=True):
            st.subheader(f"Edit Category Type (Belonging to {selected_user})")
            selected_type_edit = st.selectbox(
                "Select Type to Modify", 
                types, 
                format_func=lambda x: f"ID {x[0]} - {x[1]}",
                key="type_edit_selectbox"
            )
            up_name = st.text_input("Edit Category Label", value=selected_type_edit[1])
            if st.button("Save Changes", use_container_width=True, type="primary"):
                if up_name:
                    with st.spinner("Saving changes..."):
                        db.update_password_type(selected_type_edit[0], up_name)
                        time.sleep(2.0)
                    st.success("Category updated successfully.")
                    st.session_state.show_edit_type = False
                    st.rerun()
                else:
                    st.error("Please fill in all fields.")

    # 3. DELETE CONTAINER
    if st.session_state.show_delete_type and types:
        with st.container(border=True):
            st.subheader(f"Delete Category Type (Belonging to {selected_user})")
            selected_type_del = st.selectbox(
                "Select Type to Delete", 
                types, 
                format_func=lambda x: f"ID {x[0]} - {x[1]}",
                key="type_del_selectbox"
            )
            st.write(f"Are you sure you want to permanently delete category **{selected_type_del[1]}**? This will remove all associated sub-types and credentials.")
            
            col_del_yes, col_del_no = st.columns(2)
            with col_del_yes:
                if st.button("Yes, Delete", use_container_width=True, type="primary"):
                    with st.spinner("Deleting category..."):
                        db.delete_password_type(selected_type_del[0])
                        time.sleep(2.0)
                    st.success("Category deleted successfully.")
                    st.session_state.show_delete_type = False
                    st.rerun()
            with col_del_no:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_delete_type = False
                    st.rerun()

    # --- CATEGORY DIRECTORY TABLE ---
    st.markdown(f'<div class="section-label">Active Category Types belonging to: {selected_user}</div>', unsafe_allow_html=True)
    if not types:
        st.info(f"No custom category types defined for {selected_user}.")
    else:
        df_types = pd.DataFrame(types, columns=["Type ID", "Category Label"])
        st.dataframe(df_types, use_container_width=True, hide_index=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="types_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()