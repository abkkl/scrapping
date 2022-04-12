# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 19:49:32 2022

@author: Bakkal
"""
from bs4 import BeautifulSoup
import requests, lxml, re, json
import pandas as pd
from datetime import datetime

# user-agent headers to act as a "real" user visit
headers = {
    "user-agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
}

# search query params
params = {
    "id": "com.nintendo.zara",  # app name
    "gl": "US"  # country
}


def scrape_google_store_app():
    global app_data
    global app_user_comments
    global user_comment_likes
    global user_comment_app_rating
    
    html = requests.get("https://play.google.com/store/apps/details", params=params, headers=headers, timeout=10).text
    soup = BeautifulSoup(html, "lxml")

    # where all app data will be stored
    app_data = []

    # <script> position is not changing that's why [12] index being selected. Other <script> tags position are changing.
    # [12] index is a basic app information
    # https://regex101.com/r/DrK0ih/1
    basic_app_info = json.loads(re.findall(r"<script nonce=\".*\" type=\"application/ld\+json\">(.*?)</script>",
                                           str(soup.select("script")[12]), re.DOTALL)[0])

    app_name = basic_app_info["name"]
    app_type = basic_app_info["@type"]
    app_url = basic_app_info["url"]
    app_description = basic_app_info["description"].replace("\n", "")  # replace new line character to nothing
    app_category = basic_app_info["applicationCategory"]
    app_operating_system = basic_app_info["operatingSystem"]
    app_main_thumbnail = basic_app_info["image"]
    app_price = basic_app_info["offers"][0]["price"]
    
    app_content_rating = basic_app_info["contentRating"]
    app_rating = round(float(basic_app_info["aggregateRating"]["ratingValue"]), 1)  # 4.287856 -> 4.3
    app_reviews = basic_app_info["aggregateRating"]["ratingCount"]

    app_author = basic_app_info["author"]["name"]
    app_author_url = basic_app_info["author"]["url"]

    # https://regex101.com/r/VX8E7U/1
    app_images_data = re.findall(r",\[\d{3,4},\d{3,4}\],.*?(https.*?)\"", str(soup.select("script")))
    # delete duplicates from app_images_data
    app_images = [item for item in app_images_data if app_images_data.count(item) == 1]

    # User comments
    app_user_comments = []

    # https://regex101.com/r/SrP5DS/1
    app_user_reviews_data = re.findall(r"(\[\"gp.*?);</script>",
                                       str(soup.select("script")), re.DOTALL)

    for review in app_user_reviews_data:
        user_comment_likes = re.findall(r",?\d+\],?(\d+),?", str(review))
        user_comment_app_rating = re.findall(r"\"gp.*?https.*?\],(.*?)?,", str(review))

        for likes, user_app_rating in zip(user_comment_likes, user_comment_app_rating):
            app_user_comments.append({
                "user_app_rating": user_app_rating,
                "user__comment_likes": likes,
            })
        
        user_comment_likes = [int(x) for x in user_comment_likes]
        user_comment_app_rating = [int(x) for x in user_comment_app_rating]
        product = [x*y for x,y in zip(user_comment_likes,user_comment_app_rating)]
        comment_rating = sum(product)/sum(user_comment_likes)

        app_data.append({
            "app_name": app_name,
            "app_type": app_type,
            "app_url": app_url,
            "app_main_thumbnail": app_main_thumbnail,
            "app_description": app_description,
            "app_price": app_price,
            "app_content_rating": app_content_rating,
            "app_category": app_category,
            "app_operating_system": app_operating_system,
            "comment_rating": comment_rating,
            "app_rating": app_rating,
            "app_reviews": app_reviews,
            "app_author": app_author,
            "app_author_url": app_author_url,
            "app_screenshots": app_images
        })

        return {"app_data": app_data}


scrape_google_store_app()
data = pd.DataFrame.from_dict(app_data)
print(data)