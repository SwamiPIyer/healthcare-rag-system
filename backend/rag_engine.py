from typing import List, Dict
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from config import Config

class HealthcareRAG:
    def __init__(self):
        Config.validate()
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.llm = OpenAI(model="gpt-3.5-turbo", api_key=Config.OPENAI_API_KEY)
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        self.index = None
        self.query_engine = None
    
    def create_documents(self, data):
        docs = []
        for item in data:
            text = "Title: " + item["title"] + ". Abstract: " + item["abstract"] + ". Text: " + item["full_text"]
            docs.append(Document(text=text, metadata={"pmcid": item["pmcid"], "title": item["title"]}))
        return docs
    
    def build_index(self, documents):
        self.index = VectorStoreIndex.from_documents(documents, embed_model=self.embed_model)
    
    def setup_query_engine(self):
        self.query_engine = self.index.as_query_engine()
    
    def query(self, question):
        response = self.query_engine.query(question)
        sources = []
        for n in response.source_nodes:
            sources.append({"pmcid": n.metadata.get("pmcid"), "title": n.metadata.get("title"), "score": n.score, "text_snippet": n.text[:200]})
        return {"question": question, "answer": response.response, "sources": sources, "num_sources": len(sources)}
    
    def batch_query(self, questions):
        return [self.query(q) for q in questions]
