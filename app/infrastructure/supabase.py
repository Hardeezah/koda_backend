import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "https://placeholder.supabase.co")
key: str = os.environ.get("SUPABASE_KEY", "placeholder")
service_role_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "placeholder")

supabase_instance: Optional[Client] = None
supabase_admin_instance: Optional[Client] = None

if url != "https://placeholder.supabase.co":
    if key != "placeholder":
        supabase_instance = create_client(url, key)
    if service_role_key != "placeholder":
        supabase_admin_instance = create_client(url, service_role_key)

def get_supabase() -> Client:
    if not supabase_instance:
        raise RuntimeError("Missing Supabase Configuration")
    return supabase_instance

def get_supabase_admin() -> Client:
    if not supabase_admin_instance:
        raise RuntimeError("Missing Supabase Service Role Configuration")
    return supabase_admin_instance
