import pandas as pd
# import chromadb
import tqdm
import streamlit as st
from streamlit_chromadb_connection.chromadb_connection import ChromadbConnection


df = pd.read_csv("hf://datasets/igorriti/ambience-audio/train.csv")
df = df.dropna(subset=["id", "title", "caption"])

# chroma_client = chromadb.PersistentClient(path="audio/chroma_db")
# collection = chroma_client.get_or_create_collection(name="audio-collection")

configuration = {
    "client": "PersistentClient",
    "path": "audio/chroma_db",
}

collection_name = "audio-collection"
conn = st.connection("chromadb", type=ChromadbConnection, **configuration)
conn.create_collection(collection_name=collection_name,
  embedding_function_name="DefaultEmbeddingFunction",
  embedding_config={})

for i in tqdm.tqdm(range(len(df) // 100)):
  conn.upload_documents(
    collection_name=collection_name,
    documents=df["caption"].iloc[i:i + 100].tolist(),
    ids=df["id"].iloc[i:i + 100].tolist(),
    metadatas=[{"title": df["title"].iloc[j]} for j in range(i, i + 100)],
    embedding_function_name="DefaultEmbeddingFunction",
  )