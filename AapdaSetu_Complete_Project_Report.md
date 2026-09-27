# 🚨 AapdaSetu (आपदासेतु) — Comprehensive Architecture & Technical Report

> **AI-Powered Multi-Hazard Disaster Response, Flash Flood Early Warning, and Dam Telemetry Platform**  
> *Official Technical Documentation for System Engineers, Authorities & Evaluators*  
> **Live Production Portal**: [https://aapda-setu-one.vercel.app](https://aapda-setu-one.vercel.app)

---

## 🎯 1. Executive Summary & Problem Statement

**AapdaSetu** Bharat ka ek samarpit **AI-Powered Multi-Hazard Disaster Response & Early Warning Platform** hai. Yeh platform Himalayan cloudbursts, flash floods (Mandakini, Alaknanda, Beas), perennial river basin overflows (Kosi, Brahmaputra), mountain landslides (Wayanad, Chamoli), aur dam reservoir spillway discharges ke dauran aam nagrikon aur disaster management authorities (NDRF, SDRF, District Magistrates) ke beech ek vital digital bridge banata hai.

### The Dual Core Mission
1. **Citizens (Aam Nagrik)**: Instant hyper-local early warnings, 1-Click offline rescue dispatch, safe bypass evacuation routes, and private evacuation vehicle bookings in 31 regional languages.
2. **Authorities (EOC / District Magistrate)**: Centralized Incident Operations Center, river hydrology gauges, citizen hazard moderation, and automated multi-channel Dam Release sirens.

---

## 🛰️ 2. Data Flow Architecture & Data Sources

AapdaSetu ka data engine **5 mukhya streams (sources)** ko merge karke real-time risk assessment tayyar karta hai:

```
+-----------------------------------------------------------------------------------+
|                            AAPDASETU DATA ENGINE MATRIX                           |
+-----------------------------------------------------------------------------------+
                                          |
    +-------------------------------------+-----------------------------------+
    |                                     |                                   |
    v                                     v                                   v
[1. Weather & Precipitation]   [2. River & Dam Telemetry]      [3. Machine Learning AI]
* Open-Meteo GFS Precipitation * 18 Major Indian Rivers         * 3 Trained XGBoost Models
* ERA5 Satellite Soil Moisture * 6 Mega Reservoirs (Tehri, etc) * Slope Angle & Elevation DEM
* Current Rain Rate (mm/h)     * Central Water Commission Marks * Multi-hazard Lead Time (h)
    |                                     |                                   |
    +-------------------------------------+-----------------------------------+
                                          |
    +-------------------------------------+-----------------------------------+
    |                                                                         |
    v                                                                         v
[4. Crowdsourced Citizen Ground Reports]                  [5. Emergency Sirens & Dispatch]
* Citizen Geo-tagged Hazard Uploads                       * Web3Forms & SMTP to DM Ayush Gupta
* EOC Verification Pipeline (Pending -> Approved)         * Web Speech API Multi-lingual Siren
* Real-time Public Disaster Feed Sync                     * Universal Smart 112 Helpline
```

### Data Sources Breakdown Table

| Data Stream | Primary Source & API | Key Telemetry Attributes | Impact on Platform |
| :--- | :--- | :--- | :--- |
| **Precipitation & Weather** | Open-Meteo Live API / IMD Models | Rainfall 24h/72h (mm), Rate (mm/h), Wind, Humidity | Triggers early flash flood accumulation index |
| **Soil Moisture Saturation** | ERA5-Land Satellite (0-10cm depth) | Soil Saturation Percentage (0% to 100%) | Crucial: 90%+ saturation causes immediate runoff |
| **River Hydrological Gauges** | Central Water Commission (CWC) Grid | Current Level (m), Warning Level (m), Danger Mark (m) | Breach of Danger mark triggers emergency DM bulletin |
| **Reservoirs & Dams** | State Hydro Control Rooms | Current Inflow, Reservoir Capacity %, Gate Count | Automated downstream warning broadcast |
| **Citizen Hazard Reports** | Ground-Zero Citizen Submissions | Location, Severity, Hazard Category, Photos | Moderated by EOC Admin before public map display |

---

## 🏗️ 3. Dam Gate Release & Downstream Siren System

Jab pahaadon me musladhar barish hoti hai aur reservoir capacity 85%-90% cross karti hai, tab dam control authorities ko spillway gates kholne padte hain. Yeh paani downstream bastiyon me achanak baadh laa sakta hai.

### 6 Monitored Mega Reservoirs in AapdaSetu
1. **Tehri Dam Reservoir** (Uttarakhand) — Max: 830m | Danger: 828m | Rivers: Bhagirathi & Bhilangna
2. **Bhakra Nangal Dam** (Himachal Pradesh) — Max: 1680m | Danger: 1675m | River: Satluj
3. **Idukki Arch Dam** (Kerala) — Max: 2403m | Danger: 2400m | River: Periyar
4. **Radhanagari Dam** (Maharashtra) — Max: 350m | Danger: 348m | River: Bhogawati
5. **Hirakud Reservoir** (Odisha) — Max: 630m | Danger: 628m | River: Mahanadi
6. **Sardar Sarovar Dam** (Gujarat) — Max: 138.6m | Danger: 137m | River: Narmada

### Broadcast Workflow Process:
1. **Authority Triggers Broadcast**: Admin panel (`admin.html`) par jakar Dam select hota hai, discharge volume (e.g. `45,000 Cusecs`), gates opened (e.g. `4 Gates`), aur downstream travel ETA (e.g. `2.5 Hours to Haridwar`) enter kiya jata hai.
2. **Cross-Tab Instant Synchronisation**: LocalStorage aur backend websockets ke zariye 500 millisecond ke andar platform ke sabhi active tabs par ek flashing red emergency banner active ho jata hai.
3. **Multi-Lingual Audio Siren**: Web Speech API downstream nagrikon ko unki chuni hui bhasha me loud audio warning sunata hai taaki nadi kinare se turant door hat sakein.
4. **Authority Notification**: District Magistrate aur SDRF command units ko instant email alert chala jata hai.

---

## 🤖 4. AI / Machine Learning Multi-Hazard Classifier

AapdaSetu me 3 alag-alag trained XGBoost models hain jo `backend/multi_source_risk_engine.py` me load hote hain:

| Model File | Hazard Specialty | Primary Trigger Conditions |
| :--- | :--- | :--- |
| `xgboost_flood_model.json` | Riverine Lowland Flooding | Prolonged 72h rainfall, river gauge breach |
| `xgboost_flash_flood_model.json` | Himalayan Flash Floods | Short intense cloudburst (>30mm/h), 90%+ soil saturation |
| `xgboost_landslide_model.json` | Debris Slips & Mountain Collapse | Steep slope angle (>28°), soil waterlogging in mountain strata |

### Multi-Factor Risk Calculation Matrix
$$\text{Risk Score} = (\text{Rainfall Dynamics} \times 0.38) + (\text{Soil Moisture} \times 0.26) + (\text{Slope Angle} \times 0.22) + (\text{River Gauge} \times 0.14)$$

---

## 🛡️ 5. Citizen Rescue, Private Vehicles & Helpline Dialer

### A. Smart Emergency Helpline System (Mobile vs Desktop)
* **On Mobile Devices**: 112, 1078, 1070 par tap karte hi native dialer khulta hai.
* **On Laptops / Computers**: Dead click ke bajaye ek interactive **Helpline Assistant Modal** khulta hai jisme **⚡ 1-Click Online SOS** button hota hai jo bina phone call ke live GPS coordinates NDRF ko dispatch kar deta hai!

### B. Private Evacuation Vehicle Booking (Cab Fleet)
Sarkari rescue buses ke alawa, agar nagrik ko private vehicle chahiye, to wo `rescue.html` se 4x4 Offroad SUV, Private Cab ya Mini-Bus book kar sakta hai. Yeh request seedhe Admin EOC ke **Private Vehicle Hub** me aati hai jaha se authority driver assign karti hai.

### C. Community Hazard Moderation Pipeline
Fake news aur rumors rokne ke liye, nagrik dwara dali gayi koi bhi report pehle `PENDING` status me EOC Admin ke pas aati hai. Admin ke **"Approve & Publish to Map"** click karne ke baad hi wo public feed aur map par live dikhti hai.

---

## 📶 6. Offline / Remote Disaster Resilience (Fail-Safe Architecture)

1. **LocalStorage Persistence**: Sabhi rescue tickets, reports aur dam alerts offline browser storage me secure rehte hain.
2. **Client-Side Terrain Simulation**: Agar backend offline ho, to browser high-fidelity client simulation se terrain slope aur historical rainfall data ke aadhar par calculation continue rakhta hai.
3. **31 Indian Regional Languages**: English, Hindi, Hinglish ke alawa 22 Scheduled languages aur regional disaster dialects (Garhwali, Kumaoni, Bhojpuri, Haryanvi, etc.) support karta hai.

---
*© 2026 AapdaSetu Foundation. Dedicated to AI-powered disaster preparedness, mitigation, and life-saving technology across India.*
