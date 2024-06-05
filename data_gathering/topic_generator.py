import os
import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
import hdbscan


# Load the labeled CSV file
file_path = "shanghai_commercial_bank_data.csv"
df = pd.read_csv(file_path)

# Extract the relevant text data
texts = df['title_translated'].tolist()

# Initialize HDBSCAN model
hdbscan_model = hdbscan.HDBSCAN(min_cluster_size=11, metric='euclidean', cluster_selection_epsilon=0.5, prediction_data=True)

# Initialize BERTopic model
vectorizer_model = CountVectorizer(ngram_range=(1, 2), stop_words="english")
topic_model = BERTopic(hdbscan_model=hdbscan_model, vectorizer_model=vectorizer_model)

# Fit the model to the data
topics, probabilities = topic_model.fit_transform(texts)

# Add the topics to the dataframe
df['topic'] = topics

# Save the labeled data with topics to a new CSV file
df.to_csv(file_path, index=False)

# Save the BERTopic model
topic_model.save("bertopic_model")

print(f"Labeled data with topics saved to {file_path}")

# Print the topics
print(topic_model.get_topic_info())