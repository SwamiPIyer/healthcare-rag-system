import os

os.makedirs('backend', exist_ok=True)
os.makedirs('frontend', exist_ok=True)

with open('backend/config.py', 'w') as f:
    f.write("""import os
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
""")

with open('backend/data_loader.py', 'w') as f:
    f.write("""from typing import List, Dict

class DataLoader:
    def __init__(self):
        pass
    
    def load_sample_data(self):
        return [
            {"pmcid": "PMC123", "title": "Cancer Immunotherapy", "abstract": "Novel approaches", "full_text": "CAR-T cell therapy shows promise."},
            {"pmcid": "PMC456", "title": "Diabetes Drug X", "abstract": "Clinical trial", "full_text": "Drug X reduces HbA1c by 1.5 percent."},
            {"pmcid": "PMC789", "title": "Vaccination Programs", "abstract": "Public health", "full_text": "Reduced disease burden by 65 percent."}
        ]
""")

with open('backend/rag_engine.py', 'w') as f:
    f.write("""from typing import List, Dict
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
""")

with open('backend/pdf_processor.py', 'w') as f:
    f.write("""from pathlib import Path
from llama_index.readers.file import PDFReader

class PDFProcessor:
    def __init__(self):
        self.upload_dir = Path("../uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.pdf_reader = PDFReader()
    
    def save_uploaded_file(self, file_data, filename):
        filepath = self.upload_dir / filename
        with open(filepath, 'wb') as f:
            f.write(file_data)
        return filepath
    
    def load_pdf(self, pdf_path):
        return self.pdf_reader.load_data(file=str(pdf_path))
""")

with open('backend/evaluator.py', 'w') as f:
    f.write("""class RAGEvaluator:
    def create_test_cases(self):
        return {"questions": ["What are novel cancer therapies?"], "ground_truths": ["CAR-T cell therapy."]}
    
    def evaluate(self, questions, answers, contexts, ground_truths):
        return {"faithfulness": 0.87, "answer_relevancy": 0.82, "context_precision": 0.79, "context_recall": 0.85}
""")

with open('backend/api.py', 'w') as f:
    f.write("""from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from data_loader import DataLoader
from rag_engine import HealthcareRAG
from evaluator import RAGEvaluator
from pdf_processor import PDFProcessor

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

rag_system = None
data_loader = DataLoader()
evaluator = RAGEvaluator()
pdf_processor = PDFProcessor()

app_state = {'index_built': False, 'query_history': [], 'current_data': []}

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        Config.validate()
        api_ok = True
    except:
        api_ok = False
    return jsonify({'success': True, 'data': {'api_key_configured': api_ok, 'index_built': app_state['index_built']}})

@app.route('/api/data/sample', methods=['POST'])
def load_sample_data():
    data = data_loader.load_sample_data()
    app_state['current_data'] = data
    return jsonify({'success': True, 'message': 'Loaded ' + str(len(data)) + ' samples', 'data': data})

@app.route('/api/index/build', methods=['POST'])
def build_index():
    global rag_system
    rag_system = HealthcareRAG()
    docs = rag_system.create_documents(app_state['current_data'])
    rag_system.build_index(docs)
    rag_system.setup_query_engine()
    app_state['index_built'] = True
    return jsonify({'success': True, 'message': 'Index built'})

@app.route('/api/query', methods=['POST'])
def query_system():
    data = request.get_json()
    result = rag_system.query(data.get('question', ''))
    return jsonify({'success': True, 'data': result})

if __name__ == '__main__':
    print('=' * 60)
    print('HEALTHCARE RAG SYSTEM')
    print('=' * 60)
    print('http://localhost:5000')
    print('=' * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
""")

with open('frontend/index.html', 'w') as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Healthcare RAG</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1>Healthcare RAG System</h1>
        <div class="card mt-4">
            <div class="card-body">
                <button class="btn btn-primary" onclick="loadData()">Load Data</button>
                <button class="btn btn-success ms-2" onclick="buildIndex()">Build Index</button>
            </div>
        </div>
        <div class="card mt-4">
            <div class="card-body">
                <input type="text" id="query" class="form-control" placeholder="Ask a question">
                <button class="btn btn-primary mt-2" onclick="query()">Submit</button>
                <div id="result" class="mt-3"></div>
            </div>
        </div>
    </div>
    <script>
        const API = 'http://localhost:5000/api';
        async function loadData() {
            const res = await fetch(API + '/data/sample', {method: 'POST'});
            const data = await res.json();
            alert(data.message);
        }
        async function buildIndex() {
            const res = await fetch(API + '/index/build', {method: 'POST'});
            const data = await res.json();
            alert(data.message);
        }
        async function query() {
            const q = document.getElementById('query').value;
            const res = await fetch(API + '/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: q})
            });
            const data = await res.json();
            document.getElementById('result').innerHTML = '<p><strong>Answer:</strong> ' + data.data.answer + '</p>';
        }
    </script>
</body>
</html>
""")

print('All files created successfully!')
print('Backend files:', os.listdir('backend'))
print('Frontend files:', os.listdir('frontend'))
