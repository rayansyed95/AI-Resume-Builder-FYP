import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Storage Configuration
RESUME_BUCKET = "resumes"
AVATAR_BUCKET = "avatars"

# Database Schema
SCHEMA = {
    "users": """
        create table if not exists public.users (
            id uuid primary key default uuid_generate_v4(),
            email text unique not null,
            full_name text,
            avatar_url text,
            created_at timestamp with time zone default now(),
            updated_at timestamp with time zone default now(),
            profile_data jsonb default '{}'::jsonb,
            preferences jsonb default '{}'::jsonb
        );
    """,
    "resumes": """
        create table if not exists public.resumes (
            id uuid primary key default uuid_generate_v4(),
            user_id uuid references public.users(id) on delete cascade,
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
    """,
    "resume_files": """
        create table if not exists public.resume_files (
            id uuid primary key default uuid_generate_v4(),
            resume_id uuid references public.resumes(id) on delete cascade,
            file_path text not null,
            created_at timestamp with time zone default now()
        );
    """
}

# RLS Policies
RLS_POLICIES = {
    "users": """
        alter table public.users enable row level security;
        
        create policy "Users can view own data"
            on public.users for select
            using (auth.uid() = id);
            
        create policy "Users can update own data"
            on public.users for update
            using (auth.uid() = id);
    """,
    "resumes": """
        alter table public.resumes enable row level security;
        
        create policy "Users can view own resumes"
            on public.resumes for select
            using (auth.uid() = user_id);
            
        create policy "Users can insert own resumes"
            on public.resumes for insert
            with check (auth.uid() = user_id);
            
        create policy "Users can update own resumes"
            on public.resumes for update
            using (auth.uid() = user_id);
            
        create policy "Users can delete own resumes"
            on public.resumes for delete
            using (auth.uid() = user_id);
    """,
    "resume_files": """
        alter table public.resume_files enable row level security;
        
        create policy "Users can view own resume files"
            on public.resume_files for select
            using (exists (
                select 1 from public.resumes
                where resumes.id = resume_files.resume_id
                and resumes.user_id = auth.uid()
            ));
            
        create policy "Users can insert own resume files"
            on public.resume_files for insert
            with check (exists (
                select 1 from public.resumes
                where resumes.id = resume_files.resume_id
                and resumes.user_id = auth.uid()
            ));
            
        create policy "Users can delete own resume files"
            on public.resume_files for delete
            using (exists (
                select 1 from public.resumes
                where resumes.id = resume_files.resume_id
                and resumes.user_id = auth.uid()
            ));
    """
} 