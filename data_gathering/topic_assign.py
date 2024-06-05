import pandas as pd
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import collections

# Load the data
file_path = "news_data_analyzed.csv"
df = pd.read_csv(file_path)

# Define the hashmap of topics in traditional Chinese including 'Business', 'Markets', 'Sustainability', 'Legal', and 'Technology' topics
topic_map = {
    1: "商業",  # Business
    2: "市場",  # Markets
    3: "可持續性",  # Sustainability
    4: "法律",  # Legal
    5: "技術"  # Technology
}

# List of topics under 'Business'
business_topics = [
    "Business",
    "Finance",
    "Retail & Consumer",
    "Change",
    "Expand",
    "Growth",
    "Collaboration",
    "Credit card",
    "Investment",
]

# List of topics under 'Markets'
markets_topics = [
    "Markets"
    "Asian Markets",
    "Carbon Markets",
    "Commodities",
    "Currencies",
    "Deals",
    "Emerging Markets",
    "ETFs",
    "European Markets",
    "Funds",
    "Global Market Data",
    "Rates & Bonds",
    "Stocks",
    "U.S. Markets",
    "Wealth",
    "Macro Matters",
    "Dividends",
    "Earnings",
    "EPS",
    "Interest Rate",

]

# List of topics under 'Sustainability'
sustainability_topics = [
    "Environment",
    "Sustainability",
    "Climate & Energy",
    "Land Use & Biodiversity",
    "Green",
    "Building",
    "Donation",
]

# List of topics under 'Legal'
legal_topics = [
    "Legal",
    "Government",
    "Legal Industry",
    "Litigation",
    "Transactional",
    "US Supreme Court",
    "Sued",
    "Leaked",
    "Law",
    "Lawsuit",
    "fined",
    "exposed"
]

# List of topics under 'Technology'
technology_topics = [
    "Reuters Momentum",
    "Technology",
    "Innovation",
]

# Combine business_topics, markets_topics, sustainability_topics, legal_topics, and technology_topics into one list
all_topics = business_topics + markets_topics + sustainability_topics + legal_topics + technology_topics

# Combine topics and news titles
all_texts = all_topics + df['title_translated'].tolist()

# Create TF-IDF vectorizer and transform the texts
vectorizer = TfidfVectorizer().fit_transform(all_texts)
vectors = vectorizer.toarray()

# Get the number of topics
num_topics = len(all_topics)

# Compute cosine similarity between topics and news titles
cosine_similarities = cosine_similarity(vectors[:num_topics], vectors[num_topics:])

# Map each news title to the most similar topic index
mapping = {}
for idx, similarities in enumerate(cosine_similarities.T):
    most_similar_topic_idx = similarities.argmax()
    if most_similar_topic_idx < len(business_topics):
        mapping[df['title_translated'][idx]] = 1  # Index for "商業" (Business)
    elif most_similar_topic_idx < len(business_topics) + len(markets_topics):
        mapping[df['title_translated'][idx]] = 2  # Index for "市場" (Markets)
    elif most_similar_topic_idx < len(business_topics) + len(markets_topics) + len(sustainability_topics):
        mapping[df['title_translated'][idx]] = 3  # Index for "可持續性" (Sustainability)
    elif most_similar_topic_idx < len(business_topics) + len(markets_topics) + len(sustainability_topics) + len(legal_topics):
        mapping[df['title_translated'][idx]] = 4  # Index for "法律" (Legal)
    else:
        mapping[df['title_translated'][idx]] = 5  # Index for "技術" (Technology)

# Assign topics to the dataframe
df['topic'] = df['title_translated'].map(mapping)

# Save the updated dataframe to a new CSV file
df.to_csv("news_data_topic_assigned.csv", index=False)
print('Topics assigned to the news data and saved to news_topic_assigned.csv')
