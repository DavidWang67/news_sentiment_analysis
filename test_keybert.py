import jieba
from keybert import KeyBERT
import opencc
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import re

# Initialize KeyBERT with a multilingual model
kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')

# Example Chinese text

traditional_to_simplified = opencc.OpenCC('t2s.json')  # Traditional to Simplified
simplified_to_traditional = opencc.OpenCC('s2t.json')  # Simplified to Traditional

exclude_words = ["上海", "商银" ,"商业", "银行", "有限公司", "企业",
                  "报告", "年度", "季度", "会议",
                 "元", "美元"]

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

        # Check if any word in the keyword is in the exclusion list
        if any(word in exclude_words for word in keyword_words):
            continue

        # Check if the keyword contains only numbers
            
        # Check if any words in the keyword already exist in existing_words
        if any(word in existing_words for word in keyword_words) or any(is_number(word) for word in keyword_words):
            # Remove words from existing_words if they are not in the exclusion list
            for word in keyword_words:
                if word in existing_words or is_number(word):
                    keyword_words.remove(word)
                else:
                    existing_words.update(keyword_words)
                    unique_keywords.append(simplified_to_traditional.convert(word))
        else:
            # Add the keyword to existing_words
            existing_words.update(keyword_words)
            # Convert the keyword back to Traditional Chinese and add to unique_keywords
            for word in keyword_words:
                unique_keywords.append(simplified_to_traditional.convert(word))

        if len(unique_keywords) >= 4:
            return unique_keywords[:4]

    return unique_keywords

# print(keyword_generation("連三年相同！上海商銀每股擬配發1.8元股息股息殖利率3.72%"))
# # Read the CSV file
df = pd.read_csv('news_data_cleaned.csv')

# Function to decide whether to use 'content' or 'title'
def get_content_or_title(row, target='上海商銀'):
    pattern = re.escape(target)
    if pd.isna(row['content']) or re.search(pattern, row['content']) == None or row['content'].strip() == '':
         return row['title'], 'title'
    else:
        return row['content'], 'content'

# Apply the keyword generation function to each row
def process_row(row):
    content, source = get_content_or_title(row)
    keywords = keyword_generation(content)
    if not keywords and source == 'content' and pd.notna(row['title']):
        keywords = keyword_generation(row['title'])
    elif not keywords and source == 'title' and pd.notna(row['content']):
        keywords = keyword_generation(row['content'])
    return keywords

df['keywords'] = df.apply(lambda row: process_row(row), axis=1)

# Write the updated DataFrame to a new CSV file
df.to_csv('output_with_top_keywords.csv', index=False)

del traditional_to_simplified
del simplified_to_traditional