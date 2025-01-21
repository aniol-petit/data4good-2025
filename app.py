import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import folium_static
import random

# Load data
df = pd.read_csv('transformed_dataset.csv')
with open('camps.geojson', 'r') as f:
    geojson_data = json.load(f)

# Filter dataset to include only rows where type is 'Camp Name'
camp_destinations = df[df['Type'] == 'Camp Name']

# Count the number of people per origin location
camp_counts = camp_destinations['Origin'].value_counts().to_dict()

# Get camps that exist in the geojson data
geojson_camp_names = {feature['properties']['name'] for feature in geojson_data['features']}
valid_camps = [camp for camp in camp_counts.keys() if camp in geojson_camp_names]

# Create a Folium map with camp locations
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

def create_route_map(camp_name):
    # Filter the dataset for a random person from the selected camp
    selected_camp_data = camp_destinations[camp_destinations['Origin'] == camp_name]
    random_person = selected_camp_data.sample(n=1)
    
    # Extract relevant details for the random person's route
    person_id = random_person['ID'].iloc[0]
    person_path = df[df['ID'] == person_id].sort_values(by='Index')
    
    route_coords = []
    for _, row in person_path.iterrows():
        for feature in geojson_data['features']:
            if feature['properties']['name'] == row['Origin']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates'][::-1]
                elif feature['geometry']['type'] in ['Polygon', 'MultiPolygon']:
                    coords = feature['geometry']['coordinates'][0][0][::-1]
                route_coords.append(coords)
                break
    
    # Create a new Folium map centered around the camp location
    m = folium.Map(location=route_coords[0], zoom_start=6, tiles='CartoDB positron')

    # Add the route
    for coord in route_coords:
        folium.Marker(location=coord, tooltip="Stop").add_to(m)
    folium.PolyLine(locations=route_coords, color="blue").add_to(m)

    return m

# Streamlit app layout
st.set_page_config(page_title="Camp Regions and People Count", layout="wide")
st.title("Camp Regions and People Count")

# Show the initial camp map
m = create_camp_map()
folium_static(m)

# Camp selection - display a dropdown for the user to select a camp
selected_camp = st.selectbox("Select a Camp to view the route of a random person:", valid_camps)

# If a camp is selected, display the route map
if selected_camp:
    st.subheader(f"Route for a Random Person from {selected_camp}")
    route_map = create_route_map(selected_camp)
    folium_static(route_map)
