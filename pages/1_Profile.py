import streamlit as st
from modules.database.client import db
import os
from openai import OpenAI
import json
import PyPDF2
import io
import uuid
import requests

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_supabase_token(google_token: str) -> str:
    """Exchange Google token for Supabase token"""
    try:
        # Get Supabase token using Google token
        response = requests.post(
            f"{os.getenv('SUPABASE_URL')}/auth/v1/token",
            json={
                "provider_token": google_token,
                "provider": "google"
            },
            headers={
                "apikey": os.getenv('SUPABASE_KEY'),
                "Content-Type": "application/json"
            }
        )
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            st.error(f"Failed to get Supabase token: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error getting Supabase token: {str(e)}")
        return None

def google_sub_to_uuid(sub: str) -> str:
    """Convert Google sub to a valid UUID format"""
    # Create a deterministic UUID v5 using the sub as the namespace
    namespace = uuid.NAMESPACE_URL  # Using URL namespace as it's appropriate for Google IDs
    return str(uuid.uuid5(namespace, sub))

# Get current user info from Streamlit
def get_user_info():
    user = st.experimental_user
    if not user or not user.is_logged_in:
        return None
    
    # Get sub as user ID
    user_id = getattr(user, "sub", None)
    if not user_id:
        st.error("Could not retrieve user ID from Google authentication")
        st.stop()
    
    return {
        "id": user_id,  # Using Google sub directly
        "email": user.email,
        "fullName": user.name,
        "avatar_url": user.picture,
    }

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def parse_resume_with_llm(resume_text):
    """Parse resume text using OpenAI API"""
    prompt = """Parse the following resume text and extract information in a structured JSON format. 
    Include the following sections:
    - basics (name, email, phone, summary, location, dob, github, linkedin, postal_code, city, country)
    - education (list of education entries with institution, degree, fieldOfStudy, startDate, endDate, details)
    - workExperience (list of work entries with jobTitle, company, location, startDate, endDate, responsibilities)
    - projects (list of projects with name, description, technologies, date, link)
    - certifications (list of certifications with name, year)
    - skills (programmingLanguages, frameworksLibraries, toolsPlatforms, cloud, domains, softSkills)
    - languages (list of languages)
    - interests (list of interests)
    
    Resume text:
    {resume_text}
    
    Return only the JSON object, no additional text. For arrays of strings (like responsibilities, technologies, etc.), 
    return them as proper arrays, not comma-separated strings."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a resume parser that extracts structured information from resume text. Return arrays as proper JSON arrays, not comma-separated strings."},
                {"role": "user", "content": prompt.format(resume_text=resume_text)}
            ],
            response_format={ "type": "json_object" }
        )
        parsed_data = json.loads(response.choices[0].message.content)
        
        # Debug: Print the parsed data in a more readable format
        # st.write("Debug - Raw LLM Response:")
        # st.json(parsed_data)
        # print(parsed_data) # just to check if the data is parsed correctly
        
        return parsed_data
    except Exception as e:
        st.error(f"Error parsing resume: {str(e)}")
        return None

user = get_user_info()
if not user:
    st.warning("Please log in to view your profile.")
    st.stop()

user_id = user["id"]
email = user["email"]
full_name = user["fullName"]
avatar_url = user["avatar_url"]

# Debug output
# st.write("Debug - User ID (sub):", user_id)
# st.write("Debug - Email:", email)

# Fetch profile data from Supabase
def fetch_profile():
    # Try by UUID, fallback to email
    if user_id:
        user_record = db.get_user(user_id=user_id)
        if user_record:
            return user_record.get('profile_data', {})
    user_record = db.get_user(email=email)
    return user_record.get('profile_data', {}) if user_record else {}

profile_data = fetch_profile()

# Prefill fields from profile_data or defaults
basics = profile_data.get('basics', {})
education = profile_data.get('education', [])
work_experience = profile_data.get('workExperience', [])
projects = profile_data.get('projects', [])
certifications = profile_data.get('certifications', [])
skills = profile_data.get('skills', {})
languages = profile_data.get('languages', [])
interests = profile_data.get('interests', [])

# Use session_state to persist dynamic lists
if 'education' not in st.session_state:
    st.session_state.education = education if education else [{}]
if 'work_experience' not in st.session_state:
    st.session_state.work_experience = work_experience if work_experience else [{}]
if 'projects' not in st.session_state:
    st.session_state.projects = projects if projects else [{}]
if 'certifications' not in st.session_state:
    st.session_state.certifications = certifications if certifications else [{}]
if 'languages' not in st.session_state:
    st.session_state.languages = languages if languages else []
if 'interests' not in st.session_state:
    st.session_state.interests = interests if interests else []

st.title("👤 Profile")

# Resume Upload and Parsing Section
st.subheader("Resume Upload")
uploaded_file = st.file_uploader("Upload your resume (PDF)", type=['pdf'])

if uploaded_file is not None:
    if st.button("Parse Resume"):
        with st.spinner("Parsing resume..."):
            # Extract text from PDF
            resume_text = extract_text_from_pdf(uploaded_file)
            
            # Debug: Show extracted text
            with st.expander("Debug - Extracted Resume Text"):
                st.text(resume_text)
            
            # Parse with LLM
            parsed_data = parse_resume_with_llm(resume_text)
            
            if parsed_data:
                # Update session state with parsed data
                if 'basics' in parsed_data:
                    st.session_state.basics = parsed_data['basics']
                
                # Update education
                if 'education' in parsed_data:
                    st.session_state.education = parsed_data['education']
                    # Debug
                    st.write("Debug - Updated Education:", st.session_state.education)
                
                # Update work experience
                if 'workExperience' in parsed_data:
                    st.session_state.work_experience = parsed_data['workExperience']
                    # Debug
                    st.write("Debug - Updated Work Experience:", st.session_state.work_experience)
                
                # Update projects
                if 'projects' in parsed_data:
                    st.session_state.projects = parsed_data['projects']
                    # Debug
                    st.write("Debug - Updated Projects:", st.session_state.projects)
                
                # Update certifications
                if 'certifications' in parsed_data:
                    st.session_state.certifications = parsed_data['certifications']
                    # Debug
                    st.write("Debug - Updated Certifications:", st.session_state.certifications)
                
                # Update skills
                if 'skills' in parsed_data:
                    st.session_state.skills = parsed_data['skills']
                
                # Update languages
                if 'languages' in parsed_data:
                    st.session_state.languages = parsed_data['languages']
                
                # Update interests
                if 'interests' in parsed_data:
                    st.session_state.interests = parsed_data['interests']
                
                st.success("Resume parsed successfully! Review and edit the information below before saving.")
                st.rerun()

# Handle dynamic lists outside the form
st.subheader("Education")
edu_list = []
for i, edu in enumerate(st.session_state.education):
    with st.expander(f"Education Entry #{i+1}", expanded=True):
        institution = st.text_input(f"Institution {i+1}", value=edu.get("institution", ""), key=f"institution_{i}")
        degree = st.text_input(f"Degree {i+1}", value=edu.get("degree", ""), key=f"degree_{i}")
        field_of_study = st.text_input(f"Field of Study {i+1}", value=edu.get("fieldOfStudy", ""), key=f"field_{i}")
        edu_start = st.text_input(f"Start Date {i+1}", value=edu.get("startDate", ""), key=f"edu_start_{i}")
        edu_end = st.text_input(f"End Date {i+1}", value=edu.get("endDate", ""), key=f"edu_end_{i}")
        edu_details = st.text_area(f"Details {i+1}", value=edu.get("details", ""), key=f"edu_details_{i}")
        if st.button(f"Remove Education #{i+1}", key=f"remove_edu_{i}"):
            st.session_state.education.pop(i)
            st.rerun()
        edu_list.append({
            "institution": institution,
            "degree": degree,
            "fieldOfStudy": field_of_study,
            "startDate": edu_start,
            "endDate": edu_end,
            "details": edu_details
        })
if st.button("Add Education"):
    st.session_state.education.append({})
    st.rerun()

st.subheader("Work Experience")
work_list = []
for i, work in enumerate(st.session_state.work_experience):
    with st.expander(f"Work Experience Entry #{i+1}", expanded=True):
        job_title = st.text_input(f"Job Title {i+1}", value=work.get("jobTitle", ""), key=f"job_title_{i}")
        company = st.text_input(f"Company {i+1}", value=work.get("company", ""), key=f"company_{i}")
        work_location = st.text_input(f"Work Location {i+1}", value=work.get("location", ""), key=f"work_location_{i}")
        work_start = st.text_input(f"Start Date {i+1}", value=work.get("startDate", ""), key=f"work_start_{i}")
        work_end = st.text_input(f"End Date {i+1}", value=work.get("endDate", ""), key=f"work_end_{i}")
        # Fix: Handle None values for responsibilities
        responsibilities = work.get("responsibilities", [])
        if responsibilities is None:
            responsibilities = []
        responsibilities = st.text_area(f"Responsibilities (comma separated) {i+1}", 
                                     value=", ".join(responsibilities), 
                                     key=f"work_resp_{i}")
        if st.button(f"Remove Work Experience #{i+1}", key=f"remove_work_{i}"):
            st.session_state.work_experience.pop(i)
            st.rerun()
        work_list.append({
            "jobTitle": job_title,
            "company": company,
            "location": work_location,
            "startDate": work_start,
            "endDate": work_end,
            "responsibilities": [r.strip() for r in responsibilities.split(",") if r.strip()]
        })
if st.button("Add Work Experience"):
    st.session_state.work_experience.append({})
    st.rerun()

st.subheader("Projects")
proj_list = []
for i, proj in enumerate(st.session_state.projects):
    with st.expander(f"Project Entry #{i+1}", expanded=True):
        proj_name = st.text_input(f"Project Name {i+1}", value=proj.get("name", ""), key=f"proj_name_{i}")
        proj_desc = st.text_area(f"Project Description {i+1}", value=proj.get("description", ""), key=f"proj_desc_{i}")
        proj_tech = st.text_input(f"Technologies (comma separated) {i+1}", value=", ".join(proj.get("technologies", [])), key=f"proj_tech_{i}")
        proj_date = st.text_input(f"Project Date {i+1}", value=proj.get("date", ""), key=f"proj_date_{i}")
        proj_link = st.text_input(f"Project Link {i+1}", value=proj.get("link", ""), key=f"proj_link_{i}")
        if st.button(f"Remove Project #{i+1}", key=f"remove_proj_{i}"):
            st.session_state.projects.pop(i)
            st.rerun()
        proj_list.append({
            "name": proj_name,
            "description": proj_desc,
            "technologies": [t.strip() for t in proj_tech.split(",") if t.strip()],
            "date": proj_date,
            "link": proj_link
        })
if st.button("Add Project"):
    st.session_state.projects.append({})
    st.rerun()

st.subheader("Certifications")
cert_list = []
for i, cert in enumerate(st.session_state.certifications):
    with st.expander(f"Certification Entry #{i+1}", expanded=True):
        cert_name = st.text_input(f"Certification Name {i+1}", value=cert.get("name", ""), key=f"cert_name_{i}")
        cert_year = st.text_input(f"Certification Year {i+1}", value=str(cert.get("year", "")), key=f"cert_year_{i}")
        if st.button(f"Remove Certification #{i+1}", key=f"remove_cert_{i}"):
            st.session_state.certifications.pop(i)
            st.rerun()
        cert_list.append({
            "name": cert_name,
            "year": cert_year
        })
if st.button("Add Certification"):
    st.session_state.certifications.append({})
    st.rerun()

# Main form for basic information and skills
with st.form("profile_form"):
    st.subheader("Basic Information")
    st.text_input("Full Name", value=full_name, disabled=True)
    st.text_input("Email", value=email, disabled=True)
    st.text_input("Avatar URL", value=avatar_url, disabled=True)
    
    # Get values from session state if available, otherwise use basics dictionary
    phone = st.text_input("Phone Number", value=st.session_state.get('basics', {}).get('phone', basics.get("phone", "")))
    dob = st.text_input("Date of Birth", value=st.session_state.get('basics', {}).get('dob', basics.get("dob", "")))
    summary = st.text_area("Professional Summary", value=st.session_state.get('basics', {}).get('summary', basics.get("summary", "")))
    linkedin = st.text_input("LinkedIn", value=st.session_state.get('basics', {}).get('linkedin', basics.get("linkedin", "")))
    github = st.text_input("GitHub", value=st.session_state.get('basics', {}).get('github', basics.get("github", "")))
    
    # Handle location separately since it's nested
    location = st.session_state.get('basics', {}).get('location', basics.get("location", {}))
    if isinstance(location, str):
        # If location is a string (from LLM), split it into components
        address = location
        city = ""
        postal_code = ""
        country = ""
    else:
        # If location is a dict (from database)
        address = location.get("address", "")
        city = location.get("city", "")
        postal_code = location.get("postalCode", "")
        country = location.get("country", "")
    
    address = st.text_input("Address", value=address)
    city = st.text_input("City", value=city)
    postal_code = st.text_input("Postal Code", value=postal_code)
    country = st.text_input("Country", value=country)

    st.subheader("Skills")
    # Get skills from session state if available
    session_skills = st.session_state.get('skills', {})
    
    # Handle programming languages
    prog_langs = session_skills.get('programmingLanguages', []) if session_skills else skills.get('programmingLanguages', [])
    programming_languages = st.text_input("Programming Languages (comma separated)", value=", ".join(prog_langs))
    
    # Handle frameworks
    frameworks = session_skills.get('frameworksLibraries', []) if session_skills else skills.get('frameworksLibraries', [])
    frameworks = st.text_input("Frameworks/Libraries (comma separated)", value=", ".join(frameworks))
    
    # Handle tools
    tools = session_skills.get('toolsPlatforms', []) if session_skills else skills.get('toolsPlatforms', [])
    tools = st.text_input("Tools/Platforms (comma separated)", value=", ".join(tools))
    
    # Handle cloud
    cloud = session_skills.get('cloud', []) if session_skills else skills.get('cloud', [])
    cloud = st.text_input("Cloud (comma separated)", value=", ".join(cloud))
    
    # Handle domains
    domains = session_skills.get('domains', []) if session_skills else skills.get('domains', [])
    domains = st.text_input("Domains (comma separated)", value=", ".join(domains))
    
    # Handle soft skills
    soft_skills = session_skills.get('softSkills', []) if session_skills else skills.get('softSkills', [])
    soft_skills = st.text_input("Soft Skills (comma separated)", value=", ".join(soft_skills))

    st.subheader("Languages")
    # Handle languages - check if they're objects with 'language' field or simple strings
    session_langs = st.session_state.get('languages', [])
    if session_langs and isinstance(session_langs[0], dict):
        # If languages are objects with 'language' field
        langs = [f"{lang.get('language', '')} ({lang.get('proficiency', '')})" for lang in session_langs]
    else:
        # If languages are simple strings
        langs = session_langs if session_langs else []
    langs = st.text_input("Languages (comma separated)", value=", ".join(langs))

    st.subheader("Interests")
    # Get interests from session state if available
    session_interests = st.session_state.get('interests', [])
    ints = st.text_input("Interests (comma separated)", value=", ".join(session_interests if session_interests else interests))

    submitted = st.form_submit_button("Save Profile")
    if submitted:
        # Build the profile_data dict
        new_profile_data = {
            "basics": {
                "fullName": full_name,
                "email": email,
                "avatar_url": avatar_url,
                "phone": phone,
                "dob": dob,
                "linkedin": linkedin,
                "github": github,
                "summary": summary,
                "location": {
                    "address": address,
                    "city": city,
                    "postalCode": postal_code,
                    "country": country
                }
            },
            "education": st.session_state.education,
            "workExperience": st.session_state.work_experience,
            "projects": st.session_state.projects,
            "certifications": st.session_state.certifications,
            "skills": {
                "programmingLanguages": [l.strip() for l in programming_languages.split(",") if l.strip()],
                "frameworksLibraries": [f.strip() for f in frameworks.split(",") if f.strip()],
                "toolsPlatforms": [t.strip() for t in tools.split(",") if t.strip()],
                "cloud": [c.strip() for c in cloud.split(",") if c.strip()],
                "domains": [d.strip() for d in domains.split(",") if d.strip()],
                "softSkills": [s.strip() for s in soft_skills.split(",") if s.strip()]
            },
            "languages": [{"language": lang.split("(")[0].strip(), "proficiency": lang.split("(")[1].strip(")")} 
                         for lang in langs.split(",") if lang.strip() and "(" in lang],
            "interests": [i.strip() for i in ints.split(",") if i.strip()]
        }

        try:
            # First try to get existing user
            user_record = None
            if user_id:
                user_record = db.get_user(user_id=user_id)
            if not user_record:
                user_record = db.get_user(email=email)
            
            if user_record:
                # Update existing user
                try:
                    db.update_user(user_record['id'], {"profile_data": new_profile_data})
                    st.success("Profile updated successfully!")
                except Exception as e:
                    st.error(f"Error updating profile: {str(e)}")
            else:
                # Create new user record
                new_user = {
                    "id": user_id,  # Use Google sub as ID
                    "email": email,
                    "profile_data": new_profile_data
                }
                try:
                    created_user = db.create_user(new_user)
                    if created_user:
                        st.success("Profile created successfully!")
                    else:
                        st.error("Failed to create user profile")
                except Exception as e:
                    st.error(f"Error creating user profile: {str(e)}")
            
        except Exception as e:
            st.error(f"Error updating profile: {str(e)}") 