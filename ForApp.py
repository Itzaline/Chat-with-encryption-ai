import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Инициализация NLP
nltk.download(['punkt', 'stopwords', 'wordnet'], quiet=True)

class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        words = nltk.word_tokenize(text)
        words = [self.lemmatizer.lemmatize(w) for w in words if w not in self.stop_words]
        return ' '.join(words)

def main():
    # Загрузка данных
    df = pd.read_csv('spam.csv', encoding='latin-1')
    df = df[['v1', 'v2']].rename(columns={'v1': 'label', 'v2': 'text'})

    # Предобработка
    preprocessor = TextPreprocessor()
    df['clean_text'] = df['text'].apply(preprocessor.clean_text)

    # Создание пайплайна
    model = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('clf', MultinomialNB())
    ])

    # Обучение
    model.fit(df['clean_text'], df['label'].map({'ham': 0, 'spam': 1}))

    # Сохранение артефактов
    with open('model.pkl', 'wb') as f:
        pickle.dump(model.named_steps['clf'], f)
    with open('vectorizer.pkl', 'wb') as f:
        pickle.dump(model.named_steps['tfidf'], f)

    print("Модель успешно обучена и сохранена!")

if __name__ == "__main__":
    main()