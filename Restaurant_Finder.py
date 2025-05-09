import streamlit as st
from streamlit_js_eval import streamlit_js_eval  # For geolocation
import requests
from streamlit_javascript import st_javascript
from streamlit_geolocation import streamlit_geolocation

# Set page configuration (must be first)
st.set_page_config(page_title="Restaurant Finder", page_icon="🍴")

# Load API keys from Streamlit secrets management, retreieve from https://docs.streamlit.io/develop/concepts/connections/secrets-management
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
OPENCAGE_API_KEY = st.secrets.get("OPENCAGE_API_KEY")

# Title and Introduction
st.title("Restaurant Finder 🍴")
st.write("""
Welcome to the Restaurant Finder! Use this app to discover restaurants in Switzerland that match your preferences.
Simply select your criteria below, and we'll help you find the perfect spot.
""")

# User Inputs
st.subheader("Search Criteria")

# Price Range
price_range = st.selectbox(
    "Select your price range:",
    ["$", "$$", "$$$", "$$$$"]
)

# Cuisine Selection
food_type = st.multiselect(
    "What type of food are you in the mood for?",
    ["Italian", "Swiss", "Chinese", "Mexican", "Indian", "Japanese", "Thai", "American", "Turkish","Korean", "Vietnamese"],
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
    "Italian": ["Italian", "pizzeria", "pizza", "ristorante", "Italienisch", "Pasta", "Spaghetti"],
    "Swiss":   ["Swiss", "Schweizer", "restaurant", "fondue", "raclette", "Alpenküche"],
    "Chinese": ["Chinese", "dim sum", "noodle", "szechuan", "Chinesisch"],
    "Mexican": ["Mexican", "taco", "burrito", "enchilada", "Mexikanisch", "Tacos"],
    "Indian":  ["Indian", "curry", "tandoori", "masala", "naan", "Indisch", "Curry"],
    "Thai":    ["Thai", "pad thai", "green curry", "red curry", "Tom Yum", "Thailändisch"],
    "Japanese": ["Japanese restaurant", "sushi", "ramen", "izakaya", "udon", "tempura", "Japanisch", "Sushi"],
    "Korean":  ["Korean", "kimchi", "bulgogi", "bibimbap", "Koreanisch", "Korean BBQ"],
    "Vietnamese": ["Vietnamese", "pho", "banh mi", "spring rolls", "Vietnamese restaurant", "Vietnamesisch"],
    "American": ["American", "burger", "steakhouse", "grill", "fast food", "Amerikanisch", "Burger"],
    "Turkish": ["Turkish", "kebab", "doner", "lahmacun", "Turkish restaurant", "Türkisch"],
}


# Find Restaurants
st.subheader("Find Restaurants")
if st.button("Search Restaurants"):
    if not (latitude and longitude and GOOGLE_API_KEY):
        st.error("Missing location or API key. Cannot search.")
    else:
        # 1. Price flags: map $ to minprice/maxprice (0–4)
        price_map = {"$": (0, 1), "$$": (1, 2), "$$$": (2, 3), "$$$$": (3, 4)}
        min_price, max_price = price_map[price_range]

        # Radius
        radius_m = distance * 1000

        # Build keyword list
        selected_cuisines = [term for ft in food_type for term in cuisine_map.get(ft, [])]
        keyword = " ".join(selected_cuisines)

        # Build params dict
        params = {
            "key": GOOGLE_API_KEY,
            "location": f"{latitude},{longitude}",
            "radius": radius_m,
            "type": "restaurant",
            "keyword": keyword,
            "minprice": min_price,
            "maxprice": max_price,
            "opennow": True,
            "language": "en"
        }

        # API call
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params=params
        )
        
        if resp.status_code != 200:
            st.error(f"HTTP Error: {resp.status_code}")
        else:
            data = resp.json()
            if data.get("status") != "OK":
                st.error(f"Error: {data.get('status')} - {data.get('error_message','')}")
            else:
                places = data.get("results", [])
                if not places:
                    st.info("No restaurants found with those criteria.")
                for p in places:
                    st.write(f"**{p.get('name','N/A')}** — Rating: {p.get('rating','N/A')} — {p.get('vicinity','')}")

# Footer
st.write("---")
st.write("Restaurant Finder • by CS Geniuses 🍴")