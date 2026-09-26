import os
# pyrefly: ignore [missing-import]
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT state, district, rainfall_24h, rainfall_72h
            FROM weather_data
            ORDER BY id;
        """)

        rows = cur.fetchall()

        print("\nWEATHER DATA")
        print("-" * 60)

        for row in rows:
            print(row)

        print("\nTOTAL RECORDS:", len(rows))
