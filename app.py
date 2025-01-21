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

# Load and clean geo data
def load_geo_data():
    with open("geo_data.json", 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    def clean_and_parse(item):
        if isinstance(item, str):
            cleaned_str = item.strip('"').replace('""', '"')
            return json.loads(cleaned_str)
        elif isinstance(item, dict):
            return item
        return None
    
    return [clean_and_parse(item) for item in raw_data if clean_and_parse(item) is not None]

geo_data = load_geo_data()

def find_coordinates(location):
    for record in geo_data:
        markers = record.get("markers", [])
        for marker in markers:
            if marker.get("label") == location:
                location_data = marker.get("location", {})
                return location_data.get("lat"), location_data.get("lon")
    return None, None

# Function to create a Folium map with camp locations
def create_camp_map():
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles='CartoDB positron')
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
        return generate_story(random_person, journey_data), random_person
    else:
        return f"No records found for people associated with the camp '{camp_name}'.", None

def create_person_route_map(person_data):
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles='CartoDB positron')
    
    # Filter journey data for the specific person
    journey = df[df['ID'] == person_data['ID']]
    path_coords = []
    
    # Loop through the journey and collect coordinates
    for idx, row in journey.iterrows():
        origin_coords = find_coordinates(row['Origin'])
        dest_coords = find_coordinates(row['Dest'])

        if origin_coords and None not in origin_coords:
            path_coords.append((origin_coords, row['Origin'], "Origin"))
        
        if dest_coords and None not in dest_coords:
            path_coords.append((dest_coords, row['Dest'], "Destination"))

    # Add markers to the map
    for i, (coords, label, point_type) in enumerate(path_coords):
        if i == 0:  # Start point
            folium.Marker(
                coords,
                popup=f"{label}<br>Start Point",
                icon=folium.Icon(color='green', icon='play-circle', icon_color='white'),
                tooltip=f"Start: {label}"
            ).add_to(m)
        elif i == len(path_coords) - 1:  # End point
            folium.Marker(
                coords,
                popup=f"{label}<br>End Point",
                icon=folium.Icon(color='red', icon='stop-circle', icon_color='white'),
                tooltip=f"End: {label}"
            ).add_to(m)
        else:  # Intermediate points
            folium.Marker(
                coords,
                popup=f"{label}",
                icon=folium.Icon(color='blue', icon='info-sign', icon_color='white'),
                tooltip=f"{label}"
            ).add_to(m)

    # Draw the path connecting all points
    coords_only = [coord[0] for coord in path_coords]
    if len(coords_only) >= 2:
        folium.PolyLine(coords_only, color="blue", weight=2.5, opacity=1).add_to(m)
    else:
        st.error("Error: Not enough valid coordinates found to draw the route.")
    
    return m

    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles='CartoDB positron')
    
    journey = df[df['ID'] == person_data['ID']]
    path_coords = []
    
    # Markers list to store all origin and destination coordinates
    origin_markers = []
    dest_markers = []

    # Loop through the journey to add markers for each origin and destination
    for idx, row in journey.iterrows():
        origin_coords = find_coordinates(row['Origin'])
        dest_coords = find_coordinates(row['Dest'])

        # Add origin marker to the list
        if origin_coords and None not in origin_coords:
            path_coords.append(origin_coords)
            origin_markers.append((origin_coords, row['Origin'], idx == 0))  # True for the first origin

        # Add destination marker to the list
        if dest_coords and None not in dest_coords:
            path_coords.append(dest_coords)
            dest_markers.append((dest_coords, row['Dest'], idx == len(journey) - 1))  # True for the last destination

    # Add the origin markers to the map
    for coords, origin, is_start in origin_markers:
        if is_start:  # Starting node is colored green
            folium.Marker(
                coords,
                popup=f"Origin: {origin}<br>Start",
                icon=folium.Icon(color='green', icon='play-circle', icon_color='white'),
                tooltip=f"Start: {origin}"
            ).add_to(m)
        else:  # Intermediate origin nodes are colored blue
            folium.Marker(
                coords,
                popup=f"Origin: {origin}",
                icon=folium.Icon(color='blue', icon='info-sign', icon_color='white'),
                tooltip=origin
            ).add_to(m)

    # Add the destination markers to the map
    for coords, dest, is_end in dest_markers:
        if is_end:  # Ending node is colored red
            folium.Marker(
                coords,
                popup=f"Destination: {dest}<br>End",
                icon=folium.Icon(color='red', icon='stop-circle', icon_color='white'),
                tooltip=f"End: {dest}"
            ).add_to(m)
        else:  # Intermediate destination nodes are colored blue
            folium.Marker(
                coords,
                popup=f"Destination: {dest}",
                icon=folium.Icon(color='blue', icon='info-sign', icon_color='white'),
                tooltip=dest
            ).add_to(m)

    # Draw the path connecting all points
    if len(path_coords) >= 2:
        folium.PolyLine(path_coords, color="blue", weight=2.5, opacity=1).add_to(m)
    else:
        st.error("Error: Not enough valid coordinates found to draw the route.")
        return m

    return m



# Streamlit app layout
st.set_page_config(page_title="Camp Regions and People Count", layout="wide")
st.title("Camp Regions and People Count")
m = create_camp_map()
folium_static(m)
selected_camp = st.selectbox("Select a Camp to view the route of a person and their story:", valid_camps)
if selected_camp:
    st.subheader(f"Route of a vicitm from {selected_camp}")
    story, person_data = generate_story_for_camp(selected_camp)
    st.write(story)
    if person_data is not None:
        route_map = create_person_route_map(person_data)
        folium_static(route_map)