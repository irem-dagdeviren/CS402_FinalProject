from TextProcessor import TextProcessor
from RDFProcessor import RDFProcessor
from URLProcessor import URLProcessor
from GradingProcessor import GradingProcessor
from ImageProcessor import ImageProcessor
import numpy as np
import pandas as pd
from firebase_admin import db  # Import Firebase Admin database
import re
from urllib.parse import urlparse, urlunparse


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
        self.all_unique = set()
        self.leaf_classes = {}
        self.instancesdict = {}
        self.result_hashmaps = {}
        self.total_grades_sum = 0
        self.instagram = False
        self.facebook = False
        self.twitter = False
        self.tripAdvisor = False
        self.googlemaps = False

        

    def process_urls(self):
        urls, self.instagram, self.facebook, self.twitter, self.tripAdvisor, self.googlemaps= self.url_processor.get_all_links(self.input_url)

        for url in urls:

            parsed_url = urlparse(self.input_url)
            base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '/', '', '', ''))

            if self.image_processor.total_images_with_human < 10 and url.startswith(self.url_processor.normalize_url(base_url)):
                print(self.image_processor.find_humans(url))


            self.url_processor.find_components(url, self.all_unique)
        df = pd.DataFrame(list(self.all_unique), columns=['Unique Content'])
        return len(urls), len(self.all_unique), df

    def is_valid_turkish_phone_number(self, text_list):
        # Regex pattern to strictly match Turkish phone numbers
        pattern = r"""
            ^                                           # Start of string
            (?:\+?90|-?90|\(90\)|0)                     # Match international prefix +90, 90, (90) or start with 0, with optional spaces or dashes
            \s*                                         # Optional whitespace
            \(?0?\d{3}\)?                               # Area code (3 digits) with optional leading zero and optional parentheses
            \s*-?\s*                                    # Optional whitespace and dash
            \d{3}                                       # First 3 digits of local number
            \s*-?\s*                                    # Optional whitespace and dash
            \d{2}                                       # Next 2 digits
            \s*-?\s*                                    # Optional whitespace and dash
            \d{2}                                       # Last 2 digits
            $                                           # End of string
        """

        for text in text_list:
            digits_only = re.sub(r'[^\d]', '', text)  # Remove all non-digits
            # Use findall to search for matches within the string
            if re.findall(pattern, digits_only, re.VERBOSE):
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
                    item_synonyms = self.instancesdict.get(item, [item])
                    if item == "AboutUs":
                        category_map[item] = 1 if np.isin(0, labels_found) else 0
                    elif item == "AmenitiesFacilities":
                        category_map[item] = 1 if np.isin(1, labels_found) else 0
                    elif item == "Location":
                        category_map[item] = 1 if np.isin(3, labels_found) else 0
                    elif item == "Phone":
                        present = self.is_valid_turkish_phone_number(self.all_unique)
                        if(not present):
                            present = any(any(syn.lower() in text.lower() for syn in item_synonyms) for text in self.all_unique)
                        category_map[item] = 1 if present else 0
                    elif item == 'WebsiteSecurity':
                        isSecure = self.input_url.lower().startswith("https:")
                        category_map[item] = 1 if isSecure else 0
                    elif item == "Instagram":
                        category_map[item] = 1 if self.instagram else 0
                    elif item == "Facebook":
                        category_map[item] = 1 if self.facebook else 0
                    elif item == "Twitter":
                        category_map[item] = 1 if self.twitter else 0
                    elif item == "TripAdvisor":
                        category_map[item] = 1 if self.tripAdvisor else 0
                    elif item == "ExperientialPhotos":
                        # number of experiential photos can be change accordingly
                        category_map[item] = 1 if self.image_processor.total_images_with_human > 5 else 0
                    elif item == "Photos":
                        category_map[item] = 1 if self.image_processor.total_images > 0 else 0
                    elif item == "MapInformation":
                        if self.googlemaps:
                            category_map[item] = 1
                        else:
                            present = any(any(syn.lower() in text.lower() for syn in item_synonyms) for text in self.all_unique)
                            category_map[item] = 1 if present else 0
                    elif category == 'Language': 
                        print(self.url_processor.languages)   
                        if item == 'English':
                            category_map[item] = 1 if 'en' in self.url_processor.languages else 0
                        elif item == 'Türkçe':
                            category_map[item] = 1 if 'tr' in self.url_processor.languages else 0
                        elif item == 'Español':
                            category_map[item] = 1 if 'es' in self.url_processor.languages else 0
                        elif item == 'Deutsch':
                            category_map[item] = 1 if 'de' in self.url_processor.languages else 0
                        elif item == 'Italiano':
                            category_map[item] = 1 if 'it' in self.url_processor.languages else 0
                        elif item == 'Русский':
                            category_map[item] = 1 if 'ru' in self.url_processor.languages else 0
                        elif item == 'عربي':
                            category_map[item] = 1 if 'ar' in self.url_processor.languages else 0
                    elif category == 'UserInterface':
                        if item == 'Calendar':
                            category_map[item] = 1 if self.url_processor.datepicker else 0
                        elif item == 'Searchbar':
                            category_map[item] = 1 if self.url_processor.searchbar else 0
                        elif item == 'Slider':
                            category_map[item] = 1 if self.url_processor.slider  else 0
                        else:
                            present = any(any(syn.lower() in text.lower() for syn in item_synonyms) for text in self.all_unique)
                            category_map[item] = 1 if present else 0
                    else:
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
        # labels_found = self.process_texts(component_df)

        processor = TextProcessor()
        # df = processor.read_data('all-texts2.xlsx')  # Adjust path as per your project structure
        # processor.train_and_save_model(df)

        # Load the model and predict new data
        # new_df = pd.read_csv('new_data.csv')  # Adjust path as per your project structure
        labels, probabilities = processor.load_and_predict(component_df)

        self.process_grades(labels)
        print(self.result_hashmaps)
        # print(labels_found)
    
        # Load the provided Excel file
        file_path = 'hashmap_results.xlsx'
        existing_df = pd.read_excel(file_path)

        # Define the hashmap data
        data = self.result_hashmaps

        # Flatten the hashmap data into a single row
        flattened_data = {'URL': self.input_url}
        flattened_data.update({key2: value2 for key1, subdict in data.items() for key2, value2 in subdict.items()})
   

        # Create a DataFrame from the flattened data
        new_row_df = pd.DataFrame([flattened_data])

        # Append the new row to the existing DataFrame
        # will be check the error
        ''' 
        FutureWarning: The behavior of DataFrame concatenation with empty or all-NA entries is deprecated. 
        In a future version, this will no longer exclude empty or all-NA columns when determining the result dtypes. 
        To retain the old behavior, exclude the relevant entries before the concat operation.'''
        updated_df = pd.concat([existing_df, new_row_df], ignore_index=True)

        # Save the updated DataFrame back to the Excel file
        updated_df.to_excel(file_path, index=False)



        results = {
            "urls_processed": urls_processed,
            "total_scanned,_images": self.image_processor.total_numbers(),
            "url" : self.input_url,
            "unique_contents_count": unique_contents_count,
            "result_hashmaps": self.result_hashmaps,
            "total_grades_sum": round(self.total_grades_sum,2)
        }
        self.store_results_in_firebase(results)
        return results

