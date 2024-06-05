import requests
from bs4 import BeautifulSoup
import pandas as pd
from deep_translator import GoogleTranslator
import re
from datetime import datetime
from dateutil.parser import parse as dateutil_parse
import time
import sys
from newspaper import Article

# from newspaper import Article
# import nltk

# ------------------------DATE PARSING FUNCTIONS------------------------

# Check if the date string matches a specific format
def is_valid_date_format(input_string):
    pattern = r'^\d{4}年\d{1,2}月\d{1,2}日$'
    match = re.match(pattern, input_string)
    return bool(match)

# Extract and format the date from a string
def extract_date_only(date_str, date_format):
    return datetime.strptime(date_str, date_format).strftime("%Y年%m月%d日")

# Parse the date string into a consistent format
def parse_date(date_str):
    patterns_formats = [
        (r'\b\d{1,2} [A-Za-z]+ \d{4}\b', "%d %B %Y"),
        (r'\b[A-Za-z]+ \d{1,2}, \d{4}\b', "%B %d, %Y"),
        (r'\b\d{4}-\d{2}-\d{2}\b', "%Y-%m-%d"),
        (r'\d{4}/\d{1,2}/\d{1,2}', "%Y/%m/%d"),
        (r'\d{4}\.\d{1,2}\.\d{1,2}', "%Y.%m.%d"),
        (r'\d{4}年\d{1,2}月\d{1,2}日', "%Y年%m月%d日"),
        (r'\b\d{8}\b', "%Y%m%d"),
        (r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b', None),  # Extended ISO 8601 format
        (r'\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}\b', "%Y-%m-%d %H:%M:%S%z"),  # New format
    ]
    
    for pattern, date_format in patterns_formats:
        match = re.search(pattern, date_str)
        if match:
            date_str = match.group(0)
            try:
                if date_format is None:
                    # Use dateutil to parse ISO 8601 dates and variants
                    date_only = dateutil_parse(date_str).date()
                    return date_only.strftime("%Y年%m月%d日")
                return extract_date_only(date_str, date_format)
            except (ValueError, TypeError):
                continue
    return None

# Find and parse the date from the content of a webpage
def find_date_in_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Define common date patterns
    date_patterns = [
        r'\b\d{1,2} [A-Za-z]+ \d{4}\b',  # Example: 12 January 2024
        r'\b[A-Za-z]+ \d{1,2}, \d{4}\b',  # Example: January 12, 2024
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',     # Example: 2024-01-12
        r'\b\d{4}/\d{1,2}/\d{1,2}\b',     # Example: 2024/01/12
        r'\d{4}\.\d{1,2}\.\d{1,2}',       # Example: 2024.01.12
        r'\d{4}年\d{1,2}月\d{1,2}日',     # Example: 2024年1月12日
        r'\b\d{8}\b',                     # Example: 20240112
        r'\b\d{4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}(?:\.\d+)?(?:Z|[+-]\d{1,2}:\d{1,2})?\b'  # Example: 2024-01-12T14:30:00Z
    ]
    
    # Check for dates in meta tags
    meta_tags = [
        'date', 'article:published_time', 'pubdate', 'og:published_time',
        'parsely-pub-date', 'itemprop', 'datePublished', 'property'
    ]
    
    for tag in meta_tags:
        meta_date = soup.find('meta', {'name': tag}) or \
                    soup.find('meta', {'property': tag})
        
        if meta_date and meta_date.get('content'):
            date_str = meta_date['content']
            transformed_date = parse_date(date_str)
            if transformed_date:
                return transformed_date
            else:
                return date_str
    
    # Check for dates in the content of specific HTML tags
    for element in soup.find_all(['p', 'span', 'div']):
        element_text = element.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, element_text)
            if match:
                date_str = match.group(0)
                transformed_date = parse_date(date_str)
                if transformed_date:
                    return transformed_date
                else:
                    return date_str
    
    return None

# ------------------------DATE PARSING FUNCTIONS------------------------


# ------------------------WEB SCRAPING FUNCTIONS------------------------
# Fetch the HTML content of a webpage
def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
        return None

# Extract news articles from the parsed HTML content
def extract_news(soup, articles, existing_link=None, existing_source=None, existing_title=None,update=False, latest_date=None):
    i = 1
    if soup:
        i = 0
        translation_requests = 0
        # Loop through each news item in the search results
        for item in soup.select('div.SoaBEf'):
            title = item.select_one('div.n0jPhd.ynAwRc.MBeuO.nDgy9d').get_text(strip=True)
            link = item.select_one('a.WlydOe')['href']
            snippet = item.select_one('div.GI74Re.nDgy9d').get_text(strip=True)
            source = item.select_one('div.MgUUmf.NUnG9d span').get_text(strip=True)
            date = item.select_one('div.OSrXXb.rbYSKb.LfVVr').get_text(strip=True)

            try:
                article = Article(link)
                article.download()
                article.parse()
                article.nlp()
                content = article.text
            except:
                # print(f"Failed to download the article: {title}")
                content=""

            # Validate and parse the date
            if is_valid_date_format(date) == False and date != '':
                # date = find_date_in_content(link)
                try:
                    date = article.publish_date
                    if date == None or is_valid_date_format(date) == False:
                        date = find_date_in_content(link)
                except:
                    continue

                if date == None:
                    continue
                if type(date) != str:
                    date=date.strftime("%Y年%m月%d日")
            else:
                date = parse_date(date)

            # print(f'Title: {title}, source: {source}')            
            # Check for existing articles if updating the CSV
            # method1: check if the date is earlier than the latest date
            # method2: check if the title is in the existing title and source is in the existing source
            # articles_date = datetime.strptime(date, "%Y年%m月%d日")

            if update == True and  (link in existing_link or (source in existing_source and title in existing_title)):
                # print("Reached existing articles, stopping the scraping process.")
                continue            
            relevant_text = max(title.split('|'), key=len).strip()

            # Translate the text to English for sentiment analysis
            translated_text = GoogleTranslator(source='auto', target='en').translate(relevant_text)
            translation_requests += 1  # Increment the counter

            # lexically analyze the sentiment of the title
            # potential solution to increase sentiment analysis accuracy
            # final_label = label

            # # perform basic lexical analysis and compare with the sentiment analysis result
            # lexical_label = analyze_sentiment(translated_text)
            # if lexical_label != "neutral":
            #     final_label = lexical_label


            # # Initialize the Article object
            # article = Article(link)

            # # Download and parse the article
            # article.download()
            # article.parse()

            # # Perform natural language processing on the article
            # article.nlp()

            # # Extract the main content
            # main_content = article.text
            i += 1
            # print(f"Title: {title}")
            articles.append({
                'title': title,
                'title_translated': translated_text,
                'content': content,
                'link': link,
                'snippet': snippet,
                'source': source,
                'date': date
            })
            # Limit translation requests to 5 per second
            if translation_requests == 5:
                time.sleep(1)  # Wait for the remaining time to reach 1 second
                translation_requests = 0  # Reset the counter
    else:
        print("Soup object is None, check the HTML response and selectors.")
    return articles, i == 0

# ------------------------WEB SCRAPING FUNCTIONS------------------------

# ----------------------Updating the CSV Functions-----------------------

# Function to load existing CSV data
def load_existing_data(file_path):
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        return pd.DataFrame(columns=['label', 'title', 'title_translated', 'link', 'snippet', 'source', 'date'])

# Function to update the CSV file with new data
def update_csv(file_path, new_data):
    # print(f"New data added: {new_data}")
    existing_data = load_existing_data(file_path)
    combined_data = pd.concat([existing_data, new_data])
    combined_data.sort_values(by='date', ascending=False, inplace=True)
    # Checking for exact duplicates based on the 'link' column
    combined_data.drop_duplicates(subset=['title', 'source'], inplace=True)
    combined_data.to_csv(file_path, index=False)

# ----------------------Updating the CSV Functions-----------------------

# -----------------------------Update CSV-------------------------------
def scrape_func(update=False, target='上海商銀'):
    search_url = 'https://www.google.com/search?'
    search_target = target
    search_category = 'nws'
    search_url+=f'q={search_target}&tbm={search_category}&tbs=sbd:1&start='

    # Load existing data
    final_csv_file_path = search_target+'.csv'
    existing_data = load_existing_data(final_csv_file_path)
    existing_title = set(existing_data['title'].tolist())# Google News search URL for Shanghai Commercial Bank
    existing_source = set(existing_data['source'].tolist())
    existing_link = set(existing_data['link'].tolist())

    if not existing_data.empty:
        latest_date_str = existing_data['date'].max()
        latest_date = datetime.strptime(latest_date_str, "%Y年%m月%d日")
    else:
        latest_date = datetime.min
        update=False

    # Initialize the list to hold articles
    articles = []

    # Loop through the search result pages (pagination)
    if update:
        num_search=50
    else:
        num_search=9999

    for i in range(0, num_search, 10):
        soup = fetch_page(search_url + str(i))
        print(search_url + str(i))
        news_articles, ifEnd = extract_news(soup, articles, update=update, latest_date=latest_date, existing_link=existing_link, existing_source=existing_source, existing_title=existing_title)
        if ifEnd:
            break

    # Convert the list of articles to a DataFrame
    df = pd.DataFrame(news_articles)

    if df.empty:
        print('No news articles found. Exiting the program.')
        return
    
    
    print(f"news aritcles found: \n{df}",)
    new_csv_file_path = 'news_data_cleaned.csv'
    # create CSV file with new data
    df.to_csv(new_csv_file_path, index=False)

    print(f'News articles saved to {new_csv_file_path}')
# --------------------------------Update CSV-------------------------------

if __name__ == '__main__':
    current_target = sys.stdin.read().strip()
    scrape_func(update=True, target=current_target)