import streamlit as st
import requests
from streamlit_js_eval import streamlit_js_eval  # For geolocation
from streamlit_javascript import st_javascript
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

# Price Range
price_range = st.selectbox(
    "Select your price range:",
    ["$", "$$", "$$$", "$$$$"]
)

# Type of Food
food_type = st.multiselect(
    "What type of food are you in the mood for?",
    ["Italian", "Swiss", "Chinese", "Mexican", "Indian", "Japanese", "American", "Mediterranean", "Vegan", "Seafood"]
)

# Mood
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
st.write("Click the button below to share your location:")
location = streamlit_geolocation()

latitude = longitude = None
if location:
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude and longitude and OPENCAGE_API_KEY:
        geocoding_api_url = (
            f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}"
            f"&key={OPENCAGE_API_KEY}"
        )
        resp = requests.get(geocoding_api_url)
        if resp.status_code == 200:
            comp = resp.json()['results'][0]['components']
            city = comp.get('city') or comp.get('town') or comp.get('village') or 'Unknown'
            st.write(f"**You are in** **{city}** — {latitude}, {longitude}")
        else:
            st.write("Unable to fetch city name. Please check OPENCAGE_API_KEY.")
    elif latitude and longitude:
        st.write(f"Coordinates: {latitude}, {longitude}")
    else:
        st.write("Invalid coordinates received.")
else:
    st.write("Unable to fetch location. Please enable location services in your browser.")

# Find Restaurants
st.subheader("Find Restaurants")
if st.button("Search Restaurants"):
    if not latitude or not longitude:
        st.error("Location not available. Cannot search without coordinates.")
    elif not GOOGLE_API_KEY:
        st.error("Missing GOOGLE_API_KEY; cannot call Google Places API.")
    else:
        # 1. Price flags: map $ to minprice/maxprice (0–4)
        price_map = {"$": (0, 1), "$$": (1, 2), "$$$": (2, 3), "$$$$": (3, 4)}
        min_price, max_price = price_map[price_range]

        # 2. Open now flag
        open_now = True

        # 3. Distance radius: convert km to meters
        radius_m = distance * 1000

        # 4. Keywords: combine food types + mood
        mood_map = {
            "Casual": "casual",
            "Romantic": "romantic",
            "Family-Friendly": "family",
            "Business": "business",
            "Trendy": "trendy",
            "Quiet": "quiet"
        }
        food_keywords = " ".join(food_type)
        mood_keyword = mood_map.get(mood, "")
        keyword = f"{food_keywords} {mood_keyword}".strip()

        # 5. Type
        place_type = "restaurant"

        # 6. Language
        language = "en"

        # Build request parameters
        params = {
            "key": GOOGLE_API_KEY,
            "location": f"{latitude},{longitude}",
            "radius": radius_m,
            "type": place_type,
            "keyword": keyword,
            "minprice": min_price,
            "maxprice": max_price,
            "opennow": open_now,
            "language": language
        }

        # Call the API
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params=params
        )

        # Show debug info
        st.write("🔍 Debug params:", params)

        # Handle response
        if response.status_code != 200:
            st.error(f"HTTP Error: {response.status_code}")
        else:
            data = response.json()
            status = data.get("status")
            if status != "OK":
                st.error(f"Google Places API error: {status} — {data.get('error_message','')}" )
            else:
                places = data.get("results", [])
                if not places:
                    st.info("No restaurants found for those filters.")
                for p in places:
                    name = p.get("name", "N/A")
                    rating = p.get("rating", "N/A")
                    vicinity = p.get("vicinity", "")
                    st.write(f"**{name}** — Rating: {rating} — {vicinity}")

# Footer
st.write("---")
st.write("Restaurant Finder • by CS Geniuses 🍴")
