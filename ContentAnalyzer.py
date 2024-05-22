from TextProcessor import TextProcessor
from RDFProcessor import RDFProcessor
from URLProcessor import URLProcessor
from GradingProcessor import GradingProcessor
from ImageProcessor import ImageProcessor
import numpy as np
import pandas as pd
from firebase_admin import db  # Import Firebase Admin database
import re


class ContentAnalyzer:
    def __init__(self, input_url, rdf_file="denemequery.rdf", grades_file="grades.xlsx"):
        self.input_url = input_url
        self.rdf_file = rdf_file
        self.grades_file = grades_file
        self.text_processor = TextProcessor()
        self.rdf_processor = RDFProcessor(rdf_file)
        self.url_processor = URLProcessor()
        self.grading_processor = GradingProcessor()
        #self.image_processor = ImageProcessor()
        self.all_unique = set()
        self.leaf_classes = {}
        self.instancesdict = {}
        self.result_hashmaps = {}
        self.total_grades_sum = 0

    def process_urls(self):
        urls = self.url_processor.get_all_links(self.input_url)
        for url in urls:
            # print(self.image_processor.find_humans(url))
            # print(self.image_processor.total_numbers())
            self.url_processor.find_components(url, self.all_unique)
        df = pd.DataFrame(list(self.all_unique), columns=['Unique Content'])
        return len(urls), len(self.all_unique), df
    def is_valid_turkish_phone_number(self, text_list):
        # Regex pattern to strictly match Turkish phone numbers
        pattern = r"""
            (?:\+?90|-?90|\(90\))     # Match international prefix +90, 90, (90) or start with 0, with optional spaces or dashes
            (?:\s*\(?\d{3}\)?\s*-?)?    # Optional area code (3 digits) with optional parentheses and dash, possibly with spaces
            \s*\d{3}\s*-?\s*\d{4}       # Three digits followed by optional space or dash, then four digits
        """
        for text in text_list:
            # Use findall to search for matches within the string
            if re.findall(pattern, text, re.VERBOSE):
                return True
        return False
    def process_rdf(self):
        if not self.rdf_processor.graph:
            raise RuntimeError("RDF graph is empty.")
        
        parent_class = "http://www.semanticweb.org/kronos/ontologies/2023/10/untitled-ontology-3#Hotel"
        result = self.rdf_processor.query_subclasses(parent_class)
        
        if result:
            for row in result:
                level1 = row[0]
                level1name = self.rdf_processor.get_local_name(level1)
                nested_result = self.rdf_processor.query_subclasses(level1)
                subclassesoflevel1 = []

                if nested_result:
                    for row in nested_result:
                        level2 = row[0]
                        level2name = self.rdf_processor.get_local_name(level2)
                        subclassesoflevel1.append(level2name)
                        instances = self.rdf_processor.find_instances(level2)
                        instanceslist = [self.rdf_processor.get_local_name(instance) for instance in instances]
                        self.instancesdict[level2name] = instanceslist
                self.leaf_classes[level1name] = subclassesoflevel1

    def process_texts(self, df_unique,  file_path="all-texts2.xlsx"):
        df = self.text_processor.read_data(file_path)
        corpus = self.text_processor.porter(df)
        X, cv = self.text_processor.count_vectorizer(corpus)
        mnb = self.text_processor.multinomial_nb(df, X)
        labels_found = self.text_processor.predicting_new_labels(df_unique, cv, mnb)
        return labels_found

    def process_grades(self, labels_found):
        grades = self.grading_processor.read_grades(self.grades_file)
    
        for category, items in self.leaf_classes.items():
            category_map = {}
            try:
                for item in items:
                    if item == "AboutUs":
                        category_map[item] = 1 if np.isin(0, labels_found) else 0
                    elif item == "AmenitiesFacilities":
                        category_map[item] = 1 if np.isin(1, labels_found) else 0
                    elif item == "Location":
                        category_map[item] = 1 if np.isin(3, labels_found) else 0
                    elif item == "Phone":
                        present = self.is_valid_turkish_phone_number(self.all_unique)
                        category_map[item] = 1 if present else 0
                    else:
                        item_synonyms = self.instancesdict.get(item, [item])
                        present = any(any(syn.lower() in text.lower() for syn in item_synonyms) for text in self.all_unique)
                        category_map[item] = 1 if present else 0
                    
                    if category_map[item] == 1 and item in grades:
                        category_map[item] *= round(grades[item],2)
                        self.total_grades_sum += round(grades[item],2)
                self.result_hashmaps[category] = category_map
            except Exception as e:
                print(f"{e}")
      
    def store_results_in_firebase(self, results):
        try:
            ref = db.reference('/')
            ref.push(results)
        except Exception as e:
                print(f"{e}")
    def run(self):
        urls_processed, unique_contents_count, component_df = self.process_urls()
        self.process_rdf()
        labels_found = self.process_texts(component_df)
        print(self.all_unique)
        self.process_grades(labels_found)
        print(self.result_hashmaps)

        results = {
            "urls_processed": urls_processed,
            #"total_scanned,_images": self.image_processor.total_numbers(),
            "url" : self.input_url,
            "unique_contents_count": unique_contents_count,
            "result_hashmaps": self.result_hashmaps,
            "total_grades_sum": round(self.total_grades_sum,2)
        }
        self.store_results_in_firebase(results)
        return results
