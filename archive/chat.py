import ollama
from query import retrieve


def chat(question, model='gemma:7b'):
    try:
        context =  retrieve(question)
        response = ollama.chat(
            model = model,
            messages=[{'role':'user','content':f'You have to reply to this {question} in a certain writing style of this example -{context}'}],
            stream= False
        )
        print(response['message']['content'])
    except Exception as e:
        print(f"An error occured: {e}")

if __name__ == "__main__":
    print("Chat example")
    chat(model="gemma:7b", question="Hey how was your day")