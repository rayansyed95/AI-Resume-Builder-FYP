import streamlit as st
from modules.auth.auth_utils import check_auth
from modules.database.client import db
from openai import OpenAI
import os
import json
import re
import tempfile
from spire.doc import *
from spire.doc.common import *

# Remove unused imports
# from modules.ai.ai_utils import generate_resume
# from modules.utils.ui_utils import display_user_header

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def extract_markdown_resume(llm_output):
    """Extract the markdown resume section from the LLM output."""
    # Look for a markdown code block or the section after 'OPTIMIZED RESUME SECTION'
    match = re.search(r'```markdown(.*?)```', llm_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: try to find the section header
    match = re.search(r'OPTIMIZED RESUME SECTION.*?\n(.*)', llm_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: return everything
    return llm_output.strip()


def break_long_words(text, max_word_length=60):
    def breaker(word):
        if len(word) > max_word_length:
            return ' '.join([word[i:i+max_word_length] for i in range(0, len(word), max_word_length)])
        return word
    return ' '.join([breaker(w) for w in text.split(' ')])


def parse_contact_line(line, pdf):
    # Example: "GitHub: https://github.com/username"
    # Returns: (label, url) or (None, None)
    if "github.com" in line.lower():
        url = re.search(r'(https?://[\w\.-/]+|github\.com/[\w\.-/]+)', line, re.IGNORECASE)
        if url:
            link = url.group(0)
            if not link.startswith("http"): link = "https://" + link
            return "GitHub Profile", link
    if "linkedin.com" in line.lower():
        url = re.search(r'(https?://[\w\.-/]+|linkedin\.com/[\w\.-/]+)', line, re.IGNORECASE)
        if url:
            link = url.group(0)
            if not link.startswith("http"): link = "https://" + link
            return "LinkedIn Profile", link
    if "@" in line and "email" in line.lower():
        email = re.search(r'[\w\.-]+@[\w\.-]+', line)
        if email:
            return "Email Me", f"mailto:{email.group(0)}"
    return None, None


def markdown_to_pdf_spire(markdown_text):
    # Save markdown to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.md', mode='w', encoding='utf-8') as mdfile:
        mdfile.write(markdown_text)
        md_path = mdfile.name
    
    try:
        # Create a new Word document and load the markdown
        document = Document()
        document.LoadFromFile(md_path)
        
        # Create PDF in a new temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
            pdf_path = tmpfile.name
        
        # Save as PDF
        document.SaveToFile(pdf_path, FileFormat.PDF)
        document.Dispose()
        
        return pdf_path
    finally:
        # Clean up the markdown temp file
        try:
            os.unlink(md_path)
        except:
            pass


def resume_builder_page():
    """Display the resume builder page."""
    st.title("Create Job-Specific Resume")
    
    # Session state for LLM context and output
    if 'llm_context' not in st.session_state:
        st.session_state.llm_context = None
    if 'llm_output' not in st.session_state:
        st.session_state.llm_output = None
    if 'llm_last_prompt' not in st.session_state:
        st.session_state.llm_last_prompt = None
    if 'awaiting_improvement' not in st.session_state:
        st.session_state.awaiting_improvement = False
    if 'pdf_path' not in st.session_state:
        st.session_state.pdf_path = None
    if 'resume_db_id' not in st.session_state:
        st.session_state.resume_db_id = None

    # 1. Job Details Form (only show if no LLM output yet)
    if st.session_state.llm_output is None or st.session_state.awaiting_improvement:
        with st.form("job_details_form"):
            st.subheader("Job Details")
            job_title = st.text_input("Job Title")
            company = st.text_input("Company Name")
            job_description = st.text_area("Paste the job description here", height=200)
            
            st.subheader("Resume Preferences")
            resume_format = st.selectbox(
                "Choose Resume Format",
                ["Chronological", "Functional", "Combination", "Targeted"]
            )
            
            tone = st.selectbox(
                "Choose Writing Tone",
                ["Professional", "Confident", "Enthusiastic", "Formal"]
            )
            
            submitted = st.form_submit_button("Analyze")

        if submitted:
            if not job_title or not job_description:
                st.error("Please fill in all required fields!")
                return

            # Fetch user info and profile data
            user = st.experimental_user
            if not user or not user.is_logged_in:
                st.warning("Please login to access this page.")
                return
            user_id = getattr(user, "sub", None)
            user_record = db.get_user(user_id=user_id)
            profile_data = user_record.get("profile_data", {}) if user_record else {}

            # Construct LLM prompt
            prompt = f'''
You are an expert ATS-optimization specialist and professional resume coach with 15+ years of experience helping candidates secure interviews at top companies.

## YOUR TASK
Analyze the candidate's resume data against the specific job requirements, then provide:
1. A detailed gap analysis 
2. Strategic recommendations
3. An ATS-optimized resume draft in markdown

## INPUTS

### User Resume Data (JSON):
{json.dumps(profile_data, indent=2)}

### Target Position:
Job Title: {job_title}
Company: {company}
Job Description:
{job_description}

### Formatting Preferences:
Resume Format: {resume_format}
Writing Tone: {tone}

## OUTPUT INSTRUCTIONS

### 1. ANALYSIS SECTION (25% of response)
- Provide a keyword/skills match analysis (which skills from the job description are present/missing in the resume)
- Identify experience gaps and alignment opportunities
- Calculate an overall match score (1-100) with brief explanation
- List 3-5 specific strengths in relation to this position
- Identify 3-5 potential weaknesses or improvement areas

### 2. RECOMMENDATIONS SECTION (25% of response)
- Suggest specific, actionable changes to improve ATS performance
- Recommend skills/keywords to add, emphasize, or remove
- Propose improvements to bullet points, focusing on quantifiable achievements
- Suggest adjustments to prioritize most relevant experience based on job requirements
- Recommend sections to expand, condense, or remove entirely

### 3. OPTIMIZED RESUME SECTION (50% of response)
- Create a fully revised resume in markdown format
- Incorporate all recommended changes from earlier sections
- Ensure perfect alignment with job requirements while maintaining honesty
- Prioritize the most relevant experience and skills first
- Use strong action verbs and quantifiable results
- Format according to the specified resume style ({resume_format})
- Maintain the requested tone ({tone})
- Ensure the resume is scannable for both ATS and human readers
- Keep the resume concise (1-2 pages equivalent)

Important: Focus on creating a compelling, honest, and targeted resume that will pass ATS screening and impress hiring managers. Use your expertise to make strategic decisions about what to include, emphasize, or remove based on relevance to this specific position.
'''

            with st.spinner("Analyzing and generating suggestions..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=[
                            {"role": "system", "content": "You are a helpful resume assistant."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    llm_suggestions = response.choices[0].message.content
                except Exception as e:
                    st.error(f"Error from LLM: {str(e)}")
                    return

            st.session_state.llm_context = [
                {"role": "system", "content": "You are a helpful resume assistant."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": llm_suggestions}
            ]
            st.session_state.llm_output = llm_suggestions
            st.session_state.llm_last_prompt = prompt
            st.session_state.awaiting_improvement = False
            st.session_state.pdf_path = None
            st.session_state.resume_db_id = None
            st.rerun()

    # 2. Show LLM output and improvement options
    if st.session_state.llm_output and not st.session_state.awaiting_improvement:
        st.subheader("LLM Suggestions & Optimized Resume")
        st.markdown(st.session_state.llm_output)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Accept & Continue"):
                # Extract markdown resume
                markdown_resume = extract_markdown_resume(st.session_state.llm_output)
                # Save to DB
                user = st.experimental_user
                user_id = getattr(user, "sub", None)
                user_record = db.get_user(user_id=user_id)
                email = user_record.get("email") if user_record else ""
                # Use job title and company for title
                title = f"{st.session_state.llm_last_prompt.split('Job Title: ')[-1].split('\n')[0]} @ {st.session_state.llm_last_prompt.split('Company: ')[-1].split('\n')[0]}"
                resume_data = {
                    "title": title,
                    "company": title.split('@')[-1].strip() if '@' in title else title,
                    "job_description": st.session_state.llm_last_prompt.split('Job Description:')[-1].split('### Formatting Preferences:')[0].strip(),
                    "resume_content": markdown_resume,
                    "format_type": st.session_state.llm_last_prompt.split('Resume Format: ')[-1].split('\n')[0],
                    "tone": st.session_state.llm_last_prompt.split('Writing Tone: ')[-1].split('\n')[0],
                    "tags": []
                }
                db_resume = db.create_resume(user_id, resume_data)
                st.session_state.resume_db_id = db_resume.get('id') if db_resume else None
                # Generate PDF
                pdf_path = markdown_to_pdf_spire(markdown_resume)
                st.session_state.pdf_path = pdf_path
                st.success("Resume saved and PDF generated!")
                # Show download button
                try:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download Resume PDF",
                            data=f.read(),
                            file_name="resume.pdf",
                            mime="application/pdf"
                        )
                finally:
                    # Clean up the PDF file
                    try:
                        os.unlink(pdf_path)
                    except:
                        pass
        with col2:
            if st.button("Suggest Improvements"):
                st.session_state.awaiting_improvement = True
                st.rerun()

    # 3. If user wants to suggest improvements
    if st.session_state.awaiting_improvement:
        st.subheader("Suggest Improvements to the Resume")
        user_feedback = st.text_area("Describe what you want to improve or change:")
        if st.button("Submit Improvements"):
            if not user_feedback.strip():
                st.warning("Please enter your suggestions.")
            else:
                # Add user feedback to context and re-call LLM
                context = st.session_state.llm_context or []
                context.append({"role": "user", "content": f"Please improve the previous resume suggestions based on this feedback: {user_feedback}"})
                with st.spinner("Regenerating suggestions with your feedback..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4-turbo-preview",
                            messages=context
                        )
                        llm_suggestions = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"Error from LLM: {str(e)}")
                        return
                # Update session state
                context.append({"role": "assistant", "content": llm_suggestions})
                st.session_state.llm_context = context
                st.session_state.llm_output = llm_suggestions
                st.session_state.awaiting_improvement = False
                st.rerun()


def main():
    if check_auth():
        resume_builder_page()
    else:
        st.warning("Please login to access this page.")

if __name__ == "__main__":
    main() 