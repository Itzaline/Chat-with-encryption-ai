import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

# Проверка и загрузка необходимых ресурсов
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

# Загрузка датасета
df = pd.read_csv('spam.csv', encoding='latin-1')
df = df[['v1', 'v2']]
df.columns = ['Label', 'Text']

# Загрузка стоп-слов и токенизатора
nltk.download('stopwords')
nltk.download('punkt')
stop_words = set(stopwords.words('english'))

# Предобработка текста
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = word_tokenize(text)
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

df['Cleaned_Text'] = df['Text'].apply(preprocess_text)

# Векторизация текста с помощью TF-IDF
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['Cleaned_Text'])
y = df['Label'].map({'ham': 0, 'spam': 1})

# Разделение на обучающую и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Обучение модели
model = MultinomialNB()
model.fit(X_train, y_train)

# Оценка модели
y_pred = model.predict(X_test)
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
print("\nAccuracy Score:", accuracy_score(y_test, y_pred))

# Предсказание для новых сообщений
new_emails = [
    "Congratulations! You've won a free iPhone.",
    "Hi, let's catch up this weekend."
]
new_emails_cleaned = [preprocess_text(email) for email in new_emails]
new_emails_vectorized = vectorizer.transform(new_emails_cleaned)
predictions = model.predict(new_emails_vectorized)

for i, email in enumerate(new_emails):
    print(f"Email: {email} --> {'Spam' if predictions[i] == 1 else 'Ham'}")


# В конец файла ForApp.py добавьте:

import pickle

# Сохранение модели и векторайзера
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)