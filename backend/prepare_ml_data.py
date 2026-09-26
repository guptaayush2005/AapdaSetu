import pandas as pd

df = pd.read_csv("training_data.csv")

def calculate_risk(row):
    score = 0

    if row["rainfall_24h"] >= 100:
        score += 2
    elif row["rainfall_24h"] >= 75:
        score += 1

    if row["rainfall_72h"] >= 200:
        score += 2
    elif row["rainfall_72h"] >= 150:
        score += 1

    if row["river_level"] >= row["danger_level"]:
        score += 2
    elif row["river_level"] >= row["warning_level"]:
        score += 1

    if row["humidity"] >= 90:
        score += 1

    if score >= 5:
        return 2
    elif score >= 3:
        return 1
    else:
        return 0

df["flood_risk"] = df.apply(calculate_risk, axis=1)

df.to_csv("training_data.csv", index=False)

print("TARGET COLUMN ADDED")
print(df[["state", "district", "rainfall_24h", "rainfall_72h", "river_level", "flood_risk"]])
