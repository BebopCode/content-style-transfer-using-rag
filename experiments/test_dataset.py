import pandas as pd

# Load the dataset
# Replace 'enron_dataset.csv' with your actual filename
df = pd.read_csv('experiments/emails_cleaned.csv')

# Method 1: Get a simple list of column names
print("Column names:", df.columns.tolist())

# Method 2: See column names along with data types and non-null counts
print("\nDataset Info:")
df.info()

# Method 3: See the first few rows to understand the data
print("\nFirst 5 rows:")
print(df.head())