# Resume Builder with ATS Optimization

A Streamlit application that helps users create ATS-optimized resumes and track their application progress.

## Features

- Resume Builder with AI-powered suggestions
- ATS Score Analysis
- Profile Management
- Resume History Tracking
- PDF Export

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

## Deployment on Streamlit Cloud

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and connect your repository
4. Add your environment variables in the Streamlit Cloud dashboard
5. Deploy!

## Local Development

Run the app locally:
```bash
streamlit run app.py
```

## Project Structure

- `app.py`: Main application entry point
- `pages/`: Streamlit pages
  - `0_Dashboard.py`: Main dashboard
  - `1_Profile.py`: Profile management
  - `2_ATS_Score.py`: ATS score analysis
  - `3_Resume_Builder.py`: Resume creation
  - `4_Past_Resumes.py`: Resume history
- `modules/`: Core functionality
  - `auth/`: Authentication utilities
  - `database/`: Database operations
  - `utils/`: Utility functions