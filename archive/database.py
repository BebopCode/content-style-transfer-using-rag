
from langchain_community.document_loaders import PyPDFLoader
import os
from dotenv import load_dotenv
import cohere
import numpy as np
import argparse

load_dotenv()  

api_key = os.getenv('COHERE_API')
print(api_key)
co = cohere.ClientV2(api_key=os.getenv("COHERE_API"))
phrases = ["i love soup", "soup is my favorite", "london is far away"]
model = "embed-v4.0"
input_type = "search_query"

def load():
    document = PyPDFLoader(os.getenv('DATA_PATH'))
    return document.load()

res = co.embed(
    texts=phrases,
    model=model,
    input_type=input_type,
    output_dimension=1024,
    embedding_types=["float"],
)
(soup1, soup2, london) = res.embeddings.float

# compare them
pages =  load()
print(pages[0].page_content)

def main():