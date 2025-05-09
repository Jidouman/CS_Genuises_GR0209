import streamlit as st
from streamlit_js_eval import streamlit_js_eval  # For geolocation
import requests
from streamlit_javascript import st_javascript
from streamlit_geolocation import streamlit_geolocation

# Set page configuration (must be first)
st.set_page_config(page_title="Restaurant Finder", page_icon="🍴")

# Load API keys from Streamlit secrets management
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
price_range = st.multiselect(
    "Select your price range:",
    ["$", "$$", "$$$", "$$$$"]
)

# Cuisine Selection
food_type = st.selectbox(
    "Select cuisine type:",
    ["Italian", "Swiss", "Chinese", "Mexican", "Indian", "Japanese", "Thai", "American", "Turkish", "Korean", "Vietnamese"]
)

# Geolocation
st.subheader("Your Location")
location = streamlit_geolocation()
latitude = longitude = None
city = None
if location:
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude and longitude and OPENCAGE_API_KEY:
        geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={OPENCAGE_API_KEY}"
        r = requests.get(geocode_url)
        if r.status_code == 200 and r.json().get("results"):
            comp = r.json()["results"][0]["components"]
            city = comp.get("city") or comp.get("town") or comp.get("village")
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
    "Turkish": ["Turkish", "kebab", "döner", "lahmacun", "Döner", "Türkisch"],
}

# Find Restaurants
st.subheader("Find Restaurants")
if st.button("Search Restaurants"):
    if not GOOGLE_API_KEY:
        st.error("Missing API key. Cannot search.")
    elif not city:
        st.error("City not determined. Cannot search by city.")
    elif not price_range:
        st.error("Please select at least one price range.")
    else:
        # Price flags: map $ to minprice/maxprice (0–4)
        price_map = {"$": 0, "$$": 1, "$$$": 2, "$$$$": 3}
        min_price = min(price_map[pr] for pr in price_range)
        max_price = max(price_map[pr] for pr in price_range)

        # Build keyword list
        selected_cuisines = cuisine_map.get(food_type, [])
        cuisine_keyword = " ".join(selected_cuisines)

        # Build text search query by city
        query = f"restaurants in {city}"
        if cuisine_keyword:
            query += f" {cuisine_keyword}"

        params = {
            "key": GOOGLE_API_KEY,
            "query": query,
            "type": "restaurant",
            "minprice": min_price,
            "maxprice": max_price,
            "opennow": True,
            "language": "en"
        }

        # API call to Text Search endpoint
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
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
                # Sort by rating (highest first)
                places_sorted = sorted(places, key=lambda x: x.get('rating', 0), reverse=True)
                # Show only top 5
                top5 = places_sorted[:5]
                if not top5:
                    st.info("No restaurants found in your city with those criteria.")
                for p in top5:
                    st.write(f"**{p.get('name','N/A')}** — Rating: {p.get('rating','N/A')} — {p.get('formatted_address','')}")

# Footer
st.write("---")
st.write("Restaurant Finder • by CS Geniuses 🍴")

# Sidebar Navigation
page = st.sidebar.selectbox("Choose a page", ["Restaurant Finder", "Visited Restaurants"])

if page == "Restaurant Finder":
    st.title("Visited Restaurants ⭐")

    if "history" not in st.session_state:
        st.session_state.history = []

    with st.form("add_visit_form"):
        name = st.text_input("Restaurant Name")
        category = st.selectbox("Type of Restaurant", list(cuisine_map.keys()))
        rating = st.slider("Your Rating", 1, 5)
        submit = st.form_submit_button("Add to History")
        if submit and name:
            st.session_state.history.append({"name": name, "category": category, "rating": rating})
            st.success(f"Added {name} ({category}) with {rating}⭐")

    st.subheader("Your Visited Restaurants")
    if st.session_state.history:
        for entry in st.session_state.history:
            st.write(f"**{entry['name']}** ({entry['category']}) — {entry['rating']}⭐")
    else:
        st.info("No visits added yet.")