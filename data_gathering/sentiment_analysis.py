from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import pandas as pd
import os
import re
from nltk.tokenize import sent_tokenize
import sys
from deep_translator import GoogleTranslator

# Lexical indicators for sentiment
positive_indicators = ["donated", 'donate', 'donation', 'dividend', 'profit']
negative_indicators = ['fined', 'sued', 'lawsuit', 'lawsuits', 'sue', 'sues', 'sued', 'suing']

def analyze_sentiment_lexical(title):
    title_lower = title.lower()
    words = re.findall(r'\b\w+\b', title_lower)  # Extract words using regex
    positive_count = sum(word in words for word in positive_indicators)
    negative_count = sum(word in words for word in negative_indicators)
    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'
    
def analyze_sentiment(title, targets=[]):
    # Tokenize the text into sentences
    # Split the text into sentences based on periods, semicolons, and other delimiters
    sentences = re.split(r'[.;|/]', title)    # Extract sentences containing the keyword "Shanghai"
    sentences = [s for s in sentences if s.strip()]

    if len(sentences) > 1 and len(targets) > 0:
        target_sentences = [sentence for sentence in sentences if sentence.lower().find(targets[0].lower()) != -1]
        target_text = ". ".join(target_sentences)
        title += ". "
        title += target_text

    results = sentiment_analysis(title, top_k=None)
    # print(results)

    result = results[0]
    lexical_sentiment = analyze_sentiment_lexical(title)
    if lexical_sentiment != 'neutral':
        return lexical_sentiment
    if result['label'] == 'neutral' and result['score'] < 0.6:
        if results[1]['score'] > 5*results[2]['score']:
            result = results[1]
        elif results[2]['score'] > 5*results[1]['score']:
            result = results[2]
    return result['label']

if __name__ == '__main__':
    # download the sentiment analysis model if it does not exist
    if not os.path.exists('./saved_sentiment_model'):
        model_name = "mr8488/distilroberta-finetuned-financial-news-sentiment-analysis"
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Save the model and tokenizer locally
        model.save_pretrained("./saved_sentiment_model")
        tokenizer.save_pretrained("./saved_sentiment_model")

    model_path = 'saved_sentiment_model'
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    # the additional strs are to ensure consistent translation
    current_target = sys.stdin.read().strip()+'哈哈哈哈哈'
    translated_text = GoogleTranslator(source='auto', target='en').translate(current_target)
    targets = translated_text.split()

    sentiment_analysis = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)
    df = pd.read_csv('news_data_keywords.csv')
    df['label'] = df['title_translated'].apply(analyze_sentiment, targets=targets)
    df.to_csv('news_data_analyzed.csv', index=False)

    print('sentiment analysis completed and saved to news_data_analyzed.csv')