from sentence_words_analysis import sentence_analysis
from pos_tagging import extract_top_words

def extract_features(text: str):
    print(extract_top_words(text))
    print(sentence_analysis(text))
    return 
email_reply = """
That is a very good question!

I have just started to know other few aspects of the theory myself. It's so fascinating how it let us get a deeper understanding of space and time.

I also have a last few articles I want to send you next week about other related concepts.

Let me know your next thoughts after you get a few more insights!

Best,

Brad
"""
extract_features(text=email_reply)