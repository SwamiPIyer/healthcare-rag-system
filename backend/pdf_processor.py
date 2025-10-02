from pathlib import Path
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
