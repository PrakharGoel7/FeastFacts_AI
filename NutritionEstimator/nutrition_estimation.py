from PIL import Image
from transformers import AutoProcessor, BlipForConditionalGeneration
import spacy
import requests
from bs4 import BeautifulSoup
import json
import streamlit as st
from io import BytesIO

APP_ID = '9f986d8c'
API_KEY = '67c9d9b83eac7360ec458f12f42ca0bd'
API_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"

headers = {
    "x-app-id": APP_ID,
    "x-app-key": API_KEY,
}

class NutritionEstimation(object):
    def __init__(self, url):
        self.input = url

    def cap_generator(self):
        processor = AutoProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        response = requests.get(self.input)
        image = Image.open(BytesIO(response.content)).convert('RGB')
        text = "the image of"
        inputs = processor(images=image, text=text, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=50)
        caption = processor.decode(outputs[0], skip_special_tokens=True)
        return caption

    def get_nutrition(self, caption):
        data = {
            "query": caption
        }
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            facts = {}
            nutrients = response.json()["foods"][0]
            facts['calories'] = nutrients["nf_calories"]
            facts['total_fat'] = nutrients["nf_total_fat"]
            facts['saturated_fat'] = nutrients["nf_saturated_fat"]
            facts['total_carbohydrate'] = nutrients["nf_total_carbohydrate"]
            facts['dietary_fiber'] = nutrients["nf_dietary_fiber"]
            facts['sugar'] = nutrients["nf_sugars"]
            facts['protein'] = nutrients["nf_protein"]
            return facts
        else:
            st.error("Failed to fetch data from Nutritionix API")
            return None

    def generate_facts(self):
        caption = self.cap_generator()
        return self.get_nutrition(caption)