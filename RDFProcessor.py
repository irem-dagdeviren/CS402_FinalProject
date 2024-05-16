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


class RDFProcessor:
    def __init__(self, filepath, fmt="xml"):
        self.graph = self.load_graph(filepath, fmt)

    def load_graph(self, filepath, fmt):
        g = rdflib.Graph()
        try:
            g.parse(filepath, format=fmt)
        except Exception as e:
            print(f"Failed to load RDF file: {e}")
            return None
        return g

    def query_subclasses(self, parent_class):
        query = """
        SELECT ?subclass
        WHERE {
          ?subclass rdfs:subClassOf <%s> .
        }
        """ % parent_class
        try:
            result = self.graph.query(query)
            if not result:
                return []
            return result
        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    def find_instances(self, class_uri):
        instances = []
        query = """
        SELECT DISTINCT ?instance
        WHERE {
          ?instance rdf:type <%s> .
        }
        """ % class_uri
        try:
            for row in self.graph.query(query):
                instances.append(row[0])
            return instances
        except Exception as e:
            print(f"Error executing instance query: {e}")
            return []

    def get_local_name(self, uri):
        return uri.split('#')[-1] if '#' in uri else uri.split('/')[-1]

    def print_dict(self, d):
        for key, value in d.items():
            print(f"{key}: {value}")