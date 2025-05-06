# Importieren der verschiedenen Bibliotheken
import streamlit as st # Streamlit
from streamlit_javascript import st_javascript # Streamlit_javascript Geolocation via JavaScript based on: https://www.w3schools.com/html/html5_geolocation.asp
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt # Datenvisualisierung
import requests # API requests
import json # JSON handling
import datetime # Date handling
import time # Time handling

# Tab Title
st.set_page_config(page_title="Restaurant Recommender", page_icon="🍴") #We retrieved the emoji codepoint for page_icon from the website https://www.webfx.com/tools/emoji-cheat-sheet/

# Title & Intro
st.title("🍽️ Restaurant Recommender")
st.write("""
Welcome to the Restaurant Recommender App! 🎯 
Tell us what you're **craving**, your **mood**, your **budget**, and how **far** you're willing to travel — and we'll suggest the perfect restaurant for you. 
Feeling adventurous? Hit **Surprise Me** and discover a hidden gem!
""")

# Function to get city name from latitude and longitude
def get_city_from_coords(lat, lon):
    try:
        # Replace 'YOUR_API_KEY' with your actual API key from OpenCage or Google Maps
        api_key = "YOUR_API_KEY"
        url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={api_key}"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data["results"]:
            # Extract city name from the response
            components = data["results"][0]["components"]
            city = components.get("city", components.get("town", components.get("village", "Unknown location")))
            return city
        else:
            return "Unable to determine location"
    except Exception as e:
        return f"Error: {str(e)}"

# Get coordinates via JavaScript
coords = st_javascript("await navigator.geolocation.getCurrentPosition((loc) => loc.coords)")

# If we already got them on load, show them
if coords and isinstance(coords, dict) and "latitude" in coords:
    lat, lon = coords["latitude"], coords["longitude"]
    st.success(f"📍 Your location: {lat:.4f}, {lon:.4f}")
else:
    st.info("Click the button below to allow location access.")

if st.button("📍 Get my location"):
    coords = st_javascript(
        """
        new Promise((resolve) => {
            if (!navigator.geolocation) {
                return resolve({error: "Geolocation not supported"});
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
                (err) => resolve({error: err.message})
            );
        });
        """,
        key="get_loc"
    )

    if not coords:
        st.error("No response from browser geolocation API.")
    elif coords.get("error"):
        st.error(f"Could not get location: {coords['error']}")
    else:
        lat, lon = coords["latitude"], coords["longitude"]
        st.success(f"📍 Your coordinates: {lat:.4f}, {lon:.4f}")

        # Get city name from coordinates
        city = get_city_from_coords(lat, lon)
        st.info(f"🌍 You are in: {city}")

st.header("Tell us what you're craving:")

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
    ["Italian", "Chinese", "Mexican", "Indian", "Japanese", "American", "Mediterranean", "Vegan", "Seafood"]
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

# Submit Button
if st.button("Find Restaurants"):
    st.write("Searching for restaurants...")
    # Placeholder for API integration
    st.write("This feature will use APIs to fetch restaurant data based on your preferences.")
    st.write(f"Price Range: {price_range}")
    st.write(f"Food Type: {', '.join(food_type) if food_type else 'Any'}")
    st.write(f"Mood: {mood}")
    st.write(f"Distance: {distance} miles")
else:
    st.write("Fill in your preferences and click 'Find Restaurants' to start your search!")

# Footer
st.write("---")
st.write("Restaurant Finder • Powered by Streamlit 🍴")
