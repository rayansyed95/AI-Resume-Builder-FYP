import streamlit as st
from modules.auth.auth_utils import get_user_info

def display_user_header():
    """Display the user header with profile picture, name, and logout button."""
    user_info = get_user_info()
    if user_info:
        # Create a container for the header
        with st.container():
            # Create three columns for the header
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.header(f"Welcome, {user_info['name']}")
            
            with col2:
                st.image(user_info['picture'], width=50)
            
            with col3:
                if st.button("Logout"):
                    st.logout()
                    st.rerun()
            
            # Add a separator
            st.divider() 