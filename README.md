cd /Users/swami/healthcare_rag_system

python3 << 'PYEND'
with open('README.md', 'w') as f:
    f.write('''# 🏥 Healthcare RAG System - Multi-Document AI Assistant

A production-ready Retrieval-Augmented Generation (RAG) system for medical literature analysis with advanced multi-document support, beautiful UI, and comprehensive evaluation metrics.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![LlamaIndex](https://img.shields.io/badge/LlamaIndex-0.10-orange.svg)
![Status](https://img.shields.io/badge/Status-Production-success)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## 📸 Screenshots

### Dashboard Overview
![Dashboard](docs/screenshots/dashboard.png)
*Multi-document interface with sidebar library and tabbed navigation*

### Advanced Source Visualization
![Sources](docs/screenshots/sources.png)
*Beautiful gradient cards showing source relevance with highlighted keywords*

### Multi-Document Library
![Library](docs/screenshots/library.png)
*Manage multiple PDFs with selection controls*

### RAGAS Evaluation
![Evaluation](docs/screenshots/evaluation.png)
*Comprehensive performance metrics with visual charts*

---

## ✨ Features

### 🎯 Core Features
- **Multi-PDF Upload**: Drag & drop multiple documents simultaneously
- **Document Library**: Visual sidebar to manage and select documents
- **Cross-Document Search**: Query across multiple documents at once
- **AI-Powered Answers**: GPT-3.5 generates coherent responses from your data
- **Source Attribution**: See exactly which documents and pages were used

### 🎨 Advanced Visualization
- **Gradient Source Cards**: Beautiful color-coded source displays
- **Similarity Score Bars**: Visual representation of relevance (0-100%)
- **Keyword Highlighting**: Automatically highlights query terms in sources
- **Side-by-Side Comparison**: Grid layout to compare sources
- **Page-Level Citations**: Precise page numbers and document names

### 📊 Evaluation & Analytics
- **RAGAS Metrics**: Faithfulness, Answer Relevancy, Context Precision/Recall
- **Interactive Charts**: Bar charts visualizing performance
- **Real-time Scoring**: Instant feedback on system quality
- **Test Case Library**: Pre-configured evaluation scenarios

### 🔧 Technical Features
- **Vector Indexing**: Fast semantic search with HuggingFace embeddings
- **Efficient Retrieval**: Top-K similarity search with configurable thresholds
- **Document Filtering**: Select specific documents to query
- **REST API**: Clean API design for integration

---

## 🏗️ Architecture
