import re
from transformers import pipeline

class MessageFilter:
    def __init__(self):
        self.keyword_patterns = [
            r"(?i)\b(viagra|loan|cash)\b",
            r"http[s]?://\S+"
        ]
        self.model = pipeline(
            "text-classification", 
            model="mrm8488/bert-tiny-finetuned-sms-spam-detection"
        )
    
    def is_spam(self, text: str) -> bool:
        if any(re.search(p, text) for p in self.keyword_patterns):
            return True
        return self.model(text)[0]['label'] == 'spam'