
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



class URLProcessor:
    def normalize_url(self, url):
        parsed_url = urlparse(url)
        scheme = 'https' if not parsed_url.scheme else parsed_url.scheme
        netloc = parsed_url.netloc.replace('www.', '')
        normalized = urlunparse((scheme, netloc, parsed_url.path, '', parsed_url.query, ''))
        return normalized

    def get_all_links(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = set()

            for a_tag in soup.find_all('a', href=True):
                absolute_url = urljoin(url, a_tag['href'])
                normalized_url = self.normalize_url(absolute_url)
                links.add(normalized_url)

            return links
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return set()

    def find_components(self, url, all_unique):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            all_divs = soup.find_all('div')
            unique_contents = set()

            def find_most_inner_content(element):
                inner_divs = element.find_all('div')
                if not inner_divs:
                    return element.get_text(strip=True)
                else:
                    return find_most_inner_content(inner_divs[-1])

            for div in all_divs:
                most_inner_content = find_most_inner_content(div)
                unique_contents.add(most_inner_content)

            all_unique.update(unique_contents)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")

