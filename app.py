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

    # Function to determine marker color based on the number of people
    def get_marker_color(count):
        if count >= 10000:
            return "darkpurple"
        elif count >= 5000:
            return "red"
        elif count >= 1000:
            return "orange"
        else:
            return "lightblue"

    # Add markers for each camp with corresponding colors
    for feature in geojson_data['features']:
        location_name = feature['properties']['name']
        count = camp_counts.get(location_name, 0)
        color = get_marker_color(count)

        folium.Marker(
            location=feature['geometry']['coordinates'][::-1],  # Reverse coordinates for folium
            popup=folium.Popup(f"{location_name}: {count} people", parse_html=True),
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    # Add a legend to the map (positioned on the left)
    legend_html = '''
    <div style="
        position: fixed; 
        bottom: 50px; left: 50px; width: 250px; height: 150px; 
        background-color: rgba(255, 255, 255, 0.85); 
        z-index:9999; font-size:14px;
        border-radius: 10px; padding: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    ">
        <h4><b>Camp Size Legend</b></h4>
        <p><i class="fa fa-map-marker fa-2x" style="color:darkpurple"></i> 10,000+ people</p>
        <p><i class="fa fa-map-marker fa-2x" style="color:red"></i> 5,000 - 9,999 people</p>
        <p><i class="fa fa-map-marker fa-2x" style="color:orange"></i> 1,000 - 4,999 people</p>
        <p><i class="fa fa-map-marker fa-2x" style="color:lightblue"></i> 0 - 999 people</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

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
st.markdown("<h1 style='text-align: center;'>Camp Regions and People Count</h1>", unsafe_allow_html=True)

# Use Streamlit columns to divide the page layout
col1, col2 = st.columns([4, 1], gap="medium")  # Adjust column spacing

with col1:
    # Display the map in the first column
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles='CartoDB positron')

    # Function to determine marker color based on the number of people
    def get_marker_color(count):
        if count >= 10000:
            return "purple"  # Changed dark purple to a more visible purple
        elif count >= 5000:
            return "red"
        elif count >= 1000:
            return "orange"
        else:
            return "lightblue"

    # Add markers with tooltips for hover info
    for feature in geojson_data['features']:
        location_name = feature['properties']['name']
        count = camp_counts.get(location_name, 0)
        color = get_marker_color(count)

        folium.Marker(
            location=feature['geometry']['coordinates'][::-1],  # Reverse coordinates for folium
            tooltip=f"{location_name}: {count} people",  # Tooltip for hover info
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    folium_static(m)

    # Dropdown for camp selection and route display
    selected_camp = st.selectbox("Select a Camp to view the route of a person and their story:", valid_camps)
    if selected_camp:
        st.subheader(f"Route of a victim from {selected_camp}")
        story, person_data = generate_story_for_camp(selected_camp)
        st.write(story)
        if person_data is not None:
            route_map = create_person_route_map(person_data)
            folium_static(route_map)

with col2:
    # Display the legend in the second column, centered
    st.markdown(
        """
        <div style="text-align: center;">
            <h3>Legend</h3>
            <ul style="list-style-type:none; padding: 0; font-size: 18px;">
                <li><span style="display:inline-block; width: 20px; height: 20px; background-color: purple; margin-right: 10px; border-radius: 3px;"></span> 10,000+ people</li>
                <li><span style="display:inline-block; width: 20px; height: 20px; background-color: red; margin-right: 10px; border-radius: 3px;"></span> 5,000-9,999 people</li>
                <li><span style="display:inline-block; width: 20px; height: 20px; background-color: orange; margin-right: 10px; border-radius: 3px;"></span> 1,000-4,999 people</li>
                <li><span style="display:inline-block; width: 20px; height: 20px; background-color: lightblue; margin-right: 10px; border-radius: 3px;"></span> 0-999 people</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True  # Allow HTML for custom legend styles
    )

# Center all content
st.markdown("""
    <style>
        .block-container {
            max-width: 80%;
            margin: auto;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)
