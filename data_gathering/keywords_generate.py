import jieba
from keybert import KeyBERT
import opencc
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import re
import sys
from transformers import AutoModel, AutoTokenizer
import os


# Specify the model name
model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

# Specify the directory to save the model
save_directory = './saved_sentence_transformer_models'
if not os.path.exists(save_directory):

    # Download and save the model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    # Save the model and tokenizer
    tokenizer.save_pretrained(save_directory)
    model.save_pretrained(save_directory)

tokenizer = AutoTokenizer.from_pretrained(save_directory)
model = AutoModel.from_pretrained(save_directory)

# Initialize KeyBERT with a multilingual model
kw_model = KeyBERT(model=model)

# Example Chinese text

traditional_to_simplified = opencc.OpenCC('t2s.json')  # Traditional to Simplified
simplified_to_traditional = opencc.OpenCC('s2t.json')  # Simplified to Traditional
exclude_words = ['亿元', '百亿元', '千亿元', '百亿', '千亿', '亿', 
                 '亿美元', '百亿美元', '千亿美元',
                 '百万美元', '千万美元', '百万美元', '万美元', 
                 '千万', '百万', '万', '千万元', '百万元', '万元',
                 '今年', '去年', '明年']

target_wrods = []


def is_number(word):
    try:
        float(word)
        return True
    except ValueError:
        return False

def keyword_generation(text):
    # Convert Traditional Chinese to Simplified Chinese for processing
    # Initialize OpenCC converters for Traditional and Simplified Chinese
    if type(text) != str:
        return []
    simplified_text = traditional_to_simplified.convert(text)

    # Segment the text using Jieba
    words = " ".join(jieba.cut(simplified_text))
    # Extract keywords
    keywords = kw_model.extract_keywords(words, keyphrase_ngram_range=(1, 2), stop_words=None)
    # Convert the keywords back to Traditional Chinese and create a 1D list without duplicates
    existing_words = set()

    unique_keywords = []
    for keyword in keywords:
        keyword_text = keyword[0]
        keyword_words = keyword_text.split()

        # Check if the keyword contains only numbers
            
        # Check if any words in the keyword already exist in existing_words
        if any(word in existing_words for word in keyword_words) or any(is_number(word) for word in keyword_words) or any(word in exclude_words for word in keyword_words):
            # Remove words from existing_words if they are not in the exclusion list
            for word in keyword_words:
                if not(word in existing_words or is_number(word) or word in exclude_words):
                    existing_words.update(keyword_words)
                    unique_keywords.append(simplified_to_traditional.convert(word))
        else:
            # Add the keyword to existing_words
            existing_words.update(keyword_words)
            # Convert the keyword back to Traditional Chinese and add to unique_keywords
            for word in keyword_words:
                unique_keywords.append(simplified_to_traditional.convert(word))

        if len(unique_keywords) >= 4:
            # print(f"keywords: {keywords}, unique_keywords: {unique_keywords}")
            return unique_keywords[:4]
        

    # print(f"keywords: {keywords}, unique_keywords: {unique_keywords}")
    return unique_keywords

def get_content_or_title(row):
    """Decide whether to use 'content' or 'title' based on the presence of any target word."""
    for target in target_wrods:
        pattern = re.escape(target)
        if pd.isna(row['content']) or re.search(pattern, row['content']) is None or row['content'].strip() == '':
            return row['title'], 'title'
        
    return row['content'], 'content'

# Apply the keyword generation function to each row
def process_row(row):
    col_data, source = get_content_or_title(row)
    keywords = keyword_generation(col_data)
    if not keywords and source == 'content' and pd.notna(row['title']):
        keywords = keyword_generation(row['title'])
    elif not keywords and source == 'title' and pd.notna(row['content']):
        keywords = keyword_generation(row['content'])
    return keywords


# # Read the CSV file
df = pd.read_csv('news_data_cleaned.csv')

if __name__ == '__main__':
    current_target = sys.stdin.read().strip()
    simplified_current_target = traditional_to_simplified.convert(current_target)
#    Segmentize the current target and add all segments to exclude_words
    segmented_target = ",".join(jieba.cut(simplified_current_target)).split(',')
    exclude_words.extend(segmented_target)
    target_wrods.extend(segmented_target)
    df['keywords'] = df.apply(lambda row: process_row(row), axis=1)

    # Write the updated DataFrame to a new CSV file
    df.to_csv('news_data_keywords.csv', index=False)

    del traditional_to_simplified
    del simplified_to_traditional

    print("Keywords generated and saved to news_data_keywords.csv")