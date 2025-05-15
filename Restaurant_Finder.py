# ── Allgemeine Hinweise ─────────────────────────────────────────────────────────
# 1. Die Google Maps Plattform (Legacy Places API) erlaubt bis zu 25 000 freie Text-Suchanfragen
#    innerhalb von 24 Stunden; danach fallen die üblichen Gebühren pro Anfrage an.
#    Daher verwenden wir in diesem Projekt keinen Ersatz-API-Schlüssel.
# 2. Für Debugging und Feinschliff haben wir ChatGPT eingesetzt, insbesondere
#    bei der Einbindung der Google Maps API.
# 3. Nutzer-„Visited“-Daten werden in JSON-Dateien namens visited_<username>.json
#    direkt neben dem Skript gespeichert – daher ist keine externe Datenbank nötig.
#    Wir halten das für einen guten Kompromiss aus Einfachheit und Funktionsumfang.
# 4. Wir haben Google Übersetzer zur Übersetzung der Dokumentation von Englisch auf Deutsch verwendet.
# ───────────────────────────────────────────────────────────────────────────────

import streamlit as st # Core-Bibliothek von Streamlit für die UI-Erstellung
import pandas as pd # Datenaufbereitung & DataFrame-Support für Diagramme und Tabellen
from streamlit_js_eval import streamlit_js_eval  # Für Geolocation im Browser via JS
import requests # HTTP-Client für Aufrufe an Google Maps und OpenCage APIs
import math # Zur Entfernungsberechnung (mit der Haversine-Formel)
import datetime # Zur Anzeige der Schließzeiten und der verbleibenden Öffnungszeiten von Restaurants
from streamlit_javascript import st_javascript # Alternative JS-Ausführung in Streamlit (Fallback zur Geolokalisierung)
from streamlit_geolocation import streamlit_geolocation # Einfache Breiten-/Längenauswahl über die Geolokalisierungs-API des Browsers
from streamlit_option_menu import option_menu # Für die Seitenleistennavigation
import json # Zum Speichern besuchter Restaurants
import os # Zum Speichern besuchter Restaurants (Verlaufsdateien prüfen/schreiben)
import pandas as pd # Zur Datenmanipulation und Anzeige von Balkendiagrammen besuchter Restaurants
from collections import Counter # Zum Zählen der Küchenarten in besuchten Restaurants
from sklearn.model_selection import train_test_split # ML-Daten in Trainings-/Testdatensätze aufteilen
from sklearn.ensemble import RandomForestClassifier # Random-Forest-Klassifikator für ML-Preis-/Küchenvorhersagen
from sklearn.metrics import classification_report # Zur Bewertung von ML Modellleistung (Präzision/Küchen-Prognosen/usw.)
from imblearn.over_sampling import RandomOverSampler # Für den Umgang mit unausgewogenen Klassen in ML-Daten

# Seitenkonfiguration festlegen (muss zuerst erfolgen) 
st.set_page_config(page_title="Restaurant Finder", page_icon="🍴") # Icon abgerufen von https://www.webfx.com/tools/emoji-cheat-sheet/

# API-Schlüssel aus der Streamlit-Geheimnisverwaltung laden (um die Weitergabe unserer API-Schlüssel zu verhindern, da unser GitHub-Repository öffentlich ist)
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY") # Wir verwenden die Google Maps Places API (alt), um Informationen zu Restaurants und Orten abzurufen
OPENCAGE_API_KEY = st.secrets.get("OPENCAGE_API_KEY") # Wir verwenden OpenCage, um den aktuellen Standort des Nutzers (Geolokalisierung) ohne manuelle Eingabe abzurufen

# Helfer für persistenten Verlauf
# Wir speichern die Besuchsliste jedes Benutzers in visited_<username>.json neben diesem Skript -> Abgerufen und angepasst von: https://stackoverflow.com/questions/67761908/save-login-details-to-json-using-python
# Wir haben uns von when2meet.com inspirieren lassen. Dort muss man nur einen Link eingeben und seinen Namen eingeben, um beispielsweise seine Verfügbarkeiten zu laden und zu ändern (kein Konto oder Anmeldung erforderlich).
# Dies ermöglicht das Laden und Speichern besuchter Restaurants mithilfe von JSON-Dateien pro Benutzer.
# Weitere Quellen zum Verständnis der Logik: https://realpython.com/python-json/
def load_history(user):
    """Load visited_<user>.json or return [] if missing."""
    filename = f"visited_{user.lower().replace(' ', '_')}.json" # Dateinamen durch Kleinbuchstaben und Ersetzen von Leerzeichen durch Unterstriche erstellen
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f) # Gespeicherten Verlauf entsprechend dem Benutzer analysieren und zurückgeben
    return [] # Noch keine Datei → mit leerem Verlauf beginnen

def save_history(user, history):
    """Write out visited_<user>.json."""
    filename = f"visited_{user.lower().replace(' ', '_')}.json" # Dateinamen durch Kleinbuchstaben und Ersetzen von Leerzeichen durch Unterstriche erstellen (wie zuvor beim Laden)
    with open(filename, "w") as f: # Datei im Schreibmodus öffnen
        json.dump(history, f, indent=2) # JSON-Formatierung mit zwei Leerzeichen Einrückung für bessere Lesbarkeit

# Daten laden
@st.cache_data # Daten zwischenspeichern, um ein erneutes Laden zu vermeiden (sonst werden die Daten beim Wechseln der Navigationsseite neu geladen)
def load_ml_data():
    return pd.read_csv("merged_output_ML.csv") # Daten aus der CSV-Datei (merged_output_ML.csv) laden, um die ML-Modelle zu trainieren

# Streamlit App 
# Sicherstellen, dass immer ein Slot für „Wer ist geladen?“ vorhanden ist.
if "loaded_for" not in st.session_state:
    st.session_state.loaded_for = None

# Seitenleisten-Navigationscode aus YouTube-Video: https://www.youtube.com/watch?v=flFy5o-2MvIE
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Restaurant Finder", "Visited Restaurants", "Restaurant Recommender"],
        icons=["geo-alt-fill", "star-fill", "robot"],
        menu_icon="👨‍🍳",
        default_index=0
    )

# Küchenkarte wird von beiden Seiten genutzt
# Hinweis: Dieses Wörterbuch wird auf BEIDEN Seiten (Restaurantsuche & Besuchte Restaurants) verwendet.
# Deshalb wird es hier – vor den Bedingungsblöcken – definiert, um sicherzustellen, dass es unabhängig von der Seite, auf der sich der Nutzer befindet, zugänglich ist.
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
    "American": ["American", "burger", "steakhouse", "grill", "fast food", "Amerikanisch", "Burger", "Steak", "Fast_Food"],
    "Bar": ["Bar", "pub", "tavern", "biergarten", "Biergarten", "Cocktails", "Wine Bar"],
    "Café": ["Café", "Coffe", "Cafeteria", "Bakery", "Breakfast", "Brunch", "Café-Coffee_Shop", "Breakfast-Brunch", "dessert"],
    "Eastern Mediterranean": ["Eastern Mediterranean", "Armenian", "Mediterranean", "Lebanese", "Middle Eastern", "Armenisch", "Mediterranean", "Libanesisch", "Turkish", "kebab", "döner", "lahmacun", "Döner", "Türkisch"],
    "Seafood": ["Seafood", "Fish", "Sushi", "Crab", "Shrimp", "Tuna", "Salmon", "Scallops", "Oysters", "Shellfish", "Seafood restaurant", "Meeresfrüchte", "Fisch", "Mussels","Muscheln"],
    "Chef's Cuisine": ["Chef's Cuisine", "Gourmet", "Fine Dining", "Contemporary", "Game", "International", "Modern Cuisine", "Modern-Fusion Cuisine"],
}

# Haversine-Formel zur Berechnung der Großkreisdistanz zwischen zwei Breiten- und Längenpunkten
# Quelle: https://en.wikipedia.org/wiki/Haversine_formula
# Dadurch können wir die Entfernung jedes Restaurants vom Standort des Nutzers anzeigen.
def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371  # Radius der Erde in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 1)  # Ergebnis auf 1 Dezimalstelle gerundet zurückgeben

# Funktion zum Abrufen der heutigen Schließzeit eines Ortes mithilfe der Google Places Details API
# Quelle: https://developers.google.com/maps/documentation/places/web-service/details
# Angepasste Logik von: https://stackoverflow.com/questions/40745384/how-to-get-open-and-close-time-in-google-places-api
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
    # Ordnen Sie den Python-Wochentag (0=Mo…6=So) dem Google Places-Wochentag (0=So…6=Sa) zu (da Python standardmäßig mit Montag und Google mit Sonntag beginnt)
    py_wd = datetime.datetime.today().weekday()
    google_wd = (py_wd + 1) % 7
    now = datetime.datetime.now()

    # Schnapp dir den Zeitraum, der heute *beginnt*
    today_period = next(
        (p for p in periods if p.get("open", {}).get("day") == google_wd),
        None
    )
    if not today_period or "close" not in today_period or not today_period["close"].get("time"):
        return "Closing info not available"

    # Ziehen Sie den Schließtag und die Uhrzeit heraus
    d_close = today_period["close"]["day"]
    t_close = today_period["close"]["time"]      # e.g. "2200"
    ch, cm = int(t_close[:2]), int(t_close[2:])

    # Erstellen Sie eine vollständige Datums- und Uhrzeitangabe für diesen Abschluss (ggf. auf den nächsten Tag verschieben)
    days_ahead = (d_close - google_wd) % 7
    close_date = now.date() + datetime.timedelta(days=days_ahead)
    close_dt = datetime.datetime.combine(close_date, datetime.time(ch, cm))

    # Vergleichen
    if now > close_dt:
        return """press on "Open in Google Maps" for more details"""
    # Rückgabe der Schließzeit und der Restzeit
    remaining = close_dt - now
    hrs, rem = divmod(int(remaining.total_seconds()), 3600)
    mins = rem // 60
    return f"{ch:02d}:{cm:02d} ({hrs:02d}h{mins:02d} remaining)"

# Hauptseite
if selected == "Restaurant Finder":
    st.title("Restaurant Finder 🍴")
    st.write("""      
    Welcome to the Restaurant Finder! Use this app to discover restaurants in Switzerland and all over the world that match your preferences!
    Simply select your criteria below, and we'll help you find the perfect spot.
    You can also keep track of the restaurants you've visited and rate them. Enjoy your meal!""")

    # Benutzereingaben
    st.subheader("Search Criteria")

    # Preisklasse
    price_range = st.multiselect(
        "Select your price range:",
        ["$", "$$", "$$$"]
    )

    # Küchenauswahl
    food_type = st.selectbox(
    "Select cuisine type:",
    list(cuisine_map.keys())
)

    # Geolokalisierung über die OpenCage-API -> Quelle: https://opencagedata.com/api
    st.subheader("Your Location")
    location = streamlit_geolocation() # Standort des Nutzers über die Browser-Geolokalisierungs-API ermitteln
    latitude = longitude = None # Breiten- und Längengrad initialisieren
    city = None # Städtenamen initialisieren
    if location:
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        if latitude and longitude and OPENCAGE_API_KEY:
            geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={OPENCAGE_API_KEY}"
            r = requests.get(geocode_url) # Rufen Sie die OpenCage-API auf, um den Städtenamen abzurufen
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

    # Restaurants finden
    st.subheader("Find Restaurants")
    # Lassen Sie die Suchschaltfläche auch nach Wiederholungen eingeschaltet, damit die Ergebnisse beim Sortieren nicht gelöscht werden (vorher wurde die Ergebnisanzeige zurückgesetzt).
    if "search_clicked" not in st.session_state:
        st.session_state.search_clicked = False
    search_pressed = st.button("Search Restaurants")
    if search_pressed:
        st.session_state.search_clicked = True

    # Führen Sie den API-Aufruf und die Anzeige nur aus, wenn der Benutzer auf „Suchen“ geklickt hat (auch bei Wiederholungen).
    if st.session_state.search_clicked:
        if not GOOGLE_API_KEY:
            st.error("Missing API key. Cannot search.")
        elif not city:
            st.error("City not determined. Cannot search by city.")
        elif not price_range:
            st.error("Please select at least one price range.")
        else:
            # Preisflaggen: Ordnen Sie $ dem Mindestpreis/Höchstpreis zu (0–3)
            price_map = {"$": 0, "$$": 1, "$$$": 2, "$$$": 3}
            min_price = min(price_map[pr] for pr in price_range)
            max_price = max(price_map[pr] for pr in price_range)

            # Keyword-Liste erstellen
            selected_cuisines = cuisine_map.get(food_type, [])
            cuisine_keyword = " ".join(selected_cuisines)

            # Erstellen Sie eine Textsuchabfrage nach Stadt
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

            # API-Aufruf zum Textsuchendpunkt
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
                    # Berechnen Sie die Entfernung für jeden Ort, damit wir danach sortieren können
                    for p in places:
                        loc = p.get("geometry", {}).get("location", {})
                        lat2 = loc.get("lat")
                        lon2 = loc.get("lng")
                        if latitude is not None and longitude is not None and lat2 is not None and lon2 is not None:
                            p["distance_km"] = calculate_distance_km(latitude, longitude, lat2, lon2)
                        else:
                            # Wenn wir keine Koordinaten haben, verschieben wir sie beim Sortieren nach unten
                            p["distance_km"] = float("inf")
                    # Lassen Sie den Benutzer entscheiden, wie die sichtbaren Ergebnisse sortiert werden sollen (nach dem Laden).
                    sort_by = st.selectbox("Sort restaurants by:", ["Rating", "Distance"])
                    if sort_by == "Distance":
                        places_sorted = sorted(places, key=lambda x: x["distance_km"])[:5]
                    else:
                        places_sorted = sorted(places, key=lambda x: x.get("rating", 0), reverse=True)[:5]

                    # Anzeige mit Rangliste, Details links und Foto rechts
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

                        # Erstellen Sie zwei Spalten: Text und Bild
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"""
    **{idx}. {name}**  
    Rating: {rating}  
    {address}  
    Distance from you: {distance_km} km  
    Closing info: {closing_info}
    """)
                            # Google Maps-Link-Schaltfläche
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

# Seite „Besuchte Restaurants“
# Auf dieser Seite können Nutzer ihre besuchten Restaurants verfolgen und bewerten.
# Dieser Ansatz ist inspiriert von der Streamlit-Community und den offiziellen Dokumenten zur Verwendung von „st.session_state“, um Nutzereingaben während einer interaktiven Sitzung im Laufe der Zeit zu sammeln:
# - https://docs.streamlit.io/library/api-reference/session-state
# - https://discuss.streamlit.io/t/accumulating-user-inputs-in-a-list/21171/2
elif selected == "Visited Restaurants":
    st.title("Visited Restaurants ⭐")
    # Der Benutzer gibt den Namen ein, unter dem er die besuchten Restaurants verfolgen möchte (fungiert als Login-Konto)
    username = st.text_input("Enter your name or alias to load/save your visited history:")
    if username:
        st.success(f"👋 Happy to see you (back), {username}!")

    # Immer wenn sich der eingegebene Benutzername ändert, wird das gespeicherte JSON (oder die leere Liste) eingebunden.
    if username and st.session_state.loaded_for != username:
        st.session_state.history = load_history(username)
        st.session_state.loaded_for = username

    if not username: # Falls wir keinen Benutzernamen haben, können wir alles löschen, wenn wir unseren Namen löschen.
        st.session_state.loaded_for = None
        st.session_state.history = []

    # (Optional) Verlaufsliste initialisieren, falls sie nicht geladen wurde
    if "history" not in st.session_state:
        st.session_state.history = []
    if not username: # Damit wir den Überblick über die besuchten Restaurants behalten können, bitten wir den Benutzer, seinen Namen oder Benutzernamen einzugeben!
        st.warning("Enter your name to save/load history. Otherwise, history won't persist.")

    # ML Cuisine-Empfehlung
    liked = [e["category"] for e in st.session_state.history if e["rating"] >= 4]
    if liked:
        most_common = Counter(liked).most_common(1)[0][0]
        st.subheader("🥢 Cuisine Recommendation")
        st.info(f"Based on your preferences, you might enjoy more **{most_common}** cuisine!")
    
    # Stellen Sie sicher, dass mindestens eine Liste vorhanden ist, an die Sie anhängen können
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

            # In JSON-Datei speichern, wenn Benutzername angegeben ist
            if username:
                save_history(username, st.session_state.history)

    # Schaltfläche zum Löschen des Verlaufs
    if username and st.session_state.history: # „Verlauf zurücksetzen“ ausblenden, wenn nichts zurückzusetzen ist
        if st.button("Reset my history"): 
            st.session_state.history = []
            save_history(username, [])
            st.success("Your history has been cleared.")
    
    # Besuchte Restaurants anzeigen
    st.subheader("Your Visited Restaurants")
    if st.session_state.history:
        # 1) jeden Besuch anzeigen
        for entry in st.session_state.history:
            st.write(f"**{entry['name']}** ({entry['category']}) — {entry['rating']}⭐")
        # 2) dann erstellen und zeigen Sie das Balkendiagramm nur einmal
        df = pd.DataFrame(st.session_state.history)
        counts = df["category"].value_counts()
        st.subheader("🍽️ Your Visits by Cuisine")
        st.bar_chart(counts)
        
    else:
        st.info("No visits added yet.")

# Trainieren von Machine-Learning-Modellen
@st.cache_resource
def train_models(df):
    features = ['drink_level', 'dress_preference', 'hijos', 'birth_year', 'activity'] # define which features to use for the model
    
    # Jede Textkategorie (z. B. „Italienisch“, „Chinesisch“) wird in separate 0/1-Spalten (Dummy-/Indikatorvariablen) umgewandelt, damit das Modell sie verarbeiten kann.
    df_encoded = pd.get_dummies(df[features]) # Quelle: pandas.get_dummies-Dokumentation → https://pandas.pydata.org/docs/reference/api/pandas.get_dummies.html
    # Preismodell
    # Preisstufen sind bereits numerisch (0–4, in unserer App verwenden wir das „$“-Symbol zur Darstellung), sodass wir sie direkt verwenden können
    y_price = df['price'] # target variable for price
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(df_encoded, y_price, test_size=0.2, random_state=42) 
    model_price = RandomForestClassifier(class_weight='balanced')
    model_price.fit(X_train_p, y_train_p) # Handle imbalanced classes using RandomOverSampler

    # Küchenmodell
    # Die Küche ist kategorisch, daher müssen wir sie ebenfalls kodieren.
    # Wir verwenden dieselben Merkmale wie zuvor, wollen nun aber den Küchentyp vorhersagen.
    y_cuisine = df['Rcuisine'] # Zielvariable für den Küchentyp
    ros = RandomOverSampler(random_state=42) # Apply RandomOverSampler (to handle imbalanced classes)
    X_resampled, y_resampled = ros.fit_resample(df_encoded, y_cuisine)
    
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42)
    
    model_cuisine = RandomForestClassifier(class_weight='balanced')
    model_cuisine.fit(X_train_c, y_train_c)

    return model_price, model_cuisine, df_encoded.columns # return both models plus the ordered list of feature columns used for training

# Restaurant-Empfehlungsseite
# Auf dieser Seite können Nutzer Restaurantpreise und Gerichte basierend auf ihrem Profil vorhersagen.
if selected == "Restaurant Recommender":
    st.title("Restaurant Preference Predictor")
    st.write("Fill out the form below to get restaurant price and cuisine predictions based on your profile.")

    # Geolokalisierung mithilfe der OpenCage-API -> Quelle: https://opencagedata.com/api
    st.subheader("Your Location")
    location = streamlit_geolocation()  # Ermitteln Sie den Standort des Benutzers mithilfe der Geolocation-API des Browsers
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

    # Inputs
    drink_level = st.selectbox("Drink Level", ['abstinent', 'casual drinker', 'social drinker'])
    dress_preference = st.selectbox("Dress Preference", ['casual', 'elegant', 'no preference'])
    hijos = st.selectbox("Children", ['''doesn't matter''', '''doesn't have''', 'has'])
    birth_year = st.number_input("Birth Year", min_value=1940, max_value=2025, value=1999)
    activity = st.selectbox("Professional Activity", ['active', 'no preference', 'student', 'unemployed'])

   

    if st.button("Predict Preferences"):
        df = load_ml_data()
        model_price, model_cuisine, model_columns = train_models(df)
        input_df = pd.DataFrame([...])
        input_final = input_df.reindex(columns=model_columns, fill_value=0)
        predicted_price = model_price.predict(input_final)[0]
        predicted_cuisine = model_cuisine.predict(input_final)[0]

         # Werte für jede Spalte des trainierten Datensatzes festlegen. Aufgrund der Funktion get_dummies müssen wir die Werte für jede Spalte des trainierten Datensatzes festlegen.
        #für den Getränkestand
    if drink_level == 'abstinent':
        drink_level_abstemious = True
        drink_level_casual_drinker = False
        drink_level_social_drinker = False
    elif drink_level == 'casual drinker':
        drink_level_abstemious = False
        drink_level_casual_drinker = True
        drink_level_social_drinker = False
    else:
        drink_level_abstemious = False
        drink_level_casual_drinker = False
        drink_level_social_drinker = True

    #für die Kleidervorlieben
    if dress_preference == 'casual':
        dress_preference_q =False
        dress_preference_elegant = False
        dress_preference_formal = False
        dress_preference_informal = True
        dress_preference_nopreference = False
    elif dress_preference == 'elegant':
        dress_preference_q =False
        dress_preference_elegant = True
        dress_preference_formal = True
        dress_preference_informal = False
        dress_preference_nopreference = False
    else:
        dress_preference_q =True
        dress_preference_elegant = True
        dress_preference_formal = True
        dress_preference_informal = True
        dress_preference_nopreference = True

    #für die Kinder
    if hijos == '''doesn't matter''':
        hijos_indifferent = True
        hijos_dependent = True
        hijos_independent = True #unabhängige und erwachsene Kinder sind nicht relevant
        hijos_yes = True
    elif hijos == '''doesn't have''':
        hijos_indifferent = False
        hijos_dependent = False
        hijos_independent = True #unabhängige und erwachsene Kinder sind nicht relevant
        hijos_yes = False
    else: 
        hijos_indifferent = False
        hijos_dependent = True
        hijos_independent = False
        hijos_yes = True

    #für die Aktivität
    if activity == 'active':
        activity_q = False
        activity_professional = True
        activity_student = False
        activity_unemployed = False
        activity_working_class = True # Arbeiterklasse und Berufstätige sind beide aktiv
    elif activity == 'no preference':
        activity_q = True
        activity_professional = True
        activity_student = True
        activity_unemployed = True
        activity_working_class = True
    elif activity == 'student':
        activity_q = False
        activity_professional = False
        activity_student = True
        activity_unemployed = False
        activity_working_class = False
    else:
        activity_q = False
        activity_professional = False
        activity_student = False
        activity_unemployed = True
        activity_working_class = False

    # Datenrahmen mit Eingaben vorhersagen und erstellen
    if st.button("Predict Preferences", key="predict_preferences_button"):
        df = load_ml_data()
        model_price, model_cuisine, model_columns = train_models(df)
        input_df = pd.DataFrame([{'birth_year': birth_year,'drink_level_abstemious': drink_level_abstemious,'drink_level_casual drinker': drink_level_casual_drinker,'drink_level_social drinker': drink_level_social_drinker,'dress_preference_?': dress_preference_q,'dress_preference_elegant': dress_preference_elegant,'dress_preference_formal': dress_preference_formal,'dress_preference_informal': dress_preference_informal,'dress_preference_no preference': dress_preference_nopreference,'hijos_?': hijos_indifferent,'hijos_dependent': hijos_dependent,'hijos_independent': hijos_independent,'hijos_kids': hijos_yes,'activity_?': activity_q,'activity_professional': activity_professional,'activity_student': activity_student,'activity_unemployed': activity_unemployed,'activity_working-class': activity_working_class,}])
        input_final = input_df.reindex(columns = model_columns, fill_value=0)
        predicted_price = model_price.predict(input_final)[0]
        predicted_cuisine = model_cuisine.predict(input_final)[0]

# Konvertieren Sie das vorhergesagte Preisniveau in eine Zeichenfolgendarstellung, um es an die Restaurant Finder-Seite anzupassen
        if predicted_price == "low":
            predicted_price = "$"
        elif predicted_price == "medium":
            predicted_price = "$$"
        elif predicted_price == "high":
            predicted_price = "$$$"
 # Konvertieren Sie die vorhergesagten Küchenkategorien des von uns verwendeten Datensatzes, um sie mit den Küchenkategorien der Restaurant Finder-Seite abzugleichen    
        if predicted_cuisine == "Italian" or predicted_cuisine == "Pizzeria":
            predicted_cuisine = "Italian"
        elif predicted_cuisine == "Bar" or predicted_cuisine == "Bar_Pub_Brewery":
            predicted_cuisine = "Bar"
        elif predicted_cuisine == "American" or predicted_cuisine == "Fast_Food" or predicted_cuisine == "Burgers"or predicted_cuisine == "Family":
            predicted_cuisine = "American"
        elif predicted_cuisine == "Cafeteria" or predicted_cuisine == "Cafe-Coffee_Shop" or predicted_cuisine == "Breakfast-Brunch" or predicted_cuisine == "Bakery":
            predicted_cuisine = "Café"
        elif predicted_cuisine == "Armenian" or predicted_cuisine == "Mediterranean":
            predicted_cuisine = "Eastern Mediterranean"
        elif predicted_cuisine == "International"or predicted_cuisine == "Contemporary" or predicted_cuisine == "Game":
            predicted_cuisine = "Chef's Cuisine"
        elif predicted_cuisine == "Regional":
            predicted_cuisine = "Swiss"

        st.success(f"Predicted Price Level: {predicted_price}")
        st.success(f"Suggested Cuisine: {predicted_cuisine}")

        # Rufen Sie weiterhin Restaurants basierend auf vorhergesagten Parametern und bereits abgerufenen Standorten ab …
        if city and latitude and longitude:
            query = f"restaurants in {city}"
            if predicted_cuisine:
                query += f" {predicted_cuisine}"

            price_map = {"$": 0, "$$": 1, "$$$": 2}
            price_value = price_map.get(predicted_price, 1)

            params = {
                "key": GOOGLE_API_KEY,
                "query": query,
                "type": "restaurant",
                "minprice": price_value,
                "maxprice": price_value,
                "opennow": True,
                "language": "en"
            }

            resp = requests.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params=params
            )

            if resp.status_code != 200:
                st.error(f"HTTP Error: {resp.status_code}")
            else:
                data = resp.json()
                if data.get("status") == "ZERO_RESULTS":
                    st.warning("😕 No restaurant like that exists near you. Try changing the cuisine or price level.")
                elif data.get("status") != "OK":
                    st.error(f"Error: {data.get('status')} - {data.get('error_message','')}")
                else:
                    places = data.get("results", [])
                    if not places:
                        st.warning("😕 No restaurant like that exists near you. Try changing the cuisine or price level.")
                    for p in places:
                        loc = p.get("geometry", {}).get("location", {})
                        lat2 = loc.get("lat")
                        lon2 = loc.get("lng")
                        if latitude is not None and longitude is not None and lat2 is not None and lon2 is not None:
                            p["distance_km"] = calculate_distance_km(latitude, longitude, lat2, lon2)
                        else:
                            p["distance_km"] = float("inf")

                    sort_by = st.selectbox("Sort restaurants by:", ["Rating", "Distance"])
                    if sort_by == "Distance":
                        places_sorted = sorted(places, key=lambda x: x["distance_km"])[:5]
                    else:
                        places_sorted = sorted(places, key=lambda x: x.get("rating", 0), reverse=True)[:5]

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

                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"""
        **{idx}. {name}**  
        Rating: {rating}  
        {address}  
        Distance from you: {distance_km} km  
        Closing info: {closing_info}
        """)
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


# Footer
st.write("---")
st.write("Restaurant Finder • by CS Geniuses 🍴 • Powered by Google Maps and OpenCage")