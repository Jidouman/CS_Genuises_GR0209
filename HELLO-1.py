# Required Libraries
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Tab Title
st.set_page_config(page_title="FCS Streamlit Tutorial", page_icon=":computer:")

# Title & Intro
st.title("Hello, FCS!")
st.write("""
Welcome to the interactive Streamlit tutorial tailored for FCS bachelor students! 
Here's a introductory showcase of what you can achieve using Streamlit with very little code.
""")

# Text Input
st.subheader("Text Input")
name = st.text_input("Enter your name", placeholder="Your name here...")
if name != "":
    st.write(f"Hello, {name}! Welcome to FCS!")

# Buttons
st.subheader("Buttons")
if st.button("About"):
    st.write("This is a Streamlit tutorial for FCS bachelor students!")
    st.write("""
             Streamlit is an open-source Python library designed to simplify the process of creating web applications 
             and interactive dashboards for data science and machine learning. With its intuitive framework, 
             developers and data professionals can transform scripts into shareable web applications in just a few lines
             of code, without requiring any knowledge of web development. 
             At its core, Streamlit operates by rerunning the entire script from top to bottom each time 
             there's an interaction, ensuring that the app's state is always in sync with the user's inputs. 
             To use Streamlit, one simply needs to write a Python script, insert Streamlit-specific functions for 
             interactivity, and then run the script using the streamlit run command. 
             The result is a reactive application hosted locally in a web browser, which can then be easily 
             shared with others. Its seamless integration with data-centric libraries such as Pandas and Matplotlib, 
             along with its growing community and rich ecosystem, makes Streamlit a go-to choice for rapid application
             development in the data domain.
             """)
else:
    st.write("Click the button to learn more about this tutorial.")

# Radio Buttons
st.subheader("Radio Buttons")
department = st.radio(
    "Select your department",
    ("Finance", "Marketing", "IT", "Operations")
)
st.write(f"You've selected {department} as your department!")

# Date Input
st.subheader("Date Input")
date = st.date_input("Select a date")

# Progress Bar
st.subheader("Progress Bar")

# plot how much time of the year has already passed
if date:
    # get first day of the year of the selected date
    day_one = date.replace(month=1, day=1)
    # calculate percentage of year passed
    year_passed = (date - day_one).days / 365
    # show progress bar on screen
    st.progress(year_passed)
    st.write(f"{year_passed*100:.2f}% of the year has passed at {date.strftime('%d/%m/%Y')}")

  
# Interactive Plotting
st.subheader("Interactive Plotting")

# Generate random sales data
np.random.seed(23)  # for reproducibility
n_days = 30
sales_data = np.random.randint(1, 100, size=n_days)
dates = pd.date_range(start="2023-01-01", periods=n_days, freq="D")


# Convert to Streamlit plot
st.subheader("Sales Plot")
st.line_chart(pd.Series(sales_data, index=dates))

# Checkbox
st.subheader("Interactive Checkbox")
if st.checkbox("Show Top 5 Sales Days"):
    top_5_sales = pd.Series(sales_data, index=dates).nlargest(5)
    st.write(top_5_sales)

# Selectbox
st.subheader("Selectbox: Favourite Data Analytics Tools")
tools = ["Python", "Excel", "Tableau", "Power BI", "SAP", "R", "SQL"]
fav_tool = st.selectbox("Which is your favorite data anaylitcs tool?", tools)

# Do something with the selected tool
if fav_tool == "Python":
    st.write("Great choice! Python is a powerful programming language.")
elif fav_tool == "R":
    st.write("R is a great tool for data analysis.")
else:
    st.write("That's a nice tool!")

# Multiselect
st.subheader("Multiselect: Modules of Interest")
modules = [
    "Investment Analysis",
    "Digital Marketing",
    "Talent Management",
    "Supply Chain Optimization",
    "Business Ethics",
]
selected_modules = st.multiselect("Select the modules you're interested in:", modules)
for module in selected_modules:
    st.write(f"📘 {module}")

# Slider
st.subheader("Slider")
gpa = st.slider("Select your GPA", min_value=1.0, max_value=6.0, step=0.1, value=3.5)
st.write(f"Your GPA is: {gpa}")

# Show Chart, gauss distribution from 1-6, and show the selected GPA
st.subheader("GPA Distribution")
x = np.linspace(1, 6, 100)
# Adjusted the gaussian distribution parameters for a better fit between 1-6
y = 1 / (1 * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((x - 3.5) / 1) ** 2)

# Create dataframe for area chart
df = pd.DataFrame({"GPA": x, "Density": y})

# Plotting a vertical line for the selected GPA on the same graph requires 
# a bit more control, such as with Matplotlib. So, let's do that.
fig, ax = plt.subplots(figsize=(8, 5))
ax.fill_between(df["GPA"], df["Density"], color="lightblue", label="GPA Distribution")
ax.axvline(gpa, color="red", linestyle="--", label=f"Your GPA: {gpa}")
ax.legend(loc="upper left")
ax.set_xlabel("GPA")
ax.set_ylabel("Density")
st.pyplot(fig)

# Numerical approximation to the error function
def erf_approx(x):
    # Constants
    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911

    sign = 1 if x >= 0 else -1
    x = abs(x)

    t = 1.0 / (1.0 + p * x)
    y = (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t

    return sign * (1 - y * np.exp(-x * x))

# Compute the percentile using the CDF of the normal distribution
mu = 3.5  # mean
sigma = 1  # standard deviation
percentile = 0.5 * (1 + erf_approx((gpa - mu) / (sigma * np.sqrt(2))))

st.write(f"With a GPA of {gpa}, you're in the {percentile*100:.2f} percentile.")

st.header("Setting Up Streamlit")
# Markdown
st.markdown("""
            ### Setting Up Streamlit with Anaconda Environments

            Anaconda is a powerful platform for Python and R languages, simplifying package management and deployment. By using Anaconda, you can create isolated environments to run different projects, ensuring that dependencies do not interfere with each other. Here's how to set up Streamlit within an Anaconda environment:

            ### 1. **Install Anaconda**:
            If you haven't installed Anaconda yet, download and install it from the [official Anaconda website](https://www.anaconda.com/products/distribution).

            ### 2. **Create a New Environment**:
            After installation, open the Anaconda Navigator or the terminal (on Linux/Mac) or command prompt (on Windows) and create a new environment using the following command:
            ```bash
            conda create --name streamlit_env python=3.8
            ```
            Replace `streamlit_env` with your desired environment name and `3.8` with your preferred Python version, if different.

            ### 3. **Activate the Environment**:
            To use the new environment, you need to activate it:
            ```bash
            conda activate streamlit_env
            ```

            ### 4. **Install Streamlit**:
            With the environment activated, install Streamlit using pip:
            ```bash
            pip install streamlit
            ```

            ### 5. **Running Streamlit Apps**:
            Now, you can run any Streamlit app within this environment. For example, to run the default Streamlit app, use:
            ```bash
            streamlit hello
            ```

            ### 6. **Deactivate the Environment**:
            Once you're done working with Streamlit, you can deactivate the Anaconda environment:
            ```bash
            conda deactivate
            ```

            By following this setup, you ensure that Streamlit and its dependencies are contained within a specific Anaconda environment, preventing any potential conflicts with other Python projects or libraries.
                
    """)

# Working with external packages
st.markdown("""
            ### Managing and Installing Python Libraries in Streamlit

            In the world of Python and Streamlit, libraries are collections of functions and methods that allow you to perform actions without writing your own code. Sometimes, to run a Streamlit app, you'll need to install specific libraries. Here's how you can do that:

            ### 1. **Installing Libraries**:
            You can install required libraries using `pip`, the package installer for Python. Simply open your terminal or command prompt and use the following command:
            ```bash
            pip install library-name
            ```
            For instance, to install Streamlit, you'd use:
            ```bash
            pip install streamlit
            ```

            ### 2. **Saving Library Versions for Sharing**:
            If you're developing a Streamlit app that you intend to share with others, it's crucial to ensure that everyone uses the same versions of libraries to avoid compatibility issues. Here's how to save and share your library versions:

            - First, save the versions of all libraries you have installed in a file called `requirements.txt` using this command:
            ```bash
            pip freeze > requirements.txt
            ```
            - When someone else needs to run your Streamlit app, they can install the exact versions of the required libraries using:
            ```bash
            pip install -r requirements.txt
            ```

            This approach ensures that everyone has the necessary libraries at the correct versions to run your Streamlit app seamlessly!

            ### 3. **Running this Streamlit App**:
            First, clone the [github repository](https://github.com/hawk-li/fcs-streamlit-intro) or download and extract the zip file containing this Streamlit app. Then, navigate to the directory containing this Streamlit app using the terminal or command prompt.
            Make sure you have created and activated a new Anaconda environment as described in the previous section.
            ```bash	
            cd path/to/streamlit-tutorial
            ```
            Second, install the required libraries using the `requirements.txt` file:
            ```bash
            pip install -r requirements.txt
            ```
            Then, run this Streamlit app using:
            ```bash
            streamlit run app.py
            ```
            """)


# Documentation & Guidance
st.subheader("Documentation & Guidance")
st.write("""
To dive deeper into Streamlit and its capabilities, students are encouraged to:

1. Visit the [official Streamlit documentation](https://docs.streamlit.io/)
2. Explore the [Streamlit gallery for inspiration](https://streamlit.io/gallery)
3. Check out [30 days of Streamlit](https://30days.streamlit.app/) for a guided introduction to Streamlit
4. Check out the [Streamlit cheatsheet](https://cheat-sheet.streamlit.app/) for a quick overview of Streamlit's features
5. Check out the [Streamlit tutorial](https://docs.streamlit.io/en/stable/tutorial/index.html) for a more detailed introduction
6. Check out the [Streamlit API reference](https://docs.streamlit.io/en/stable/api.html) for a detailed overview of Streamlit's API
7. Check out the [Streamlit extras](https://extras.streamlit.app/) for additional features
8. Check out the [Streamlit community](https://discuss.streamlit.io/) for help

Happy Learning!
""")

# Footer
st.write("---")
st.write("FCS Streamlit Tutorial • Designed with ❤️ for Bachelor Students in Business Administration")