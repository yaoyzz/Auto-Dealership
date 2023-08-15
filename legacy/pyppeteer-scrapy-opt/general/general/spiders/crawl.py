import scrapy
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor

from pyppeteer import launch
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError

import asyncio
import time
import nest_asyncio

from urllib.parse import urljoin
from urllib.parse import urlparse

import jsonlines
import json

import re

nest_asyncio.apply()

class MyClass:
    def __init__(self, page, crawled_vins):
            self.page = page
            self.crawled_vins = crawled_vins
            self.function_map = {
            'parse_car': self.parse_car,
        }

    async def get_attribute_value(self, page, attribute, attr_names, div_element):
        attr_name = next((attr_name for attr_name in attr_names if attribute in attr_name), None)
        if attr_name is not None:
            attribute_value = await page.evaluate(f'(element) => element.getAttribute("{attr_name}")', div_element)
            
            if attribute in ['year', 'price']:
                number_match = re.search(r'\d+', attribute_value)
                if number_match:
                    return number_match.group()
                else:
                    return None
            elif attribute in ['website', 'name']:
                if any(substring in attribute_value.lower() for substring in ['filter', 'website', 'header']):
                    return None
                else:
                    return attribute_value
            else:
                return attribute_value
        else:
            return None

    async def get_attribute_from_sub_element(self, element, sub_element_tag, attribute_name, response=None):
        """
        Get the attribute value from a sub-element of a given element.

        :param element: The parent element.
        :param sub_element_tag: The tag of the sub-element (e.g. 'a', 'img').
        :param attribute_name: The name of the attribute to get (e.g. 'href', 'src').
        :param response: The response object, used for url joining in case of 'src' attribute.
        :return: The value of the attribute, or None if the sub-element or the attribute doesn't exist.
        """
        sub_element = await element.querySelector(sub_element_tag)
        if sub_element:
            attribute_value = await self.page.evaluate(f'(element) => element.getAttribute("{attribute_name}")', sub_element)
            if attribute_name == 'src' and response:
                attribute_value = urljoin(response.url, attribute_value)
            return attribute_value
        else:
            return None

    async def get_all_attributes(self, element):
        attributes = await self.page.evaluate('(element) => { let attrs = {}; for(let i=0; i<element.attributes.length; i++) { let attr = element.attributes[i]; attrs[attr.name] = attr.value; }; return attrs; }', element)
        return attributes


    async def parse_car(self, response, condition:str):
        try:
            await self.page.goto(response.url)
        except PyppeteerTimeoutError:
            print('Caught PyppeteerTimeoutError')
            return

        data_list = []
        div_elements = await self.page.querySelectorAll('div')
        

        for div_element in div_elements:
            # Get all attribute names of div element
            attributes = await self.get_all_attributes(div_element)
            vin = img_src = year = model = make = name = price = href = trim = stock = fueltype = type = None
            
            vin = attributes.get('vin', None)
            year = attributes.get('year', None)
            model = attributes.get('model', None)
            make = attributes.get('make', None)
            name = attributes.get('name', None)
            price = attributes.get('price', None)

            href = await self.get_attribute_from_sub_element(div_element, 'a', 'href')
            img_src = await self.get_attribute_from_sub_element(div_element, 'img', 'src', response)

            non_empty_count = sum(bool(attr) for attr in [vin, img_src, model, make, name, price])
            
            if non_empty_count < 3:
                vehicle_data_json = attributes.get('data-vehicle', None)
                if vehicle_data_json is not None:
                    vehicle_data = json.loads(vehicle_data_json)
                
                    vin = vehicle_data.get('vin', None)
                    make = vehicle_data.get('make', None)
                    stock = vehicle_data.get('stock', None)
                    fueltype = vehicle_data.get('fueltype', None)
                    type = vehicle_data.get('type', None)
                    year = vehicle_data.get('year', None)
                    model = vehicle_data.get('model', None)
                    trim = vehicle_data.get('trim', None)
                    price = vehicle_data.get('price', None)

                    href = await self.get_attribute_from_sub_element(div_element, 'a', 'href')
                    img_src = await self.get_attribute_from_sub_element(div_element, 'img', 'src', response)

            non_empty_count = sum(bool(attr) for attr in [vin, img_src, model, make, name, price])

            if vin and non_empty_count > 1:
                if vin in self.crawled_vins:
                    # Skip this car
                    continue
                self.crawled_vins.add(vin)
                data = {
                    'website' : urlparse(response.url).scheme + "://" + urlparse(response.url).netloc,
                    'vin': vin,
                    'img_src': img_src,
                    'year': year,
                    'stock': stock,
                    'fueltype': fueltype,
                    'type': type,
                    'model': model,
                    'make': make,
                    'name': name,
                    'price': price,
                    'trim': trim,
                    'href': href
                }

                data_list.append(data)

        filename = f'{condition}_car_info.jsonl'
        with jsonlines.open(filename, mode='a') as writer:
            for item in data_list:
                writer.write(item)

    # async def close_browser(self):
    #     await self.page.browser.close()


class MySpider(scrapy.Spider):
    name = 'myspider'
    start_urls = [
                  'https://www.beavertontoyota.com', # initial built
                #   'https://www.mypowerhonda.com/'
                #   'https://www.toyotaofcorvallis.com/'
                  ]
    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        self.loop = asyncio.get_event_loop()
        self.browser = self.loop.run_until_complete(launch())
        self.page = self.loop.run_until_complete(self.browser.newPage())
        self.crawled_vins = set()  # Create set to store crawled VINs
        try:
            with open('crawled_vins.txt', 'r') as file:
                for line in file:
                    vin = line.strip() 
                    self.crawled_vins.add(vin)
        except FileNotFoundError:
            pass  
    
    def parse(self, response):
        # Extract links to new cars
        new_inventory_links = LinkExtractor(allow='new').extract_links(response)
        for link in new_inventory_links:
            yield scrapy.Request(url=link.url, callback=self.parse_item, cb_kwargs={'func': 'parse_car', 'condition': 'new'})
        
        used_inventory_links = LinkExtractor(allow='used').extract_links(response)
        for link in used_inventory_links:
            yield scrapy.Request(url=link.url, callback=self.parse_item, cb_kwargs={'func': 'parse_car', 'condition': 'used'})

        # Extract link to next page and yield a new request
        # translate() allows case insensitive
        next_page_link = response.xpath(
            '//a[contains(translate(text(), "NEXT", "next"), "next") or contains(translate(@class, "NEXT", "next"), "next") or contains(translate(@rel, "NEXT", "next"), "next")]/@href'
        ).get()

        if next_page_link:
            yield scrapy.Request(url=response.urljoin(next_page_link), callback=self.parse)


    async def parse_item(self, response, func, condition):
        obj = MyClass(self.page, self.crawled_vins)
        resp = HtmlResponse(url=response.url, body=response.text, encoding='utf-8')
        await obj.function_map[func](resp, condition)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=scrapy.signals.spider_closed)
        return spider

    async def spider_closed(self):
        with open('crawled_vins.txt', 'w') as file:
            for vin in self.crawled_vins:
                file.write(vin + '\n')
        await self.browser.close()