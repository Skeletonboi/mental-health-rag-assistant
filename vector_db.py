import faiss
import numpy as np
from numpy.linalg import norm

class NormalizedVectorDatabase():
    def __init__(self, embedder, dim, txts=[], index_path=None):
        self.embedder = embedder
        self.dim = dim
        if index_path:
            self.index = faiss.read_index(index_path)
        else:
            self.index = faiss.IndexFlatL2(dim)
        self.txts = txts
        
    def embed_txts(self, txts=None):
        txts = txts if txts else self.txts
        embds = np.array(embedder.embed_documents(txts), dtype=np.float32)
        for i in range(len(embds)):
            embds[i] = embds[i] / norm(embds[i])
        return embds
    
    def renormalize_index(self):
        embds = []
        for i in range(self.index.ntotal):
            old_embd = self.index.reconstruct(i)
            embds.append(old_embd / norm(old_embd))
        embds = np.array(embds, dtype=np.float32)
        self.index.reset()
        self.add_embds(embds)
        return

    def add_embds(self, embds):
        self.index.add(embds)
        return
    
    def export_index(self, index_path='faiss_index.bin'):
        faiss.write_index(self.index, index_path)
        return
    
    def search(self, user_query, k):
        q_embd = np.array([self.embedder.embed_query(f'Instruct: Given a web search query, retrieve relevant passages that answer the query.\nQuery: {user_query}')], dtype=np.float32)
        q_embd_normd = q_embd / norm(q_embd)
        
        D, I = self.index.search(q_embd_normd, k)
        return D, I


if __name__ == '__main__':
    # EXAMPLE USAGE
    import json
    from langchain_huggingface import HuggingFaceEmbeddings

    renorm_index = False
    
    with open('filtered_vid_ts.json', 'r') as file:
        filtered_vids = json.load(file)
    summaries = [vid['summary'] for vid in filtered_vids]

    embedder = HuggingFaceEmbeddings(model_name='NovaSearch/stella_en_1.5B_v5',
                                    model_kwargs={'device': 'cuda'},
                                    encode_kwargs={'convert_to_numpy' : True}
                                    )

    vdb = NormalizedVectorDatabase(embedder, 1024, txts=summaries, index_path='faiss_renorm_index.bin')

    if renorm_index:
        vdb.renormalize_index()
        vdb.export_index('faiss_renorm_index.bin')

    query = 'What is the ego? How does it manifest in healthy and unhealthy ways? What are some strategies to manage it? What are the effects of it on mental health?'
    k = 10

    D, I = vdb.search(query, k)

    for i in range(k):
        print(D[0][i], I[0][i], filtered_vids[I[0][i]]['title'])
        
    # LANGCHAIN HF FAISS
    # from langchain.text_splitter import RecursiveCharacterTextSplitter
    # from langchain_community.vectorstores import FAISS
    # from langchain_community.docstore.in_memory import InMemoryDocstore
    # from langchain.docstore.document import Document
    # docs =  [Document(page_content=vid['summary'], metadata={"source": "local", "title":vid['title']}) for vid in filtered_vids[:10]]
    # vector_db = FAISS(embedding_function=embedder,
    #                 index=index,
    #                 docstore=InMemoryDocstore(),
    #                 index_to_docstore_id={},
    #                 )
    # vector_db.add_documents(docs)
    # res = vector_db.similarity_search_with_score("Issues with controlling parent, peter pan, stuck in life, can't make progress", k=2)
    # print(res)