import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import pandas as pd
import numpy as np
import rdflib
from rdflib import Graph, RDFS, URIRef
from sklearn.metrics import ConfusionMatrixDisplay
import sys
import nltk
import ssl
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import confusion_matrix, accuracy_score
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import re
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from io import BytesIO

class TextProcessor:
    def read_data(self, file_name):
        df = pd.read_excel(file_name)
        df = df[df['label'] != 2].reset_index(drop=True)
        df = df[df['label'] != 4].reset_index(drop=True)
        df.dropna(inplace=True)
        df.reset_index(inplace=True)
        df.drop("index", axis=1, inplace=True)
        return df

    def porter(self, df):
        df['text'] = df['text'].astype(str)
        porter = PorterStemmer()
        corpus = []
        for i in range(0, len(df)):
            review = re.sub('[^a-zA-Z]', ' ', df['text'][i])
            review = review.lower()
            review = review.split()
            review = [porter.stem(word) for word in review if not word in stopwords.words("english")]
            review = " ".join(review)
            corpus.append(review)
        return corpus

    def count_vectorizer(self, corpus):
        cv = CountVectorizer(max_features=4000, ngram_range=(1, 4))
        X = cv.fit_transform(corpus).toarray()
        cv.get_feature_names_out()[:20]
        return X, cv

    def multinomial_nb(self, df, X):
        y = df["label"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
        mnb = MultinomialNB()
        mnb.fit(X_train, y_train)
        y_pred = mnb.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        print("Naive Bayes accuracy is ", round(accuracy_score(y_test, y_pred), 2) * 100, "%")
        print("\n")
        print("Confusion matrix for Naive Bayes ")
        disp = ConfusionMatrixDisplay(confusion_matrix=cm)
        disp.plot()
        return mnb

    def predicting_new_labels(self, new_file_path, cv, mnb):
        new_excel = pd.read_csv(new_file_path)
        new_excel.dropna(inplace=True)
        new = cv.transform(new_excel["Unique Content"]).toarray()
        new_labels = mnb.predict(new)
        new_prob = mnb.predict_proba(new)
        return new_labels
    