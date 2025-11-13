import json, os
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'clinic_info.json')

class FAQRetriever:
    def __init__(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.docs = json.load(f)
        except Exception:
            self.docs = {}

    def get_answer(self, query: str) -> str:
        q = query.lower()
        for k, v in self.docs.items():
            if k.lower() in q or any(tok in q for tok in k.lower().split()):
                return v
        return "Here's some clinic information:\n" + "\n".join([f"- {k}: {v}" for k,v in self.docs.items()])
