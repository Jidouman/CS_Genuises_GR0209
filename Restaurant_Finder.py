import streamlit as st
from streamlit_js_eval import streamlit_js_eval  # For geolocation
import requests
import math # For distance calculation
import datetime # For displaying closing time and remaining time of restaurants 
from streamlit_javascript import st_javascript
from streamlit_geolocation import streamlit_geolocation
from streamlit_option_menu import option_menu # For sidebar navigation
import json # For user visited restaurant save
import os # For user visited restaurant save
from collections import Counter

# test
# Set page configuration (must be first) 
st.set_page_config(page_title="Restaurant Finder", page_icon="🍴") # Icon retrieved from https://www.webfx.com/tools/emoji-cheat-sheet/

# Load API keys from Streamlit secrets management
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY") # We're using the Google Maps Places API (old) to retrieve the informations about the restaurant and places
OPENCAGE_API_KEY = st.secrets.get("OPENCAGE_API_KEY") # We're using OpenCage to retrieve the user's current location (geolocation) without manual input or typing

# Load and save visited restaurants using JSON files per user
# Source for this logic:
# - https://discuss.streamlit.io/t/saving-user-data-to-file/12840/2
# - https://realpython.com/python-json/
# - https://github.com/streamlit/streamlit/issues/4716
# We inspired ourself from when2meet.com, where you just have a link and enter your name to then load up and modify for example your availabilities (no account or sign-up needed)
# User ID (for persistence)
# Persisted History Helpers
def load_history(user):
    """Load visited_<user>.json or return [] if missing."""
    filename = f"visited_{user.lower().replace(' ', '_')}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def save_history(user, history):
    """Write out visited_<user>.json."""
    filename = f"visited_{user.lower().replace(' ', '_')}.json"
    with open(filename, "w") as f:
        json.dump(history, f, indent=2)

# Make sure we always have a slot for “who’s loaded”
if "loaded_for" not in st.session_state:
    st.session_state.loaded_for = None

# ML Cuisine Recommender
liked = [e["category"] for e in st.session_state.history if e["rating"] >= 4]
if liked:
    most_common = Counter(liked).most_common(1)[0][0]
    st.subheader("🥢 Cuisine Recommendation")
    st.info(f"Based on your preferences, you might enjoy more **{most_common}** cuisine!")

# Sidebar Navigation code retrieved from Youtube video: https://www.youtube.com/watch?v=flFy5o-2MvIE
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Restaurant Finder", "Visited Restaurants"],
        icons=["geo-alt-fill", "star-fill"],
        menu_icon="👨‍🍳",
        default_index=0
    )

# User enter the name he wants to keep track of the visited restaurants (acts as a login account)
username = st.text_input("Enter your name or alias to load/save your visited history:")
if username:
    st.success(f"👋 Happy to see you (back), {username}!")

# Whenever the input username changes, pull in their saved JSON (or empty list)
if username and st.session_state.loaded_for != username:
    st.session_state.history = load_history(username)
    st.session_state.loaded_for = username

if not username: # In case we don't have username, it allows to wipe everything when they delete their name
    st.session_state.loaded_for = None
    st.session_state.history = []

# (Optional) Initialize history list if it wasn’t loaded
if "history" not in st.session_state:
    st.session_state.history = []

# Cuisine map shared between both pages
# Note: This dictionary is used in BOTH pages (Restaurant Finder & Visited Restaurants).
# That's why it is defined here — before the conditional blocks — to ensure
# it is accessible no matter which page the user is on.
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
    "Turkish": ["Turkish", "kebab", "döner", "lahmacun", "Döner", "Türkisch"]
}

# Haversine formula to calculate great-circle distance between two lat/lon points
# Source: https://en.wikipedia.org/wiki/Haversine_formula
# This will allow us to show how far each restaurant is from the user's location
def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 1)  # return result rounded to 1 decimal place

# Function to get today's closing time for a place using Google Places Details API
# Source: https://developers.google.com/maps/documentation/places/web-service/details
# Adapted logic from: https://stackoverflow.com/questions/40745384/how-to-get-open-and-close-time-in-google-places-api
def get_closing_time(place_id, api_key):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "opening_hours",
        "key": api_key
    }
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return None

    data = res.json()
    if "result" not in data or "opening_hours" not in data["result"]:
        return None

    periods = data["result"]["opening_hours"].get("periods", [])
    # Map Python weekday (0=Mon…6=Sun) to Google Places weekday (0=Sun…6=Sat)
    py_wd = datetime.datetime.today().weekday()
    google_wd = (py_wd + 1) % 7
    now = datetime.datetime.now()

    # 1) grab the period that *starts* today
    today_period = next(
        (p for p in periods if p.get("open", {}).get("day") == google_wd),
        None
    )
    if not today_period or "close" not in today_period or not today_period["close"].get("time"):
        return "Closing info not available"

    # 2) pull out the close-day and time
    d_close = today_period["close"]["day"]
    t_close = today_period["close"]["time"]      # e.g. "2200"
    ch, cm = int(t_close[:2]), int(t_close[2:])

    # 3) build a full datetime for that closing (roll into next day if needed)
    days_ahead = (d_close - google_wd) % 7
    close_date = now.date() + datetime.timedelta(days=days_ahead)
    close_dt = datetime.datetime.combine(close_date, datetime.time(ch, cm))

    # 4) compare
    if now > close_dt:
        return """press on "Open in Google Maps" for more details"""
    # 5) return the closing time and remaining time
    remaining = close_dt - now
    hrs, rem = divmod(int(remaining.total_seconds()), 3600)
    mins = rem // 60
    return f"{ch:02d}:{cm:02d} ({hrs:02d}h{mins:02d} remaining)"

# Main Page
if selected == "Restaurant Finder":
    st.title("Restaurant Finder 🍴")
    st.write("""      
    Welcome to the Restaurant Finder! Use this app to discover restaurants in Switzerland and all over the world that match your preferences!
    Simply select your criteria below, and we'll help you find the perfect spot.
    You can also keep track of the restaurants you've visited and rate them. Enjoy your meal!""")

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

    # Find Restaurants
    st.subheader("Find Restaurants")
    # keep the search button “on” even after reruns, so sorting doesn’t clear results (before that it was resetting the result display)
    if "search_clicked" not in st.session_state:
        st.session_state.search_clicked = False
    search_pressed = st.button("Search Restaurants")
    if search_pressed:
        st.session_state.search_clicked = True

    # only run the API call & display if the user has clicked “Search” (even on reruns)
    if st.session_state.search_clicked:
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
                
                    places = data.get("results", [])
                    # Compute distance for each place so we can sort by it
                    for p in places:
                        loc = p.get("geometry", {}).get("location", {})
                        lat2 = loc.get("lat")
                        lon2 = loc.get("lng")
                        if latitude is not None and longitude is not None and lat2 is not None and lon2 is not None:
                            p["distance_km"] = calculate_distance_km(latitude, longitude, lat2, lon2)
                        else:
                            # if we don’t have coords, push it to the bottom when sorting
                            p["distance_km"] = float("inf")
                    # Let the user choose how to sort the visible results (after loading)
                    sort_by = st.selectbox("Sort restaurants by:", ["Rating", "Distance"])
                    if sort_by == "Distance":
                        places_sorted = sorted(places, key=lambda x: x["distance_km"])[:5]
                    else:
                        places_sorted = sorted(places, key=lambda x: x.get("rating", 0), reverse=True)[:5]

                    # Display with ranking, details on left and photo on right
                    for idx, p in enumerate(places_sorted, start=1):
                        name = p.get('name', 'N/A')
                        rating = p.get('rating', 'N/A')
                        address = p.get('formatted_address', '')
                        closing_info = get_closing_time(p.get("place_id"), GOOGLE_API_KEY) if p.get("place_id") else "N/A"
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(name + ' ' + city)}"
                        p_loc = p.get("geometry", {}).get("location", {})
                        rest_lat = p_loc.get("lat")
                        rest_lng = p_loc.get("lng")
                        if latitude is not None and longitude is not None and rest_lat is not None and rest_lng is not None:
                            distance_km = calculate_distance_km(latitude, longitude, rest_lat, rest_lng)
                        else:
                            distance_km = "N/A"

                        # Create two columns: text and image
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"""
    **{idx}. {name}**  
    Rating: {rating}  
    {address}  
    Distance from you: {distance_km} km  
    Closing info: {closing_info}
    """)
                            # Google Maps link button
                            maps_url = f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(name + ' ' + city)}"
                            st.markdown(
                                f'<a href="{maps_url}" target="_blank"><button style="padding:6px 12px; border-radius:4px;">Open in Google Maps</button></a>',
                                unsafe_allow_html=True
                         )
                        with col2:
                            photos = p.get('photos')
                            if photos:
                                photo_ref = photos[0].get('photo_reference')
                                photo_url = (
                                    f"https://maps.googleapis.com/maps/api/place/photo"
                                    f"?maxwidth=200&photoreference={photo_ref}&key={GOOGLE_API_KEY}"
                                )
                                st.image(photo_url, width=200)
                        st.write("---")

# Visited Restaurants Page
# This page allows users to keep track of restaurants they have visited and rate them.
# 📝 This approach is inspired by the Streamlit community and official docs on using `st.session_state`to accumulate user input over time during an interactive session:
# - https://docs.streamlit.io/library/api-reference/session-state
# - https://discuss.streamlit.io/t/accumulating-user-inputs-in-a-list/21171/2
# - https://www.kanaries.net/blog/building-a-chat-app-with-streamlit#handling-user-messages-and-state
elif selected == "Visited Restaurants":
    st.title("Visited Restaurants ⭐")
    if not username: # To ensure we can keep track of the visited reataurants ID, we invite the user to enter their name or username!
        st.warning("Enter your name to save/load history. Otherwise, history won't persist.")

    # Ensure there's at least a list to append to
    if "history" not in st.session_state:
        st.session_state.history = []

    with st.form("add_visit_form"):
        name = st.text_input("Restaurant Name")
        category = st.selectbox("Type of Restaurant", list(cuisine_map.keys()))
        rating = st.slider("Your Rating", 1, 5)
        submit = st.form_submit_button("Add to History")
        if submit and name:
            new_entry = {"name": name, "category": category, "rating": rating}
            st.session_state.history.append(new_entry)
            st.success(f"Added {name} ({category}) with {rating}⭐")

            # Save to JSON file if username is provided
            if username:
                save_history(username, st.session_state.history)

    # Button to clear history
    if username and st.session_state.history: # Hide “Reset my history” when there’s nothing to reset
        if st.button("Reset my history"): 
            st.session_state.history = []
            save_history(username, [])
            st.success("Your history has been cleared.")
    
    # Display Visited Restaurants
    st.subheader("Your Visited Restaurants")
    if st.session_state.history:
        for entry in st.session_state.history:
            st.write(f"**{entry['name']}** ({entry['category']}) — {entry['rating']}⭐")
    else:
        st.info("No visits added yet.")
# Footer
st.write("---")
st.write("Restaurant Finder • by CS Geniuses 🍴 • Powered by Google Maps and OpenCage")