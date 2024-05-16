import pandas as pd


class GradingProcessor:
    def __init__(self):
        self.grades = {}

    def read_grades(self, file_path):
        df = pd.read_excel(file_path)  # Read the Excel file without headers
        print("First few rows of the Excel file:\n", df.head())  # Print the first few rows to inspect the data
        self.grades = dict(zip(df['item'], df['grade']))  # Assuming the first column is 'item' and the second column is 'grade'
        return self.grades
