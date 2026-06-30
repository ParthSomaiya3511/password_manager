import streamlit as st
import pandas as pd
import database as db
import time

# Modal: Delete Category Popup (સેન્ટ્રલ ડાયલોગ પોપઅપ તરીકે - ઇન્સ્ટન્ટ ડીલીટ ફ્લો)
@st.dialog("⚠️ Delete Category Type")
def show_delete_popup(type_id, name):
    st.write(f"Are you sure you want to permanently delete category **{name}**? This will remove all associated sub-types and credentials.")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete", use_container_width=True, type="primary"):
            # Instant database execution without loader
            db.delete_password_type(type_id)
            st.success("Category deleted successfully.")
            st.rerun()
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def render_manage_types():
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="font-size: 3rem;">📁</span>
            <h2 style="margin: 0; color: #1e293b; font-weight: 700;">Manage Categories (Types)</h2>
            <p style="color: #64748b; font-size: 0.95rem;">Configure user-specific password category groups</p>
        </div>
    """, unsafe_allow_html=True)
    
    users = db.get_users()

    # Initialize page-level toggle states
    if 'show_add_type' not in st.session_state:
        st.session_state.show_add_type = False
        
    # State-driven trigger for Delete Popup
    if 'delete_type_triggered' not in st.session_state:
        st.session_state.delete_type_triggered = False
    if 'delete_type_id' not in st.session_state:
        st.session_state.delete_type_id = None
    if 'delete_type_name' not in st.session_state:
        st.session_state.delete_type_name = None

    # ➕ Add Toggle Button
    add_label = "❌ Close Add Panel" if st.session_state.show_add_type else "➕ Add New Category Type"
    if st.button(add_label, use_container_width=True, type="primary"):
        st.session_state.show_add_type = not st.session_state.show_add_type
        st.rerun()

    # --- DYNAMIC ON-PAGE ADD CONTAINER ---
    if st.session_state.show_add_type:
        with st.container(border=True):
            st.subheader("➕ Create New Category Type")
            
            if not users:
                st.warning("Please configure at least one active User Profile first.")
            else:
                user_opts = {u[1]: u[0] for u in users}
                selected_user = st.selectbox("👤 Select User Profile to Assign Category", list(user_opts.keys()), key="type_add_user_scope")
                active_user_id = user_opts[selected_user]
                
                name = st.text_input("Category Type Name (e.g. Enterprise, Personal)", placeholder="Enter category type name...")
                if st.button("Save Category Type", use_container_width=True, type="primary"):
                    if name:
                        clean_name = name.strip()
                        
                        # Validate if the category already exists for the selected user profile context
                        existing_types = db.get_password_types()
                        type_exists = any(
                            t[1] == active_user_id and t[3].lower() == clean_name.lower() 
                            for t in existing_types
                        )
                        
                        if type_exists:
                            st.error(f"Category '{clean_name}' already exists for user profile '{selected_user}'.")
                        else:
                            try:
                                with st.spinner("Saving Category Type..."):
                                    db.add_password_type(active_user_id, clean_name)
                                    time.sleep(2.0)
                                st.success(f"Category added: {name} under {selected_user}")
                                st.session_state.show_add_type = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to add: {e}")
                    else:
                        st.error("Please enter a category name.")

    # Fetch all category types globally across all users for the Master action-grid
    types = db.get_password_types()

    # --- CATEGORY ACTION-GRID DIRECTORY ---
    st.markdown('<div class="section-label">Active Category Types (All Profiles)</div>', unsafe_allow_html=True)
    if not types:
        st.info("No custom category types defined yet.")
    else:
        # Borderless Table Header Layout
        st.markdown("""
            <div style="font-weight: 700; color: #475569; padding-bottom: 8px; border-bottom: 2px solid #cbd5e1; margin-bottom: 12px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 25%; color: #475569;">User Profile</div>
                    <div style="width: 15%; color: #475569;">Type ID</div>
                    <div style="width: 35%; color: #475569;">Category Label</div>
                    <div style="width: 25%; text-align: right; color: #475569; padding-right: 25px;">Access</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Grid rows
        for t in types:
            tid, uid, uname, tname = t
            col_row, col_act = st.columns([75, 25])
            with col_row:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; padding: 6px 0;">
                        <div style="width: 33.3%; font-weight: 600; color: #334155;">{uname}</div>
                        <div style="width: 20%; color: #475569; font-family: monospace;">{tid}</div>
                        <div style="width: 46.7%; font-weight: 600; color: #0f172a;">{tname}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col_act:
                col_v, col_e, col_d = st.columns(3)
                with col_v:
                    # Reroutes cleanly to standalone view_type_vault.py on click
                    if st.button("👁️", key=f"view_t_{tid}", help=f"View category details", use_container_width=True):
                        st.session_state.view_type_id = tid
                        st.session_state.page = 'view_type_vault'
                        st.rerun()
                with col_e:
                    # Redirects cleanly to edit_type.py on click
                    if st.button("✏️", key=f"edit_t_{tid}", help=f"Edit {tname}", use_container_width=True):
                        st.session_state.edit_type_id = tid
                        st.session_state.page = 'edit_type'
                        st.rerun()
                with col_d:
                    # Triggers state-driven modal popup cleanly while hiding Add container
                    if st.button("🗑️", key=f"del_t_{tid}", help=f"Delete {tname}", use_container_width=True):
                        st.session_state.delete_type_id = tid
                        st.session_state.delete_type_name = tname
                        st.session_state.delete_type_triggered = True
                        st.session_state.show_add_type = False
                        st.rerun()
            # Under-row separator divider line
            st.markdown("<div style='border-bottom: 1px solid #f1f5f9; margin-top: 2px;'></div>", unsafe_allow_html=True)

    # Execute State-driven delete modal popup cleanly outside page loops
    if st.session_state.delete_type_triggered:
        st.session_state.delete_type_triggered = False # resets trigger
        show_delete_popup(st.session_state.delete_type_id, st.session_state.delete_type_name)

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="types_back_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()