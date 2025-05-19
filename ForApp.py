import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import pickle

# Загрузка данных
df = pd.read_csv('spam.csv', encoding='latin-1')
df = df[['v1', 'v2']].rename(columns={'v1': 'label', 'v2': 'text'})

# Обновленные стоп-слова
nltk.download(['punkt', 'stopwords'])
stop_words = set(stopwords.words('english') + ['ur', 'nbsp', 'lt', 'gt'])

def preprocess(text):
    text = re.sub(r'[^a-zA-Z]', ' ', str(text).lower())
    words = word_tokenize(text)
    return ' '.join([w for w in words if w not in stop_words and len(w) > 2])

df['clean_text'] = df['text'].apply(preprocess)

# Векторизация и обучение
vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=5000)
X = vectorizer.fit_transform(df['clean_text'])
y = df['label'].map({'ham':0, 'spam':1})

model = MultinomialNB()
model.fit(X, y)

# Сохранение артефактов
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

print("Модель успешно обучена!")