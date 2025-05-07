import streamlit as st
from streamlit_js_eval import streamlit_js_eval  # For geolocation
import requests
from streamlit_javascript import st_javascript
from streamlit_geolocation import streamlit_geolocation


# Set page configuration
st.set_page_config(page_title="Restaurant Finder", page_icon="🍴")

# Title and Introduction
st.title("Restaurant Finder 🍴🇨🇭")
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
st.write("Click the button below:")

location = streamlit_geolocation()

if location:
    latitude = location.get("latitude", "N/A")
    longitude = location.get("longitude", "N/A")
    
    # Reverse Geocoding to get city name
    if latitude != "N/A" and longitude != "N/A":
        geocoding_api_url = f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key=dab40f92430549bcb3b5f3c0144d911b"
        response = requests.get(geocoding_api_url)
        if response.status_code == 200:
            data = response.json()
            city = data['results'][0]['components'].get('city') or \
                   data['results'][0]['components'].get('town') or \
                   data['results'][0]['components'].get('village') or \
                   'Unknown Location'
            st.write(f"**You are in** **{city}** - {latitude}, {longitude}")
        else:
            st.write("Unable to fetch city name. Please check your API key or network connection.")
    else:
        st.write("Invalid coordinates received.")
else:
    st.write("Unable to fetch location. Please enable location services in your browser.")

# Function to fetch restaurants using Google Places API


# Footer
st.write("---")
st.write("Restaurant Finder • by CS Geniuses 🍴")