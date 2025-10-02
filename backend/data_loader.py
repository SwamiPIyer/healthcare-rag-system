from typing import List, Dict

class DataLoader:
    def __init__(self):
        pass
    
    def load_sample_data(self):
        return [
            {"pmcid": "PMC123", "title": "Cancer Immunotherapy", "abstract": "Novel approaches", "full_text": "CAR-T cell therapy shows promise."},
            {"pmcid": "PMC456", "title": "Diabetes Drug X", "abstract": "Clinical trial", "full_text": "Drug X reduces HbA1c by 1.5 percent."},
            {"pmcid": "PMC789", "title": "Vaccination Programs", "abstract": "Public health", "full_text": "Reduced disease burden by 65 percent."}
        ]
