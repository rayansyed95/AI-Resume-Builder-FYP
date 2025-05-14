import streamlit as st
from modules.auth.auth_utils import check_auth
from modules.database.client import db
from modules.utils.ui_utils import display_user_header

def calculate_profile_completion(profile_data):
    """Calculate profile completion percentage based on filled fields."""
    if not profile_data:
        return 0
    
    # Define required fields and their weights
    required_fields = {
        'basics': ['name', 'email', 'location', 'summary'],
        'workExperience': ['company', 'position', 'startDate'],
        'education': ['institution', 'degree'],
        'skills': ['programmingLanguages', 'frameworksLibraries']
    }
    
    total_fields = 0
    filled_fields = 0
    
    # Check basics section
    basics = profile_data.get('basics', {})
    for field in required_fields['basics']:
        total_fields += 1
        if basics.get(field):
            filled_fields += 1
    
    # Check work experience (only count once if at least one entry exists)
    work_exp = profile_data.get('workExperience', [])
    if work_exp:
        total_fields += len(required_fields['workExperience'])
        # Check if at least one work experience entry has all required fields
        for exp in work_exp:
            exp_filled = all(exp.get(field) for field in required_fields['workExperience'])
            if exp_filled:
                filled_fields += len(required_fields['workExperience'])
                break
    
    # Check education (only count once if at least one entry exists)
    education = profile_data.get('education', [])
    if education:
        total_fields += len(required_fields['education'])
        # Check if at least one education entry has all required fields
        for edu in education:
            edu_filled = all(edu.get(field) for field in required_fields['education'])
            if edu_filled:
                filled_fields += len(required_fields['education'])
                break
    
    # Check skills
    skills = profile_data.get('skills', {})
    for field in required_fields['skills']:
        total_fields += 1
        if skills.get(field) and len(skills[field]) > 0:
            filled_fields += 1
    
    # Calculate percentage
    if total_fields == 0:
        return 0
    return min(100, int((filled_fields / total_fields) * 100))

def dashboard_page():
    """Display the main dashboard with user overview and statistics."""
    # Display user header
    display_user_header()
    
    st.title("Dashboard")
    
    # Get user data
    user = st.experimental_user
    if not user or not user.is_logged_in:
        st.warning("Please login to access this page.")
        return
    
    user_id = getattr(user, "sub", None)
    user_record = db.get_user(user_id=user_id)
    profile_data = user_record.get("profile_data", {}) if user_record else {}
    resumes = db.get_user_resumes(user_id)
    
    # Overview Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Resumes", len(resumes))
    
    with col2:
        profile_completion = calculate_profile_completion(profile_data)
        st.metric("Profile Completion", f"{profile_completion}%")
    
    # Recent Resumes
    st.subheader("Recent Resumes")
    if resumes:
        # Sort resumes by created_at in descending order and take last 3
        sorted_resumes = sorted(resumes, key=lambda x: x.get('created_at', ''), reverse=True)[:3]
        for resume in sorted_resumes:
            with st.container(border=True):
                st.markdown(f"**{resume.get('title', 'Untitled Resume')}**")
                st.markdown(f"Company: {resume.get('company', 'N/A')}")
                st.markdown(f"Created: {resume.get('created_at', 'N/A')}")
                if resume.get('ats_score'):
                    st.markdown(f"ATS Score: {resume.get('ats_score')}%")
    else:
        st.info("No resumes created yet!")
        if st.button("Create Resume"):
            st.switch_page("pages/3_Resume_Builder.py")

def main():
    if check_auth():
        dashboard_page()
    else:
        st.warning("Please login to access this page.")

if __name__ == "__main__":
    main() 