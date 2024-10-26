import pandas as pd
import os

csv_directory = os.path.join(os.getcwd(), 'csv')

# Load the CSV files into DataFrames
learning_outcomes_df = pd.read_csv(os.path.join(csv_directory, 'learning_outcomes_ids.csv'))
skills_df = pd.read_csv(os.path.join(csv_directory, 'skills.csv'))
knowledge_df = pd.read_csv(os.path.join(csv_directory, 'knowledge.csv'))

# Create a mapping from ID to URI for skills and knowledge
skills_uri_map = dict(zip(skills_df['index'], skills_df['uri']))
knowledge_uri_map = dict(zip(knowledge_df['index'], knowledge_df['uri']))

# Prepare a list to hold the rows for the new DataFrame
learning_outcomes_uris_data = []

for _, row in learning_outcomes_df.iterrows():
    module_title = row['Module Title']
    learning_outcome = row['Learning Outcome']

    promoted_skills_and_knowledge = row['Promoted Skill and Knowledge'].split(',')

    promoted_skills = []
    promoted_knowledge = []

    for item in promoted_skills_and_knowledge:
        item = item.strip()
        if item.startswith('S'):
            uri = skills_uri_map[item]
            promoted_skills.append(uri)
        elif item.startswith('K'):
            uri = knowledge_uri_map[item]
            promoted_knowledge.append(uri)

    learning_outcomes_uris_data.append({
        'Module Title': module_title,
        'Learning Outcome': learning_outcome,
        'Promoted skill': ', '.join(promoted_skills),
        'Promoted knowledge': ', '.join(promoted_knowledge)
    })

learning_outcomes_uris_df = pd.DataFrame(learning_outcomes_uris_data)
output_file_path = os.path.join(csv_directory, 'learning_outcomes_uris.csv')
learning_outcomes_uris_df.to_csv(output_file_path, index=False)

print("learning_outcomes_uris.csv has been created successfully.")
