import pandas as pd
import random

# Load the datasets
try:
    dataset = pd.read_csv("Data4Good_Arolsen_Archives_50k.csv")
    journey_data = pd.read_csv("/mnt/c/Users/Pol/Downloads/intervals.csv")
except Exception as e:
    print(f"Error loading datasets: {e}")
    exit()

# Fill missing values with "Unknown"
dataset = dataset.fillna("Unknown")
journey_data = journey_data.fillna("Unknown")

# Normalize text columns for consistency
def normalize_text(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].str.strip().str.lower()
    return df

dataset = normalize_text(dataset, ['First Name', 'Last_Name', 'Father (Vater - Eltern)', 'Mother (Mutter - Eltern)', 'Birthdate (Geb)', 'Birth Place', 'Nationality'])
journey_data = normalize_text(journey_data, ['First Name', 'Last Name', 'Origin', 'Dest', 'Nationality', 'Religion'])

# Replace known synonyms or common noise in the Religion column
religion_replacements = {
    'judieeh': 'jewish',
    'jewishüdtsch': 'jewish',
    'moslem': 'muslim',
    'roman catholic': 'catholic',
    'orthodox christian': 'orthodox',
    'evangelical christian': 'evangelical',
}

dataset['Religion'] = dataset['Religion'].replace(religion_replacements)
journey_data['Religion'] = journey_data['Religion'].replace(religion_replacements)

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

# Generate a story based on a person's record
# Generate a story based on a person's record
def generate_story(record, journey_data):
    if not record:
        return "No person found for the given location."

    first_name = record.get('First Name', 'Unknown').title()
    last_name = record.get('Last_Name', 'Unknown').title()

    # Opening statement
    opening = f"{first_name} {last_name}'s story is one of resilience and human experience."

    # Family details
    family_details = []
    if 'Father (Vater - Eltern)' in record and record['Father (Vater - Eltern)'] != "Unknown":
        family_details.append(f"Their father was {record['Father (Vater - Eltern)'].title()}")
    if 'Mother (Mutter - Eltern)' in record and record['Mother (Mutter - Eltern)'] != "Unknown":
        family_details.append(f"and their mother was {record['Mother (Mutter - Eltern)'].title()}")
    family_details = " ".join(family_details) + "." if family_details else "Family details are not available."

    # Birth details
    birth_details = []
    if 'Birthdate (Geb)' in record and record['Birthdate (Geb)'] != "Unknown":
        birth_details.append(f"They were born on {record['Birthdate (Geb)']}")
    if 'Birth Place' in record and record['Birth Place'] != "Unknown":
        birth_details.append(f"in {record['Birth Place'].title()}")
    birth_details = " and ".join(birth_details) + "." if birth_details else "Birth details are not available."

    # Nationality
    nationality = record.get('Nationality', 'unknown').title()
    nationality_statement = f"They were of {nationality} nationality." if nationality != "Unknown" else "Nationality details are not available."

    # Religion
    religion = record.get('Religion', 'unknown').title()
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
            origin = row['Origin'].title() if row['Origin'] != "Unknown" else "an unknown location"
            destination = row['Dest'].title() if row['Dest'] != "Unknown" else "an unknown location"
            interval = row['Interval'] if row['Interval'] != "Unknown" else "an unknown period"

            # Use varied transitions
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


# Main program
camp_name = input("Enter a camp name: ")
filtered_journey = filter_by_camp(journey_data, camp_name)
random_person = pick_random_person_with_features(filtered_journey, dataset)

if random_person:
    story = generate_story(random_person, journey_data)
    print("\nGenerated Story:")
    print(story)
else:
    print(f"No records found for people associated with the camp '{camp_name}'.")
