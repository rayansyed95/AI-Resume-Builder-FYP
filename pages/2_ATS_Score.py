import streamlit as st
from modules.auth.auth_utils import check_auth
from modules.utils.ui_utils import display_user_header
from openai import OpenAI
import os
import json
from PyPDF2 import PdfReader

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_text_from_pdf(file):
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None

def analyze_resume_ats(resume_text, job_details):
    """Analyze resume against job description using LLM."""
    prompt = f"""
You are an expert ATS (Applicant Tracking System) analyst with 15+ years of experience in recruitment and HR technology.

## TASK
Analyze the provided resume against the job description and provide a detailed ATS compatibility assessment.

## INPUTS

### Job Description:
{job_details}

### Resume Text:
{resume_text}

## OUTPUT FORMAT
Provide your analysis in the following JSON format:
{{
    "overall_score": <score out of 100>,
    "score_breakdown": {{
        "keyword_match": <score out of 100>,
        "format_compatibility": <score out of 100>,
        "content_relevance": <score out of 100>,
        "experience_alignment": <score out of 100>
    }},
    "missing_keywords": [<list of important keywords from job description missing in resume>],
    "format_issues": [<list of format-related issues>],
    "content_suggestions": [<list of content improvement suggestions>],
    "experience_gaps": [<list of experience gaps or misalignments>],
    "strengths": [<list of resume strengths>],
    "improvement_areas": [<list of areas needing improvement>]
}}

Focus on providing specific, actionable feedback that will help improve the resume's ATS compatibility.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful ATS analysis assistant. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Get the response content and clean it
        response_content = response.choices[0].message.content.strip()
        
        # Debug: Print the raw response content
        # st.write("Debug - Raw response content:")
        # st.code(response_content)
        
        # Try to clean the response content
        # Remove any potential BOM or special characters
        response_content = response_content.encode('utf-8').decode('utf-8-sig')
        
        # Try to parse the JSON
        try:
            # First try direct parsing
            analysis = json.loads(response_content)
        except json.JSONDecodeError:
            try:
                # If that fails, try to find JSON content between curly braces
                import re
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    analysis = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON object found in response", response_content, 0)
            except Exception as e:
                st.error(f"Error parsing API response as JSON: {str(e)}")
                st.error("Raw response content:")
                st.code(response_content)
                return None
        
        # Format the analysis as markdown
        markdown_output = f"""
### Overall ATS Score: {analysis['overall_score']}%

#### Score Breakdown
- **Keyword Match:** {analysis['score_breakdown']['keyword_match']}%
- **Format Compatibility:** {analysis['score_breakdown']['format_compatibility']}%
- **Content Relevance:** {analysis['score_breakdown']['content_relevance']}%
- **Experience Alignment:** {analysis['score_breakdown']['experience_alignment']}%

#### Missing Keywords
{chr(10).join([f"- {keyword}" for keyword in analysis['missing_keywords']])}

#### Format Issues
{chr(10).join([f"- {issue}" for issue in analysis['format_issues']])}

#### Content Suggestions
{chr(10).join([f"- {suggestion}" for suggestion in analysis['content_suggestions']])}

#### Experience Gaps
{chr(10).join([f"- {gap}" for gap in analysis['experience_gaps']])}

#### Resume Strengths
{chr(10).join([f"- {strength}" for strength in analysis['strengths']])}

#### Areas for Improvement
{chr(10).join([f"- {area}" for area in analysis['improvement_areas']])}
"""
        return {"markdown": markdown_output, "data": analysis}
            
    except Exception as e:
        st.error(f"Error analyzing resume: {str(e)}")
        return None

def ats_score_page():
    """Display the ATS score analysis page."""
    # Display user header
    display_user_header()
    
    st.title("ATS Score Analysis")
    
    st.markdown("""
    ### Check your resume's ATS compatibility for a specific job
    
    Our AI will analyze your resume against the job description and provide:
    - Comprehensive ATS compatibility score
    - Detailed score breakdown
    - Keyword matching analysis
    - Format and content recommendations
    """)
    
    # Job Details Section
    st.subheader("1. Job Details")
    job_title = st.text_input("Job Title")
    company = st.text_input("Company Name")
    job_description = st.text_area("Paste the job description here", height=200)
    
    # Resume Upload Section
    st.subheader("2. Upload Your Resume")
    uploaded_file = st.file_uploader("Choose your resume file (PDF only)", type=['pdf'])
    
    # Analysis Button (only show if both sections are filled)
    if job_title and company and job_description and uploaded_file:
        if st.button("Analyze Resume", type="primary"):
            with st.spinner("Analyzing your resume..."):
                # Extract text from resume
                resume_text = extract_text_from_pdf(uploaded_file)
                
                if resume_text:
                    # Combine job details
                    job_details = f"""
                    Job Title: {job_title}
                    Company: {company}
                    Description: {job_description}
                    """
                    
                    # Get ATS analysis
                    analysis = analyze_resume_ats(resume_text, job_details)
                    
                    if analysis:
                        # Display the analysis using markdown
                        st.markdown(analysis["markdown"])
                        
                        # Store the analysis data in session state for potential future use
                        st.session_state.ats_analysis = analysis["data"]
    elif uploaded_file or (job_title or company or job_description):
        st.info("Please fill in all job details and upload your resume to begin analysis.")

def main():
    if check_auth():
        ats_score_page()
    else:
        st.warning("Please login to access this page.")

if __name__ == "__main__":
    main() 