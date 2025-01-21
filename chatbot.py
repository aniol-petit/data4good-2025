import pandas as pd

# Load the datasets
try:
    dataset = pd.read_csv("Data4Good_Arolsen_Archives_50k.csv")
    journey_data = pd.read_csv("intervals.csv")
except Exception as e:
    print(f"Error loading datasets: {e}")
    exit()

# Normalize the text columns for consistency
def normalize_text(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].str.strip().str.lower()
    return df

dataset = normalize_text(dataset, ['First Name', 'Last_Name', 'Father (Vater - Eltern)', 'Mother (Mutter - Eltern)', 'Birthdate (Geb)', 'Birth Place', 'Nationality'])
journey_data = normalize_text(journey_data, ['First Name', 'Last Name', 'Origin', 'Dest', 'Nationality', 'Religion'])

# Function to filter dataset by camp origin
def filter_by_camp(journey_data, camp):
    camp = camp.lower()
    return journey_data[(journey_data['Origin'].str.lower() == camp) & (journey_data['Type'] == 'Camp Name')]

# Function to pick a random person with sufficient features
def pick_random_person_with_features(filtered_data, dataset):
    if filtered_data.empty:
        print("No matching records found in journey data.")
        return None

    # Merge the journey data with the main dataset
    candidates = dataset.merge(
        filtered_data,
        left_on=['First Name', 'Last_Name'],
        right_on=['First Name', 'Last Name'],
        how='inner'
    )

    # Rename columns for easier access
    candidates.rename(columns={'Nationality_x': 'Nationality', 'Religion_x': 'Religion'}, inplace=True)

    # Count meaningful features (non-"Unknown")
    candidates['Feature Count'] = candidates.apply(
        lambda row: sum([1 for value in row.values if value != "Unknown" and pd.notnull(value)]),
        axis=1
    )

    # Filter candidates with 5 or more features
    candidates_with_features = candidates[candidates['Feature Count'] >= 5]

    if not candidates_with_features.empty:
        return candidates_with_features.sample(1).iloc[0].to_dict()

    print("No candidates with 5 or more features. Selecting randomly.")
    return candidates.sample(1).iloc[0].to_dict() if not candidates.empty else None

def generate_story(record, journey_data):
    if not record:
        return "No person found for the given location."

    def safe_title(value):
        """Convert value to string and apply title-case if it's not 'Unknown'."""
        return str(value).title() if pd.notna(value) and value != "Unknown" else "Unknown"

    first_name = safe_title(record.get('First Name', 'Unknown'))
    last_name = safe_title(record.get('Last_Name', 'Unknown'))

    # Opening statement
    opening = f"{first_name} {last_name}'s story is one of resilience and human experience."

    # Family details
    family_details = []
    if 'Father (Vater - Eltern)' in record:
        father = safe_title(record['Father (Vater - Eltern)'])
        if father != "Unknown":
            family_details.append(f"Their father was {father}")

    if 'Mother (Mutter - Eltern)' in record:
        mother = safe_title(record['Mother (Mutter - Eltern)'])
        if mother != "Unknown":
            family_details.append(f"and their mother was {mother}")

    family_details = " ".join(family_details) + "." if family_details else "Family details are not available."

    # Birth details
    birth_details = []
    birth_date = safe_title(record.get('Birthdate (Geb)', 'Unknown'))
    birth_place = safe_title(record.get('Birth Place', 'Unknown'))
    if birth_date != "Unknown":
        birth_details.append(f"They were born on {birth_date}")
    if birth_place != "Unknown":
        birth_details.append(f"in {birth_place}")

    birth_details = " and ".join(birth_details) + "." if birth_details else "Birth details are not available."

    # Nationality
    nationality = safe_title(record.get('Nationality', 'Unknown'))
    nationality_statement = f"They were of {nationality} nationality." if nationality != "Unknown" else "Nationality details are not available."

    # Religion
    religion = safe_title(record.get('Religion', 'Unknown'))
    religion_statement = f"They practiced the {religion} faith." if religion != "Unknown" else "Religion details are not available."

    # Journey details with varied connectors
    journey_details = []
    journey_records = journey_data[
        (journey_data['First Name'] == record['First Name']) & 
        (journey_data['Last Name'] == record['Last_Name'])
    ]

    if not journey_records.empty:
        journey_details.append("Their recorded movements paint a picture of a life uprooted by the events of the war.")
        transitions = [
            "They were moved from", 
            "Next, they were taken to", 
            "Later, they found themselves in", 
            "Subsequently, they were relocated to", 
            "Finally, they arrived at"
        ]
        for i, (_, row) in enumerate(journey_records.iterrows()):
            origin = safe_title(row['Origin'])
            destination = safe_title(row['Dest'])
            interval = safe_title(row['Interval'])

            transition = transitions[i % len(transitions)] if i < len(journey_records) - 1 else "Ultimately, they reached"
            journey_details.append(f"{transition} {destination} from {origin} during {interval}.")
    else:
        journey_details.append("No journey details are available.")

    # Closing statement
    closing = f"The story of {first_name} {last_name} serves as a reminder of the resilience of individuals during this time."

    # Combine all parts
    story = " ".join([
        opening,
        family_details,
        birth_details,
        nationality_statement,
        religion_statement,
        " ".join(journey_details),
        closing,
    ])
    return story
