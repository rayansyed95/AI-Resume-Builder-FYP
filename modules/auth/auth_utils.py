import streamlit as st

def check_auth():
    """Check if the user is authenticated."""
    return st.experimental_user.is_logged_in

def get_user_info():
    """Get the current user's information."""
    if check_auth():
        return {
            "name": st.experimental_user.name,
            "email": st.experimental_user.email,
            "picture": st.experimental_user.picture
        }
    return None

def require_auth():
    """Decorator to require authentication for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_auth():
                st.warning("Please login to access this feature.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator 