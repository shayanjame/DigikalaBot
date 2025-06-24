# Copyright 2025 Shayan Jame

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

import requests
from fake_useragent import UserAgent

from logger import get_logger

logger = get_logger(__name__)


class Crawler:
    """
    A class to crawl product data and reviews from a given Digikala API.
    """

    def __init__(self, config, page=1):
        """
        Initialize the Crawler with configuration data.

        Args:
            config (dict): Configuration dictionary containing API endpoint templates.
        """
        self.crawler_config = config["crawler"]
        self.url_get_products = self.crawler_config["url_get_products"]
        self.url_get_product_detail = self.crawler_config["url_get_product_detail"]
        self.category = self.crawler_config["category"]
        self.brand = self.crawler_config["brand"]
        self.page = page

    def get_products(self, category, brand, page=1):
        """
        Fetches a list of products based on category and brand.

        Args:
            category (str): Product category to filter.
            brand (str): Product brand to filter.
            page (int, optional): Page number for pagination. Defaults to 1.

        Returns:
            list: A list of product dictionaries.
        """
        url = self.url_get_products.format(category=category, brand=brand, page=page)
        headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": UserAgent().random,
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()["data"]["products"]
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            return []

    def get_product_details(self, productid):
        """
        Fetch detailed information of a single product by ID.

        Args:
            productid (int): Product ID.

        Returns:
            dict: JSON response containing product details.
        """
        url = self.url_get_product_detail.format(productid=productid)
        headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": UserAgent().random,
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch product details for ID {productid}: {e}")
            return {}

    @staticmethod
    def clean_text(text):
        """
        Cleans text by removing non-breaking spaces and redundant whitespaces.

        Args:
            text (str): Input string.

        Returns:
            str: Cleaned string.
        """
        text = text.replace("\u200c", "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def get_product_review(self, jsonfile):
        """
        Extracts product review description and attributes from product detail JSON.

        Args:
            jsonfile (dict): JSON containing product detail data.

        Returns:
            tuple: Cleaned review description and attributes.
        """
        try:
            reviews = jsonfile.get("data", {}).get("product", {}).get("review", {})
            description = self.clean_text(reviews.get("description", ""))

            attributes = ""
            if "attributes" in reviews:
                for attr in reviews["attributes"]:
                    title = self.clean_text(attr.get("title", ""))
                    values = " ".join(
                        self.clean_text(v) for v in attr.get("values", [])
                    )
                    attributes += f"{title}: {values}\n"

            return description, attributes.strip()
        except Exception as e:
            logger.error(f"Error while extracting review: {e}")
            return "", ""

    def store_in_db(self, description, attributes):
        pass

    def run(self):
        """
        Executes the crawling process for a given category and brand.

        Examples
        --------
        >>> from config_reader import read_config
        >>> from crawler import Crawler
        >>> crawler = Crawler(config)
        >>> crawler.run()

        """

        logger.info(f"Digikala Crawler has started - page {self.page}")

        try:
            products = self.get_products(category=self.category, brand=self.brand)
            logger.info(f"{len(products)} item in page {self.page} Crawled data")
            for product in products:
                product_id = product.get("id")
                if not product_id:
                    continue
                details = self.get_product_details(product_id)
                description, attributes = self.get_product_review(details)
                self.store_in_db(description, attributes)
        except Exception as e:
            logger.error(f"Error during crawler run at page {self.page}: {e}")

        logger.info(f"Crawling of page {self.page} completed successfully")
