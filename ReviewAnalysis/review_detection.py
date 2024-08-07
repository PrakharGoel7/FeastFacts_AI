import os
import typing
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
import heapq
from collections import Counter

endpoint = "https://reviewdetect.cognitiveservices.azure.com/"
key = "ebdddff49c9c467ab524e5bc17155cc6"

text_analytics_client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

import requests
from bs4 import BeautifulSoup
import random

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    # Add more user agents if needed
]

custom_headers = {
    "User-Agent": random.choice(user_agents),
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",  # Do Not Track Request Header
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

class ReviewDetection (object):
    def __init__(self, search_url):
        self.search_url = search_url

    def get_soup(self,url):
        response = requests.get(url, headers=custom_headers)
        if response.status_code != 200:
            print("Error in getting webpage")
            exit(-1)
        soup = BeautifulSoup(response.text, "lxml")
        return soup

    # Only needed for Zomato
    def find_att(self,soup):
        review_elements = soup.select("p.sc-1hez2tp-0")
        att = ""
        for review in review_elements:
            if len(review.get_text(strip=True).split()) > 5:
                start = str(review).find('sc')
                end = str(review).find('>', start)
                att = str(review)[start:end - 1]
                att = att.replace(" ", ".")
                break
        if att != "":
            att = "p." + att
        return att

    def get_zomato_reviews(self, soup, att):
        review_elements = soup.select(att)
        page_reviews = [review.get_text(strip=True) for review in review_elements]
        return page_reviews

    def scrape_all_zomato_pages(self):
        i = 1
        scraped_reviews = []
        is_next = None
        while is_next is not None or i == 1:
            edited_url = self.search_url + "?page=" + str(i) + "&sort=dd&filter=reviews-dd"
            soup = self.get_soup(edited_url)
            is_next = soup.find('path', {
                'd': "M6.98 15.94c-0.3-0.28-0.3-0.76 0-1.060l4.46-4.46-4.46-4.48c-0.3-0.28-0.3-0.76 0-1.060s0.76-0.28 1.060 0l5 5c0.28 0.3 0.28 0.78 0 1.060l-5 5c-0.3 0.3-0.78 0.3-1.060 0z"})
            att = self.find_att(soup)
            if att != "" and att != None:
                data = self.get_zomato_reviews(soup, att)
                for review in data:
                    scraped_reviews.append(review)
            i = i + 1
        return scraped_reviews

    def zomato_analyzer(self, documents):
        positive_reviews = []
        mixed_reviews = []
        negative_reviews = []
        target_to_complaints: typing.Dict[str, typing.Any] = {}
        target_to_complement: typing.Dict[str, typing.Any] = {}
        for i in range(10, len(documents), 10):
            result = text_analytics_client.analyze_sentiment(documents[i - 10:i], show_opinion_mining=True)
            doc_result = [doc for doc in result if not doc.is_error]
            for doc in doc_result:
                if doc.sentiment == 'positive':
                    positive_reviews.append(doc)
                elif doc.sentiment == 'negative':
                    negative_reviews.append(doc)
                elif doc.sentiment == 'mixed':
                    mixed_reviews.append(doc)
                for sentence in doc.sentences:
                    if sentence.mined_opinions:
                        for mined_opinion in sentence.mined_opinions:
                            target = mined_opinion.target
                            target.text = target.text.lower()
                            if target.sentiment == 'negative':
                                target_to_complaints.setdefault(target.text, [])
                                target_to_complaints[target.text].append(mined_opinion)
                            elif target.sentiment == 'positive':
                                target_to_complement.setdefault(target.text, [])
                                target_to_complement[target.text].append(mined_opinion)

        result = {"general_sentiment": {"positive_reviews": len(positive_reviews), "mixed_reviews": len(mixed_reviews),
                                        "negative_reviews": len(negative_reviews)},
                  "complaints": {},
                  "complements": {},
                  "categories": {}}

        for target_name, complaints in target_to_complaints.items():
            result["complaints"][target_name] = {
                "count": len(complaints),
                "details": []
            }
            for complaint in complaints:
                for assessment in complaint.assessments:
                    result["complaints"][target_name]["details"].append(assessment.text)

        for target_name, complements in target_to_complement.items():
            result["complements"][target_name] = {
                "count": len(complements),
                "details": []
            }
            for complement in complements:
                for assessment in complement.assessments:
                    result["complements"][target_name]["details"].append(assessment.text)

        #cat_to_target_reviews = {}
        for i in range(5, len(documents), 5):
            reviews = text_analytics_client.recognize_entities(documents[i - 5:i])
            reviews = [review for review in reviews if not review.is_error]
            cat_to_target_reviews = {}
            for idx, review in enumerate(reviews):
                for entity in review.entities:
                    entity.text = entity.text.lower()
                    if entity.text in target_to_complaints.keys() or entity.text in target_to_complement.keys():
                        if entity.category not in cat_to_target_reviews.keys():
                            cat_to_target_reviews[entity.category] = {}
                        if entity.text not in cat_to_target_reviews[entity.category].keys():
                            cat_to_target_reviews[entity.category][entity.text] = []
                        if entity.text in target_to_complaints.keys():
                            cat_to_target_reviews[entity.category][entity.text] = result['complaints'][entity.text][
                                'details']
                        if entity.text in target_to_complement.keys():
                            cat_to_target_reviews[entity.category][entity.text].extend(
                                result['complements'][entity.text][
                                    'details'])

        result["categories"] = cat_to_target_reviews
        loc_string = ""

        if 'Location' in result['categories'].keys():
            locations = result['categories']['Location']  # {Ground Floor: [x, y, z]}
            top_locs = heapq.nlargest(5, locations.items(), key=lambda x: len(x[1]))
            locations = dict(top_locs)

            loc_dict = {}
            for location in locations.keys():
                lowercase_list = [s.lower() for s in locations[location]]
                word_count = Counter(lowercase_list)
                top_10 = word_count.most_common(10)
                locations[location] = top_10
                loc_dict[location] = ""
                for adj in locations[location]:
                    loc_dict[location] += adj[0] + ", "
                loc_dict[location] = loc_dict[location][:-2]
            for location in loc_dict.keys():
                loc_string += location + " is described as " + loc_dict[location] + "<br>"

        result["Location Details"] = loc_string

        prod_string = ""
        if 'Product' in result['categories'].keys():
            products = result['categories']['Product']
            if 'food' in products:
                del products['food']
            top_prods = heapq.nlargest(7, products.items(), key=lambda x: len(x[1]))
            products = dict(top_prods)
            prod_dict = {}
            for product in products.keys():
                lowercase_list = [s.lower() for s in products[product]]
                word_count = Counter(lowercase_list)
                top_10 = word_count.most_common(10)
                products[product] = top_10
                prod_dict[product] = ""
                for adj in products[product]:
                    prod_dict[product] += adj[0] + ", "
                prod_dict[product] = prod_dict[product][:-2]
            for product in prod_dict.keys():
                prod_string += product + " is described as " + prod_dict[product] + "<br>"

        result["Product Details"] = prod_string

        sk_string = ""
        if 'Skill' in result['categories'].keys():
            skills = result['categories']['Skill']
            top_skills = heapq.nlargest(5, skills.items(), key=lambda x: len(x[1]))
            skills = dict(top_skills)
            sk_dict = {}

            for skill in skills.keys():
                lowercase_list = [s.lower() for s in skills[skill]]
                word_count = Counter(lowercase_list)
                top_10 = word_count.most_common(10)
                skills[skill] = top_10
                sk_dict[skill] = ""
                for adj in skills[skill]:
                    sk_dict[skill] += adj[0] + ", "
                sk_dict[skill] = sk_dict[skill][:-2]
            for skill in sk_dict.keys():
                sk_string += skill + " is described as " + sk_dict[skill] + "<br>"

        result["Skill Details"] = sk_string
        per_string = ""

        if 'Person' in result['categories'].keys():
            people = result['categories']['Person']
            top_people = heapq.nlargest(5, people.items(), key=lambda x: len(x[1]))
            people = dict(top_people)

            per_dict = {}
            for person in people.keys():
                lowercase_list = [s.lower() for s in people[person]]
                word_count = Counter(lowercase_list)
                top_10 = word_count.most_common(10)
                people[person] = top_10
                per_dict[person] = ""
                for adj in people[person]:
                    per_dict[person] += adj[0] + ", "
                per_dict[person] = per_dict[person][:-2]
            for person in per_dict.keys():
                per_string += person + " is described as " + per_dict[person] + "<br>"

        result["Person Details"] = per_string

        # Sort and get top 5 complaints
        sorted_complaints = sorted(result["complaints"].items(), key=lambda item: item[1]["count"], reverse=True)[:7]
        result["complaints"] = {k: v for k, v in sorted_complaints}

        # Sort and get top 5 complements
        sorted_complements = sorted(result["complements"].items(), key=lambda item: item[1]["count"], reverse=True)[:7]
        result["complements"] = {k: v for k, v in sorted_complements}

        for target in result['complaints'].keys():
            lowercase_list = [s.lower() for s in result['complaints'][target]['details']]
            word_count = Counter(lowercase_list)
            top_10 = word_count.most_common(10)
            result['complaints'][target]['details'] = top_10

        for target in result['complements'].keys():
            lowercase_list = [s.lower() for s in result['complements'][target]['details']]
            word_count = Counter(lowercase_list)
            top_10 = word_count.most_common(10)
            result['complements'][target]['details'] = top_10

        return result

    def review_zomato_detector(self):
        scraped_reviews = self.scrape_all_zomato_pages()
        return self.zomato_analyzer(scraped_reviews)