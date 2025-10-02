import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    LLM_MODEL = "gpt-3.5-turbo"
    LLM_TEMPERATURE = 0.1
    TOP_K = 3
    SIMILARITY_THRESHOLD = 0.7
    
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found")
        return True
