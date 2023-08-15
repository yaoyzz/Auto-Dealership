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
    def __init__(self):
            self.function_map = {
            # 'parse_test': self.parse_test,
            'parse_new': self.parse_new,
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

    async def parse_new(self, response, page):
        try:
            await page.goto(response.url)
        except PyppeteerTimeoutError:
            print('Caught PyppeteerTimeoutError')
            return

        data_list = []
        div_elements = await page.querySelectorAll('div')

        for div_element in div_elements:
            # Get all attribute names of div element
            attr_names = await page.evaluate('(element) => element.getAttributeNames()', div_element)

            if any('vin' in attr_name.lower() or 
                    'model' in attr_name.lower() or 
                    'vehicle' in attr_name.lower() or
                    'year' in attr_name.lower() or
                    'make' in attr_name.lower() or
                    'name' in attr_name.lower() or
                    'price' in attr_name.lower()
                    for attr_name in attr_names):

                # Get the VIN, year, model, make, name, and price from the identified attributes
                vin = await self.get_attribute_value(page, 'vin', attr_names, div_element)
                year = await self.get_attribute_value(page, 'year', attr_names, div_element)
                model = await self.get_attribute_value(page, 'model', attr_names, div_element)
                make = await self.get_attribute_value(page, 'make', attr_names, div_element)
                name = await self.get_attribute_value(page, 'name', attr_names, div_element)
                price = await self.get_attribute_value(page, 'price', attr_names, div_element)

                a_element = await div_element.querySelector('a')
                href = await page.evaluate('(element) => element.getAttribute("href")', a_element) if a_element else None
                # Get img src link from sub-xpath of the container
                img_element = await div_element.querySelector('img')
                if img_element:
                    img_src = await page.evaluate('(element) => element.getAttribute("src")', img_element)
                    img_src = urljoin(response.url, img_src)
                else:
                    img_src = None

                non_empty_count = sum(bool(attr) for attr in [img_src, model, make, name, price])

                if vin and non_empty_count > 0:
                    # Save the car information to a dictionary
                    data = {
                        'website' : urlparse(response.url).scheme + "://" + urlparse(response.url).netloc,
                        'vin': vin,
                        'img_src': img_src,
                        'year': year,
                        'model': model,
                        'make': make,
                        'name': name,
                        'price': price,
                        'href': href
                    }

                    data_list.append(data)

        filename = 'new_car_info.jsonl'
        with jsonlines.open(filename, mode='a') as writer:
            for item in data_list:
                writer.write(item)

    async def close_browser(self, page):
        await page.browser.close()


class MySpider(scrapy.Spider):
    name = 'myspider'
    start_urls = ['https://www.beavertontoyota.com', # initial built
                  # DealerInspire
                #   'https://www.beavertonhonda.com/',
                #   'https://www.toyotaofcorvallis.com/',
                #   'https://www.mercedesbenzbeaverton.com/',
                  # DealerOn
                  'https://www.mypowerhonda.com/',
                #   'https://www.carltonmb.com/',
                #   'https://www.greshamtoyota.com/',
                #   # Dealer.com
                #   'https://www.malonetoyota.com/',
                #   'https://www.mercedesbenzofbellevue.com/',
                #   'https://www.beavertonnissan.com/',
                #   # FoxDealer
                #   'https://www.tonkinwilsonvillenissan.com/',
                #   'https://www.claremonttoyota.com/',
                #   # DealerFire
                #   'https://www.mbscottsdale.com/',
                #   'https://www.jpauleytoyota.com/',
                #   # Carforsale                   
                #   'https://www.siamaks.com/',
                #   'https://www.prestigeautopdx.com/',
                #   # Dealer eProcess                  
                #   'https://www.foxtoyotaofelpaso.com/',
                #   'https://www.marianoriverahonda.com/',
                #   # Sincro                  
                #   'https://www.dublinnissan.com/',
                #   'https://www.crestmontcadillac.com/'
                  ]
    
    def parse(self, response):
        # Extract links to new cars
        new_inventory_links = LinkExtractor(allow='new').extract_links(response)
        for link in new_inventory_links:
            yield scrapy.Request(url=link.url, callback=self.parse_item, cb_kwargs={'func': 'parse_new'})
        
        used_inventory_links = LinkExtractor(allow='used').extract_links(response)
        for link in used_inventory_links:
            yield scrapy.Request(url=link.url, callback=self.parse_item, cb_kwargs={'func': 'parse_new'})

        

        # Extract link to next page and yield a new request
        # translate() allows case insensitive
        next_page_link = response.xpath(
            '//a[contains(translate(text(), "NEXT", "next"), "next") or contains(translate(@class, "NEXT", "next"), "next") or contains(translate(@rel, "NEXT", "next"), "next")]/@href'
        ).get()

        if next_page_link:
            yield scrapy.Request(url=response.urljoin(next_page_link), callback=self.parse)


    async def parse_item(self, response, func):
        obj = MyClass()
        browser = await launch(headless=True)
        page = await browser.newPage()
        await asyncio.sleep(5)
        
        # Convert text response to HtmlResponse to get url
        resp = HtmlResponse(url=response.url, body=response.text, encoding='utf-8')
        await obj.function_map[func](resp, page)
        await obj.close_browser(page)