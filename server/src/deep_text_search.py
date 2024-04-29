import os
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import numpy as np
import pickle

EMBEDDINGS_MODEL = "sentence-transformers/nli-mpnet-base-v2"
EMBEDDING_DATA_DIR = "./data/nli-mpnet-base-v2_metadata"
CORPUS_LIST_DATA_FILE = "corpus_list_data.pickle"
CORPUS_EMBEDDINGS_DATA_FILE = "corpus_embeddings_data.pickle"


class LoadData:
    def __init__(self):
        self.corpus_list = None

    def from_csv(self, file_path: str):
        csv_data = pd.read_csv(file_path)
        column_name = str(input("Input the text Column Name Please ? : "))
        self.corpus_list = csv_data[column_name].dropna().to_list()
        return self.corpus_list


class TextEmbedder:
    def __init__(self):
        self.corpus_embeddings_data = os.path.join(
            EMBEDDING_DATA_DIR, CORPUS_EMBEDDINGS_DATA_FILE
        )
        self.corpus_list_data = os.path.join(EMBEDDING_DATA_DIR, CORPUS_LIST_DATA_FILE)
        self.corpus_list = None
        self.embedder = SentenceTransformer(EMBEDDINGS_MODEL)
        self.corpus_embeddings = None
        if EMBEDDING_DATA_DIR not in os.listdir():
            os.makedirs(EMBEDDING_DATA_DIR)

    def embed(self, corpus_list: list):
        self.corpus_list = corpus_list
        if len(os.listdir(EMBEDDING_DATA_DIR)) == 0:
            self.corpus_embeddings = self.embedder.encode(
                self.corpus_list, convert_to_tensor=True, show_progress_bar=True
            )
            pickle.dump(self.corpus_embeddings, open(self.corpus_embeddings_data, "wb"))
            pickle.dump(self.corpus_list, open(self.corpus_list_data, "wb"))
            print("Embedding data Saved Successfully!")
            print(os.listdir(EMBEDDING_DATA_DIR))
        else:
            print(
                "Embedding data already present, Do you want Embed & Save Again? Enter yes or no"
            )
            flag = str(input())
            if flag.lower() == "yes":
                self.corpus_embeddings = self.embedder.encode(
                    self.corpus_list, convert_to_tensor=True, show_progress_bar=True
                )
                pickle.dump(
                    self.corpus_embeddings, open(self.corpus_embeddings_data, "wb")
                )
                pickle.dump(self.corpus_list, open(self.corpus_list_data, "wb"))
                print("Embedding data Saved Successfully Again!")
                print(os.listdir(EMBEDDING_DATA_DIR))
            else:
                print("Embedding data already Present, Please Apply Search!")
                print(os.listdir(EMBEDDING_DATA_DIR))

    def load_embedding(self):
        if len(os.listdir(EMBEDDING_DATA_DIR)) == 0:
            print("Embedding data Not present, Please Run Embedding First")
        else:
            print("Embedding data Loaded Successfully!")
            print(os.listdir(EMBEDDING_DATA_DIR))
            return pickle.load(open(self.corpus_embeddings_data, "rb"))


class TextSearch:
    def __init__(self):
        self.corpus_embeddings = pickle.load(
            open(os.path.join(EMBEDDING_DATA_DIR, CORPUS_EMBEDDINGS_DATA_FILE), "rb")
        )
        self.data = pickle.load(
            open(os.path.join(EMBEDDING_DATA_DIR, CORPUS_LIST_DATA_FILE), "rb")
        )

    def find_similar(self, query_text: str, top_n=10):
        self.top_n = top_n
        self.query_text = query_text
        self.query_embedding = TextEmbedder().embedder.encode(
            self.query_text, convert_to_tensor=True
        )
        self.cos_scores = (
            util.pytorch_cos_sim(self.query_embedding, self.corpus_embeddings)[0]
            .cpu()
            .data.numpy()
        )
        self.sort_list = np.argsort(-self.cos_scores)
        self.all_data = []
        for idx in self.sort_list[1 : self.top_n + 1]:
            data_out = {}
            data_out["index"] = int(idx)
            data_out["text"] = self.data[idx]
            data_out["score"] = self.cos_scores[idx]
            self.all_data.append(data_out)
        return self.all_data
