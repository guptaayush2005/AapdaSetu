import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

try:
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), version();")
            result = cur.fetchone()

            print("DATABASE CONNECTION: SUCCESS")
            print("Database:", result[0])
            print("PostgreSQL:", result[1].split(",")[0])

except Exception as e:
    print("DATABASE CONNECTION: FAILED")
    print(e)
