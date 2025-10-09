from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from data_loader import DataLoader
from rag_engine import HealthcareRAG
from evaluator import RAGEvaluator
from pdf_processor import PDFProcessor
import os
from datetime import datetime

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

rag_system = None
data_loader = DataLoader()
evaluator = RAGEvaluator()
pdf_processor = PDFProcessor()

app_state = {
    'index_built': False,
    'query_history': [],
    'current_data': [],
    'data_source': 'none',
    'documents': [],  # List of uploaded documents
    'selected_docs': []  # Documents to query
}

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
    return jsonify({
        'success': True,
        'data': {
            'api_key_configured': api_ok,
            'index_built': app_state['index_built'],
            'num_documents': len(app_state['documents']),
            'data_source': app_state['data_source']
        }
    })

@app.route('/api/data/sample', methods=['POST'])
def load_sample_data():
    try:
        data = data_loader.load_sample_data()
        
        # Clear existing documents and add sample data
        app_state['documents'] = [{
            'id': 'sample_' + str(i),
            'name': item['title'],
            'type': 'sample',
            'pages': 1,
            'uploaded_at': datetime.now().isoformat(),
            'data': [item]
        } for i, item in enumerate(data)]
        
        app_state['current_data'] = data
        app_state['data_source'] = 'sample'
        app_state['selected_docs'] = [doc['id'] for doc in app_state['documents']]
        
        return jsonify({
            'success': True,
            'message': 'Loaded ' + str(len(data)) + ' samples',
            'documents': app_state['documents']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    return jsonify({
        'success': True,
        'documents': app_state['documents'],
        'selected_docs': app_state['selected_docs']
    })

@app.route('/api/documents/select', methods=['POST'])
def select_documents():
    try:
        data = request.get_json()
        doc_ids = data.get('doc_ids', [])
        
        # Validate doc IDs
        valid_ids = [doc['id'] for doc in app_state['documents']]
        doc_ids = [id for id in doc_ids if id in valid_ids]
        
        app_state['selected_docs'] = doc_ids
        
        # Rebuild current_data based on selection
        app_state['current_data'] = []
        for doc in app_state['documents']:
            if doc['id'] in doc_ids:
                app_state['current_data'].extend(doc['data'])
        
        return jsonify({
            'success': True,
            'message': 'Selected ' + str(len(doc_ids)) + ' documents',
            'selected_docs': doc_ids
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/documents/delete', methods=['POST'])
def delete_document():
    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        
        # Remove from documents
        app_state['documents'] = [doc for doc in app_state['documents'] if doc['id'] != doc_id]
        
        # Remove from selected
        if doc_id in app_state['selected_docs']:
            app_state['selected_docs'].remove(doc_id)
        
        # Rebuild current_data
        app_state['current_data'] = []
        for doc in app_state['documents']:
            if doc['id'] in app_state['selected_docs']:
                app_state['current_data'].extend(doc['data'])
        
        # Mark index as not built since data changed
        if len(app_state['documents']) == 0:
            app_state['index_built'] = False
        
        return jsonify({
            'success': True,
            'message': 'Document deleted',
            'documents': app_state['documents']
        })
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
        
        filename = secure_filename(file.filename)
        file_data = file.read()
        filepath = pdf_processor.save_uploaded_file(file_data, filename)
        
        print('File saved to:', filepath)
        
        documents = pdf_processor.load_pdf(filepath)
        
        print('Loaded', len(documents), 'pages')
        
        # Create data for this PDF
        data = []
        for i, doc in enumerate(documents):
            data.append({
                'pmcid': 'PDF_' + filename + '_page_' + str(i+1),
                'title': filename + ' - Page ' + str(i+1),
                'abstract': doc.text[:300] + ('...' if len(doc.text) > 300 else ''),
                'full_text': doc.text,
                'doc_id': filename,
                'page_num': i+1
            })
        
        # Add to documents list
        doc_id = 'pdf_' + str(len(app_state['documents'])) + '_' + filename
        app_state['documents'].append({
            'id': doc_id,
            'name': filename,
            'type': 'pdf',
            'pages': len(documents),
            'uploaded_at': datetime.now().isoformat(),
            'data': data
        })
        
        # Add to current data and selected docs
        app_state['current_data'].extend(data)
        app_state['selected_docs'].append(doc_id)
        app_state['data_source'] = 'multi-pdf' if len(app_state['documents']) > 1 else 'pdf'
        
        # Mark index as not built since new data was added
        app_state['index_built'] = False
        
        pdf_info = {
            'filename': filename,
            'num_pages': len(documents),
            'file_size_kb': len(file_data) / 1024,
            'doc_id': doc_id
        }
        
        print('PDF processed successfully')
        
        return jsonify({
            'success': True,
            'message': 'Successfully processed ' + filename,
            'documents': app_state['documents'],
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
        
        return jsonify({
            'success': True,
            'message': 'Index built successfully with ' + str(len(docs)) + ' documents from ' + str(len(app_state['selected_docs'])) + ' sources'
        })
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
        
        # Add timestamp and enhance sources
        result['timestamp'] = datetime.now().isoformat()
        result['num_selected_docs'] = len(app_state['selected_docs'])
        
        # Enhance source information
        for source in result['sources']:
            # Find which document this came from
            for doc in app_state['documents']:
                if doc['id'] in app_state['selected_docs']:
                    for item in doc['data']:
                        if item.get('pmcid') == source.get('pmcid'):
                            source['doc_name'] = doc['name']
                            source['doc_type'] = doc['type']
                            source['page_num'] = item.get('page_num', 'N/A')
                            break
        
        app_state['query_history'].append(result)
        
        print('Query completed')
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print('Error processing query:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/evaluate', methods=['POST'])
def run_evaluation():
    try:
        if not app_state['index_built']:
            return jsonify({'success': False, 'error': 'Index not built. Please build the index first.'}), 400
        
        print('Starting RAGAS evaluation...')
        
        test_cases = evaluator.create_test_cases()
        questions = test_cases['questions']
        ground_truths = test_cases['ground_truths']
        
        print('Running queries for evaluation...')
        
        results = rag_system.batch_query(questions)
        
        answers = [r['answer'] for r in results]
        contexts = [[s['text_snippet'] for s in r['sources']] for r in results]
        
        print('Evaluating with RAGAS...')
        
        eval_results = evaluator.evaluate(questions, answers, contexts, ground_truths)
        
        print('Evaluation complete:', eval_results)
        
        return jsonify({
            'success': True,
            'data': eval_results,
            'message': 'Evaluation completed successfully'
        })
        
    except Exception as e:
        print('Error during evaluation:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print('=' * 60)
    print('HEALTHCARE RAG SYSTEM - MULTI-DOCUMENT')
    print('=' * 60)
    print('http://localhost:5001')
    print('=' * 60)
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
