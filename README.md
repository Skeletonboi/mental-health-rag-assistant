# mental-health-rag-assistant

### Ask questions to a LLM with detailed up-to-date knowledge from the entire HealthyGamerGG Youtube Channel.
### Currently hosted on HuggingFace Spaces at: https://huggingface.co/spaces/Skeletonboy/healthygamer-rag-assistant

#### This code repo contains:
- **yt-transcript.py** - automatic video transcript scraper for all uploads of any Youtube channel
- **vector_db.py** - FAISS vector store wrapper to use custom normalized embeddings
- **transcript_ops.py** - transcript summarizer using third-party LLMs
- **app.py** - deploy RAG question-answerer as Gradio app

Each video from the HealthyGamerGG Youtube channel is summarized in detail using GPT-4o, and embedded using [stella_en_1.5B_v5](https://huggingface.co/NovaSearch/stella_en_1.5B_v5) before being passed into a FAISS vector index for quick similarity-searching.

By passing in a mental-health related user query, the query is then embedded locally and used to retrieve top-K relevant summarized video transcripts. 

All code written 100% completely from scratch.

## Setup
To use, install required libraries:
'''
pip install -r requirements.txt
'''

Setup your API tokens in a .env file:
```
OPENAI_API_KEY = ...
YT_API_KEY = ...
HF_WRITE_TOKEN = ...
```

Run yt_transcript.py to pull transcripts from every youtube video available in the channel. Auto-generated transcripts will be used for videos without manually uploaded transcripts.
```
yt_transcript.py <YT_CHANNEL_ID> <transcript_savepath.json>
```

Run transcript_ops.py to clean, filter, and summarize transcripts. Embedding model is compatible on both CPU and GPU devices:
```
transcript_ops.py <transcript_savepath.json> <new_svepath.json>
```

Set file paths and run app.py to publish as Gradio app
```
gradio app.py
```
