import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models.detection as models
from torchvision.models.detection.faster_rcnn import FasterRCNN_ResNet50_FPN_Weights
from io import BytesIO
import hashlib

from PIL import Image
from io import BytesIO

from Flag_Detection import flag_detection


class ImageProcessor:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.setup_model()
        self.transform = self.get_transform()
        self.processed_hashes = set()
        self.processed_urls = set()
        self.total_images = 0
        self.total_images_with_human = 0



    def total_numbers(self):
        return self.total_images, self.total_images_with_human
    def setup_model(self):
        model = models.fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)
        model.to(self.device)
        model.eval()
        return model

    def get_transform(self):
        return transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((800, 800))
        ])

    def get_image_hash(self, image_data):
        """Generate a hash for the image data."""
        hash_obj = hashlib.sha256()
        hash_obj.update(image_data)
        return hash_obj.hexdigest()

    def fetch_images(self, url):
        urls = []
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            for img in soup.find_all("img"):
                img_url = img.attrs.get("src")
                if img_url and self.is_duplicate_url(img_url):
                    img_url = urljoin(url, img_url)
                    urls.append(img_url)

            for a in soup.find_all("a", href=True):
                a_url = a.attrs.get("href")
                if a_url.lower().endswith((".jpg", ".jpeg", ".png" , ".gif", ".JPG")) and self.is_duplicate_url(a_url):
                    a_url = urljoin(url, a_url)
                    urls.append(a_url)
        except Exception as a:
            print(" Doesn't work this link: ", a)
        return list(set(urls))

    def is_duplicate_url(self, url):
        if url in self.processed_urls:
            return False
        else:
            self.processed_urls.add(url)
            return True

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
            # Check if the image URL ends with '.svg'
            if img_url.endswith('.svg'):

                print(flag_detection(img_url))

            else:
                try:
                    predictions, _ = self.load_and_predict_image(img_url)
                    human_counts = sum(1 for i in range(len(predictions[0]['labels'])) if
                                       predictions[0]['labels'][i] == 1 and predictions[0]['scores'][i] >= 0.95)
                    if human_counts > 0:
                        print(img_url)
                        images_with_humans += 1
                except Exception as e:
                    print(f"Failed to process image {img_url}: {e}")

        self.total_images += total_images
        self.total_images_with_human += images_with_humans

        human_percentage = (images_with_humans / total_images * 100) if total_images > 0 else 0
        result = f"Images: {total_images}, Images with humans: {images_with_humans} ({human_percentage:.2f}%)"
        return result
