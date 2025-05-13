import streamlit as st
from pygame import mixer # handling music files
import glob # working with OS files and directories

def get_tracks(folder='', file_type='mp3'):
    if not folder == '' and not folder.endswith('/'):
        folder += '/'
    return glob.glob(f"{folder}*.{file_type}")

def play_track(filename):
    # st.audio(filename, format="audio/mpeg", loop=False) #this is a streamlit native function as an alternative
    mixer.init()
    mixer.music.load(track)
    mixer.music.play()

def stop_playback():
    mixer.music.stop()

# set some configurations of our app
st.set_page_config(
    page_title="Music Player v01",
    page_icon=":sound:",
    layout="centered",
    initial_sidebar_state="auto",
)

# the sidebar contains links to some useful resources
st.sidebar.write('''
    ## About _streamlit_
    [Streamlit](https://streamlit.io/) is a Python library that 
    allows the creation of interactive, data-driven web applications 
    in Python.

    ## Resources
    - [Streamlit Documentation](https://docs.streamlit.io/)
    - [Cheat sheet](https://docs.streamlit.io/library/cheatsheet)
    - [30 Days of Streamlit](https://30days-tmp.streamlit.app/)
    ''')

# set a titel of our app 
st.title("Play my music")

# we partition our application's main area into two columns
col1, col2 = st.columns(2)

# in the first column we get inputs 
with col1:
    folder = st.text_input("Folder", "music")
    track = st.selectbox("Which track to play?",get_tracks(folder))

# in the second column we have some player buttons
with col2:
    if st.button('play'):
        play_track(track)
    if st.button('stop'):
        stop_playback()


