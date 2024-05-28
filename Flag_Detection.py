import os
import cv2
import numpy as np
import cairosvg
from PIL import Image
from io import BytesIO

class Flag_Detection:
    def __init__(self):
        # self.image_directory = image_directory
        # self.preprocess_and_save_images()
        self.image_vectors, self.labels = self.load_vectors()

    def preprocess_and_save_images(self):
        images = []
        labels = []
        for filename in os.listdir(self.image_directory):
            filepath = os.path.join(self.image_directory, filename)
            if filename.endswith('.svg'):
                png_image = cairosvg.svg2png(url=filepath)
                img = Image.open(BytesIO(png_image))
                img = img.convert('RGB')
                img = np.array(img)
            else:
                img = cv2.imread(filepath, cv2.IMREAD_COLOR)
            img = cv2.resize(img, (32, 32))
            vector = img.flatten().astype('float32')
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector /= norm
            images.append(vector)
            labels.append(filename[:-4])
        np.savez('flag_vectors.npz', images=np.array(images), labels=np.array(labels))
        print("Images and labels have been processed and saved.")

    def load_vectors(self):
        data = np.load('flag_vectors.npz')
        return data['images'], data['labels']

    def find_similar_images(self, image_path):
        print(image_path)
        if image_path.endswith('.svg'):
            png_image = cairosvg.svg2png(url=image_path)
            img = Image.open(BytesIO(png_image))
            img = img.convert('RGB')
            img = np.array(img)
        else:
            img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (32, 32))
        vector = img.flatten().astype('float32')
        norm_new_vector = np.linalg.norm(vector)
        if norm_new_vector > 0:
            vector /= norm_new_vector
        similarities = np.dot(self.image_vectors, vector)
        most_similar_index = np.argmax(similarities)
        return self.labels[most_similar_index], similarities[most_similar_index]

def flag_detection(image_path):
    detector = Flag_Detection()
    label, similarity = detector.find_similar_images(image_path)
    print(f'Most similar image is {label} with a similarity of {similarity:.2f}')

if __name__ == "__main__":

    print()
