"""
AapdaSetu - PostgreSQL Database Seeder
Populates comprehensive, realistic disaster relief data matching existing schema:
- Locations (45 districts across 9 states)
- Real-time weather stations
- River monitoring gauges
- Reservoirs & Dams
- Safe Shelters with GPS coordinates & amenities
- Historical & active flood alerts
- Citizen community incident reports
- Relief donations
"""

import os
from datetime import datetime
import psycopg
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv("backend/.env")

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL is not set.")

LOCATIONS_DATA = [
    # Uttarakhand
    ("Uttarakhand", "Chamoli", 30.2937, 79.5603),
    ("Uttarakhand", "Rudraprayag", 30.2844, 78.9811),
    ("Uttarakhand", "Uttarkashi", 30.7268, 78.4354),
    ("Uttarakhand", "Haridwar", 29.9457, 78.1642),
    ("Uttarakhand", "Dehradun", 30.3165, 78.0322),
    ("Uttarakhand", "Pauri Garhwal", 30.1500, 78.7800),

    # Himachal Pradesh
    ("Himachal Pradesh", "Kullu", 31.9579, 77.1095),
    ("Himachal Pradesh", "Mandi", 31.7087, 76.9320),
    ("Himachal Pradesh", "Shimla", 31.1048, 77.1734),
    ("Himachal Pradesh", "Kangra", 32.0998, 76.2691),
    ("Himachal Pradesh", "Kinnaur", 31.6510, 78.4752),

    # Assam
    ("Assam", "Dhemaji", 27.4812, 94.5583),
    ("Assam", "Barpeta", 26.3216, 91.0064),
    ("Assam", "Morigaon", 26.2503, 92.3421),
    ("Assam", "Cachar", 24.8333, 92.7789),
    ("Assam", "Kamrup", 26.1844, 91.7458),
    ("Assam", "Dibrugarh", 27.4728, 94.9120),

    # Bihar
    ("Bihar", "Patna", 25.5941, 85.1376),
    ("Bihar", "Darbhanga", 26.1542, 85.8918),
    ("Bihar", "Muzaffarpur", 26.1209, 85.3647),
    ("Bihar", "Bhagalpur", 25.2425, 86.9842),
    ("Bihar", "Saharsa", 25.8835, 86.6006),
    ("Bihar", "Supaul", 26.1261, 86.6062),

    # Kerala
    ("Kerala", "Wayanad", 11.6854, 76.1320),
    ("Kerala", "Idukki", 9.8494, 76.9804),
    ("Kerala", "Ernakulam", 9.9816, 76.2999),
    ("Kerala", "Alappuzha", 9.4981, 76.3388),
    ("Kerala", "Kottayam", 9.5916, 76.5222),

    # Maharashtra
    ("Maharashtra", "Kolhapur", 16.7050, 74.2433),
    ("Maharashtra", "Sangli", 16.8524, 74.5815),
    ("Maharashtra", "Raigad", 18.5158, 73.1822),
    ("Maharashtra", "Ratnagiri", 16.9902, 73.3120),
    ("Maharashtra", "Pune", 18.5204, 73.8567),

    # Odisha
    ("Odisha", "Puri", 19.8135, 85.8312),
    ("Odisha", "Cuttack", 20.4625, 85.8828),
    ("Odisha", "Kendrapara", 20.5029, 86.4230),
    ("Odisha", "Balasore", 21.4934, 86.9135),

    # Gujarat
    ("Gujarat", "Surat", 21.1702, 72.8311),
    ("Gujarat", "Bharuch", 21.7051, 72.9959),
    ("Gujarat", "Vadodara", 22.3072, 73.1812),
    ("Gujarat", "Navsari", 20.9467, 72.9520),

    # Uttar Pradesh
    ("Uttar Pradesh", "Varanasi", 25.3176, 82.9739),
    ("Uttar Pradesh", "Prayagraj", 25.4358, 81.8463),
    ("Uttar Pradesh", "Gorakhpur", 26.7606, 83.3732),
    ("Uttar Pradesh", "Ballia", 25.7588, 84.1482),
]

WEATHER_DATA = [
    # state, district, rain1, rain6, rain24, rain72, temp, hum, wind, lat, lon
    ("Uttarakhand", "Chamoli", 4.2, 18.5, 42.0, 95.0, 19.5, 82.0, 14.2, 30.2937, 79.5603),
    ("Uttarakhand", "Rudraprayag", 16.8, 52.4, 142.0, 260.0, 21.0, 94.0, 22.5, 30.2844, 78.9811),
    ("Uttarakhand", "Uttarkashi", 8.5, 31.0, 85.0, 175.0, 18.2, 86.0, 16.0, 30.7268, 78.4354),
    ("Uttarakhand", "Haridwar", 14.0, 48.0, 115.0, 210.0, 25.5, 89.0, 19.2, 29.9457, 78.1642),
    ("Uttarakhand", "Dehradun", 5.1, 20.2, 48.0, 102.0, 23.4, 78.0, 12.0, 30.3165, 78.0322),
    ("Uttarakhand", "Pauri Garhwal", 12.5, 42.0, 98.0, 188.0, 20.1, 88.0, 17.5, 30.1500, 78.7800),

    ("Himachal Pradesh", "Kullu", 9.8, 38.0, 92.0, 184.0, 17.5, 87.0, 16.8, 31.9579, 77.1095),
    ("Himachal Pradesh", "Mandi", 6.2, 22.4, 54.0, 112.0, 21.0, 79.0, 13.5, 31.7087, 76.9320),
    ("Himachal Pradesh", "Shimla", 4.0, 15.0, 36.0, 78.0, 16.2, 75.0, 11.2, 31.1048, 77.1734),
    ("Himachal Pradesh", "Kangra", 5.5, 19.8, 44.0, 92.0, 22.8, 77.0, 12.5, 32.0998, 76.2691),
    ("Himachal Pradesh", "Kinnaur", 15.2, 49.0, 128.0, 245.0, 13.8, 92.0, 24.0, 31.6510, 78.4752),

    ("Assam", "Dhemaji", 18.5, 62.0, 158.0, 310.0, 26.5, 96.0, 28.0, 27.4812, 94.5583),
    ("Assam", "Barpeta", 14.2, 48.5, 124.0, 255.0, 27.2, 93.0, 22.0, 26.3216, 91.0064),
    ("Assam", "Morigaon", 11.0, 39.0, 95.0, 198.0, 27.8, 90.0, 18.5, 26.2503, 92.3421),
    ("Assam", "Cachar", 15.0, 52.0, 130.0, 268.0, 26.0, 95.0, 21.0, 24.8333, 92.7789),
    ("Assam", "Kamrup", 8.2, 29.0, 72.0, 150.0, 28.5, 85.0, 15.0, 26.1844, 91.7458),
    ("Assam", "Dibrugarh", 13.5, 46.0, 118.0, 238.0, 25.8, 92.0, 20.5, 27.4728, 94.9120),

    ("Bihar", "Patna", 7.0, 25.0, 62.0, 130.0, 29.5, 82.0, 14.0, 25.5941, 85.1376),
    ("Bihar", "Darbhanga", 16.2, 54.0, 136.0, 272.0, 28.0, 94.0, 23.0, 26.1542, 85.8918),
    ("Bihar", "Muzaffarpur", 13.8, 47.0, 119.0, 242.0, 28.4, 91.0, 19.5, 26.1209, 85.3647),
    ("Bihar", "Bhagalpur", 8.5, 30.0, 75.0, 155.0, 29.8, 84.0, 16.0, 25.2425, 86.9842),
    ("Bihar", "Saharsa", 17.5, 58.0, 148.0, 298.0, 27.5, 95.0, 25.0, 25.8835, 86.6006),
    ("Bihar", "Supaul", 19.0, 64.0, 162.0, 320.0, 27.2, 96.0, 26.5, 26.1261, 86.6062),

    ("Kerala", "Wayanad", 15.8, 55.0, 138.0, 280.0, 22.0, 95.0, 24.0, 11.6854, 76.1320),
    ("Kerala", "Idukki", 17.2, 59.0, 149.0, 302.0, 21.5, 96.0, 25.5, 9.8494, 76.9804),
    ("Kerala", "Ernakulam", 8.0, 28.0, 68.0, 140.0, 27.5, 86.0, 16.0, 9.9816, 76.2999),
    ("Kerala", "Alappuzha", 16.0, 53.0, 132.0, 265.0, 27.0, 94.0, 22.0, 9.4981, 76.3388),
    ("Kerala", "Kottayam", 11.5, 41.0, 102.0, 210.0, 26.8, 90.0, 18.0, 9.5916, 76.5222),

    ("Maharashtra", "Kolhapur", 14.5, 51.0, 126.0, 258.0, 25.5, 92.0, 21.0, 16.7050, 74.2433),
    ("Maharashtra", "Sangli", 11.2, 40.0, 98.0, 202.0, 27.0, 88.0, 17.5, 16.8524, 74.5815),
    ("Maharashtra", "Raigad", 16.5, 56.0, 142.0, 285.0, 26.2, 94.0, 24.5, 18.5158, 73.1822),
    ("Maharashtra", "Ratnagiri", 13.0, 45.0, 114.0, 230.0, 26.8, 91.0, 20.0, 16.9902, 73.3120),
    ("Maharashtra", "Pune", 5.0, 18.0, 42.0, 88.0, 25.0, 76.0, 13.0, 18.5204, 73.8567),

    ("Odisha", "Puri", 12.0, 43.0, 108.0, 220.0, 27.8, 91.0, 22.5, 19.8135, 85.8312),
    ("Odisha", "Cuttack", 10.5, 38.0, 94.0, 192.0, 28.5, 89.0, 19.0, 20.4625, 85.8828),
    ("Odisha", "Kendrapara", 14.0, 49.0, 122.0, 248.0, 27.5, 93.0, 24.0, 20.5029, 86.4230),
    ("Odisha", "Balasore", 9.0, 32.0, 78.0, 160.0, 28.2, 86.0, 17.0, 21.4934, 86.9135),

    ("Gujarat", "Surat", 9.5, 34.0, 82.0, 168.0, 29.5, 85.0, 18.0, 21.1702, 72.8311),
    ("Gujarat", "Bharuch", 8.0, 29.0, 70.0, 145.0, 30.2, 82.0, 16.0, 21.7051, 72.9959),
    ("Gujarat", "Vadodara", 10.2, 37.0, 88.0, 180.0, 30.0, 86.0, 17.5, 22.3072, 73.1812),
    ("Gujarat", "Navsari", 7.5, 27.0, 65.0, 135.0, 29.0, 83.0, 15.5, 20.9467, 72.9520),

    ("Uttar Pradesh", "Varanasi", 7.2, 26.0, 64.0, 132.0, 29.8, 81.0, 14.5, 25.3176, 82.9739),
    ("Uttar Pradesh", "Prayagraj", 6.5, 23.0, 56.0, 118.0, 30.5, 78.0, 13.0, 25.4358, 81.8463),
    ("Uttar Pradesh", "Gorakhpur", 15.5, 53.0, 131.0, 264.0, 28.2, 93.0, 22.0, 26.7606, 83.3732),
    ("Uttar Pradesh", "Ballia", 13.2, 46.0, 112.0, 228.0, 28.8, 90.0, 19.0, 25.7588, 84.1482),
]

RIVERS_DATA = [
    # name, state, district, river_level, danger_level, warning_level, lat, lon
    ("Alaknanda", "Uttarakhand", "Chamoli", 1.8, 3.2, 2.5, 30.2937, 79.5603),
    ("Mandakini", "Uttarakhand", "Rudraprayag", 3.6, 3.4, 2.8, 30.2844, 78.9811),
    ("Bhagirathi", "Uttarakhand", "Uttarkashi", 2.6, 3.0, 2.4, 30.7268, 78.4354),
    ("Ganga", "Uttarakhand", "Haridwar", 3.5, 3.6, 3.0, 29.9457, 78.1642),
    ("Song", "Uttarakhand", "Dehradun", 1.4, 2.8, 2.2, 30.3165, 78.0322),
    ("Nayyar", "Uttarakhand", "Pauri Garhwal", 2.9, 3.2, 2.6, 30.1500, 78.7800),

    ("Beas", "Himachal Pradesh", "Kullu", 3.1, 3.5, 2.8, 31.9579, 77.1095),
    ("Beas", "Himachal Pradesh", "Mandi", 2.2, 3.4, 2.7, 31.7087, 76.9320),
    ("Giri", "Himachal Pradesh", "Shimla", 1.5, 2.8, 2.2, 31.1048, 77.1734),
    ("Banganga", "Himachal Pradesh", "Kangra", 1.8, 3.0, 2.3, 32.0998, 76.2691),
    ("Satluj", "Himachal Pradesh", "Kinnaur", 3.2, 3.0, 2.4, 31.6510, 78.4752),

    ("Brahmaputra", "Assam", "Dhemaji", 4.2, 3.8, 3.2, 27.4812, 94.5583),
    ("Brahmaputra", "Assam", "Barpeta", 3.7, 3.6, 3.0, 26.3216, 91.0064),
    ("Kopili", "Assam", "Morigaon", 3.1, 3.4, 2.8, 26.2503, 92.3421),
    ("Barak", "Assam", "Cachar", 3.6, 3.5, 2.9, 24.8333, 92.7789),
    ("Brahmaputra", "Assam", "Kamrup", 2.7, 3.6, 3.0, 26.1844, 91.7458),
    ("Brahmaputra", "Assam", "Dibrugarh", 3.5, 3.7, 3.1, 27.4728, 94.9120),

    ("Ganga", "Bihar", "Patna", 2.8, 3.8, 3.2, 25.5941, 85.1376),
    ("Bagmati", "Bihar", "Darbhanga", 3.8, 3.6, 3.0, 26.1542, 85.8918),
    ("Budhi Gandak", "Bihar", "Muzaffarpur", 3.4, 3.5, 2.9, 26.1209, 85.3647),
    ("Ganga", "Bihar", "Bhagalpur", 2.9, 3.7, 3.1, 25.2425, 86.9842),
    ("Kosi", "Bihar", "Saharsa", 4.1, 3.7, 3.1, 25.8835, 86.6006),
    ("Kosi", "Bihar", "Supaul", 4.4, 3.8, 3.2, 26.1261, 86.6062),

    ("Kabini", "Kerala", "Wayanad", 3.5, 3.4, 2.8, 11.6854, 76.1320),
    ("Periyar", "Kerala", "Idukki", 3.8, 3.6, 3.0, 9.8494, 76.9804),
    ("Periyar", "Kerala", "Ernakulam", 2.4, 3.2, 2.6, 9.9816, 76.2999),
    ("Pamba", "Kerala", "Alappuzha", 3.6, 3.3, 2.7, 9.4981, 76.3388),
    ("Meenachil", "Kerala", "Kottayam", 2.8, 3.2, 2.6, 9.5916, 76.5222),

    ("Panchganga", "Maharashtra", "Kolhapur", 3.6, 3.5, 2.9, 16.7050, 74.2433),
    ("Krishna", "Maharashtra", "Sangli", 3.2, 3.4, 2.8, 16.8524, 74.5815),
    ("Savitri", "Maharashtra", "Raigad", 3.7, 3.5, 2.9, 18.5158, 73.1822),
    ("Vashishti", "Maharashtra", "Ratnagiri", 3.1, 3.3, 2.7, 16.9902, 73.3120),
    ("Mula-Mutha", "Maharashtra", "Pune", 1.8, 3.2, 2.5, 18.5204, 73.8567),

    ("Bhargavi", "Odisha", "Puri", 3.2, 3.5, 2.9, 19.8135, 85.8312),
    ("Mahanadi", "Odisha", "Cuttack", 2.9, 3.6, 3.0, 20.4625, 85.8828),
    ("Brahmani", "Odisha", "Kendrapara", 3.5, 3.4, 2.8, 20.5029, 86.4230),
    ("Subarnarekha", "Odisha", "Balasore", 2.5, 3.3, 2.7, 21.4934, 86.9135),

    ("Tapi", "Gujarat", "Surat", 2.8, 3.5, 2.9, 21.1702, 72.8311),
    ("Narmada", "Gujarat", "Bharuch", 2.4, 3.4, 2.8, 21.7051, 72.9959),
    ("Vishwamitri", "Gujarat", "Vadodara", 2.9, 3.2, 2.6, 22.3072, 73.1812),
    ("Purna", "Gujarat", "Navsari", 2.2, 3.1, 2.5, 20.9467, 72.9520),

    ("Ganga", "Uttar Pradesh", "Varanasi", 2.6, 3.7, 3.1, 25.3176, 82.9739),
    ("Yamuna", "Uttar Pradesh", "Prayagraj", 2.4, 3.8, 3.2, 25.4358, 81.8463),
    ("Rapti", "Uttar Pradesh", "Gorakhpur", 3.6, 3.5, 2.9, 26.7606, 83.3732),
    ("Ghaghra", "Uttar Pradesh", "Ballia", 3.3, 3.6, 3.0, 25.7588, 84.1482),
]

RESERVOIRS_DATA = [
    ("Tehri Dam Reservoir", "Uttarakhand", "Uttarkashi", 820.5, 830.0, 828.0, 1450.0, 1200.0, 30.3780, 78.4800),
    ("Bhakra Nangal Dam", "Himachal Pradesh", "Mandi", 1660.0, 1680.0, 1675.0, 2100.0, 1800.0, 31.4110, 76.4360),
    ("Pong Dam Reservoir", "Himachal Pradesh", "Kangra", 1375.0, 1400.0, 1390.0, 1200.0, 950.0, 31.9700, 75.9500),
    ("Idukki Arch Dam", "Kerala", "Idukki", 2398.0, 2403.0, 2400.0, 1850.0, 1400.0, 9.8500, 76.9700),
    ("Mullaperiyar Dam", "Kerala", "Idukki", 138.5, 142.0, 140.0, 850.0, 600.0, 9.5290, 77.1460),
    ("Koyna Hydroelectric Dam", "Maharashtra", "Sangli", 2150.0, 2163.0, 2158.0, 1600.0, 1250.0, 17.3990, 73.7480),
    ("Radhanagari Dam", "Maharashtra", "Kolhapur", 345.0, 350.0, 348.0, 950.0, 800.0, 16.4170, 73.9870),
    ("Hirakud Dam", "Odisha", "Cuttack", 625.0, 630.0, 628.0, 3200.0, 2800.0, 21.5700, 83.8700),
    ("Sardar Sarovar Dam", "Gujarat", "Bharuch", 135.5, 138.6, 137.0, 4100.0, 3500.0, 21.8300, 73.7500),
    ("Ukai Dam", "Gujarat", "Surat", 341.0, 345.0, 343.0, 2400.0, 1900.0, 21.2500, 73.5800),
]

SHELTERS_DATA = [
    ("NDRF Relief Shelter 01", "Uttarakhand", "Chamoli", "Joshimath Main Road, Joshimath", 30.5500, 79.5667, 500, 320, "+91 1372 252101", "Medical Camp, Food, Bedding, Power Generator"),
    ("SDRF Evacuation Base", "Uttarakhand", "Rudraprayag", "NH-58 Bypass, Rudraprayag Town", 30.2844, 78.9811, 650, 180, "+91 1364 233301", "Doctor on Duty, Rescue Boats, Water Filtration"),
    ("Community Shelter High School", "Uttarakhand", "Uttarkashi", "Bhatwari Road, Uttarkashi", 30.7268, 78.4354, 400, 240, "+91 1374 222123", "Food Supply, Blanket Storage, First Aid"),
    ("Haridwar Stadium Relief Center", "Uttarakhand", "Haridwar", "Near Railway Station, Haridwar", 29.9457, 78.1642, 1200, 750, "+91 1334 226060", "Community Kitchen, Doctors, Security, Bedding"),

    ("Beas Valley Emergency Shelter", "Himachal Pradesh", "Kullu", "Akhara Bazar, Kullu", 31.9579, 77.1095, 450, 150, "+91 1902 222226", "Heaters, Medicines, Meals, Safe Drinking Water"),
    ("Mandi District Relief Camp", "Himachal Pradesh", "Mandi", "Near Victoria Bridge, Mandi", 31.7087, 76.9320, 500, 310, "+91 1905 225201", "Power Backup, Food Packets, Blankets"),

    ("Brahmaputra Flood Shelter Alpha", "Assam", "Dhemaji", "Silapathar Road, Dhemaji", 27.4812, 94.5583, 800, 120, "+91 3753 224424", "Rescue Speedboats, Food Packets, Anti-Venom Kits"),
    ("Barpeta High Ground Camp", "Assam", "Barpeta", "Town Hall Ground, Barpeta", 26.3216, 91.0064, 700, 210, "+91 3665 252125", "Medical Post, Community Kitchen, Infant Care"),
    ("Cachar District Relief Hall", "Assam", "Cachar", "Park Road, Silchar", 24.8333, 92.7789, 600, 190, "+91 3842 245056", "Doctors, Clean Water Tanks, Emergency Lights"),

    ("Gandhi Maidan Relief Complex", "Bihar", "Patna", "Gandhi Maidan North, Patna", 25.5941, 85.1376, 2000, 1400, "+91 612 2219810", "NDRF Command Post, Central Kitchen, Hospital Ambulances"),
    ("Kosi Embankment Safe Center", "Bihar", "Saharsa", "Kosi Project Colony, Saharsa", 25.8835, 86.6006, 850, 280, "+91 6478 223401", "Chlorinated Water, Food Supplies, Boat Dock"),
    ("Supaul Flood Relief Center", "Bihar", "Supaul", "Sadar Block Compound, Supaul", 26.1261, 86.6062, 900, 180, "+91 6473 224212", "Emergency Medicine, Tents, Solar Charging Hub"),

    ("Meppadi Community Relief Shelter", "Kerala", "Wayanad", "Govt Higher Secondary School, Meppadi", 11.5540, 76.1250, 600, 140, "+91 4936 202251", "Trauma Care, Kitchen, Power Backup, Bedding"),
    ("Idukki Dam Evacuation Facility", "Kerala", "Idukki", "Cheruthoni Town Hall, Idukki", 9.8500, 76.9700, 750, 260, "+91 4862 232242", "Life Jackets, Medical Team, 24x7 Control Room"),
    ("Alappuzha Waterlogged Camp", "Kerala", "Alappuzha", "Boat Jetty Compound, Alappuzha", 9.4981, 76.3388, 800, 190, "+91 477 2251720", "Houseboat Evacuation, Dry Rations, Water Purifiers"),

    ("Panchganga Flood Relief Camp", "Maharashtra", "Kolhapur", "Shiroli Ground, Kolhapur", 16.7050, 74.2433, 950, 280, "+91 231 2659232", "Inflatable Rescue Boats, Meals, Doctor Staff"),
    ("Sangli Krishi Hall Safe Shelter", "Maharashtra", "Sangli", "Near Krishna River Bridge, Sangli", 16.8524, 74.5815, 700, 220, "+91 233 2373005", "Ambulance Station, Food, Blankets, Charging Point"),
    ("Mahad Coastal Relief Base", "Maharashtra", "Raigad", "Shivaji Chowk, Mahad", 18.0828, 73.4222, 600, 160, "+91 2141 222129", "Coast Guard Support, Food, Clothes, Doctor"),

    ("Puri Cyclone & Flood Shelter", "Odisha", "Puri", "Marine Drive Relief Station, Puri", 19.8135, 85.8312, 1100, 650, "+91 6752 222107", "Reinforced Structure, Food, Satellite Phone"),
    ("Mahanadi Delta Evacuation Hall", "Odisha", "Cuttack", "Barabati Stadium Campus, Cuttack", 20.4625, 85.8828, 1500, 890, "+91 671 2301200", "State Disaster Ops, 50 Bed Mini-Hospital, Food"),

    ("Surat Tapi Embankment Shelter", "Gujarat", "Surat", "Adajan Community Complex, Surat", 21.1702, 72.8311, 1300, 720, "+91 261 2422285", "Drinking Water Supply, Kitchen, Emergency Lights"),
    ("Gorakhpur Rapti Flood Center", "Uttar Pradesh", "Gorakhpur", "University Ground Shelter, Gorakhpur", 26.7606, 83.3732, 900, 240, "+91 551 2201796", "Rescue Motorboats, Medical Units, Dry Rations"),
]


def seed_database():
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            # 1. Locations Table
            print("Seeding locations table...")
            cur.execute("DELETE FROM locations;")
            for state, dist, lat, lon in LOCATIONS_DATA:
                cur.execute("""
                    INSERT INTO locations (state, district, latitude, longitude)
                    VALUES (%s, %s, %s, %s);
                """, (state, dist, lat, lon))

            # 2. Weather Data Table
            print("Seeding weather_data table...")
            cur.execute("DELETE FROM weather_data;")
            for row in WEATHER_DATA:
                cur.execute("""
                    INSERT INTO weather_data (
                        state, district, rainfall_1h, rainfall_6h, rainfall_24h, rainfall_72h,
                        temperature, humidity, wind_speed, latitude, longitude, recorded_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP);
                """, row)

            # 3. Rivers Table
            print("Seeding rivers table...")
            cur.execute("DELETE FROM rivers;")
            for name, state, dist, r_lvl, d_lvl, w_lvl, lat, lon in RIVERS_DATA:
                status = "DANGER" if r_lvl >= d_lvl else ("WARNING" if r_lvl >= w_lvl else "NORMAL")
                cur.execute("""
                    INSERT INTO rivers (
                        name, state, district, river_level, danger_level, warning_level,
                        latitude, longitude, status, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP);
                """, (name, state, dist, r_lvl, d_lvl, w_lvl, lat, lon, status))

            # 4. Reservoirs Table
            print("Seeding reservoirs table...")
            cur.execute("DELETE FROM reservoirs;")
            for name, state, dist, c_lvl, f_lvl, d_lvl, inf, outf, lat, lon in RESERVOIRS_DATA:
                status = "CRITICAL" if c_lvl >= d_lvl else "OPERATIONAL"
                cur.execute("""
                    INSERT INTO reservoirs (
                        name, state, district, current_level, full_level, danger_level,
                        inflow, outflow, latitude, longitude, status, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP);
                """, (name, state, dist, c_lvl, f_lvl, d_lvl, inf, outf, lat, lon, status))

            # 5. Shelters Table
            print("Seeding shelters table...")
            cur.execute("DELETE FROM shelters;")
            for name, state, dist, addr, lat, lon, cap, avail, cont, fac in SHELTERS_DATA:
                sh_id = f"SH-{dist[:3].upper()}-{abs(hash(name)) % 10000:04d}"
                cur.execute("""
                    INSERT INTO shelters (
                        shelter_id, name, state, district, address,
                        latitude, longitude, capacity, available_capacity,
                        contact, facilities, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE');
                """, (sh_id, name, state, dist, addr, lat, lon, cap, avail, cont, fac))

            # 6. Alert History Table
            print("Seeding alert_history table...")
            cur.execute("DELETE FROM alert_history;")
            sample_alerts = [
                ("AS-ALT-101", "Uttarakhand", "Rudraprayag", "HIGH", 100.0, "CRITICAL", "🚨 RED ALERT: Mandakini Water Level Crossing Danger Mark", "Mandakini river level has touched 3.6m against danger mark of 3.4m. Continuous cloudburst rains over past 24h.", "Immediate evacuation of riverside settlements to SDRF Evacuation Base.", "#d92d20"),
                ("AS-ALT-102", "Assam", "Dhemaji", "HIGH", 100.0, "CRITICAL", "🚨 SEVERE INUNDATION: Brahmaputra Embankment Breach Alert", "Water level 4.2m exceeding danger level of 3.8m. 18 villages affected.", "Move immediately to Brahmaputra Flood Shelter Alpha. Avoid highway culverts.", "#d92d20"),
                ("AS-ALT-103", "Bihar", "Supaul", "HIGH", 100.0, "CRITICAL", "🚨 KOSI BARRAGE DISCHARGE: Severe Flood Warning", "High discharge from Kosi barrage combined with 162mm rain.", "Follow SDRF motorboat evacuation orders to Sadar Block compound.", "#d92d20"),
                ("AS-ALT-104", "Kerala", "Wayanad", "HIGH", 99.8, "CRITICAL", "🚨 FLASH FLOOD & LANDSLIDE WARNING: Meppadi & Vythiri", "Torrential rainfall of 138mm in 24 hours. High soil saturation.", "Evacuate hillside slopes to Meppadi Community Relief Shelter immediately.", "#d92d20"),
                ("AS-ALT-105", "Himachal Pradesh", "Kullu", "MEDIUM", 96.1, "WARNING", "⚠️ ORANGE ALERT: Beas River Spate Warning", "Beas river rising close to warning mark. Intermittent cloudburst showers in catchment.", "Stay clear of riverbeds and low-lying campsites.", "#e58b18"),
            ]
            for aid, st, dst, rsk, prb, lvl, ttl, msg, act, clr in sample_alerts:
                cur.execute("""
                    INSERT INTO alert_history (
                        alert_id, state, district, risk, probability, level,
                        title, message, action, color, data_source, river_source, authority_notified
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'AapdaSetu AI Early Warning System', 'CWC River Telemetry', TRUE);
                """, (aid, st, dst, rsk, prb, lvl, ttl, msg, act, clr))

            # 7. Community Reports Table
            print("Seeding community_reports table...")
            cur.execute("DELETE FROM community_reports;")
            sample_reports = [
                ("REP-7801", "Uttarakhand", "Rudraprayag", "WATERLOGGING", "Water level rising rapidly near bridge. NH-58 partially submerged.", 30.2844, 78.9811, 14, "HIGH", False, "Rajesh Negi", "+91 98765 43210"),
                ("REP-7802", "Assam", "Dhemaji", "EMERGENCY_RESCUE", "Family of 6 trapped on rooftop in Silapathar ward 3. Water current high.", 27.4812, 94.5583, 6, "CRITICAL", False, "Barun Bora", "+91 94350 12345"),
                ("REP-7803", "Kerala", "Wayanad", "LANDSLIDE_BLOCK", "Minor road mudslide near Meppadi school road. Small vehicles unable to pass.", 11.5540, 76.1250, 0, "MEDIUM", True, "", ""),
                ("REP-7804", "Maharashtra", "Kolhapur", "SHELTER_NEEDED", "Panchganga backwaters entering residential colony in Shiroli. Around 25 people need shelter transport.", 16.7050, 74.2433, 25, "HIGH", False, "Sanjay Patil", "+91 98220 54321"),
            ]
            for rid, st, dst, cat, msg, lat, lon, ppl, urg, anon, cname, cphone in sample_reports:
                cur.execute("""
                    INSERT INTO community_reports (
                        report_id, state, district, category, message, latitude, longitude,
                        people_count, urgency, anonymous, contact_name, contact_phone, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'VERIFIED');
                """, (rid, st, dst, cat, msg, lat, lon, ppl, urg, anon, cname, cphone))

            # 8. Donations Table
            print("Seeding donations table...")
            cur.execute("DELETE FROM donations;")
            sample_donations = [
                ("AS-DON-A194", "Vikram Malhotra", 5000.00, "DISASTER RELIEF", "Praying for quick recovery in Wayanad and Rudraprayag."),
                ("AS-DON-B832", "Ananya Sharma", 2500.00, "MEDICAL AID", "For medicines and infant supplies in relief camps."),
                ("AS-DON-C447", "Karthik Iyer", 10000.00, "EMERGENCY FOOD", "Contributed for community kitchens in Assam & Bihar."),
                ("AS-DON-D911", "Rohan Mehta", 1500.00, "DISASTER RELIEF", "Stay strong everyone, rescue teams are doing great work."),
            ]
            for did, name, amt, purp, msg in sample_donations:
                cur.execute("""
                    INSERT INTO donations (donation_id, donor_name, amount, purpose, message)
                    VALUES (%s, %s, %s, %s, %s);
                """, (did, name, amt, purp, msg))

            conn.commit()

            print("=" * 60)
            print("AAPDASETU DATABASE SEEDED SUCCESSFULLY")
            print("=" * 60)
            for t in ['locations', 'weather_data', 'rivers', 'reservoirs', 'shelters', 'alert_history', 'community_reports', 'donations']:
                cur.execute(f"SELECT COUNT(*) FROM {t};")
                print(f"  - {t:<20s}: {cur.fetchone()[0]} rows")
            print("=" * 60)


if __name__ == "__main__":
    seed_database()
