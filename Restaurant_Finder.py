# Importieren der verschiedenen Bibliotheken
import streamlit as st # Streamlit
from streamlit_javascript import st_javascript # Streamlit_javascript Geolocation via JavaScript based on: https://www.w3schools.com/html/html5_geolocation.asp
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt # Datenvisualisierung
import os # Dateimanagement
import requests # API requests
import json # JSON handling
import datetime # Date handling
import time # Time handling

# Tab Title
st.set_page_config(page_title="Restaurant Recommender", page_icon="🍴") #We retrieved the emoji codepoint for page_icon from the website https://www.webfx.com/tools/emoji-cheat-sheet/

# Title & Intro
st.title("🍽️ Restaurant Recommender")
st.write("""
Welcome to the Restaurant Finder! Use this app to discover restaurants that match your preferences. Simply select your criteria below, and we'll help you find the perfect spot.
Feeling adventurous? Hit **Surprise Me** and discover a hidden gem!
""")

# Function to get city name from latitude and longitude
if st.button("📍 Get my location"):
    # 1) Browser geolocation
    coords = st_javascript(
        """
        new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject("Geolocation not supported");
                return;
            }
            navigator.geolocation.getCurrentPosition(
                pos => resolve([pos.coords.latitude, pos.coords.longitude]),
                err => reject(err.message || "Permission denied")
            );
        });
        """,
        key="get_loc",
    )

    if isinstance(coords, list) and len(coords) == 2:
        lat, lon = coords
        st.write(f"🗺️ Coordinates: {lat:.5f}, {lon:.5f}")

        # 2) Reverse-geocode with your provided key
        GOOGLE_API_KEY = "AIzaSyDYHYia7dhNnqbIvpxveK6gaipW9z0_zX4"
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"latlng": f"{lat},{lon}", "key": GOOGLE_API_KEY}
        resp = requests.get(geocode_url, params=params).json()

        if resp.get("status") == "OK" and resp.get("results"):
            address = resp["results"][0]["formatted_address"]
            st.success(f"🏠 Your address: **{address}**")
        else:
            st.error("❌ Could not retrieve address from coordinates.")
    else:
        st.warning(f"Could not get location: {coords}")
else:
    st.info("Click the button above to allow location access and see your address.")
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
    ["Italian", "Swiss", "Mexican", "Indian", "Japanese", "Chinese", "Mediterranean", "Vegan", "Seafood", "American"]
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