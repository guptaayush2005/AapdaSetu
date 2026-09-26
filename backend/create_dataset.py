import os
import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

query = """
SELECT
    w.state,
    w.district,
    w.rainfall_1h,
    w.rainfall_6h,
    w.rainfall_24h,
    w.rainfall_72h,
    w.temperature,
    w.humidity,
    w.wind_speed,
    r.river_level,
    r.danger_level,
    r.warning_level,
    res.current_level AS reservoir_level,
    res.danger_level AS reservoir_danger_level
FROM weather_data w
LEFT JOIN rivers r
    ON w.state = r.state
    AND w.district = r.district
LEFT JOIN reservoirs res
    ON w.state = res.state
    AND w.district = res.district
ORDER BY w.id;
"""

with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    df = pd.read_sql(query, conn)

df.to_csv("training_data.csv", index=False)

print("ML DATASET CREATED")
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("\nColumns:")
print(df.columns.tolist())
print("\nDataset:")
print(df)
