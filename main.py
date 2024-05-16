from TextProcessor import TextProcessor
from RDFProcessor import RDFProcessor
from URLProcessor import URLProcessor
from ImageProcessor import ImageProcessor
from GradingProcessor import GradingProcessor
import numpy as np
import pandas as pd


def main():
    text_processor = TextProcessor()
    rdf_processor = RDFProcessor("denemequery.rdf")
    url_processor = URLProcessor()
    grading_processor = GradingProcessor()
    #image_processor = ImageProcessor()

    url = 'https://www.flyingpig.nl/beach-hostel/'
    urls = url_processor.get_all_links(url)
    all_unique = set()

    for url in urls:
        url_processor.find_components(url, all_unique)

    # for content in all_unique:
    #     print("\n", content)

    df = pd.DataFrame(list(all_unique), columns=['Unique Content'])
    df.to_csv('unique_contents.csv', index=False)

    print("Excel file created with total contents:", len(all_unique))
    print("Total URLs processed:", len(urls))

    if not rdf_processor.graph:
        exit(1)

    parent_class = "http://www.semanticweb.org/kronos/ontologies/2023/10/untitled-ontology-3#Hotel"
    leaf_classes = {}
    instancesdict = {}

    result = rdf_processor.query_subclasses(parent_class)
    if result:
        subclasses = []
        for row in result:
            level1 = row[0]
            level1name = rdf_processor.get_local_name(level1)
            nested_result = rdf_processor.query_subclasses(level1)
            if nested_result:
                subclassesoflevel1 = []
                for row in nested_result:
                    level2 = row[0]
                    level2name = rdf_processor.get_local_name(level2)
                    subclassesoflevel1.append(level2name)
                    deeper_result = rdf_processor.query_subclasses(level2)
                    instances = rdf_processor.find_instances(level2)
                    if instances:
                        instanceslist = []
                        for instance in instances:
                            instanceslist.append(rdf_processor.get_local_name(instance))
                    instancesdict[level2name] = instanceslist
            leaf_classes[level1name] = subclassesoflevel1

    print("\nMain category to subclasses")
    rdf_processor.print_dict(leaf_classes)
    print("\nSubclasses to instances")
    rdf_processor.print_dict(instancesdict)

    file_path = "all-texts2.xlsx"
    df = text_processor.read_data(file_path)
    corpus = text_processor.porter(df)
    X, cv = text_processor.count_vectorizer(corpus)
    mnb = text_processor.multinomial_nb(df, X)
    labels_found = text_processor.predicting_new_labels("unique_contents.csv", cv, mnb)
    print(f"Label array {labels_found}")
    
    print(type(labels_found))
    print(np.isin(0,labels_found))
    print(np.isin(1,labels_found))
    print(np.isin(3,labels_found))
    print(np.isin(5,labels_found))


    grades_file_path = "grades.xlsx"
    grades = grading_processor.read_grades(grades_file_path)

    result_hashmaps = {}
    total_grades_sum = 0  # Initialize a variable to accumulate the sum of grades

    for category, items in leaf_classes.items():
        category_map = {}
        for item in items:
            print(item)
            if item == "AboutUs":
                category_map[item] = 1 if np.isin(0, labels_found) else 0
            elif item == "Amenities":
                category_map[item] = 1 if np.isin(1, labels_found) else 0
            elif item == "Location":
                category_map[item] = 1 if np.isin(3, labels_found) else 0
                    
  
            else:
                item_synonyms = instancesdict.get(item, [item])
                present = any(any(syn in text for syn in item_synonyms) for text in all_unique)
                category_map[item] = 1 if present else 0

            # Multiply the value by the grade if the value is 1
            print(category_map[item], "buraaaa")
            if category_map[item] == 1 and item in grades:
                category_map[item] *= grades[item]
                total_grades_sum += grades[item]  # Add the grade to the total sum

        result_hashmaps[category] = category_map

    print(result_hashmaps)
    print(f"Sum of grades: {total_grades_sum}")

    print(f"Label array {labels_found}")
    print(type(labels_found))
    print(np.isin(0, labels_found))
    print(np.isin(1, labels_found))
    print(np.isin(3, labels_found))
    print(np.isin(5, labels_found))



if __name__ == "__main__":
    main()