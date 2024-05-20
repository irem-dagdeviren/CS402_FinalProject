from TextProcessor import TextProcessor
from RDFProcessor import RDFProcessor
from URLProcessor import URLProcessor
from GradingProcessor import GradingProcessor
from ImageProcessor import ImageProcessor
import numpy as np
import pandas as pd

class ContentAnalyzer:
    def __init__(self, input_url, rdf_file="denemequery.rdf", grades_file="grades.xlsx"):
        self.input_url = input_url
        self.rdf_file = rdf_file
        self.grades_file = grades_file
        self.text_processor = TextProcessor()
        self.rdf_processor = RDFProcessor(rdf_file)
        self.url_processor = URLProcessor()
        self.grading_processor = GradingProcessor()
        self.image_processor = ImageProcessor()

        print(self.image_processor.device)

        self.all_unique = set()
        self.leaf_classes = {}
        self.instancesdict = {}
        self.result_hashmaps = {}
        self.total_grades_sum = 0

    def process_urls(self):
        urls = self.url_processor.get_all_links(self.input_url)
        for url in urls:
            print(self.image_processor.find_humans(url))
            self.url_processor.find_components(url, self.all_unique)

        df = pd.DataFrame(list(self.all_unique), columns=['Unique Content'])
        df.to_csv('unique_contents.csv', index=False)
        return len(urls), len(self.all_unique)

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

    def process_texts(self, file_path="all-texts2.xlsx"):
        df = self.text_processor.read_data(file_path)
        corpus = self.text_processor.porter(df)
        X, cv = self.text_processor.count_vectorizer(corpus)
        mnb = self.text_processor.multinomial_nb(df, X)
        labels_found = self.text_processor.predicting_new_labels("unique_contents.csv", cv, mnb)
        return labels_found

    def process_grades(self, labels_found):
        grades = self.grading_processor.read_grades(self.grades_file)
        
        for category, items in self.leaf_classes.items():
            category_map = {}
            for item in items:
                if item == "AboutUs":
                    category_map[item] = 1 if np.isin(0, labels_found) else 0
                elif item == "Amenities":
                    category_map[item] = 1 if np.isin(1, labels_found) else 0
                elif item == "Location":
                    category_map[item] = 1 if np.isin(3, labels_found) else 0
                else:
                    item_synonyms = self.instancesdict.get(item, [item])
                    present = any(any(syn in text for syn in item_synonyms) for text in self.all_unique)
                    category_map[item] = 1 if present else 0
                
                if category_map[item] == 1 and item in grades:
                    category_map[item] *= round(grades[item],2)
                    self.total_grades_sum += round(grades[item],2)
            print(category_map)
            self.result_hashmaps[category] = category_map
        

    def run(self):
        urls_processed, unique_contents_count = self.process_urls()
        self.process_rdf()
        labels_found = self.process_texts()
        self.process_grades(labels_found)
        print(self.result_hashmaps)

        return {
            "urls_processed": urls_processed,
            "total_scanned,_images": self.image_processor.total_numbers(),
            "unique_contents_count": unique_contents_count,
            "result_hashmaps": self.result_hashmaps,
            "total_grades_sum": self.total_grades_sum
        }