import asyncio
from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_KEY, SCHEMA, RLS_POLICIES

async def init_database():
    """Initialize database schema and RLS policies"""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Create tables
    for table_name, schema in SCHEMA.items():
        try:
            # Execute raw SQL using rpc
            await client.rpc('exec_sql', {'query': schema})
            print(f"Created table: {table_name}")
        except Exception as e:
            print(f"Error creating table {table_name}: {str(e)}")
    
    # Apply RLS policies
    for table_name, policies in RLS_POLICIES.items():
        try:
            # Execute raw SQL using rpc
            await client.rpc('exec_sql', {'query': policies})
            print(f"Applied RLS policies for: {table_name}")
        except Exception as e:
            print(f"Error applying RLS policies for {table_name}: {str(e)}")
    
    # Create storage buckets if they don't exist
    try:
        await client.storage.create_bucket(
            id="resumes",
            options={"public": True, "file_size_limit": 52428800}  # 50MB limit
        )
        print("Created resumes bucket")
    except Exception as e:
        print(f"Error creating resumes bucket: {str(e)}")
    
    try:
        await client.storage.create_bucket(
            id="avatars",
            options={"public": True, "file_size_limit": 5242880}  # 5MB limit
        )
        print("Created avatars bucket")
    except Exception as e:
        print(f"Error creating avatars bucket: {str(e)}")

if __name__ == "__main__":
    asyncio.run(init_database()) 