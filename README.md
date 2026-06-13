# 📄 AI-Powered Resume Builder & ATS Optimizer

An advanced, end-to-end web application built with **Streamlit**, **Supabase**, and **OpenAI GPT-4o** designed to help job seekers create tailormade, professionally optimized resumes that pass Applicant Tracking Systems (ATS) and impress recruiters.

---

## 🌟 Key Features

*   **🔑 Google Authentication**: Secure sign-in using Streamlit's built-in OIDC authentication (Google Accounts).
*   **👤 Comprehensive Profile Manager**:
    *   Parse details directly from an existing PDF resume using AI.
    *   Fine-tune and edit your professional summary, work experience, projects, skills, education, certifications, and languages.
    *   Syncs all data in real-time with a remote database.
*   **🎯 Job-Specific Resume Customization**:
    *   Input a target job title, company name, and description.
    *   Generate a target resume using OpenAI GPT-4o optimized with relevant keywords and an appropriate professional tone.
    *   Edit generated resumes with an interactive feedback loop.
*   **📊 ATS Score & Compatibility Analyzer**:
    *   Upload any PDF resume against a job description.
    *   Get an overall compatibility score (out of 100).
    *   Receive a detailed breakdown (Keyword Match, Format, Content Relevance, Experience Alignment) alongside actionable suggestions for improvement.
*   **📚 Past Resumes & History**:
    *   Save and manage multiple resumes targeted at different roles.
    *   Render and download saved resumes as formatted PDFs on demand.
*   **🖨️ High-Fidelity PDF Generation**: Powered by Spire.Doc, converting optimized Markdown layouts into Word documents and saving them as clean, printable PDFs.

---

## 🛠️ Technology Stack

*   **Frontend & UI**: [Streamlit](https://streamlit.io/) (Python-based interactive web framework)
*   **Database & File Storage**: [Supabase](https://supabase.com/) (PostgreSQL with Row-Level Security, Supabase Storage)
*   **AI Orchestration**: [OpenAI API](https://openai.com/) (using GPT-4o for parsing, evaluation, and optimization)
*   **PDF Processing**: [PyPDF2](https://pypi.org/project/PyPDF2/) (text extraction) and [Spire.Doc for Python](https://www.e-iceblue.com/Introduce/spire-doc-python.html) (Markdown-to-PDF generation)
*   **OAuth Provider**: Google Identity Services

---

## 📂 Project Structure

```text
├── .streamlit/
│   └── secrets.toml          # Local Streamlit authentication secrets
├── modules/
│   ├── auth/
│   │   └── auth_utils.py     # Session authentication checks & decorators
│   ├── database/
│   │   ├── client.py         # Supabase database client wrapper
│   │   ├── config.py         # DB schema, configuration, and policies
│   │   └── init_db.py        # Database schema initialization script
│   └── utils/
│       └── ui_utils.py       # Custom UI components and layouts
├── pages/
│   ├── 0_Dashboard.py        # User home: metrics, resume history overview
│   ├── 1_Profile.py          # Resume parsing and profile management form
│   ├── 2_ATS_Score.py        # ATS compatibility scanner
│   ├── 3_Resume_Builder.py   # Job-tailored resume generation interface
│   └── 4_Past_Resumes.py     # Historical resumes collection and PDF downloads
├── app.py                    # Landing page and application entrypoint
├── requirements.txt          # Python dependencies
└── .env                      # Local environment configurations (ignored by git)
```

---

## 🚀 Local Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/rayansyed95/AI-Resume-Builder-FYP.git
cd AI-Resume-Builder-FYP
```

### 2. Configure Virtual Environment & Install Dependencies
```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Setup Supabase
1. Create a free account on [Supabase](https://supabase.com/).
2. Create a new project named `ai-resume-fyp`.
3. Open the **SQL Editor** in the Supabase Dashboard, create a new query, paste the contents of `modules/database/config.py` (or execute the script below), and click **Run**:
   ```sql
   create extension if not exists "uuid-ossp";

   -- Create Users table
   create table if not exists public.users (
       id text primary key,
       email text unique not null,
       full_name text,
       avatar_url text,
       created_at timestamp with time zone default now(),
       updated_at timestamp with time zone default now(),
       profile_data jsonb default '{}'::jsonb,
       preferences jsonb default '{}'::jsonb
   );

   -- Create Resumes table
   create table if not exists public.resumes (
       id uuid primary key default uuid_generate_v4(),
       user_id text references public.users(id) on delete cascade,
       title text not null,
       company text,
       job_description text,
       resume_content jsonb not null,
       ats_score integer,
       ats_analysis jsonb,
       format_type text,
       tone text,
       created_at timestamp with time zone default now(),
       updated_at timestamp with time zone default now(),
       is_template boolean default false,
       tags text[]
   );

   -- Create Resume Files table
   create table if not exists public.resume_files (
       id uuid primary key default uuid_generate_v4(),
       resume_id uuid references public.resumes(id) on delete cascade,
       file_path text not null,
       created_at timestamp with time zone default now()
   );

   -- Enable RLS
   alter table public.users enable row level security;
   alter table public.resumes enable row level security;
   alter table public.resume_files enable row level security;

   -- RLS Policies
   create policy "Users can view own data" on public.users for select using (true);
   create policy "Users can update own data" on public.users for update using (true);
   create policy "Users can view own resumes" on public.resumes for select using (true);
   create policy "Users can insert own resumes" on public.resumes for insert with check (true);
   create policy "Users can update own resumes" on public.resumes for update using (true);
   create policy "Users can delete own resumes" on public.resumes for delete using (true);
   create policy "Users can view own resume files" on public.resume_files for select using (true);
   create policy "Users can insert own resume files" on public.resume_files for insert with check (true);
   create policy "Users can delete own resume files" on public.resume_files for delete using (true);
   ```
4. Navigate to **Storage** on Supabase and create two **Public** buckets:
   * **`resumes`**
   * **`avatars`**

### 4. Configure Local Environment Variables
Create a file named `.env` in the project root:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-service-role-key
OPENAI_API_KEY=your-openai-api-key
```

### 5. Configure Local Authentication secrets
Create `.streamlit/secrets.toml`:
```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "your_random_cookie_secret_string"

[auth.google]
client_id = "your_google_client_id.apps.googleusercontent.com"
client_secret = "your_google_client_secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

### 6. Run the App
```bash
streamlit run app.py
```

---

## 🌐 Deployed Configuration (Streamlit Cloud)

When deploying to [Streamlit Community Cloud](https://share.streamlit.io/), configure your environment secrets directly within the Streamlit deployment settings:

1. In the Streamlit settings dashboard, go to the **Secrets** section.
2. Copy and paste all parameters from both your `.env` and `.streamlit/secrets.toml` files:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your-supabase-service-role-key"
   OPENAI_API_KEY = "your-openai-api-key"

   [auth]
   redirect_uri = "https://your-deployed-app-name.streamlit.app/oauth2callback"
   cookie_secret = "your_random_cookie_secret_string"

   [auth.google]
   client_id = "your_google_client_id.apps.googleusercontent.com"
   client_secret = "your_google_client_secret"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```
3. Update the **Authorized redirect URIs** in your **Google Cloud Console** under Credentials to match:
   `https://your-deployed-app-name.streamlit.app/oauth2callback`

---

## 🤝 Contributing & Support

1. Fork the Repository.
2. Create a Feature Branch (`git checkout -b feature/NewFeature`).
3. Commit changes (`git commit -m 'Add NewFeature'`).
4. Push to branch (`git push origin feature/NewFeature`).
5. Open a Pull Request.

For questions or details, connect with **Rayan Syed**:
*   [GitHub](https://github.com/rayansyed95)
*   [LinkedIn](https://www.linkedin.com/in/rayan-syed-866596253/)