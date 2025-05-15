import pandas as pd
import chromadb
import tqdm

df = pd.read_csv("hf://datasets/igorriti/ambience-audio/train.csv")
df = df.dropna(subset=["id", "title", "caption"])

chroma_client = chromadb.PersistentClient(path="audio/chroma_db")
collection = chroma_client.get_or_create_collection(name="audio-collection")

for i in tqdm.tqdm(range(len(df) // 100)):
  collection.add(
    documents=df["caption"].iloc[i:i + 100].tolist(),
    ids=df["id"].iloc[i:i + 100].tolist(),
    metadatas=[{"title": df["title"].iloc[j]} for j in range(i, i + 100)],
  )