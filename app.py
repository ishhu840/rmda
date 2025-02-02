import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt

# NASA POWER API Base URL
BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Hide Streamlit status bar
hide_bar = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div.st-emotion-cache-1kyxreq {
            display: none !important;
        }
    </style>
"""
st.markdown(hide_bar, unsafe_allow_html=True)

# Function to fetch climate data
def fetch_nasa_data(lat, lon, start, end, parameters):
    params = {
        "parameters": ",".join(parameters),
        "community": "AG",  # Agriculture community
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "format": "JSON"
    }
    
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")
    
    data = response.json()
    if "properties" not in data or "parameter" not in data["properties"]:
        raise Exception("No climate data found for the given parameters.")
    
    # Extract climate data into a dictionary of DataFrames
    result = {}
    for param in parameters:
        if param in data["properties"]["parameter"]:
            df = pd.DataFrame(
                data["properties"]["parameter"][param].items(), 
                columns=["Date", param]
            )
            result[param] = df
        else:
            st.warning(f"Parameter '{param}' is not available for the given location and time range.")
    
    return result

# Process data for monthly trends
def process_monthly_data(data):
    data["Date"] = pd.to_datetime(data["Date"])
    data["Year"] = data["Date"].dt.year
    data["Month"] = data["Date"].dt.month
    monthly_avg = data.groupby(["Year", "Month"]).mean().reset_index()
    return monthly_avg

# Dengue case data
dengue_data = {
    "Year": [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
    "Jan": [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    "Feb": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "Mar": [0, 0, 1, 2, 0, 0, 0, 0, 1, 2, 1],
    "Apr": [0, 0, 0, 5, 0, 2, 0, 0, 0, 0, 1],
    "May": [0, 0, 2, 13, 0, 2, 1, 0, 0, 0, 3],
    "Jun": [0, 0, 2, 7, 0, 1, 2, 0, 0, 5, 9],
    "Jul": [1, 2, 0, 7, 0, 14, 27, 1, 2, 9, 25],
    "Aug": [1, 2, 55, 22, 6, 9, 684, 4, 12, 420, 148],
    "Sep": [36, 51, 813, 412, 135, 98, 4686, 16, 420, 1912, 1044],
    "Oct": [396, 907, 2317, 2053, 386, 444, 5581, 13, 2126, 2106, 1112],
    "Nov": [408, 479, 603, 770, 122, 142, 961, 0, 948, 565, 361],
    "Dec": [19, 15, 124, 16, 1, 4, 0, 4, 17, 20, 34],
    "Total": [861, 1456, 3917, 3307, 651, 717, 11942, 38, 3526, 5039, 2738]
}

# Convert dengue cases to DataFrame
dengue_df = pd.DataFrame(dengue_data)
dengue_df = pd.melt(dengue_df, id_vars=["Year"], var_name="Month", value_name="Dengue Cases")

# Convert month names to numbers
month_mapping = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}
dengue_df["Month"] = dengue_df["Month"].map(month_mapping)

# Streamlit App
st.title("Climate Impact on Dengue Cases and Mosquito Population Growth Trends in Rawalpindi, Pakistan")
st.markdown("**Analyze the correlation between temperature, rainfall, and dengue cases over the past years (2013 - 2023).**")

# Inputs
start_date = "20130101"  # Start date for the past 10 years
end_date =  "20231201"   
lat, lon = 33.6, 73.0  # Central coordinates for Rawalpindi

# Parameters for the analysis
parameters = ["T2M", "PRECTOTCORR"]  # Temperature & corrected precipitation

# Fetch and process data
st.info("Fetching climate data from NASA POWER API...")
try:
    climate_data = fetch_nasa_data(lat, lon, start_date, end_date, parameters)
    
    # Merge climate data
    all_data = []
    for param, df in climate_data.items():
        all_data.append(df)
    combined_data = pd.concat(all_data, axis=1).loc[:, ~pd.concat(all_data, axis=1).columns.duplicated()]
    
    # Convert dates and compute monthly trends
    combined_data["Date"] = pd.to_datetime(combined_data["Date"])
    monthly_data = process_monthly_data(combined_data)

    # Merge dengue data
    final_df = pd.merge(monthly_data, dengue_df, on=["Year", "Month"], how="left")

    # Display visual trends
    st.subheader("Monthly Trends of Temperature, Rainfall, and Dengue Cases")
    
    monthly_data = monthly_data[monthly_data["T2M"] >= -5]
    monthly_data = monthly_data[monthly_data["PRECTOTCORR"] >= 0]
    
    # Temperature vs Dengue Cases per Month
    if "T2M" in final_df:
        fig = px.line(final_df, x="Month", y="T2M", color="Year", 
                      title="Monthly Temperature Trends (°C)", 
                      labels={"T2M": "Temperature (°C)", "Month": "Month", "Year": "Year"})
        st.plotly_chart(fig)

    # Rainfall vs Dengue Cases per Month
    if "PRECTOTCORR" in final_df:
        fig = px.line(final_df, x="Month", y="PRECTOTCORR", color="Year", 
                      title="Monthly Rainfall Trends (mm)", 
                      labels={"PRECTOTCORR": "Rainfall (mm)", "Month": "Month", "Year": "Year"})
        st.plotly_chart(fig)

    # Dengue Cases per Month
    fig = px.line(final_df, x="Month", y="Dengue Cases", color="Year", 
                  title="Monthly Dengue Cases", 
                  labels={"Dengue Cases": "Dengue Cases", "Month": "Month", "Year": "Year"})
    st.plotly_chart(fig)

    # Yearly Overview of Dengue Cases, Temperature, and Rainfall
    st.subheader("Yearly Overview")
    year_avg = final_df.groupby("Year").agg({"T2M": "mean", "PRECTOTCORR": "mean", "Dengue Cases": "sum"}).reset_index()

    fig = px.line(year_avg, x="Year", y=["T2M", "PRECTOTCORR"], 
                  title="Yearly Temperature and Rainfall Trends",
                  labels={"Year": "Year", "value": "Value"})
    st.plotly_chart(fig)

    # Yearly Dengue Cases
    fig = px.bar(year_avg, x="Year", y="Dengue Cases", 
                 title="Yearly Dengue Cases", 
                 labels={"Dengue Cases": "Dengue Cases", "Year": "Year"})
    st.plotly_chart(fig)

    # Display the table in Streamlit
    df = pd.DataFrame(dengue_data)

    # Display the table in Streamlit
    st.title('Dengue Cases Over the Years')
    st.table(df)
    

except Exception as e:
    st.error(f"Error fetching data: {e}")

# Function to compute and display correlation with year and month info
def display_correlation_with_year_month(df):
    # Compute correlation matrix for T2M, PRECTOTCORR, and Dengue Cases
    correlation_matrix = df[["T2M", "PRECTOTCORR", "Dengue Cases"]].corr()
    

    # Create scatter plots with trendlines and year-month information
    st.subheader("Scatter Plots with Trendlines (Year and Month Info)")
    
    # Temperature vs Dengue Cases
    fig_temp_dengue = px.scatter(df, x="T2M", y="Dengue Cases", trendline="ols", 
                                 title="Temperature vs Dengue Cases (Year and Month Info)", 
                                 labels={"T2M": "Temperature (°C)", "Dengue Cases": "Dengue Cases"},
                                 hover_data=["Year", "Month"])
    st.plotly_chart(fig_temp_dengue)

    # Rainfall vs Dengue Cases
    fig_rain_dengue = px.scatter(df, x="PRECTOTCORR", y="Dengue Cases", trendline="ols", 
                                 title="Rainfall vs Dengue Cases (Year and Month Info)", 
                                 labels={"PRECTOTCORR": "Rainfall (mm)", "Dengue Cases": "Dengue Cases"},
                                 hover_data=["Year", "Month"])
    st.plotly_chart(fig_rain_dengue)

# Call the new function to display correlation with year and month info
display_correlation_with_year_month(final_df)


# Ensure 'Year' and 'Month' columns are added to the DataFrame
def add_year_month_column(df):
    if 'Year' not in df.columns:
        # Assuming 'Date' column is in YYYY-MM-DD format
        df['Year'] = pd.to_datetime(df['Date'], errors='coerce').dt.year
    if 'Month' not in df.columns:
        df['Month'] = pd.to_datetime(df['Date'], errors='coerce').dt.month_name()  # Month as name (e.g., January)
    return df

# Function to create a more advanced graphical representation of the correlation
def advanced_visual_representation(df):
    # Ensure Year and Month columns are present
    df = add_year_month_column(df)
    
    # Update column names to match those in the final dataframe
    temperature_column = "T2M"  # Assuming T2M is the temperature column
    rainfall_column = "PRECTOTCORR"  # Assuming PRECTOTCORR is the rainfall column

    # 3D scatter plot for Temperature, Rainfall, Dengue Cases, and Month
    st.subheader("3D Scatter Plot: Temperature, Rainfall, Dengue Cases, and Month")
    fig_3d = px.scatter_3d(df, x=temperature_column, y=rainfall_column, z="Dengue Cases", color="Month", 
                           title="3D Scatter Plot of Temperature, Rainfall, Dengue Cases, and Month",
                           labels={temperature_column: "Temperature (°C)", rainfall_column: "Rainfall (mm)", "Dengue Cases": "Dengue Cases"})
    
    # Adjust the layout to set the 3D plot's width and height to a larger size
    fig_3d.update_layout(scene=dict(
                        xaxis_title="Temperature (°C)",
                        yaxis_title="Rainfall (mm)",
                        zaxis_title="Dengue Cases"),
                        width=1000,  # width of the plot (increased size)
                        height=800  # height of the plot (increased size)
    )
    
    # Show the plot with container width set to true for better view
    st.plotly_chart(fig_3d, use_container_width=True)

    # Pair plot for Temperature, Rainfall, and Dengue Cases
    st.subheader("Pair Plot: Temperature, Rainfall, and Dengue Cases by Month")
    pair_plot_data = df[[temperature_column, rainfall_column, "Dengue Cases", "Year", "Month"]]
    
    # Create a pair plot using seaborn
    sns.set(style="ticks")
    pair_plot = sns.pairplot(pair_plot_data, kind="scatter", hue="Month", palette="viridis")
    pair_plot.fig.suptitle("Pair Plot of Temperature, Rainfall, and Dengue Cases by Month", y=1.02)

    # Display pair plot using Streamlit
    st.pyplot(pair_plot.fig)

# Call the function to display advanced visualizations
advanced_visual_representation(final_df)


####################

def clear_heatmap_representation(df):
    # Ensure Year and Month columns are present
    df = add_year_month_column(df)
    
    # Update column names to match those in the final dataframe
    temperature_column = "T2M"  # Assuming T2M is the temperature column
    rainfall_column = "PRECTOTCORR"  # Assuming PRECTOTCORR is the rainfall column

    # Group the data by Month to calculate mean Temperature, Rainfall and sum Dengue Cases
    df_monthly = df.groupby(['Month']).agg(
        {temperature_column: 'mean', rainfall_column: 'mean', 'Dengue Cases': 'sum'}).reset_index()
    
    # Create a heatmap using Plotly
    fig_heatmap = px.imshow(df_monthly.set_index('Month').T,
                            title="Heatmap - Temperature, Rainfall & Dengue Cases by Month",
                            labels={"color": "Values"},
                            x=df_monthly['Month'], y=df_monthly.columns[1:], 
                            color_continuous_scale="RdYlGn",  # Better color scale for clarity
                            aspect="auto")

    # Update the layout for better readability
    fig_heatmap.update_layout(
        xaxis_title="Month",
        yaxis_title="Metrics",
        title_x=0.5,  # Center the title
        title_y=0.95,  # Move title slightly upwards
        margin=dict(l=50, r=50, t=50, b=50)  # Add some margin around the plot
    )

    # Display the heatmap with annotations
    fig_heatmap.update_traces(texttemplate="%{z:.2f}", text=df_monthly.values.T, hoverinfo="text")
    
    # Show the plot in Streamlit
    st.subheader("Heatmap: Temperature, Rainfall, and Dengue Cases by Month")
    st.plotly_chart(fig_heatmap, use_container_width=True)

# Call the function to display the enhanced heatmap
clear_heatmap_representation(final_df)

########################



# Data: Mosquito population findings and trends
data = {
    "Year": [2016, 2024],
    "Mosquito Population (Aedes aegypti)": [3484 * 0.46, None],  # Estimate based on Aedes aegypti proportion
    "Mosquito Population (Aedes albopictus)": [3484 * 0.54, None],  # Estimate based on Aedes albopictus proportion
    "Dengue Larvae Sites Detected (2024)": [None, 8064],  # Data for 2024 larvae sites
    "Homes with Dengue Larvae (2024)": [None, 6735],  # Homes data for 2024
    "Outdoor Locations with Dengue Larvae (2024)": [None, 1361],  # Outdoor locations for 2024
}

# Convert to DataFrame for better visualization
df = pd.DataFrame(data)

# Main Section: Visualizing the Mosquito Population
st.title("Mosquito Population Growth and Trends in Rawalpindi")

st.write("""
    The following data highlights the mosquito population findings in Rawalpindi from 2016 and 2024. 
    It includes the distribution of Aedes mosquitoes and the number of dengue larvae sites detected in the area.
""")

# Update mosquito population data to also show in 2024 (based on 2024 larvae site information)
df["Mosquito Population (Aedes aegypti)"][1] = df["Dengue Larvae Sites Detected (2024)"][1] * 0.46 / 8064 * 3484  # Estimate based on dengue sites
df["Mosquito Population (Aedes albopictus)"][1] = df["Dengue Larvae Sites Detected (2024)"][1] * 0.54 / 8064 * 3484  # Estimate based on dengue sites

# Create a bar plot showing mosquito population
fig, ax = plt.subplots(figsize=(8, 5))

# Bar plot for mosquito population in 2016 and 2024
ax.bar(df["Year"][:-1], df["Mosquito Population (Aedes aegypti)"][:-1], width=0.4, label="Aedes aegypti (2016)", color="blue", align="center")
ax.bar(df["Year"][:-1], df["Mosquito Population (Aedes albopictus)"][:-1], width=0.4, label="Aedes albopictus (2016)", color="green", align="edge")
ax.bar(df["Year"][1:], df["Mosquito Population (Aedes aegypti)"][1:], width=0.4, label="Aedes aegypti (2024)", color="lightblue", align="center")
ax.bar(df["Year"][1:], df["Mosquito Population (Aedes albopictus)"][1:], width=0.4, label="Aedes albopictus (2024)", color="lightgreen", align="edge")

# Labels and title
ax.set_xlabel("Year")
ax.set_ylabel("Population (Number of Mosquitoes)")
ax.set_title("Mosquito Population Distribution in Rawalpindi (2016 vs 2024)")
ax.legend()

# Show the plot
st.pyplot(fig)



# Additional Text for 2024 Data
st.write("""
    In 2024, significant data on the presence of dengue larvae sites in Rawalpindi has been recorded. 
    This includes detection at **8,064 locations**, with a substantial portion found in **homes (6,735)** and **outdoor areas (1,361)**.
""")


# Additional Information below the graph
st.write("""
    - **2016 Findings**: A study published in the *Journal of Vector Borne Diseases* found that **62.5% of ovitraps were positive for eggs**. 
    - A total of **3,484 mosquitoes emerged**, with **46% Aedes aegypti** and **54% Aedes albopictus**.
    - **2024 Data**: As of June 26, 2024, **8,064 dengue larvae sites were detected** across Rawalpindi, with **6,735 homes** and **1,361 outdoor locations** involved.
    - This data indicates a substantial and ongoing mosquito population, highlighting the continued risks of dengue outbreaks and the need for vector control.
""")


# Visualizing dengue larvae sites in 2024
st.write("### Dengue Larvae Sites in 2024")
fig2, ax2 = plt.subplots(figsize=(8, 5))

# Bar plot for dengue larvae sites in 2024
ax2.bar([1, 2, 3], 
        [df["Dengue Larvae Sites Detected (2024)"][1], 
         df["Homes with Dengue Larvae (2024)"][1], 
         df["Outdoor Locations with Dengue Larvae (2024)"][1]], 
        width=0.4, color=["red", "purple", "orange"], align="center")

# Labels and title
ax2.set_xticks([1, 2, 3])
ax2.set_xticklabels(['Total Larvae Sites', 'Homes with Larvae', 'Outdoor Locations'])
ax2.set_ylabel("Number of Sites")
ax2.set_title("Dengue Larvae Sites in Rawalpindi (2024)")

# Show the plot
st.pyplot(fig2)

st.markdown("### **References**")
st.markdown("""
1. **Dengue Cases Data from 2013-2023 in Rawalpindi & Adjacent Hospitals**  
   *Rawalpindi Medical University (RMU) DDEAG Database*  
   [Read More](https://rmur.edu.pk/rmu-ddeag/)
2. **2016 Study on Aedes Mosquitoes in Rawalpindi**  
   Published in *Journal of Vector Borne Diseases*  
   [Read More](https://journals.lww.com/jvbd/fulltext/2016/53020/spatial_distribution_and_insecticide.7.aspx?utm_source=chatgpt.com)
3. **2024 Report on Dengue Larvae in Rawalpindi**  
   *Medical News Pakistan* Report, June 26, 2024  
   [Read More](https://www.medicalnews.pk/26-Jun-2024/8-064-dengue-larvae-sites-detected-in-rawalpindi?utm_source=chatgpt.com)
""")


# Custom footer with styling (appears at the bottom, not fixed)
footer = """
    <style>
        .footer {
            width: 100%;
            background-color: #f8f9fa;
            text-align: center;
            padding: 15px;
            font-size: 14px;
            font-weight: bold;
            color: #333;
            border-top: 1px solid #ddd;
            margin-top: 50px;
        }
    </style>
    <div class="footer">
        📢 <b>This analysis is for educational purposes only.</b><br>
        🏫 <b>Supervised by:</b> Dr. Valerie Odon, Strathclyde University, UK<br>
        💻 <b>Developed by:</b> Odon’s Lab, PhD Students<br>
        📌 <i>Note: All data used here is completely publicly available.</i>
    </div>
"""

st.write("\n" * 20)

st.markdown(footer, unsafe_allow_html=True)
