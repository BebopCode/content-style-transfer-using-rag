from extract import extract_features

FILE = 'vince-kaminski-at-enron-com-combined.txt'
def func(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    if not text.strip():
        print("Error: The file is empty or contains only whitespace.")
        return
    extract_features(text)

func(FILE)


