import pandas as pd
import networkx as nx

# Load the dataset
df = pd.read_csv("./data/transformed_dataset_with_intervals.csv")
df = df.head(500)
# Create a graph
G = nx.Graph()

# Add individuals as nodes
for _, row in df.iterrows():
    person_id = row["ID"]
    person_name = f"{row['First Name']} {row['Last Name']}".strip()  # Full name of the individual
    
    # Add the individual as a node, using their unique ID as the identifier
    G.add_node(person_id, name=person_name)
    
    # Add relationships between the individual and their origin and destination
    origin = row["Origin"]
    dest = row["Dest"]
    
    # Add origin location as a node and connect the individual to it
    G.add_node(origin, type="location")  # Add the origin location as a node
    G.add_edge(person_id, origin, relationship="origin")  # Edge between individual and origin location
    
    # Add destination location as a node and connect the individual to it
    G.add_node(dest, type="location")  # Add the destination location as a node
    G.add_edge(person_id, dest, relationship="destination")  # Edge between individual and destination location

# Export the network to GraphML format for Cytoscape
output_file = "individual_location_network.graphml"
nx.write_graphml(G, output_file)

print(f"Network saved to {output_file}")
