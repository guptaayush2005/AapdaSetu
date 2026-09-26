# 🚨 AapdaSetu (आपदा सेतु)
### AI-Powered Multi-Hazard Early Warning, Evacuation Routing & Emergency Response Platform

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Status](https://img.shields.io/badge/Deployment-Ready-brightgreen.svg)
![Version](https://img.shields.io/badge/Version-2.5.0-orange.svg)

**AapdaSetu** is a next-generation disaster management and flood early warning system designed for Indian disaster response teams (NDRF/SDRF), state authorities, and citizens. It delivers real-time hazard analytics, AI-driven flood prediction, safe evacuation navigation, and 1-Click SOS rescue alerts.

---

## 🌟 Key Features

- **🗺️ Interactive Safe Evacuation Routes**: Real-time obstacle-aware route calculations guiding citizens away from inundated zones to nearest relief shelters.
- **🚨 1-Click Emergency SOS ("Mai Khatre Me Hu")**:
  - Instant WhatsApp alert pre-filled with live GPS coordinates & Google Maps link.
  - One-tap 112 emergency calling and SMS dispatch.
  - Audio siren alert and pulsing visual rescue beacons on live operational maps.
- **🌊 Hyperlocal River & Dam Telemetry**: Real-time river monitoring across major basins (Ganga, Yamuna, Brahmaputra, Godavari, Kosi).
- **🤖 AI Multi-Hazard Risk Engine**: Pre-trained machine learning models for Flash Flood, Riverine Inundation, and Landslide probability estimation.
- **🌐 Multilingual Support**: Instant localization in **English**, **हिन्दी (Hindi)**, and **Hinglish**.
- **🏕️ Safe Relief Shelters**: Directory with real-time occupancy status, food/medical provisions, and contact details.
- **🛡️ National Operations Command (Admin Dashboard)**: Centralized coordination interface for disaster response units.

---

## 🚀 Live Deployment on Vercel

The frontend is ready for instant 1-click deployment on **Vercel**:

1. Push this repository to your GitHub account.
2. Visit [Vercel Dashboard](https://vercel.com/new).
3. Import the `AapdaSetu` repository.
4. Keep the Framework Preset as **Other** (Root directory `./`).
5. Click **Deploy**!

> `vercel.json` is pre-configured with URL rewrites to route requests directly to `/frontend`.

---

## 💻 Local Development Setup

### 1. Frontend
You can serve the frontend with any static HTTP server or Live Server:
```bash
# Using Python built-in server
python -m http.server 3000

# Open in browser:
# http://localhost:3000/frontend/index.html
```

### 2. Backend (FastAPI Risk Engine)
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt # or install fastapi uvicorn
uvicorn main:app --reload --port 8000
```

---

## 📂 Project Architecture

```
AapdaSetu/
├── frontend/
│   ├── index.html            # Main platform dashboard
│   ├── safe-route.html       # Safe evacuation routes & 1-Click SOS
│   ├── monitoring.html       # Live river & dam telemetry
│   ├── rescue.html           # Emergency rescue request hub
│   ├── emergency.html        # Emergency contacts & helplines
│   ├── shelters.html         # Relief camps & shelter locator
│   ├── alerts.html           # Hyperlocal hazard bulletins
│   ├── weather.html          # Meteorological Doppler radar
│   ├── prediction.html       # AI hazard probability engine
│   ├── community.html        # Community citizen reports
│   ├── donation.html         # Relief fund donation portal
│   ├── admin.html            # National Operations Center
│   ├── app.js                # Core frontend controller & 1-Click SOS
│   ├── style.css             # Glassmorphism & responsive design system
│   └── translations.js       # Multilingual dictionary (EN, HI, Hinglish)
├── backend/                  # FastAPI prediction & telemetry services
├── vercel.json               # Vercel deployment & routing configuration
├── .gitignore                # Git exclusions
└── README.md
```

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
