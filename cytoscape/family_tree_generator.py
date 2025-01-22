import pandas as pd
import networkx as nx

# Load dataset
df = pd.read_csv("./data/Data4Good_Arolsen_Archives_50k.csv")

# Limit to 500 persons
df_subset = df.head(500)

# Create an undirected graph for a family tree structure
G = nx.Graph()

# Add nodes and edges
for _, row in df_subset.iterrows():
    # Create a unique identifier for each individual
    person_id = row["Unnamed: 0"]
    last_name = row.get("Last_Name", "")
    first_name = row.get("First Name", "")
    person_name = f"{first_name} {last_name}".strip()

    # Ensure unique node names by using both person ID and name
    full_person_name = f"{person_name} ({person_id})"
    G.add_node(person_id, name=full_person_name)

    # Add edges for parent relationships if available
    father_name = row.get("Father (Vater - Eltern)", None)
    mother_name = row.get("Mother (Mutter - Eltern)", None)

    if pd.notna(father_name):
        # Create unique identifier for father
        father_id = f"father_{person_id}"
        G.add_node(father_id, name=father_name)
        G.add_edge(father_id, person_id)  # Edge from father to child

    if pd.notna(mother_name):
        # Create unique identifier for mother
        mother_id = f"mother_{person_id}"
        G.add_node(mother_id, name=mother_name)
        G.add_edge(mother_id, person_id)  # Edge from mother to child

    # Add edges for spouse relationships if available
    spouse_name = row.get("Spouse (Ehem/Ehefr)", None)
    if pd.notna(spouse_name):
        # Ensure the spouse has a unique identifier and avoid creating a node for the same person
        spouse_id = f"spouse_{person_id}"
        G.add_node(spouse_id, name=spouse_name)
        G.add_edge(spouse_id, person_id)  # Edge between the person and their spouse

        # Look for the spouse in the dataset and connect them back to the person
        spouse_row = df[df["Spouse (Ehem/Ehefr)"] == person_name]
        if not spouse_row.empty:
            spouse_person_id = spouse_row["Unnamed: 0"].values[0]
            G.add_edge(spouse_person_id, person_id)  # Edge from spouse to person
    
    # Handle siblings (children of the same parents)
    if pd.notna(father_name) and pd.notna(mother_name):
        # Identify all children of the same parents (siblings)
        siblings = df[(df["Father (Vater - Eltern)"] == father_name) & (df["Mother (Mutter - Eltern)"] == mother_name)]
        for _, sibling_row in siblings.iterrows():
            sibling_id = sibling_row["Unnamed: 0"]
            if sibling_id != person_id:  # Avoid self-loop
                G.add_edge(person_id, sibling_id)  # Edge between siblings

# Export the network to GraphML format
output_file = "holocaust_family_tree_500_improved.graphml"
nx.write_graphml(G, output_file)

print(f"Improved family tree for 500 individuals saved to {output_file}")
