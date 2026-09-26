"""
AapdaSetu - Multi-District Flood Dataset Generator
Generates realistic, physically consistent hydrological & meteorological data
for flood-prone regions across 10 Indian states and 40+ vulnerable districts.
"""

import os
import random
import numpy as np
import pandas as pd

# Fix random seed for reproducibility
np.random.seed(42)
random.seed(42)

DISTRICTS_DATA = [
    # Uttarakhand (Himalayan / Flash flood prone)
    {"state": "Uttarakhand", "district": "Chamoli", "river": "Alaknanda", "base_temp": 18, "elevation": "High", "flood_freq": 0.45},
    {"state": "Uttarakhand", "district": "Rudraprayag", "river": "Mandakini", "base_temp": 19, "elevation": "High", "flood_freq": 0.50},
    {"state": "Uttarakhand", "district": "Uttarkashi", "river": "Bhagirathi", "base_temp": 17, "elevation": "High", "flood_freq": 0.42},
    {"state": "Uttarakhand", "district": "Haridwar", "river": "Ganga", "base_temp": 26, "elevation": "Plains", "flood_freq": 0.35},
    {"state": "Uttarakhand", "district": "Dehradun", "river": "Rispana/Song", "base_temp": 24, "elevation": "Valley", "flood_freq": 0.30},
    {"state": "Uttarakhand", "district": "Pauri Garhwal", "river": "Nayyar", "base_temp": 20, "elevation": "Mid", "flood_freq": 0.38},

    # Himachal Pradesh (Cloudburst / High gradient rivers)
    {"state": "Himachal Pradesh", "district": "Kullu", "river": "Beas", "base_temp": 17, "elevation": "High", "flood_freq": 0.45},
    {"state": "Himachal Pradesh", "district": "Mandi", "river": "Beas", "base_temp": 20, "elevation": "Valley", "flood_freq": 0.48},
    {"state": "Himachal Pradesh", "district": "Shimla", "river": "Giri/Satluj", "base_temp": 16, "elevation": "High", "flood_freq": 0.30},
    {"state": "Himachal Pradesh", "district": "Kangra", "river": "Banganga", "base_temp": 22, "elevation": "Mid", "flood_freq": 0.35},
    {"state": "Himachal Pradesh", "district": "Kinnaur", "river": "Satluj", "base_temp": 14, "elevation": "High", "flood_freq": 0.40},

    # Assam (Brahmaputra Basin - Annual Severe Flooding)
    {"state": "Assam", "district": "Dhemaji", "river": "Brahmaputra", "base_temp": 27, "elevation": "Plains", "flood_freq": 0.60},
    {"state": "Assam", "district": "Barpeta", "river": "Brahmaputra", "base_temp": 28, "elevation": "Plains", "flood_freq": 0.58},
    {"state": "Assam", "district": "Morigaon", "river": "Kopili", "base_temp": 28, "elevation": "Plains", "flood_freq": 0.55},
    {"state": "Assam", "district": "Cachar", "river": "Barak", "base_temp": 27, "elevation": "Valley", "flood_freq": 0.50},
    {"state": "Assam", "district": "Kamrup", "river": "Brahmaputra", "base_temp": 29, "elevation": "Plains", "flood_freq": 0.45},
    {"state": "Assam", "district": "Dibrugarh", "river": "Brahmaputra", "base_temp": 26, "elevation": "Plains", "flood_freq": 0.52},

    # Bihar (Kosi / Gandak / Ganga River Floods)
    {"state": "Bihar", "district": "Patna", "river": "Ganga", "base_temp": 30, "elevation": "Plains", "flood_freq": 0.42},
    {"state": "Bihar", "district": "Darbhanga", "river": "Bagmati", "base_temp": 29, "elevation": "Plains", "flood_freq": 0.55},
    {"state": "Bihar", "district": "Muzaffarpur", "river": "Budhi Gandak", "base_temp": 29, "elevation": "Plains", "flood_freq": 0.52},
    {"state": "Bihar", "district": "Bhagalpur", "river": "Ganga", "base_temp": 30, "elevation": "Plains", "flood_freq": 0.46},
    {"state": "Bihar", "district": "Saharsa", "river": "Kosi", "base_temp": 28, "elevation": "Plains", "flood_freq": 0.60},
    {"state": "Bihar", "district": "Supaul", "river": "Kosi", "base_temp": 28, "elevation": "Plains", "flood_freq": 0.62},

    # Kerala (Western Ghats / Monsoonal Floods & Landslides)
    {"state": "Kerala", "district": "Wayanad", "river": "Kabini", "base_temp": 23, "elevation": "High", "flood_freq": 0.50},
    {"state": "Kerala", "district": "Idukki", "river": "Periyar", "base_temp": 22, "elevation": "High", "flood_freq": 0.52},
    {"state": "Kerala", "district": "Ernakulam", "river": "Periyar", "base_temp": 28, "elevation": "Coastal", "flood_freq": 0.40},
    {"state": "Kerala", "district": "Alappuzha", "river": "Pamba", "base_temp": 28, "elevation": "Low-lying", "flood_freq": 0.58},
    {"state": "Kerala", "district": "Kottayam", "river": "Meenachil", "base_temp": 27, "elevation": "Low-lying", "flood_freq": 0.45},

    # Maharashtra (Krishna & Coastal Konkan Basin)
    {"state": "Maharashtra", "district": "Kolhapur", "river": "Panchganga", "base_temp": 26, "elevation": "Mid", "flood_freq": 0.48},
    {"state": "Maharashtra", "district": "Sangli", "river": "Krishna", "base_temp": 28, "elevation": "Plains", "flood_freq": 0.45},
    {"state": "Maharashtra", "district": "Raigad", "river": "Savitri", "base_temp": 27, "elevation": "Coastal", "flood_freq": 0.46},
    {"state": "Maharashtra", "district": "Ratnagiri", "river": "Vashishti", "base_temp": 27, "elevation": "Coastal", "flood_freq": 0.44},
    {"state": "Maharashtra", "district": "Pune", "river": "Mutha/Mula", "base_temp": 25, "elevation": "Plateau", "flood_freq": 0.28},

    # Odisha (Mahanadi Delta / Cyclone Inundation)
    {"state": "Odisha", "district": "Puri", "river": "Bhargavi", "base_temp": 28, "elevation": "Coastal", "flood_freq": 0.48},
    {"state": "Odisha", "district": "Cuttack", "river": "Mahanadi", "base_temp": 29, "elevation": "Delta", "flood_freq": 0.46},
    {"state": "Odisha", "district": "Kendrapara", "river": "Brahmani", "base_temp": 28, "elevation": "Coastal", "flood_freq": 0.50},
    {"state": "Odisha", "district": "Balasore", "river": "Subarnarekha", "base_temp": 29, "elevation": "Coastal", "flood_freq": 0.45},

    # Gujarat (Narmada / Tapi Basin Floods)
    {"state": "Gujarat", "district": "Surat", "river": "Tapi", "base_temp": 30, "elevation": "Coastal", "flood_freq": 0.40},
    {"state": "Gujarat", "district": "Bharuch", "river": "Narmada", "base_temp": 31, "elevation": "Plains", "flood_freq": 0.38},
    {"state": "Gujarat", "district": "Vadodara", "river": "Vishwamitri", "base_temp": 31, "elevation": "Plains", "flood_freq": 0.42},
    {"state": "Gujarat", "district": "Navsari", "river": "Purna", "base_temp": 29, "elevation": "Coastal", "flood_freq": 0.36},

    # Uttar Pradesh (Ganga-Yamuna-Ghaghra Confluence)
    {"state": "Uttar Pradesh", "district": "Varanasi", "river": "Ganga", "base_temp": 30, "elevation": "Plains", "flood_freq": 0.38},
    {"state": "Uttar Pradesh", "district": "Prayagraj", "river": "Ganga/Yamuna", "base_temp": 31, "elevation": "Plains", "flood_freq": 0.35},
    {"state": "Uttar Pradesh", "district": "Gorakhpur", "river": "Rapti", "base_temp": 29, "elevation": "Plains", "flood_freq": 0.52},
    {"state": "Uttar Pradesh", "district": "Ballia", "river": "Ganga/Ghaghra", "base_temp": 29, "elevation": "Plains", "flood_freq": 0.48}
]

RECORDS_PER_DISTRICT = 36  # 45 districts * 36 records = 1620 records


def generate_dataset():
    records = []

    for d in DISTRICTS_DATA:
        state = d["state"]
        district = d["district"]
        base_temp = d["base_temp"]
        flood_freq = d["flood_freq"]

        # Standard river levels for this basin
        warning_level = round(random.uniform(2.0, 3.5), 2)
        danger_level = round(warning_level + random.uniform(0.4, 0.8), 2)
        res_danger_level = round(random.uniform(150.0, 300.0), 1)

        for _ in range(RECORDS_PER_DISTRICT):
            # Determine scenario: normal (50%), monsoon/moderate (30%), severe storm/cloudburst (20%)
            scenario_prob = random.random()

            if scenario_prob < (1.0 - flood_freq):
                # Normal / Mild rainfall scenario
                rainfall_1h = round(np.random.gamma(shape=1.5, scale=1.5), 1)
                rainfall_6h = round(rainfall_1h * random.uniform(2.0, 3.8) + random.uniform(0, 5), 1)
                rainfall_24h = round(rainfall_6h * random.uniform(2.0, 3.2) + random.uniform(0, 10), 1)
                rainfall_72h = round(rainfall_24h * random.uniform(1.4, 2.0) + random.uniform(0, 15), 1)

                temp = round(base_temp + random.uniform(-2, 4), 1)
                humidity = round(random.uniform(55, 80), 1)
                wind = round(random.uniform(6, 18), 1)

                river_level = round(random.uniform(0.5, warning_level - 0.2), 2)
                res_level = round(res_danger_level * random.uniform(0.40, 0.75), 1)

            elif scenario_prob < (1.0 - flood_freq * 0.35):
                # Moderate Monsoon / Heavy Rains Scenario
                rainfall_1h = round(np.random.gamma(shape=3.5, scale=2.5), 1)
                rainfall_6h = round(rainfall_1h * random.uniform(3.0, 4.5) + random.uniform(10, 25), 1)
                rainfall_24h = round(rainfall_6h * random.uniform(2.2, 3.5) + random.uniform(20, 45), 1)
                rainfall_72h = round(rainfall_24h * random.uniform(1.5, 2.2) + random.uniform(30, 60), 1)

                temp = round(base_temp - random.uniform(0, 3), 1)
                humidity = round(random.uniform(80, 92), 1)
                wind = round(random.uniform(15, 32), 1)

                # River around warning level
                river_level = round(random.uniform(warning_level - 0.2, danger_level + 0.1), 2)
                res_level = round(res_danger_level * random.uniform(0.72, 0.92), 1)

            else:
                # Severe Storm / Cloudburst / Flash Flood Scenario
                rainfall_1h = round(random.uniform(18.0, 65.0), 1)
                rainfall_6h = round(rainfall_1h * random.uniform(3.5, 5.2) + random.uniform(30, 70), 1)
                rainfall_24h = round(rainfall_6h * random.uniform(2.0, 3.2) + random.uniform(60, 140), 1)
                rainfall_72h = round(rainfall_24h * random.uniform(1.4, 2.0) + random.uniform(80, 180), 1)

                temp = round(base_temp - random.uniform(2, 5), 1)
                humidity = round(random.uniform(88, 98), 1)
                wind = round(random.uniform(25, 65), 1)

                # River exceeding danger mark
                river_level = round(danger_level + random.uniform(0.05, 1.40), 2)
                res_level = round(res_danger_level * random.uniform(0.92, 1.08), 1)

            # Cap reasonable ranges
            rainfall_1h = max(0.0, rainfall_1h)
            rainfall_6h = max(rainfall_1h, rainfall_6h)
            rainfall_24h = max(rainfall_6h, rainfall_24h)
            rainfall_72h = max(rainfall_24h, rainfall_72h)

            # Calculate deterministic Ground Truth Risk (0: Low, 1: Moderate, 2: High)
            risk_score = 0

            # 24h rainfall factor
            if rainfall_24h >= 120:
                risk_score += 3
            elif rainfall_24h >= 75:
                risk_score += 2
            elif rainfall_24h >= 45:
                risk_score += 1

            # 72h accumulation factor
            if rainfall_72h >= 240:
                risk_score += 2
            elif rainfall_72h >= 140:
                risk_score += 1

            # River level vs danger factor (strongest hydrological driver)
            if river_level >= danger_level:
                risk_score += 4
            elif river_level >= warning_level:
                risk_score += 2

            # Reservoir overflow risk
            if res_level >= res_danger_level:
                risk_score += 2
            elif res_level >= (res_danger_level * 0.88):
                risk_score += 1

            # Atmospheric moisture & 1h burst
            if rainfall_1h >= 25.0:  # Cloudburst threshold (>25mm/hr)
                risk_score += 2
            if humidity >= 90.0:
                risk_score += 1

            if risk_score >= 6:
                flood_risk = 2  # High Risk / Disaster Alert
            elif risk_score >= 3:
                flood_risk = 1  # Moderate Risk / Warning
            else:
                flood_risk = 0  # Low Risk / Safe

            records.append({
                "state": state,
                "district": district,
                "rainfall_1h": rainfall_1h,
                "rainfall_6h": rainfall_6h,
                "rainfall_24h": rainfall_24h,
                "rainfall_72h": rainfall_72h,
                "temperature": temp,
                "humidity": humidity,
                "wind_speed": wind,
                "river_level": river_level,
                "danger_level": danger_level,
                "warning_level": warning_level,
                "reservoir_level": res_level,
                "reservoir_danger_level": res_danger_level,
                "flood_risk": flood_risk
            })

    df = pd.DataFrame(records)

    # Save to root and data/ directory
    os.makedirs("data", exist_ok=True)
    df.to_csv("training_data.csv", index=False)
    df.to_csv("data/flood_dataset.csv", index=False)

    print("=" * 60)
    print("AAPDASETU FLOOD DATASET GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Total Records: {len(df)}")
    print(f"Unique States: {df['state'].nunique()}")
    print(f"Unique Districts: {df['district'].nunique()}")
    print("\nRisk Class Distribution:")
    print(df["flood_risk"].value_counts().rename({0: "0 (Low Risk)", 1: "1 (Moderate)", 2: "2 (High Risk)"}))
    print("\nSample Data:")
    print(df[["state", "district", "rainfall_24h", "river_level", "danger_level", "flood_risk"]].head(10))
    print("=" * 60)

    return df


if __name__ == "__main__":
    generate_dataset()
