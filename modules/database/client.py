from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY, RESUME_BUCKET, AVATAR_BUCKET
from typing import Dict, List, Optional, Any
import json

class DatabaseClient:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    def get_user(self, user_id: str = None, email: str = None) -> Optional[Dict]:
        """Get user data by ID or email"""
        try:
            if user_id:
                response = self.client.table('users').select('*').eq('id', str(user_id)).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
            if email:
                response = self.client.table('users').select('*').eq('email', email).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None
        
    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user record"""
        try:
            # Ensure id is present and is a string
            if 'id' not in user_data or not user_data['id']:
                raise ValueError("User ID is required for creating a user record")
            
            # Convert id to string
            user_data['id'] = str(user_data['id'])
            
            # Extract full_name and avatar_url from profile_data if they exist
            if 'profile_data' in user_data and 'basics' in user_data['profile_data']:
                basics = user_data['profile_data']['basics']
                user_data['full_name'] = basics.get('fullName')
                user_data['avatar_url'] = basics.get('avatar_url')
            
            # Remove created_at as it's handled by Supabase
            if 'created_at' in user_data:
                del user_data['created_at']
            
            # Debug the data being sent
            print("Debug - Creating user with data:", user_data)
            
            # Insert the user
            response = self.client.table('users').insert(user_data).execute()
            
            if not response.data:
                raise Exception("No data returned from insert operation")
                
            return response.data[0]
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            raise
        
    def update_user(self, user_id: str, data: Dict) -> Dict:
        """Update user data"""
        try:
            # Extract full_name and avatar_url from profile_data if they exist
            if 'profile_data' in data and 'basics' in data['profile_data']:
                basics = data['profile_data']['basics']
                data['full_name'] = basics.get('fullName')
                data['avatar_url'] = basics.get('avatar_url')
            
            response = self.client.table('users').update(data).eq('id', str(user_id)).execute()
            if not response.data:
                raise Exception("No data returned from update operation")
            return response.data[0]
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            raise
        
    def create_resume(self, user_id: str, data: Dict) -> Dict:
        """Create a new resume"""
        resume_data = {
            'user_id': user_id,
            'title': data.get('title', 'Untitled Resume'),
            'company': data.get('company'),
            'job_description': data.get('job_description'),
            'resume_content': data.get('resume_content', {}),
            'format_type': data.get('format_type', 'professional'),
            'tone': data.get('tone', 'professional'),
            'tags': data.get('tags', [])
        }
        response = self.client.table('resumes').insert(resume_data).execute()
        return response.data[0] if response.data else None
        
    def get_resume(self, resume_id: str) -> Optional[Dict]:
        """Get resume by ID"""
        response = self.client.table('resumes').select('*').eq('id', resume_id).single().execute()
        if response.data and isinstance(response.data, list):
            return response.data[0]
        elif response.data:
            return response.data
        return None
        
    def get_user_resumes(self, user_id: str) -> List[Dict]:
        """Get all resumes for a user"""
        response = self.client.table('resumes').select('*').eq('user_id', user_id).execute()
        return response.data if response.data else []
        
    def update_resume(self, resume_id: str, data: Dict) -> Dict:
        """Update resume data"""
        response = self.client.table('resumes').update(data).eq('id', resume_id).execute()
        return response.data[0] if response.data else None
        
    def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume"""
        response = self.client.table('resumes').delete().eq('id', resume_id).execute()
        return bool(response.data)
        
    def upload_resume_file(self, resume_id: str, file_path: str, file_data: bytes) -> str:
        """Upload resume file to storage"""
        file_name = f"{resume_id}/{file_path}"
        self.client.storage.from_(RESUME_BUCKET).upload(file_name, file_data)
        # Create file record
        self.client.table('resume_files').insert({
            'resume_id': resume_id,
            'file_path': file_name
        }).execute()
        return file_name
        
    def get_resume_file_url(self, file_path: str) -> str:
        """Get public URL for resume file"""
        response = self.client.storage.from_(RESUME_BUCKET).get_public_url(file_path)
        return response
        
    def upload_avatar(self, user_id: str, file_data: bytes) -> str:
        """Upload user avatar"""
        file_name = f"{user_id}/avatar"
        self.client.storage.from_(AVATAR_BUCKET).upload(file_name, file_data)
        return file_name
        
    def get_avatar_url(self, file_path: str) -> str:
        """Get public URL for avatar"""
        response = self.client.storage.from_(AVATAR_BUCKET).get_public_url(file_path)
        return response
        
    def update_ats_analysis(self, resume_id: str, score: int, analysis: Dict) -> Dict:
        """Update ATS score and analysis for a resume"""
        data = {
            'ats_score': score,
            'ats_analysis': analysis
        }
        response = self.client.table('resumes').update(data).eq('id', resume_id).execute()
        return response.data[0] if response.data else None

# Create a singleton instance
db = DatabaseClient() 