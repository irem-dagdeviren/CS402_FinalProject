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

class ImageProcessor:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.setup_model()
        self.transform = self.get_transform()

    def setup_model(self):
        model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
        model.to(self.device)
        model.eval()
        return model

    def get_transform(self):
        return transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((800, 800))
        ])

    def fetch_images(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        urls = []

        for img in soup.find_all("img"):
            img_url = img.attrs.get("src")
            if img_url:
                img_url = urljoin(url, img_url)
                urls.append(img_url)

        for tag in soup.find_all(style=re.compile(r'background[-image]*:.*url')):
            style = tag.attrs.get('style')
            match = re.search(r'url\((.*?)\)', style)
            if match:
                bg_url = match.group(1).replace('"', '').replace("'", "")
                bg_url = urljoin(url, bg_url)
                urls.append(bg_url)

        for a in soup.find_all("a", href=True):
            a_url = a.attrs.get("href")
            if a_url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                a_url = urljoin(url, a_url)
                urls.append(a_url)

        return list(set(urls))

    def load_and_predict_image(self, url):
        response = requests.get(url)
        image = Image.open(BytesIO(response.content)).convert("RGB")
        image_tensor = self.transform(image).to(self.device)

        with torch.no_grad():
            predictions = self.model([image_tensor])

        return predictions, image_tensor

    def find_humans(self, url):
        image_urls = self.fetch_images(url)
        total_images = len(image_urls)
        images_with_humans = 0

        for img_url in image_urls:
            try:
                predictions, _ = self.load_and_predict_image(img_url)
                human_counts = sum(1 for i in range(len(predictions[0]['labels'])) if predictions[0]['labels'][i] == 1 and predictions[0]['scores'][i] >= 0.8)
                if human_counts > 0:
                    images_with_humans += 1
            except Exception as e:
                print(f"Failed to process image {img_url}: {e}")

        human_percentage = (images_with_humans / total_images * 100) if total_images > 0 else 0
        result = f"Images: {total_images}, Images with humans: {images_with_humans} ({human_percentage:.2f}%)"
        return result

