import streamlit as st
import requests
import time
from streamlit_geolocation import streamlit_geolocation

# Set page configuration (must be first)
st.set_page_config(page_title="Restaurant Finder", page_icon="🍴")

# Load API keys from Streamlit Cloud secrets
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
OPENCAGE_API_KEY = st.secrets.get("OPENCAGE_API_KEY")

# Warn if keys missing
if not GOOGLE_API_KEY:
    st.error("Missing GOOGLE_API_KEY in Streamlit secrets. Please add it under App settings > Secrets.")
if not OPENCAGE_API_KEY:
    st.warning("OPENCAGE_API_KEY not set—reverse geocoding may fail.")

# Title and Introduction
st.title("Restaurant Finder 🍴")
st.write("""
Welcome to the Restaurant Finder! Use this app to discover restaurants in Switzerland that match your preferences.
Simply select your criteria below, and we'll help you find the perfect spot.
""")

# User Inputs
st.subheader("Search Criteria")

# Price Range with option to ignore
price_range = st.selectbox(
    "Select your price range:",
    ["Any", "$", "$$", "$$$", "$$$$"]
)

# Cuisine Selection
food_type = st.multiselect(
    "What type of food are you in the mood for?",
    ["Italian", "Swiss", "Chinese", "Mexican", "Indian", "Japanese", "American", "Mediterranean", "Vegan", "Seafood"]
)

# Mood Selection
mood = st.radio(
    "What's your dining mood?",
    ["Casual", "Romantic", "Family-Friendly", "Business", "Trendy", "Quiet"]
)

# Distance
distance = st.slider(
    "How far are you willing to travel? (in km)",
    min_value=1, max_value=50, value=10
)

# Geolocation
st.subheader("Your Location")
location = streamlit_geolocation()
latitude = longitude = None
if location:
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude and longitude and OPENCAGE_API_KEY:
        geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={OPENCAGE_API_KEY}"
        r = requests.get(geocode_url)
        if r.status_code == 200:
            comp = r.json()["results"][0]["components"]
            city = comp.get("city") or comp.get("town") or comp.get("village") or "Unknown"
            st.write(f"**You are in {city}** — {latitude}, {longitude}")
        else:
            st.write("Unable to fetch city name.")
    elif latitude and longitude:
        st.write(f"Coordinates: {latitude}, {longitude}")
    else:
        st.write("Invalid coordinates received.")
else:
    st.write("Enable location services to fetch your coordinates.")

# Maps for robust keywords
cuisine_map = {
    "Italian": ["Italian restaurant", "pizzeria", "pizza", "ristorante", "Italienisches Restaurant"],
    "Swiss":   ["Swiss restaurant", "fondue", "raclette", "Schweizer Restaurant", "Alpine cuisine"],
    "Chinese": ["Chinese restaurant", "dim sum", "noodle", "szechuan", "Chinesisches Restaurant"],
    "Mexican": ["Mexican restaurant", "taco", "burrito", "enchilada", "Mexikanisches Restaurant"],
    "Indian":  ["Indian restaurant", "curry", "tandoori", "masala", "naan", "Indisches Restaurant"],
    "Japanese": ["Japanese restaurant", "sushi", "ramen", "izakaya", "udon", "tempura", "Japanisches Restaurant"],
    "American": ["American restaurant", "burger", "steakhouse", "grill", "fast food", "Amerikanisches Restaurant"],
    "Mediterranean": ["Mediterranean restaurant", "meze", "kebab", "hummus", "falafel", "grilled vegetables"],
    "Vegan":   ["vegan restaurant", "plant based", "vegetarian", "Veganes Restaurant", "fleischlos"],
    "Seafood": ["seafood restaurant", "fish", "oyster bar", "shrimp", "lobster", "Fischrestaurant"]
}

mood_map = {
    "Casual": ["casual", "diner", "lässig", "Speiselokal"],
    "Romantic": ["romantic", "cozy", "intimate", "romantisch", "gemütlich"],
    "Family-Friendly": ["family", "kids", "familienfreundlich", "Kinderfreundlich"],
    "Business": ["business", "meeting", "geschäftlich", "Business lunch"],
    "Trendy": ["trendy", "hipster", "angesagt", "modern", "stylish"],
    "Quiet": ["quiet", "peaceful", "ruhig", "leise"]
}

# Find Restaurants
st.subheader("Find Restaurants")
if st.button("Search Restaurants"):
    if not (latitude and longitude and GOOGLE_API_KEY):
        st.error("Missing location or API key. Cannot search.")
    else:
        # Price flags
        price_map = {"$": (0,1), "$$": (1,2), "$$$": (2,3), "$$$$": (3,4)}
        use_price = price_range != "Any"
        if use_price:
            min_price, max_price = price_map[price_range]

        # Radius
        radius_m = distance * 1000

        # Build keyword list
        selected_cuisines = [term for ft in food_type for term in cuisine_map.get(ft, [])]
        selected_moods    = mood_map.get(mood, [])
        keyword = " ".join(selected_cuisines + selected_moods)

        # Base params
        params = {
            "key": GOOGLE_API_KEY,
            "location": f"{latitude},{longitude}",
            "radius": radius_m,
            "type": "restaurant",
            "keyword": keyword,
            "opennow": True,
            "language": "en"
        }
        if use_price:
            params["minprice"] = min_price
            params["maxprice"] = max_price

        # Fetch with pagination
        all_places = []
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        response = requests.get(url, params=params)
        if response.status_code != 200:
            st.error(f"HTTP Error: {response.status_code}")
        else:
            data = response.json()
            status = data.get("status")
            if status != "OK" and status != "ZERO_RESULTS":
                st.error(f"Google Places API error: {status} - {data.get('error_message','')}")
            else:
                all_places.extend(data.get("results", []))
                # paginate
                while data.get("next_page_token") and len(all_places) < 60:
                    time.sleep(2)
                    pagetoken = data.get("next_page_token")
                    params_page = params.copy()
                    params_page.pop("keyword", None)  # keep same
                    params_page["pagetoken"] = pagetoken
                    response = requests.get(url, params=params_page)
                    if response.status_code != 200:
                        break
                    data = response.json()
                    all_places.extend(data.get("results", []))

                if not all_places:
                    st.info("No restaurants found with those criteria.")
                for p in all_places:
                    st.write(f"**{p.get('name','N/A')}** — Rating: {p.get('rating','N/A')} — {p.get('vicinity','')}")

# Footer
st.write("---")
st.write("Restaurant Finder • by CS Geniuses 🍴")
