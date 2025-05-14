import streamlit as st
from modules.auth.auth_utils import check_auth

# App Configuration
st.set_page_config(
    page_title="AI Resume Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def setup_sidebar():
    """Setup the sidebar navigation."""
    if check_auth():
        with st.sidebar:
            st.title("Navigation")
            st.page_link("pages/0_Dashboard.py", label="Dashboard", icon="📊")
            st.page_link("pages/1_Profile.py", label="Profile", icon="👤")
            st.page_link("pages/2_ATS_Score.py", label="ATS Score", icon="🎯")
            st.page_link("pages/3_Resume_Builder.py", label="Resume Builder", icon="📝")
            st.page_link("pages/4_Past_Resumes.py", label="Past Resumes", icon="📚")
            
            st.divider()
            
            

def landing_page():
    """Display the landing page for non-authenticated users."""
    st.title("🚀 AI-Powered Resume Builder")
    
    # Hero Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Create Your Perfect Resume in Just 2 Minutes!")
        st.markdown("""
        **Have you applied to dozens of jobs but never heard back?**
        
        Chances are, your resume isn't getting past the Applicant Tracking Systems (ATS) used by most companies today. Creating job-specific resumes that match employer requirements can be time-consuming and confusing.
        
        **Do you wish there was an easier way to tailor your resume for each job and boost your chances of getting noticed?**

        Our AI-powered Resume Builder is designed to help job seekers like you create optimized, professional, and customized resumes effortlessly – all within minutes. Whether you're applying for your first job or aiming for a career change, our smart system guides you every step of the way.
        """)
        st.markdown("**Wait no more! Create your perfect resume in just 2 minutes! Literally**")
        
        # Login Button
        if st.button("Login with Google"):
            st.login("google")
    
    with col2:
        st.image("https://jobbloghq.com/wp-content/uploads/2024/05/ai-resume-builder-future.jpg.webp", caption="Resume Builder Illustration")
    
    # Features Section
    st.markdown("<h2 style='text-align: center; color: #fff;'>Key Features</h2>", unsafe_allow_html=True)

    # Feature details with icons, headings, and descriptions
    features = [
        {
            "icon": "🎯",
            "heading": "Job-Specific Optimization",
            "description": "Tailor your resume to specific job descriptions, increasing your chances of getting noticed by recruiters."
        },
        {
            "icon": "📊",
            "heading": "ATS Score Matching",
            "description": "Optimize your resume to pass Applicant Tracking Systems (ATS) with our intelligent scoring mechanism."
        },
        {
            "icon": "🤖",
            "heading": "AI-Powered Content Generation",
            "description": "Leverage AI to craft compelling job descriptions, achievements, and skill highlights."
        }
    ]

    # Create three columns
    col1, col2, col3 = st.columns(3)

    # Populate columns with feature containers
    columns = [col1, col2, col3]

    for i, feature in enumerate(features):
        with columns[i]:
            # Create a container for each feature
            with st.container(border=True):
                # Icon
                st.markdown(f"<div style='text-align: center; font-size: 3rem; margin-bottom: 10px;'>{feature['icon']}</div>", unsafe_allow_html=True)
                
                # Heading
                st.markdown(f"<h3 style='text-align: center; color: #fff;'>{feature['heading']}</h3>", unsafe_allow_html=True)
                
                # Description
                st.markdown(f"<p style='text-align: center; color: #fff;'>{feature['description']}</p>", unsafe_allow_html=True)

    # Developer Information Dialog
    with st.container():
        with st.expander("About me", expanded=False):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Developer Image
                st.image("rayan.jpg", width=200, caption="Its me!")
                
                # Social Links
                st.markdown("### Connect")
                st.markdown("[GitHub](https://github.com/rayansyed95)")
                st.markdown("[LinkedIn](https://www.linkedin.com/in/rayan-syed-866596253/)")
            
            with col2:
                # Developer Information
                st.markdown("## Rayan Syed")
                st.markdown("**Program:** BS Software Engineering")
                st.markdown("**Batch:** 2022-2025")
                
                # About Section
                st.markdown("### About")
                st.markdown("""
                I'm a passionate developer with expertise in AI and web technologies. 
                I created this AI Resume Builder to help people craft job-specific resumes 
                that stand out from the crowd and pass ATS screenings.
                
                My background includes:
                - 1+ year of experience in AI/ML development
                - I am Full-stack web development with Python & React
                - My Core interest is in AI, Machine Learning and Generative AI
                
                Feel free to connect with me on GitHub or LinkedIn for collaborations 
                or to share your experience with this tool!
                """)

def main():
    # Setup sidebar if user is logged in
    setup_sidebar()
    
    # Check if user is logged in
    if not check_auth():
        landing_page()
    else:
        # Redirect to dashboard
        st.switch_page("pages/0_Dashboard.py")

# Run the app
if __name__ == "__main__":
    main()