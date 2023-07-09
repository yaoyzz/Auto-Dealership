import scrapy
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor

from pyppeteer import launch
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError
import nest_asyncio

from urllib.parse import urljoin
import jsonlines
import json
import re

nest_asyncio.apply()

class MyClass:
    def __init__(self):
            self.function_map = {
            'parse_test': self.parse_test,
            'parse_new': self.parse_new,
        }
    
    async def parse_test(self, response, page):
        await page.goto(response.url)
        try:
            await page.waitForXPath('/html/body/div[2]/section/div[4]/div[2]/div[1]/h3')

            test2_element = await page.xpath('/html/body/div[2]/div[2]/a/div/div/div/h3')
            test2 = await page.evaluate('(element) => element.textContent', test2_element[0])
            test3_element = await page.xpath('/html/body/div[2]/section/div[4]/div[2]/div[1]/h3')
            test3 = await page.evaluate('(element) => element.textContent', test3_element[0])
        except PyppeteerTimeoutError:
            print('PyppeteerTimeoutError caught')
            test2 = ''
            test3 = ''
        data = {
            'test2': test2,
            'test3': test3
        }
        filename = 'test.json'
        with open(filename, 'a') as f:
            json.dump(data, f, indent=4)
        await page.browser.close()

    async def get_attribute_value(page, attribute, attr_names, div_element):
        attr_name = next((attr_name for attr_name in attr_names if attribute in attr_name), None)
        if attr_name is not None:
            attribute_value = await page.evaluate(f'(element) => element.getAttribute("{attr_name}")', div_element)
            
            if attribute in ['year', 'price']:
                number_match = re.search(r'\d+', attribute_value)
                if number_match:
                    return number_match
                else:
                    return ''
            elif attribute in ['website', 'name']:
                if any(substring in attribute_value.lower() for substring in ['filter', 'website', 'header']):
                    return ''
                else:
                    return attribute_value
            else:
                return attribute_value
        else:
            return ''

    async def parse_new(self, response, page):
        await page.goto(response.url)
        data_list = []

        try:
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

                    # Get img src link from sub-xpath of the container
                    img_element = await div_element.querySelector('img')
                    if img_element:
                        img_src = await page.evaluate('(element) => element.getAttribute("src")', img_element)
                        img_src = urljoin(response.url, img_src)
                    else:
                        img_src = ''

                    non_empty_count = sum(bool(attr) for attr in [vin, img_src, year, model, make, name, price])

                    if non_empty_count > 1:
                        # Save the car information to a dictionary
                        data = {
                            'vin': vin,
                            'img_src': img_src,
                            'year': year,
                            'model': model,
                            'make': make,
                            'name': name,
                            'price': price
                        }

                        data_list.append(data)

        except PyppeteerTimeoutError:
            print('Caught PyppeteerTimeoutError')

        filename = 'car_info.jsonl'
        with jsonlines.open(filename, mode='a') as writer:
            for item in data_list:
                writer.write(item)

        await page.browser.close()


class MySpider(scrapy.Spider):
    name = 'myspider'
    url = 'https://www.beavertontoyota.com'
    start_urls = [url]

    def parse(self, response):
        # For testing
        # test_inventory_links = LinkExtractor(allow='new').extract_links(response)
        # for link in test_inventory_links:
        #     yield scrapy.Request(url=link.url, callback=self.parse_item, cb_kwargs={'func': 'parse_test'})
        
        # '/searchnew\.aspx$'
        new_inventory_links = LinkExtractor(allow='new').extract_links(response)
        for link in new_inventory_links:
            yield scrapy.Request(url=link.url, callback=self.parse_item, cb_kwargs={'func': 'parse_new'})
    
    def parse(self, response):
        # Extract links to new cars
        new_inventory_links = LinkExtractor(allow='new').extract_links(response)
        for link in new_inventory_links:
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

        # Convert text response to HtmlResponse to get url
        resp = HtmlResponse(url=response.url, body=response.text, encoding='utf-8')
        await obj.function_map[func](resp, page)