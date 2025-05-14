import streamlit as st
from modules.auth.auth_utils import check_auth
from modules.database.client import db
from modules.utils.ui_utils import display_user_header
from spire.doc import *
from spire.doc.common import *
import tempfile
import os

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

def past_resumes_page():
    """Display the past resumes page."""
    # Display user header
    display_user_header()
    
    st.title("Your Resumes")
    
    # Get user ID
    user = st.experimental_user
    if not user or not user.is_logged_in:
        st.warning("Please login to access this page.")
        return
    user_id = getattr(user, "sub", None)
    
    # Get user's resumes from database
    resumes = db.get_user_resumes(user_id)
    
    if not resumes:
        st.info("You haven't created any resumes yet. Go to the Resume Builder to create your first resume!")
        return
    
    # Display resumes
    for resume in resumes:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(resume.get("title", "Untitled Resume"))
                st.text(f"Company: {resume.get('company', 'N/A')}")
                st.text(f"Format: {resume.get('format_type', 'N/A')}")
                st.text(f"Created: {resume.get('created_at', 'N/A')}")
            
            with col2:
                if st.button("Download", key=f"download_{resume.get('id', '')}"):
                    with st.spinner("Generating PDF..."):
                        try:
                            # Generate PDF from markdown content
                            pdf_path = markdown_to_pdf_spire(resume.get('resume_content', ''))
                            
                            # Show download button
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="Click to Download",
                                    data=f.read(),
                                    file_name=f"{resume.get('title', 'resume')}.pdf",
                                    mime="application/pdf",
                                    key=f"download_btn_{resume.get('id', '')}"
                                )
                        finally:
                            # Clean up the PDF file
                            try:
                                os.unlink(pdf_path)
                            except:
                                pass

def main():
    if check_auth():
        past_resumes_page()
    else:
        st.warning("Please login to access this page.")

if __name__ == "__main__":
    main() 