from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
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

app_state = {'index_built': False, 'query_history': [], 'current_data': [], 'data_source': 'none'}

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
    try:
        data = data_loader.load_sample_data()
        app_state['current_data'] = data
        app_state['data_source'] = 'sample'
        return jsonify({'success': True, 'message': 'Loaded ' + str(len(data)) + ' samples', 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pdf/upload', methods=['POST'])
def upload_pdf():
    try:
        print('PDF upload request received')
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400
        
        print('Processing file:', file.filename)
        
        # Save and process PDF
        filename = secure_filename(file.filename)
        file_data = file.read()
        filepath = pdf_processor.save_uploaded_file(file_data, filename)
        
        print('File saved to:', filepath)
        
        # Load PDF documents
        documents = pdf_processor.load_pdf(filepath)
        
        print('Loaded', len(documents), 'pages')
        
        # Convert to data format
        data = []
        for i, doc in enumerate(documents):
            data.append({
                'pmcid': 'PDF_page_' + str(i+1),
                'title': filename + ' - Page ' + str(i+1),
                'abstract': doc.text[:300] + ('...' if len(doc.text) > 300 else ''),
                'full_text': doc.text
            })
        
        app_state['current_data'] = data
        app_state['data_source'] = 'pdf'
        
        # Get PDF info
        pdf_info = {
            'filename': filename,
            'num_pages': len(documents),
            'file_size_kb': len(file_data) / 1024
        }
        
        print('PDF processed successfully')
        
        return jsonify({
            'success': True,
            'message': 'Successfully processed ' + filename,
            'data': data,
            'pdf_info': pdf_info
        })
        
    except Exception as e:
        print('Error processing PDF:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/index/build', methods=['POST'])
def build_index():
    global rag_system
    try:
        if not app_state['current_data']:
            return jsonify({'success': False, 'error': 'No data loaded. Please load data first.'}), 400
        
        print('Building index with', len(app_state['current_data']), 'documents')
        
        rag_system = HealthcareRAG()
        docs = rag_system.create_documents(app_state['current_data'])
        rag_system.build_index(docs)
        rag_system.setup_query_engine()
        app_state['index_built'] = True
        
        print('Index built successfully')
        
        return jsonify({'success': True, 'message': 'Index built successfully with ' + str(len(docs)) + ' documents'})
    except Exception as e:
        print('Error building index:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_system():
    try:
        if not app_state['index_built']:
            return jsonify({'success': False, 'error': 'Index not built. Please build the index first.'}), 400
        
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'success': False, 'error': 'No question provided'}), 400
        
        print('Processing query:', question)
        
        result = rag_system.query(question)
        app_state['query_history'].append(result)
        
        print('Query completed')
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print('Error processing query:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print('=' * 60)
    print('HEALTHCARE RAG SYSTEM WITH PDF UPLOAD')
    print('=' * 60)
    print('http://localhost:5001')
    print('=' * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
