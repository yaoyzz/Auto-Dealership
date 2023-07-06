import scrapy
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from pyppeteer import launch
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError
import nest_asyncio
import json

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

    async def parse_new(self, response, page):
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
        


    async def parse_item(self, response, func):
        obj = MyClass()
        browser = await launch(headless=True)
        page = await browser.newPage()

        # Convert text response to HtmlResponse to get url
        resp = HtmlResponse(url=response.url, body=response.text, encoding='utf-8')
        await obj.function_map[func](resp, page)