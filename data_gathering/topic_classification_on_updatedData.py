import pandas as pd
from bertopic import BERTopic

# Load the existing CSV file
file_path = "shanghai_commercial_bank_data.csv"
df = pd.read_csv(file_path)

# Separate rows with and without topics
existing_data = df[df['topic'].notna()]
new_data = df[df['topic'].isna()]

# Extract the relevant text data from new data
new_texts = new_data['title_translated'].tolist()

# Load the saved BERTopic model
topic_model = BERTopic.load("bertopic_model")
if len(new_data) != 0:
    # Assign topics to the new data
    new_topics, new_probabilities = topic_model.transform(new_texts)

    # Add the topics to the new data dataframe
    new_data['topic'] = new_topics

# Combine the existing data with the newly assigned topics data
updated_df = pd.concat([existing_data, new_data])
updated_df.sort_values(by='date',inplace=True,ascending=False)
# Save the updated data to the original CSV file
updated_df.to_csv(file_path, index=False)


print(f"Updated data with topics saved to {file_path}")