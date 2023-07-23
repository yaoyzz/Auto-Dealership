import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json

import time


# Def custom CarItem class that contains various fields
class CarItem(scrapy.Item):
    cover_image = scrapy.Field()
    title = scrapy.Field()
    vin_number = scrapy.Field()

class CrawlingSpider(CrawlSpider):
    name = "mycrawler"
    allowed_domains = ["beavertontoyota.com"]
    url = 'https://www.beavertontoyota.com'
    start_urls = [url]
    
    rules = (
    #Rule(LinkExtractor(allow='/hours\.aspx'), callback='parse_dealer'),
    # Rule(LinkExtractor(allow='/searchnew\.aspx'), callback='parse_new'),
    Rule(LinkExtractor(allow='/searchnew\.aspx$'), callback='parse_test'),
    )

    def __init__(self, *args, **kwargs):
        super(CrawlingSpider, self).__init__(*args, **kwargs)
        self.driver = webdriver.Chrome()

    # sample table xpath
    def extract_hours_rows(self, tablePath, response):
        hours = []
        for i in range(1, 8):
            day = response.xpath(f'{tablePath}/tr[{i}]/td[1]/text()').get()
            opening_hour = response.xpath(f'{tablePath}/tr[{i}]/td[2]/text()').get()
            closing_hour = response.xpath(f'{tablePath}/tr[{i}]/td[3]/text()').get()
            hours.append({
                'day': day.strip() if day else None,
                'opening_hour': opening_hour.strip() if opening_hour else None,
                'closing_hour': closing_hour.strip() if closing_hour else None
            })
        return hours


    def parse_dealer(self, response):
        # parse the dealer information 
        dealer_logo_url = response.xpath('/html/body/div[1]/header/div/div[1]/div[1]/ul/li[2]/a/img/@src').get()
        dealer_brand_url = response.xpath('/html/body/div[1]/header/div/div[1]/div[1]/ul/li[1]/a/img[1]/@src').get()
        dealer_contact = response.xpath('/html/body/div[1]/header/div/div[1]/div[2]/ul/li[1]/ul/li/span[2]/span/text()').get()
        
        dealer_address = ''
        dealer_hours = []
        
        # parse main dealer address
        dealer_address_list = response.xpath('/html/body/div[2]/section/div/div[2]/div[2]/div[1]/div[1]//text()').getall()
        dealer_address = '\n'.join([i.strip() for i in dealer_address_list if i.strip()])

        #parse main dealer opening hours 
        # ** null value needs to be fixed **
        sales_hours_rows = '/html/body/div[2]/section/div/div[2]/div[3]/div[2]/div[2]/div/div[1]/table/tbody'
        sales_hours = self.extract_hours_rows(sales_hours_rows, response)
        dealer_hours.append({'type': 'SalesHours', 'hours': sales_hours})

        service_hours_rows = '/html/body/div[2]/section/div/div[2]/div[3]/div[2]/div[2]/div/div[2]/table/tbody'
        service_hours = self.extract_hours_rows(service_hours_rows, response)
        dealer_hours.append({'type': 'ServiceHours', 'hours': service_hours})

        parts_hours_rows = '/html/body/div[2]/section/div/div[2]/div[3]/div[2]/div[2]/div/div[3]/table/tbody'
        parts_hours = self.extract_hours_rows(parts_hours_rows, response)
        dealer_hours.append({'type': 'PartsHours', 'hours': parts_hours})

        data = {
            'website': self.url,
            'dealer_logo_url': self.url + dealer_logo_url,
            'dealer_brand_url' : self.url + dealer_brand_url,
            'dealer_address' : dealer_address,
            'dealer_contact' : dealer_contact,
            'dealer_hours' : dealer_hours
        }
        filename = 'dealer_info.json'

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def parse_new(self, response):
    
        car_list = response.xpath('/html/body/div[2]/section/div[4]/div[2]/div[2]/div/div[6]/div/div/div[1]/div[2]').get()
        car_items = []
        for car in car_list:
            item = CarItem()
            # /div[1]/div[1]/div/div/div/div[1]/div[1]/a/div/div[2]/img[1]
            # /div[2]/div[1]/div/div/div/div[1]/div[1]/a/div/div[2]/img[1]
            item['cover_image'] = car.xpath('.//div[1]/div/div/div/div[1]/div[1]/a/div/div[2]/img[1]/@src').get()
            item['cover_image'] = car.xpath('.//div[1]/div[1]/div/div/div/div[1]/div[1]/a/div/div[2]/img[1]/@src').get()

            item['title'] = car.xpath('.//div[2]/div/div[1]/a/h3/span/text()').get()
            item['vin_number'] = car.xpath('.//div[2]/div/div[3]/div/div[1]/span[2]/text()').get()
            car_items.append(item)

        data = {
            'car_items': car_items
        }

        filename = 'new_car.json'

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)


    def parse_test(self, response):
        self.driver.get(response.url)
        # time.sleep(3)
        
        test1 = response.xpath('/html/body/div[2]/div[2]/a/div/div/div/h3/text()').get()
        test2 = self.driver.find_element('xpath', '/html/body/div[2]/div[2]/a/div/div/div/h3').text
        
        # Wait for the element to be visible
        wait = WebDriverWait(self.driver, 10)
        test3_element = wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/section/div[4]/div[2]/div[1]/h3')))
        test3 = test3_element.text

        data = {
            'test1' : test1,
            'test2': test2,
            'test3' : test3
            # 'test1' : test1,
            # 'test5' : test5
        }

        filename = 'test.json'

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            

        
    