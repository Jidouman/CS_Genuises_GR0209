import streamlit as st

# This function is an adapted and extended version of the roll the dice
# implementation from week 2.
def roll_the_dice(rolls, sides=6, print_results=False):
    import random  

    # face frequency counters
    # this time as a dictionary
    frequencies = {}

    # here we roll  number of rolls times
    for roll in range(rolls):
        face = random.randrange(1, sides+1)

        # increment appropriate face counter
        # this time as a dictionary
        #
        # fist we check, whether the the resulting face 
        # is in our dictonary already, then increase its
        # frequency by one 
        if face in frequencies:
            frequencies[face] += 1
        #otherwise insert this face and set it to one
        else:
            frequencies[face] = 1
    
    # we may print the results to the console
    # this, however, is not (very) useful in streamlit            
    if print_results:
        sides_len = len(str(sides))
        value_len = len(str(max(frequencies.values())))
        for key, value in sorted(frequencies.items()):
            print(f'{key:>{sides_len}}: {value:>{value_len}}')
    
    # finally we return the dictionary sorted by keys
    return dict(sorted(frequencies.items()))


# set some configurations of our app
st.set_page_config(
    page_title="Roll the dice",
    page_icon=":game_die:",
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

# set a titel and a first header of our app 
st.title("Here is our first Web Application")
st.header("Let's roll the dice :sunglasses: ", divider='rainbow')

# we partition our application's main area into two columns
col1, col2 = st.columns(2)

# in the first column we get inputs for the number of rolls
# and the type of dice we use
# for those we provide default values as well as valid ranges
with col1:
    rolls = st.number_input(
        "Number of rolls", 
        value=100, 
        min_value=1, 
        max_value=1_000_000_000, 
        placeholder="# rolls"
        )
    sides = st.number_input(
        "Number of sides the dice have", 
        value=6, 
        min_value=1, 
        max_value=100, 
        placeholder="# sides"
        )

# in the second column we have some toggle switches to configure the output
with col2:
    show_results_raw_data = st.toggle('show results as raw data ', value=False)
    show_results_bar_chart = st.toggle('show results as bar chart ', value=True)


# finally, when all is configured we define a button to roll the dice
# and show the results according to our configurations above
if st.button('Roll the dice!'):
    with st.container():
        st.header('Results')
        col_c_1, col_c_2 = st.columns(2)
        results = roll_the_dice(rolls, sides)
        with col_c_1: 
            if show_results_raw_data:
                st.write(results)
            else:
                st.data_editor(results)
        with col_c_2:
            if show_results_bar_chart:
                st.bar_chart(results)


