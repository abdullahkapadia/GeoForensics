import math
from typing import Dict, List, Optional, Any, Tuple
from geopy.distance import geodesic

# Comprehensive forensic knowledge base

COUNTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "IN": {
        "name": "India",
        "driving_side": "left",
        "phone_code": "+91",
        "tld": ".in",
        "scripts": ["Devanagari", "Latin", "Gujarati", "Bengali", "Tamil", "Telugu", "Kannada", "Malayalam", "Gurmukhi", "Urdu"],
        "plate_style": "White/Black for private, Yellow/Black for commercial, high aspect ratio with IND badge",
        "road_markings": "Broken white/yellow center lines, kerb stones painted alternating black-and-white or yellow-and-black",
        "utility_poles": "Steel tubular or concrete ladder poles, often bundled overhead cabling",
        "vegetation": ["Tropical Dry", "Subtropical Deciduous", "Arid Scrub", "Monsoon Canopy"],
        "architecture_cues": ["RCC frame with brick infill", "Indo-Saracenic", "Mughal arches", "Colonial British", "Haveli balconies", "Bright exterior distemper"],
        "default_lat": 20.5937,
        "default_lng": 78.9629
    },
    "GB": {
        "name": "United Kingdom",
        "driving_side": "left",
        "phone_code": "+44",
        "tld": ".uk",
        "scripts": ["Latin"],
        "plate_style": "White front, Yellow rear, UK flag or GB/UK blue strip",
        "road_markings": "Double yellow curb lines (no parking), zigzag pedestrian crossing lines, white dashes",
        "utility_poles": "Creosote-treated wooden telegraph poles, low-hanging copper lines",
        "vegetation": ["Temperate Deciduous", "Rolling green pasture", "Hedgerows", "Oak and Beech"],
        "architecture_cues": ["Victorian red/brown brick terrace", "Georgian townhouse", "Tudor timber frame", "Slate roofs", "Sash windows"],
        "default_lat": 55.3781,
        "default_lng": -3.4360
    },
    "FR": {
        "name": "France",
        "driving_side": "right",
        "phone_code": "+33",
        "tld": ".fr",
        "scripts": ["Latin"],
        "plate_style": "EU standard white front and rear with blue EU strip left and department logo right",
        "road_markings": "White dotted lines with long gaps (T1/T2 markings), no yellow centerlines",
        "utility_poles": "Perforated concrete poles (holes along the spine) or wooden poles with green markings",
        "vegetation": ["Temperate Oceanic", "Mediterranean Scrub / Maquis", "Poplar tree lined avenues"],
        "architecture_cues": ["Haussmannian dressed stone facades", "Mansard zinc roofs", "Wrought-iron balconies", "French shutters (volets)"],
        "default_lat": 46.2276,
        "default_lng": 2.2137
    },
    "US": {
        "name": "United States",
        "driving_side": "right",
        "phone_code": "+1",
        "tld": ".us",
        "scripts": ["Latin"],
        "plate_style": "Square aspect ratio (12x6 inches), colorful state designs, rear plate mandatory",
        "road_markings": "Double solid yellow centerlines for no-passing, white lane markings, yellow edge lines",
        "utility_poles": "Tall wooden poles with horizontal wooden crossarms, cylindrical transformers mounted high",
        "vegetation": ["Broadleaf Deciduous", "Pine barrens", "Prairie grassland", "Chaparral", "Suburban lawn"],
        "architecture_cues": ["Wood siding / clapboard", "Asphalt shingle roofs", "Front porches", "Steel skyscrapers", "Strip malls with prominent parking"],
        "default_lat": 37.0902,
        "default_lng": -95.7129
    },
    "JP": {
        "name": "Japan",
        "driving_side": "left",
        "phone_code": "+81",
        "tld": ".jp",
        "scripts": ["Kanji", "Hiragana", "Katakana", "Latin"],
        "plate_style": "White with green embossed text for standard cars, Yellow with black text for Kei cars",
        "road_markings": "White stop lines with '止まれ' (Tomare) painted on asphalt, narrow streets often without sidewalks",
        "utility_poles": "Dense cylindrical concrete poles packed with multiple transformers, complex cable spiderwebs, reflective yellow-black base tape",
        "vegetation": ["Japanese Cedar (Sugi)", "Bamboo groves", "Cherry blossoms", "Lush mountainous greenery"],
        "architecture_cues": ["Ceramic tile roofs (Kawara)", "Narrow multi-story siding houses", "Modular concrete", "Vending machines on sidewalks"],
        "default_lat": 36.2048,
        "default_lng": 138.2529
    },
    "DE": {
        "name": "Germany",
        "driving_side": "right",
        "phone_code": "+49",
        "tld": ".de",
        "scripts": ["Latin"],
        "plate_style": "EU standard white with D euro-band, city letter code, TÜV and state seal stickers",
        "road_markings": "Thick white thermo-plastic markings, no yellow curbs",
        "utility_poles": "Mostly underground utilities in urban areas; rural uses lattice metal or wooden poles",
        "vegetation": ["Central European Mixed Forest", "Spruce plantations", "Rapeseed fields"],
        "architecture_cues": ["Fachwerk (half-timbered)", "Bauhaus functionalist", "Gabled red-tile roofs", "Thermal double/triple glazed tilt-and-turn windows"],
        "default_lat": 51.1657,
        "default_lng": 10.4515
    },
    "IT": {
        "name": "Italy",
        "driving_side": "right",
        "phone_code": "+39",
        "tld": ".it",
        "scripts": ["Latin"],
        "plate_style": "EU standard with dual blue bands (left EU flag, right year and province initials)",
        "road_markings": "Continuous and broken white lines, blue parking lines (paid zone)",
        "utility_poles": "Thin concrete or wall-mounted power brackets with ceramic insulators",
        "vegetation": ["Cypress trees", "Olive groves", "Stone pine (Umbrella pines)", "Citrus"],
        "architecture_cues": ["Ochre, terracotta, and pastel plaster", "Roman tile roofs", "Green or brown wooden louvers", "Arched porticos"],
        "default_lat": 41.8719,
        "default_lng": 12.5674
    },
    "AU": {
        "name": "Australia",
        "driving_side": "left",
        "phone_code": "+61",
        "tld": ".au",
        "scripts": ["Latin"],
        "plate_style": "State-specific plates, alphanumeric combinations",
        "road_markings": "Broken white centerlines, yellow hazard lines on mountain roads",
        "utility_poles": "Stobie poles (steel flange with concrete core in SA) or treated hardwood",
        "vegetation": ["Eucalyptus / Gum trees", "Acacia / Wattle", "Spinifex", "Dry red earth"],
        "architecture_cues": ["Corrugated iron roofs (Colorbond)", "Weatherboard cottages", "Verandahs with iron lacework", "Brick veneer bungalows"],
        "default_lat": -25.2744,
        "default_lng": 133.7751
    }
}

# Curated High-Precision Exact Landmark Database
WORLD_LANDMARKS: List[Dict[str, Any]] = [
    {
        "id": "lmk_sidi_saiyyed",
        "name": "Sidi Saiyyed Mosque (Jali)",
        "keywords": ["sidi saiyyed", "jali", "carved stone window", "tree of life stone", "ahmedabad jali"],
        "city": "Ahmedabad",
        "state_province": "Gujarat",
        "country": "India",
        "country_code": "IN",
        "lat": 23.02701,
        "lng": 72.58134,
        "resolved_address": "Sidi Saiyyed Mosque, Mirzapur, Ahmedabad, Gujarat 380001, India",
        "architecture_style": "Indo-Islamic / Sultanate Architecture",
        "visual_features": ["Ornate semicircular stone fretwork", "Tree of life motif", "Yellow sandstone jali", "Pointed arches"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_atal_bridge",
        "name": "Atal Pedestrian Bridge, Sabarmati Riverfront",
        "keywords": ["atal bridge", "sabarmati riverfront", "atal pedestrian bridge", "sabarmati bridge", "ahmedabad riverfront"],
        "city": "Ahmedabad",
        "state_province": "Gujarat",
        "country": "India",
        "country_code": "IN",
        "lat": 23.02322,
        "lng": 72.57140,
        "resolved_address": "Atal Bridge, Sabarmati Riverfront, Paldi, Ahmedabad, Gujarat 380009, India",
        "architecture_style": "Modernist Steel Truss / Tensile Structure",
        "visual_features": ["Eye-shaped steel truss", "Kite-inspired canopy", "Sabarmati river promenade", "LED illuminated steel diagrid"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_sabarmati_ashram",
        "name": "Sabarmati Ashram (Gandhi Ashram)",
        "keywords": ["sabarmati ashram", "gandhi ashram", "hridaya kunj", "sabarmati", "ahmedabad ashram"],
        "city": "Ahmedabad",
        "state_province": "Gujarat",
        "country": "India",
        "country_code": "IN",
        "lat": 23.05987,
        "lng": 72.58045,
        "resolved_address": "Sabarmati Ashram, Gandhi Smarak Sangrahalaya, Ashram Road, Ahmedabad, Gujarat 380027, India",
        "architecture_style": "Vernacular Terracotta Tile / Charles Correa Memorial",
        "visual_features": ["Low-rise tiled roofs", "Brick piers", "Open-air courtyards", "Sabarmati riverbank embankment"],
        "precision": "exact",
        "uncertainty_radius_km": 0.08
    },
    {
        "id": "lmk_adalaj_stepwell",
        "name": "Adalaj Stepwell (Rudabai Stepwell)",
        "keywords": ["adalaj stepwell", "adalaj vav", "rudabai stepwell", "stepwell gandhinagar", "adalaj"],
        "city": "Adalaj / Ahmedabad",
        "state_province": "Gujarat",
        "country": "India",
        "country_code": "IN",
        "lat": 23.16667,
        "lng": 72.58000,
        "resolved_address": "Adalaj Stepwell, Adalaj, Gandhinagar - Ahmedabad Border, Gujarat 382421, India",
        "architecture_style": "Solanki / Indo-Islamic Stepwell Architecture",
        "visual_features": ["Multi-story underground stone pavilions", "Carved octagonal shafts", "Sandstone pillar galleries"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_big_ben",
        "name": "Elizabeth Tower (Big Ben) & Palace of Westminster",
        "keywords": ["big ben", "elizabeth tower", "westminster", "parliament london", "thames river london"],
        "city": "London",
        "state_province": "Greater London",
        "country": "United Kingdom",
        "country_code": "GB",
        "lat": 51.50073,
        "lng": -0.12463,
        "resolved_address": "Palace of Westminster, Westminster, London SW1A 0AA, United Kingdom",
        "architecture_style": "Perpendicular Gothic Revival",
        "visual_features": ["Four-faced clock tower", "Gothic spires", "Westminster Bridge", "River Thames parapet"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_tower_bridge",
        "name": "Tower Bridge",
        "keywords": ["tower bridge", "london suspension bridge", "thames twin towers bridge", "tower of london bridge"],
        "city": "London",
        "state_province": "Greater London",
        "country": "United Kingdom",
        "country_code": "GB",
        "lat": 51.50546,
        "lng": -0.07536,
        "resolved_address": "Tower Bridge Rd, London SE1 2UP, United Kingdom",
        "architecture_style": "Victorian Gothic Bascule Bridge",
        "visual_features": ["Twin stone-clad towers", "High-level walkways", "Blue painted suspension cables", "Bascule opening deck"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_eiffel_tower",
        "name": "Eiffel Tower",
        "keywords": ["eiffel tower", "tour eiffel", "champ de mars", "trocadero", "paris wrought iron tower"],
        "city": "Paris",
        "state_province": "Île-de-France",
        "country": "France",
        "country_code": "FR",
        "lat": 48.85837,
        "lng": 2.29448,
        "resolved_address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris, France",
        "architecture_style": "Wrought-Iron Puddle Lattice Tower",
        "visual_features": ["Four-legged lattice pylon", "Arched base spans", "Champ de Mars lawns", "Seine riverbank"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_arc_de_triomphe",
        "name": "Arc de Triomphe",
        "keywords": ["arc de triomphe", "champs elysees arc", "place de letoile", "triumphal arch paris"],
        "city": "Paris",
        "state_province": "Île-de-France",
        "country": "France",
        "country_code": "FR",
        "lat": 48.87379,
        "lng": 2.29503,
        "resolved_address": "Place Charles de Gaulle, 75008 Paris, France",
        "architecture_style": "Neoclassical Triumphal Arch",
        "visual_features": ["Monolithic stone arch", "High relief sculptures of departure of volunteers", "Star roundabout cobblestone"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_gateway_of_india",
        "name": "Gateway of India",
        "keywords": ["gateway of india", "taj mahal palace mumbai", "apollo bunder", "mumbai gateway", "mumbai harbor"],
        "city": "Mumbai",
        "state_province": "Maharashtra",
        "country": "India",
        "country_code": "IN",
        "lat": 18.92198,
        "lng": 72.83465,
        "resolved_address": "Apollo Bandar, Colaba, Mumbai, Maharashtra 400001, India",
        "architecture_style": "Indo-Saracenic Basalt Arch",
        "visual_features": ["Yellow basalt monumental triumphal arch", "Arabian sea waterfront", "Taj Mahal Palace hotel backdrop"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_bandra_worli",
        "name": "Bandra-Worli Sea Link",
        "keywords": ["bandra worli sea link", "sea link mumbai", "rajiv gandhi sea link", "cable stayed bridge mumbai"],
        "city": "Mumbai",
        "state_province": "Maharashtra",
        "country": "India",
        "country_code": "IN",
        "lat": 19.03680,
        "lng": 72.81720,
        "resolved_address": "Bandra-Worli Sea Link, Mahim Bay, Mumbai, Maharashtra 400050, India",
        "architecture_style": "Cable-Stayed Bridge / Precast Concrete Viaduct",
        "visual_features": ["Diamond-shaped concrete pylons", "White stay cables", "Arabian Sea Mahim bay sweeping viaduct"],
        "precision": "exact",
        "uncertainty_radius_km": 0.1
    },
    {
        "id": "lmk_shibuya_crossing",
        "name": "Shibuya Scramble Crossing",
        "keywords": ["shibuya crossing", "shibuya scramble", "shibuya 109", "hachiko square", "tokyo scramble"],
        "city": "Tokyo",
        "state_province": "Tokyo Prefecture",
        "country": "Japan",
        "country_code": "JP",
        "lat": 35.65951,
        "lng": 139.70057,
        "resolved_address": "2 Chome-2-1 Dogenzaka, Shibuya City, Tokyo 150-0043, Japan",
        "architecture_style": "High-Density Neon Commercial Metropole",
        "visual_features": ["Massive diagonal zebra crossing", "QFRONT Tsutaya LED facade", "Curved glass Shibuya 109 cylinder", "Pedestrian sea"],
        "precision": "exact",
        "uncertainty_radius_km": 0.04
    },
    {
        "id": "lmk_tokyo_tower",
        "name": "Tokyo Tower",
        "keywords": ["tokyo tower", "minato tower", "red white lattice tower tokyo", "nippon denpatō"],
        "city": "Tokyo",
        "state_province": "Tokyo Prefecture",
        "country": "Japan",
        "country_code": "JP",
        "lat": 35.65858,
        "lng": 139.74543,
        "resolved_address": "4 Chome-2-8 Shibakoen, Minato City, Tokyo 105-0011, Japan",
        "architecture_style": "Communications Lattice Tower (Eiffel-inspired)",
        "visual_features": ["International orange and white alternating lattice steel", "Shiba Park greenery", "Observation decks"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_colosseum",
        "name": "Colosseum (Flavian Amphitheatre)",
        "keywords": ["colosseum", "colosseo", "flavian amphitheatre", "rome amphitheater", "ancient rome colosseum"],
        "city": "Rome",
        "state_province": "Lazio",
        "country": "Italy",
        "country_code": "IT",
        "lat": 41.89021,
        "lng": 12.49223,
        "resolved_address": "Piazza del Colosseo, 1, 00184 Roma RM, Italy",
        "architecture_style": "Ancient Roman Travertine Amphitheatre",
        "visual_features": ["Elliptical stone arcades", "Doric, Ionic, and Corinthian pilasters", "Crumbling outer ring", "Travertine stone"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_brandenburg_gate",
        "name": "Brandenburg Gate",
        "keywords": ["brandenburg gate", "brandenburger tor", "pariser platz berlin", "quadriga gate berlin"],
        "city": "Berlin",
        "state_province": "Berlin",
        "country": "Germany",
        "country_code": "DE",
        "lat": 52.51628,
        "lng": 13.37770,
        "resolved_address": "Pariser Platz, 10117 Berlin, Germany",
        "architecture_style": "Neoclassical Sandstone Propylaea",
        "visual_features": ["Twelve Doric sandstone columns", "Quadriga bronze chariot sculpted on top", "Pariser Platz stone square"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    },
    {
        "id": "lmk_brooklyn_bridge",
        "name": "Brooklyn Bridge",
        "keywords": ["brooklyn bridge", "east river bridge ny", "manhattan brooklyn suspension bridge", "gothic revival stone bridge"],
        "city": "New York",
        "state_province": "New York",
        "country": "United States",
        "country_code": "US",
        "lat": 40.70609,
        "lng": -73.99686,
        "resolved_address": "Brooklyn Bridge, New York, NY 10038, United States",
        "architecture_style": "Neo-Gothic Stone and Steel Suspension Bridge",
        "visual_features": ["Limestone and granite dual-pointed arch towers", "Diagonal criss-cross stay cables", "Elevated timber pedestrian promenade"],
        "precision": "exact",
        "uncertainty_radius_km": 0.06
    },
    {
        "id": "lmk_sydney_opera_house",
        "name": "Sydney Opera House",
        "keywords": ["sydney opera house", "bennelong point", "sydney harbor shells", "utzon opera house"],
        "city": "Sydney",
        "state_province": "New South Wales",
        "country": "Australia",
        "country_code": "AU",
        "lat": -33.85678,
        "lng": 151.21530,
        "resolved_address": "Bennelong Point, Sydney NSW 2000, Australia",
        "architecture_style": "Expressionist Precast Concrete Shells",
        "visual_features": ["Interlocking vaulted sail-shaped shells", "Swedish ceramic granite tile finish", "Sydney Harbour waters", "Granite podium"],
        "precision": "exact",
        "uncertainty_radius_km": 0.05
    }
]

# Major World Geocoding Reference Entities
CITIES_DB: List[Dict[str, Any]] = [
    {"city": "Ahmedabad", "state": "Gujarat", "country": "India", "country_code": "IN", "lat": 23.0225, "lng": 72.5714, "radius_km": 15.0},
    {"city": "Vadodara", "state": "Gujarat", "country": "India", "country_code": "IN", "lat": 22.3072, "lng": 73.1812, "radius_km": 12.0},
    {"city": "Surat", "state": "Gujarat", "country": "India", "country_code": "IN", "lat": 21.1702, "lng": 72.8311, "radius_km": 14.0},
    {"city": "Mumbai", "state": "Maharashtra", "country": "India", "country_code": "IN", "lat": 18.9220, "lng": 72.8347, "radius_km": 25.0},
    {"city": "New Delhi", "state": "Delhi", "country": "India", "country_code": "IN", "lat": 28.6139, "lng": 77.2090, "radius_km": 20.0},
    {"city": "Bengaluru", "state": "Karnataka", "country": "India", "country_code": "IN", "lat": 12.9716, "lng": 77.5946, "radius_km": 22.0},
    {"city": "London", "state": "Greater London", "country": "United Kingdom", "country_code": "GB", "lat": 51.5074, "lng": -0.1278, "radius_km": 18.0},
    {"city": "Manchester", "state": "Greater Manchester", "country": "United Kingdom", "country_code": "GB", "lat": 53.4808, "lng": -2.2426, "radius_km": 12.0},
    {"city": "Paris", "state": "Île-de-France", "country": "France", "country_code": "FR", "lat": 48.8566, "lng": 2.3522, "radius_km": 14.0},
    {"city": "Lyon", "state": "Auvergne-Rhône-Alpes", "country": "France", "country_code": "FR", "lat": 45.7640, "lng": 4.8357, "radius_km": 10.0},
    {"city": "Berlin", "state": "Berlin", "country": "Germany", "country_code": "DE", "lat": 52.5200, "lng": 13.4050, "radius_km": 16.0},
    {"city": "Munich", "state": "Bavaria", "country": "Germany", "country_code": "DE", "lat": 48.1351, "lng": 11.5820, "radius_km": 12.0},
    {"city": "Rome", "state": "Lazio", "country": "Italy", "country_code": "IT", "lat": 41.9028, "lng": 12.4964, "radius_km": 15.0},
    {"city": "Tokyo", "state": "Tokyo Prefecture", "country": "Japan", "country_code": "JP", "lat": 35.6762, "lng": 139.6503, "radius_km": 28.0},
    {"city": "Kyoto", "state": "Kyoto Prefecture", "country": "Japan", "country_code": "JP", "lat": 35.0116, "lng": 135.7681, "radius_km": 12.0},
    {"city": "New York", "state": "New York", "country": "United States", "country_code": "US", "lat": 40.7128, "lng": -74.0060, "radius_km": 20.0},
    {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US", "lat": 37.7749, "lng": -122.4194, "radius_km": 10.0},
    {"city": "Sydney", "state": "New South Wales", "country": "Australia", "country_code": "AU", "lat": -33.8688, "lng": 151.2093, "radius_km": 18.0}
]

def calculate_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculates geodesic distance between two GPS coordinates in kilometers."""
    try:
        return geodesic((lat1, lng1), (lat2, lng2)).kilometers
    except Exception:
        # Haversine fallback
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

def find_nearest_city(lat: float, lng: float) -> Tuple[Optional[Dict[str, Any]], float]:
    """Finds nearest known reference city from database."""
    best_city = None
    min_dist = float("inf")
    for city in CITIES_DB:
        dist = calculate_distance_km(lat, lng, city["lat"], city["lng"])
        if dist < min_dist:
            min_dist = dist
            best_city = city
    return best_city, min_dist
