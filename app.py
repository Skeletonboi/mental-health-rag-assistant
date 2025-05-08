import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from vector_db import NormalizedVectorDatabase
from langchain_huggingface import HuggingFaceEmbeddings
import gradio as gr
import pandas as pd
import torch

# LOAD ENVIRONMENT VARIABLES AND PARAMETERS
load_dotenv()
transcript_savepath = 'filtered_vid_ts.json'
vectordb_index_savepath = 'faiss_renorm_index.bin'
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# LOAD EMBEDDING MODEL AND VECTOR DATABASE
embedder = HuggingFaceEmbeddings(model_name='NovaSearch/stella_en_1.5B_v5',
                                model_kwargs={'device': device},
                                encode_kwargs={'convert_to_numpy' : True}
                                )

with open(transcript_savepath, 'r') as file:
    vids = json.load(file)

vdb = NormalizedVectorDatabase(embedder, 1024, index_path=vectordb_index_savepath)

# GRADIO FUNCTIONS
def retrieve_context(query, k):
    D, I = vdb.search(query, k)
    D, I = D.flatten(), I.flatten()
    
    retrieved_context = " \n\n\n ".join(' <CONTEXT TITLE> ' + vids[idx]['title'] + ' <CONTEXT SUMMARY> ' + vids[idx]['summary'] for idx in I)
    retrieved_titles = [vids[idx]['title'] for idx in I]
    return {'retrieved_context': retrieved_context, 'retrieved_titles': retrieved_titles, 'embedding_dists': D}

def inference(query, inference_model_name, state):
    retrieved_context, retrieved_titles = state['retrieved_context'], state['retrieved_titles']

    client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
    completion = client.chat.completions.create(
        model=inference_model_name,
        messages=[
            {'role': 'developer', 'content': f'You are a mental health assistant to help answer questions, supplemented by the following retrieved context \
                                            from a mental health professional. Use only the content from the provided context to answer the user\'s question. \
                                            Do not introduce any of your own bias or subjectivity. \
                                            Do not provide any information that is not present in the context. \
                                            Make sure to make detailed references to the context and draw several examples from it. \
                                            {retrieved_context}'},
            {'role': 'user', 'content': f'{query}'}
        ]
    )
    return completion.choices[0].message.content

def buildInfoTable(state):
    retrieved_titles, embedding_dists = state['retrieved_titles'], state['embedding_dists']
    return pd.DataFrame({
        'Retrieved Video Title': retrieved_titles, 
        'Embedding Distance': embedding_dists
        })

# GRADIO MAIN
with gr.Blocks() as main:
    example_query_1 = 'What is the ego? How does it manifest in healthy and unhealthy ways? What are some strategies to manage it? What are the effects of it on mental health?'
    example_query_2 = 'What is the Sanskrit term Dr K uses for our purpose, meaning, to describe something that only we can do?'
    example_query_3 = 'How do I find a partner? What are some traumas to look out for? Looking for relationship advice, what are some practical tips? What mindset should I use to approach with all this red-pill / black-pill stuff on the internet?'
    
    state = gr.State({})
    query = gr.Textbox(label='Query', placeholder=example_query_1, value=example_query_1)
    k = gr.Slider(label='k', info='Number of retrieved documents', minimum=1, maximum=10, step=1, value=10)
    inference_model_name = gr.Radio(['gpt-4o','gpt-4o-mini'], label='Inference Model', value=1)
    submit = gr.Button('Submit')

    output = gr.Textbox(label='Response', container=True)
    table = gr.Dataframe(label='Retrieved Video Titles and Embedding Distances')

    submit.click(
        fn=retrieve_context,
        inputs=[query, k],
        outputs=[state]
    ).then(
        fn=inference,
        inputs=[query, inference_model_name, state],
        outputs=[output]
    ).then(
        fn=buildInfoTable,
        inputs=[state],
        outputs=[table]
    )

if __name__ == '__main__':
    main.launch(share=True)
