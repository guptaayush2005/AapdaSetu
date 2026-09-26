from dotenv import load_dotenv
import os
import psycopg

load_dotenv()

conn = psycopg.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

updates = {
    "Kullu": 2.3,
    "Mandi": 1.8,
    "Chamoli": 2.1,
    "Rudraprayag": 2.4,
    "Uttarkashi": 1.6
}

for district, level in updates.items():
    cur.execute(
        "UPDATE rivers SET river_level = %s WHERE district = %s",
        (level, district)
    )

conn.commit()

print("Demo river data updated successfully!")

cur.close()
conn.close()
