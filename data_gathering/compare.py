import pandas as pd

# Paths to your CSV files
csv_file_path_1 = 'sentiment_analysis_v1_data.csv'
csv_file_path_2 = 'shanghai_commercial_bank_data.csv'

# Read the CSV files
df1 = pd.read_csv(csv_file_path_1)
df2 = pd.read_csv(csv_file_path_2)

# Merge the DataFrames on 'title' and 'source'
merged_df = pd.merge(df1, df2, on=['title', 'source'], suffixes=('_df1', '_df2'))

# Compare the labels and create a new column to show the comparison
merged_df['label_comparison'] = merged_df.apply(lambda row: row['label_df1'] == row['label_df2'], axis=1)

# Print the rows where the labels do not match
mismatched_labels = merged_df[merged_df['label_comparison'] == False]
print(mismatched_labels[['title', 'source', 'label_df1', 'label_df2']])

# Save the comparison results to a new CSV file if needed
comparison_csv_path = 'comparison_results.csv'
merged_df.to_csv(comparison_csv_path, index=False)
