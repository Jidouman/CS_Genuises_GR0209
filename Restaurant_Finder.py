import streamlit as st
from streamlit_js_eval import streamlit_js_eval  # For geolocation
import requests
from streamlit_javascript import st_javascript  # For opening links client-side
from streamlit_geolocation import streamlit_geolocation
from streamlit_option_menu import option_menu  # For sidebar navigation

# Page config
st.set_page_config(page_title="Restaurant Finder", page_icon="🍴")

# API keys
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
OPENCAGE_API_KEY = st.secrets.get("OPENCAGE_API_KEY")

# Sidebar navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Restaurant Finder", "Visited Restaurants"],
        icons=["geo-alt-fill", "star-fill"],
        menu_icon="👨‍🍳",
        default_index=0
    )

# Shared cuisine map
cuisine_map = {
    "Italian": ["Italian", "pizzeria", "pizza", "ristorante"],
    "Swiss":   ["Swiss", "fondue", "raclette", "Schweizer"],
    "Chinese": ["Chinese", "dim sum", "noodle"],
    "Mexican": ["Mexican", "taco", "burrito"],
    "Indian":  ["Indian", "curry", "naan"],
    "Thai":    ["Thai", "pad thai", "green curry"],
    "Japanese": ["Japanese", "sushi", "ramen"],
    "Korean":  ["Korean", "kimchi", "bibimbap"],
    "Vietnamese": ["Vietnamese", "pho", "banh mi"],
    "American": ["American", "burger", "steakhouse"],
    "Turkish": ["Turkish", "kebab", "döner"]
}

# Restaurant Finder Page
if selected == "Restaurant Finder":
    st.title("Restaurant Finder 🍴")
    st.write("Use this app to discover restaurants in Switzerland. Select criteria below.")

    # Inputs
    price_range = st.multiselect("Select your price range:", ["$", "$$", "$$$", "$$$$"])
    food_type = st.selectbox("Select cuisine type:", list(cuisine_map.keys()))

    # Geolocation
    st.subheader("Your Location")
    location = streamlit_geolocation()
    city = None
    if location:
        lat, lon = location.get("latitude"), location.get("longitude")
        if lat and lon and OPENCAGE_API_KEY:
            res = requests.get(
                f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={OPENCAGE_API_KEY}"
            ).json()
            if res.get("results"):
                comp = res["results"][0]["components"]
                city = comp.get("city") or comp.get("town") or comp.get("village")
                st.write(f"**You are in {city}** — {lat}, {lon}")
            else:
                st.write("Unable to fetch city name.")
        else:
            st.write(f"Coordinates: {lat}, {lon}")
    else:
        st.write("Enable location services.")

    # Search
    if st.button("Search Restaurants"):
        if not (GOOGLE_API_KEY and city and price_range):
            st.error("Missing input or API key.")
        else:
            # Build query
            price_map = {"$":0, "$$":1, "$$$":2, "$$$$":3}
            min_p = min(price_map[p] for p in price_range)
            max_p = max(price_map[p] for p in price_range)
            keywords = " ".join(cuisine_map[food_type])
            query = f"restaurants in {city} {keywords}"

            params = {
                "key": GOOGLE_API_KEY,
                "query": query,
                "minprice": min_p,
                "maxprice": max_p,
                "opennow": True
            }
            places = requests.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json", params=params
            ).json().get("results", [])

            # Ensure session history exists
            if "history" not in st.session_state:
                st.session_state.history = []

            # Display top 5
            for idx, p in enumerate(sorted(places, key=lambda x: x.get("rating",0), reverse=True)[:5], start=1):
                name = p.get("name","N/A")
                rating = p.get("rating","N/A")
                addr = p.get("formatted_address","")
                maps_url = (
                    "https://www.google.com/maps/search/?api=1&query=" +
                    requests.utils.quote(f"{name} {city}")
                )

                col1, col2 = st.columns([3,1])
                with col1:
                    # Basic info
                    st.markdown(f"**{idx}. {name}**  \nRating: {rating}  \n{addr}")
                    # Show user rating if exists
                    user_rating = next((e["rating"] for e in st.session_state.history if e["name"].lower()==name.lower()), None)
                    if user_rating is not None:
                        st.markdown(f"Your rating: ⭐{user_rating}")

                    # Auto-save & open map
                    if st.button("Visit & Open Google Maps"):
                        if not any(e["name"].lower()==name.lower() for e in st.session_state.history):
                            st.session_state.history.append({"name":name,"category":food_type,"rating":0})
                            st.success(f"{name} added to your visited list.")
                        else:
                            st.info(f"{name} already visited.")
                        st_javascript(f"window.open('{maps_url}')")

                with col2:
                    photo_ref = p.get("photos",[])
                    if photo_ref:
                        url = (
                            "https://maps.googleapis.com/maps/api/place/photo?maxwidth=200" +
                            f"&photoreference={photo_ref[0]['photo_reference']}&key={GOOGLE_API_KEY}"
                        )
                        st.image(url, width=150)
                st.markdown("---")

# Visited Restaurants Page
elif selected == "Visited Restaurants":
    st.title("Visited Restaurants ⭐")
    if "history" not in st.session_state:
        st.session_state.history = []

    with st.form("add_visit_form"):
        n = st.text_input("Restaurant Name")
        c = st.selectbox("Type of Restaurant", list(cuisine_map.keys()))
        r = st.slider("Your Rating",1,5)
        if st.form_submit_button("Add to History") and n:
            st.session_state.history.append({"name":n,"category":c,"rating":r})
            st.success(f"Added {n} ({c}) — {r}⭐")

    st.subheader("Your Visited Restaurants")
    if st.session_state.history:
        for e in st.session_state.history:
            st.write(f"**{e['name']}** ({e['category']}) — {e['rating']}⭐")
    else:
        st.info("No visits yet.")

# Footer
st.markdown("---")
st.write("Restaurant Finder • by CS Geniuses 🍴 • Powered by Google Maps and OpenCage")