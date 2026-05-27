import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("DATABASE_URL is not set.")
    exit(1)

try:
    print(f"Connecting to database...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()

    alter_sql = """
    ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS business_name TEXT,
    ADD COLUMN IF NOT EXISTS business_type TEXT,
    ADD COLUMN IF NOT EXISTS trade_type TEXT,
    ADD COLUMN IF NOT EXISTS primary_category TEXT,
    ADD COLUMN IF NOT EXISTS sub_categories TEXT[],
    ADD COLUMN IF NOT EXISTS target_countries TEXT[],
    ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;
    
    -- Reload Supabase postgrest schema cache
    NOTIFY pgrst, 'reload schema';
    """
    
    print("Executing ALTER TABLE and NOTIFY pgrst...")
    cursor.execute(alter_sql)
    print("Schema updated successfully!")
    
    cursor.close()
    conn.close()

except Exception as e:
    print(f"An error occurred: {e}")
