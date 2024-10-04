from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import pandas as pd
import subprocess
import re
from apscheduler.schedulers.background import BackgroundScheduler
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

app = Flask(__name__)
current_target='上海商銀'
# Path to your CSV file
csv_file_path = f"{current_target}.csv"

# periodically refresh data
def refresh_data_scheduler():
    try:
        result = subprocess.run(['python3', 'data_gathering/web_scrape.py'], 
                                input=current_target,
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                text=True, 
                                check=True)
        output = result.stdout

        if "No news articles found. Exiting the program." in output:
            print("Scheduler: No new articles found.")
            return
        # subprocess.run(['python3', 'data_gathering/data_cleaning.py'], check=True)
        process_keyword=subprocess.Popen(['python3', 'data_gathering/keywords_generate.py'],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True
                                )
        stdout, stderr = process_keyword.communicate(input=current_target)
        print(stdout)
        if process.returncode == 0:
            process_sentiment = subprocess.run(['python3', 'data_gathering/sentiment_analysis.py'], input=current_target, capture_output=True, text=True, check=True)
            print(process_sentiment.stdout)
            process_topic = subprocess.run(['python3', 'data_gathering/topic_assign.py'], capture_output=True, check=True)
            print(process_topic.stdout)
            process_update = subprocess.run(['python3', 'data_gathering/update_finalCSV.py'], input=current_target, capture_output=True, text=True, check=True)
            print(process_update.stdout)

        global data
        data = read_data(csv_file_path)
        return
    except subprocess.CalledProcessError as e:
        print(f"Error refreshing data: {e}")
        return
def schedule_jobs():
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_data_scheduler, 'cron', hour=9, minute=10)
    scheduler.start()


def convert_date_format(date_str):
    # Use regular expression to extract year, month, and day
    match = re.match(r"(\d{4})年(\d{2})月(\d{2})日", date_str)
    if match:
        year, month, day = match.groups()
        # Return date in yyyy-mm-dd format
        return f"{year}-{month}-{day}"
    else:
        return date_str


def read_data(csv_file_path):
    try:
        data = pd.read_csv(csv_file_path)
        topic_map = {
            1: "商業",  # Business
            2: "市場",  # Markets
            3: "可持續性",  # Sustainability
            4: "法律",  # Legal
            5: "技術"  # Technology
        }
        data['topic_description'] = data['topic'].map(topic_map)
        data['title'] = data.apply(lambda row: f'<a href="{row["link"]}" target="_blank">{row["title"]}</a>', axis=1)
        data['snippet'] = data.apply(lambda row: f'{row["snippet"]} <a href="#" class="keyword-link" data-keyword="{" ".join([i.strip() for i in row['keywords'].replace('\'','').strip('][').split(",")])}">{"/ ".join([i.strip() for i in row['keywords'].replace('\'','').strip('][').split(",")])}</a>', axis=1)
        data['date'] = pd.to_datetime(data['date'].apply(convert_date_format))
        return data
    except Exception as e:
        print(f"Error reading data: {e}")
        return pd.DataFrame()

@app.route('/')
def index():
    display_data=data.copy()
    display_data.drop(columns=['topic_description', 'topic','link', 'title_translated','content', 'keywords'],inplace=True)
    # Add classes to the columns
    display_data.columns = [
        '<th class="label-col">label</th>',
        '<th class="title-col">title</th>',
        '<th class="snippet-col">snippet</th>',
        '<th class="source-col">source</th>',
        '<th class="date-col">date</th>',
    ]
    data_html = display_data.to_html(classes='table table-striped', escape=False, index=False)
    return render_template('index.html', table=data_html, topics=unique_topics, current_target=current_target, sentiments=unique_sentiments)

@app.route('/cancel', methods=['POST'])
def cancel():
    global process
    process.terminate()
    process.wait()
    return redirect(url_for('index'))

@app.route('/filter', methods=['POST'])
def filter_data():
    topic = request.form.get('topic')
    sentiment = request.form.get('sentiment')
    search = request.form.get('search')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    filtered_data = data.copy()
    if topic:
        filtered_data = filtered_data[filtered_data['topic_description'] == topic]
    if sentiment:
        filtered_data = filtered_data[filtered_data['label'] == sentiment]
    if search:
        search_terms = search.lower().split()
        filtered_data = filtered_data[filtered_data.apply(lambda row: any(term in row['title'].lower() or term in row['snippet'].lower() for term in search_terms), axis=1)]
    if start_date:
        filtered_data = filtered_data[filtered_data['date'] >= start_date]
    if end_date:
        filtered_data = filtered_data[filtered_data['date'] <= end_date]

    display_data = filtered_data.drop(columns=['topic_description', 'topic', 'link', 'title_translated', 'content', 'keywords'])
    data_html = display_data.to_html(classes='table table-striped', escape=False, index=False)
    return data_html

@app.route('/refresh', methods=['POST'])
def refresh_data():
    try:
        global data
        global current_target

        target = request.form.get('target', current_target)
        csv_file_path = target+'.csv'
        print(f"Refreshing data for target: {target}")
        global process

        print("Looking for news articles...")
        process = subprocess.Popen(
            ['python3', 'data_gathering/web_scrape.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=target)
        # subprocess.run(['python3', 'data_gathering/data_cleaning.py'], check=True)

        # if process.returncode != 0:
        #     raise subprocess.CalledProcessError(process.returncode, process.args, output=stdout, stderr=stderr)
        print(stdout)

        if process.returncode != 0:
            print(stderr)
            return redirect(url_for('index'))

        if "No news articles found. Exiting the program." in stdout:
            try:
                data = read_data(csv_file_path)
            except Exception as e:
                print(f"No articles found and no such file exists: {csv_file_path}")
            current_target = target
            return redirect(url_for('index'))
        
        print("Generating keywords...")
        # subprocess.run(['python3', 'data_gathering/data_cleaning.py'], check=True)
        process=subprocess.Popen(['python3', 'data_gathering/keywords_generate.py'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
        stdout, stderr = process.communicate(input=target)
        print(stdout)
        if process.returncode == 0:
            print("Analyzing sentiment...")
            process_sentiment = subprocess.run(['python3', 'data_gathering/sentiment_analysis.py'], input=target, capture_output=True, text=True, check=True)
            print(process_sentiment.stdout)
            print("Assigning topics...")
            process_topic = subprocess.run(['python3', 'data_gathering/topic_assign.py'], capture_output=True, check=True)
            print(process_topic.stdout)
            print("Updating target CSV...")
            process_update = subprocess.run(['python3', 'data_gathering/update_finalCSV.py'], input=target, capture_output=True, text=True, check=True)
            print(process_update.stdout)
        else:
            print(stderr)
        current_target = target
        data = read_data(csv_file_path)
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as e:
        print(f"Error refreshing data: {e}")
        return jsonify({"error": "Failed to refresh data"}), 500

@app.route('/get_sentiment_data', methods=['POST'])
def get_sentiment_data():
    topic = request.form.get('topic')
    sentiment = request.form.get('sentiment')
    search = request.form.get('search')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    filtered_data = data.copy()
    if topic:
        filtered_data = filtered_data[filtered_data['topic_description'] == topic]
    if sentiment:
        filtered_data = filtered_data[filtered_data['label'] == sentiment]
    if search:
        search_terms = search.lower().split()
        filtered_data = filtered_data[filtered_data.apply(lambda row: any(term in row['title'].lower() or term in row['snippet'].lower() for term in search_terms), axis=1)]
    if start_date:
        filtered_data = filtered_data[filtered_data['date'] >= start_date]
    if end_date:
        filtered_data = filtered_data[filtered_data['date'] <= end_date]

    sentiment_counts = filtered_data['label'].value_counts().reindex(['neutral', 'positive', 'negative'], fill_value=0)
    sentiment_data = {
        'neutral': int(sentiment_counts['neutral']),
        'positive': int(sentiment_counts['positive']),
        'negative': int(sentiment_counts['negative'])
    }
    print(sentiment)

    return jsonify(sentiment_data)

@app.route('/get_trend_data', methods=['POST'])
def get_trend_data():
    topic = request.form.get('topic')
    sentiment = request.form.get('sentiment')
    search = request.form.get('search')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    time_frame = request.form.get('timeFrame', 'M')  # Default to monthly
    filtered_data = data.copy()
    if topic:
        filtered_data = filtered_data[filtered_data['topic_description'] == topic]
    if sentiment:
        filtered_data = filtered_data[filtered_data['label'] == sentiment]
    if search:
        search_terms = search.lower().split()
        filtered_data = filtered_data[filtered_data.apply(lambda row: any(term in row['title'].lower() or term in row['snippet'].lower() for term in search_terms), axis=1)]
    if start_date:
        filtered_data = filtered_data[filtered_data['date'] >= start_date]
    if end_date:
        filtered_data = filtered_data[filtered_data['date'] <= end_date]

    if 'date' not in filtered_data.columns:
        return jsonify({"error": "Date column not found in the data"}), 500

    if time_frame == 'D':
        resample_rule = 'D'
        time_format = '%Y-%m-%d'
    elif time_frame == 'W':
        resample_rule = 'W-MON'
        time_format = '%Y-%W'
    else:
        resample_rule = 'ME'
        time_format = '%Y-%m'

    filtered_data.set_index('date', inplace=True)

    monthly_counts = filtered_data.resample(resample_rule).size().rename('total').to_frame()
    monthly_counts['neutral'] = filtered_data[filtered_data['label'] == 'neutral'].resample(resample_rule).size()
    monthly_counts['positive'] = filtered_data[filtered_data['label'] == 'positive'].resample(resample_rule).size()
    monthly_counts['negative'] = filtered_data[filtered_data['label'] == 'negative'].resample(resample_rule).size()
    monthly_counts['total'] = monthly_counts['positive'] - monthly_counts['negative']

    monthly_counts.fillna(0, inplace=True)
    monthly_counts = monthly_counts.astype(int)

    trend_data = {
        'months': monthly_counts.index.strftime(time_format).tolist(),
        'neutral_counts': monthly_counts['neutral'].tolist(),
        'positive_counts': monthly_counts['positive'].tolist(),
        'negative_counts': monthly_counts['negative'].tolist(),
        'total_counts': monthly_counts['total'].tolist()
    }

    return jsonify(trend_data)

def generate_wordcloud(data):
    word_list = []
    for _, row in data.iterrows():
        val = row['keywords']
        words = [i.strip() for i in val.replace('\'','').strip('][').split(",")]
        word_list.extend(words)

    word_freq = pd.Series(word_list).value_counts().to_dict()
    font_path = 'data_gathering/Font/STHeiti Light.ttc' # 字型路徑

    #文字雲繪製參數設定
    wc = WordCloud(
            background_color='black',        #   背景顏色
            max_words=500,                   #   最大分詞數量
            max_font_size=None,              #   顯示字體的最大值
            font_path=font_path,             #   若為中文則需引入中文字型(.TTF)
            random_state=None,               #   隨機碼生成各分詞顏色
            prefer_horizontal=0.9)           #   調整分詞中水平和垂直的比例
    
    wc.generate_from_frequencies(word_freq)

    # Save the word cloud image to a BytesIO object
    img = io.BytesIO()
    wc.to_image().save(img, format='PNG')
    img.seek(0)
    return img

@app.route('/filtered_wordcloud', methods=['GET'])
def filtered_wordcloud():
    topic = request.args.get('topic')
    sentiment = request.args.get('sentiment')
    search = request.args.get('search')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    filtered_data = data.copy()
    if topic:
        filtered_data = filtered_data[filtered_data['topic_description'] == topic]
    if sentiment:
        filtered_data = filtered_data[filtered_data['label'] == sentiment]
    if search:
        search_terms = search.lower().split()
        filtered_data = filtered_data[filtered_data.apply(lambda row: any(term in row['title'].lower() or term in row['snippet'].lower() for term in search_terms), axis=1)]
    if start_date:
        filtered_data = filtered_data[filtered_data['date'] >= start_date]
    if end_date:
        filtered_data = filtered_data[filtered_data['date'] <= end_date]

    img = generate_wordcloud(filtered_data)
    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    try:
        print("Looking for news articles...")
        process = subprocess.Popen(
            ['python3', 'data_gathering/web_scrape.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=current_target)
        print(stdout)
        # subprocess.run(['python3', 'data_gathering/data_cleaning.py'], check=True)
  
        if process.returncode == 0 and "No news articles found. Exiting the program." not in stdout:
            process_keyword=subprocess.Popen(['python3', 'data_gathering/keywords_generate.py'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
            stdout, stderr = process_keyword.communicate(input=current_target)
            print(stdout)
            if process.returncode == 0:
                process_sentiment = subprocess.run(['python3', 'data_gathering/sentiment_analysis.py'], input=current_target, capture_output=True, text=True, check=True)
                print(process_sentiment.stdout)
                process_topic = subprocess.run(['python3', 'data_gathering/topic_assign.py'], capture_output=True, text=True, check=True)
                print(process_topic.stdout)
                process_update = subprocess.run(['python3', 'data_gathering/update_finalCSV.py'], input=current_target, capture_output=True, text=True, check=True)
                print(process_update.stdout)

        data = read_data(csv_file_path)
        unique_topics = data['topic_description'].unique()
        unique_sentiments = data['label'].unique()
        schedule_jobs()
        app.run(host='0.0.0.0', port=4000, debug=False)
    except subprocess.CalledProcessError as e:
        print(f"Error initializing application: {e}")
        exit(1)
