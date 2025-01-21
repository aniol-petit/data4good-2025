import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import folium_static
from chatbot import filter_by_camp, pick_random_person_with_features, generate_story

# Load data
df = pd.read_csv('final_transformed_dataset_with_names.csv')

# Load geojson data to extract camp names
with open('camps.geojson', 'r') as f:
    geojson_data = json.load(f)

# Extract camp names from the geojson file
camp_names = [feature['properties']['name'] for feature in geojson_data['features']]

# Filter dataset to include only rows where type is 'Camp Name'
camp_destinations = df[df['Type'] == 'Camp Name']

# Count the number of people per origin location
camp_counts = camp_destinations['Dest'].value_counts().to_dict()

# Validate camps against geojson data
valid_camps = [camp for camp in camp_counts.keys() if camp in camp_names]

# Function to create a Folium map with camp locations
def create_camp_map():
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles='CartoDB positron')

    # Add geojson polygons and labels
    for feature in geojson_data['features']:
        location_name = feature['properties']['name']
        count = camp_counts.get(location_name, 0)
        folium.GeoJson(
            feature,
            name=location_name,
            style_function=lambda feature, count=count: {
                'fillColor': '#3186cc' if count > 0 else '#cccccc',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.6 if count > 0 else 0.3
            },
            tooltip=folium.Tooltip(f"{location_name}: {count} people")
        ).add_to(m)

    return m

# Function to generate story for a selected camp
def generate_story_for_camp(camp_name):
    journey_data = pd.read_csv("intervals.csv")
    dataset = pd.read_csv("Data4Good_Arolsen_Archives_50k.csv")

    filtered_journey = filter_by_camp(journey_data, camp_name)
    random_person = pick_random_person_with_features(filtered_journey, dataset)

    if random_person:
        return generate_story(random_person, journey_data)
    else:
        return f"No records found for people associated with the camp '{camp_name}'."

# Streamlit app layout
st.set_page_config(page_title="Camp Regions and People Count", layout="wide")
st.title("Camp Regions and People Count")

# Show the initial camp map
m = create_camp_map()
folium_static(m)

# Camp selection dropdown
selected_camp = st.selectbox("Select a Camp to view the route of a random person and their story:", valid_camps)

# Display route map for the selected camp
if selected_camp:
    st.subheader(f"Route for a Random Person from {selected_camp}")
    route_map = create_camp_map()
    folium_static(route_map)

    # Generate and display the person's story
    st.subheader(f"Story for a Random Person from {selected_camp}")
    story = generate_story_for_camp(selected_camp)
    st.write(story)
