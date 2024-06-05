from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import nltk
import re
import pandas as pd
# ----------------------------Data Cleaning----------------------------
# Define the cleaning function
def clean_text(text):
    text = str(text)  # Ensure the input is a string
    text = text.strip()  # Remove leading and trailing whitespace
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    stop = stopwords.words('english')
    text = ' '.join([word for word in text.split() if word not in (stop)])  # Remove stop words
    stemmer = SnowballStemmer('english')
    text = ' '.join([stemmer.stem(word) for word in text.split()])  # Apply stemming
    return text

df = pd.read_csv("news_data.csv")
df['title_translated'] = df['title_translated'].apply(clean_text)
df.to_csv("news_data_cleaned.csv", index=False)
print('Data cleaned and saved to news_data_cleaned.csv')