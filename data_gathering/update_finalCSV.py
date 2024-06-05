import pandas as pd
import sys
def move_column_to_front(df, col_name):
    # Get a list of columns
    cols = df.columns.tolist()
    
    # Move the specified column to the front
    cols.insert(0, cols.pop(cols.index(col_name)))
    
    # Reorder the DataFrame columns
    return df[cols]

# Function to update the CSV file with new data
def update_csv(file_path, new_data):
    # print(f"New data added: {new_data}")
    try:
        # Try to read the CSV file
        existing_data = pd.read_csv(file_path)
    except FileNotFoundError:
        existing_data = pd.DataFrame()

    if existing_data.empty:
        new_data = move_column_to_front(new_data, 'label')
        new_data.to_csv(file_path, index=False)
        return
    combined_data = pd.concat([existing_data, new_data])
    combined_data.drop_duplicates(subset=['link'], keep='last',inplace=True)
    combined_data.drop_duplicates(subset=['title','source'], keep='last',inplace=True)
    combined_data.sort_values(by='date', ascending=False, inplace=True)
    # Checking for exact duplicates based on the 'link' column
    combined_data = move_column_to_front(combined_data, 'label')
    combined_data.to_csv(file_path, index=False)

if __name__ == '__main__':
    current_target = sys.stdin.read().strip()
    pf = pd.read_csv('news_data_topic_assigned.csv')
    update_csv(current_target+'.csv', pf)

    print(f"{current_target}.csv updated successfully!")