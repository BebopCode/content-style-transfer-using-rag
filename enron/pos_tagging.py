import spacy
from collections import Counter

def extract_top_words(text):
    # Load English language model
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    # Initialize counters
    verbs = Counter()
    adverbs = Counter()
    adjectives = Counter()
    stop_words = Counter()

    # Iterate through tokens
    for token in doc:
        if token.is_alpha:  # ignore punctuation/numbers
            if token.pos_ == "VERB":
                verbs[token.lemma_.lower()] += 1
            elif token.pos_ == "ADV":
                adverbs[token.lemma_.lower()] += 1
            elif token.pos_ == "ADJ":
                adjectives[token.lemma_.lower()] += 1
            elif token.is_stop:
                stop_words[token.text.lower()] += 1

    # Get top 5 of each category
    top_verbs = [w for w, _ in verbs.most_common(20)]
    top_adverbs = [w for w, _ in adverbs.most_common(20)]
    top_adjectives = [w for w, _ in adjectives.most_common(20)]
    top_stop_words = [w for w, _ in stop_words.most_common(20)]

    return {
        "verbs": top_verbs,
        "adverbs": top_adverbs,
        "adjectives": top_adjectives,
        "stop_words": top_stop_words
    }