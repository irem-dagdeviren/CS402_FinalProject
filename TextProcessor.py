import os
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import confusion_matrix, accuracy_score
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import re
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
import joblib

class TextProcessor:
    def read_data(self, file_name):
        df = pd.read_excel(file_name)
        df = df[df['label'] != 2].reset_index(drop=True)
        df = df[df['label'] != 4].reset_index(drop=True)
        df.dropna(inplace=True)
        df.reset_index(inplace=True)
        df.drop("index", axis=1, inplace=True)
        return df

    class StemmedCountVectorizer(BaseEstimator, TransformerMixin):
        def __init__(self):
            self.porter = PorterStemmer()
            self.vectorizer = CountVectorizer(max_features=4000, ngram_range=(1, 4))

        def _preprocess(self, text):
            review = re.sub('[^a-zA-Z]', ' ', text)
            review = review.lower()
            review = review.split()
            review = [self.porter.stem(word) for word in review if word not in stopwords.words("english")]
            return " ".join(review)

        def fit(self, X, y=None):
            corpus = [self._preprocess(text) for text in X]
            self.vectorizer.fit(corpus)
            return self

        def transform(self, X):
            corpus = [self._preprocess(text) for text in X]
            return self.vectorizer.transform(corpus)

    def train_and_save_model(self, df):
        y = df["label"]
        X = df["text"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

        pipeline = Pipeline([
            ('stemmed_vect', self.StemmedCountVectorizer()),
            ('clf', MultinomialNB())
        ])

        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        print("Naive Bayes accuracy is ", round(accuracy_score(y_test, y_pred) * 100, 2), "%")
        print("\n")
        print("Confusion matrix for Naive Bayes ")
        print(cm)

        # Save the pipeline to a file in the project directory
        save_path = 'text_classification_pipeline.joblib'  # Relative path within the project directory
        joblib.dump(pipeline, save_path)
        print(f"Pipeline saved successfully at {save_path}")

    def load_and_predict(self, new_df):
        # Load the saved pipeline from the project directory
        load_path = 'text_classification_pipeline.joblib'  # Relative path within the project directory
        pipeline = joblib.load(load_path)
        print(f"Pipeline loaded successfully from {load_path}")

        new_df.dropna(inplace=True)
        new = new_df["Unique Content"]

        new_labels = pipeline.predict(new)
        new_prob = pipeline.predict_proba(new)

        return new_labels, new_prob