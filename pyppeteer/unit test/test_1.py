import asyncio
from pyppeteer import launch
from urllib.parse import urljoin, urlparse
import json
import jsonlines
import re
import random

class MyCrawler:
    def __init__(self, start_urls):
        self.start_urls = start_urls
        self.browser = None
        self.page = None
        self.crawled_vins = set()
        self.visited_urls = set() 

        # Load crawled_vins from file
        try:
            with open('crawled_vins.txt', 'r') as file:
                for line in file:
                    vin = line.strip()
                    self.crawled_vins.add(vin)
        except FileNotFoundError:
            pass

    async def get_all_attributes(self, element):
        attributes = await self.page.evaluate('(element) => { let attrs = {}; for(let i=0; i<element.attributes.length; i++) { let attr = element.attributes[i]; attrs[attr.name] = attr.value; }; return attrs; }', element)
        return attributes

    async def get_attribute_from_sub_element(self, element, sub_element_tag, attribute_name):
        sub_element = await element.querySelector(sub_element_tag)
        if sub_element:
            attribute_value = await self.page.evaluate('(element) => element.getAttribute("{}")'.format(attribute_name), sub_element)
            return attribute_value
        else:
            return None

    async def check_attribute_name(self, attributes, substrings):
        for attr_name, attr_value in attributes.items():
            if any(substring in attr_name.lower() for substring in substrings):
                return attr_value
        return None

    async def parse_page(self, url):
        if url in self.visited_urls:  # Skip if the URL was already visited
            return        
        # await self.page.setCookie({
        #     'name': 'session_1',
        #     'value': 'abcd1234',
        #     'domain': f'{urlparse(url).scheme}'
        # })

        # cookies = await self.page.cookies()
        # print(cookies)
        # # Set cookies
        
        await self.page.goto(url)
        # for inspecting current page
        h1_text = await self.page.evaluate('document.querySelector("h1").textContent')
        print(h1_text)
        self.visited_urls.add(url)
        # Check for the presence of the 'Accept' button and click it if it exists
        accept_buttons = await self.page.querySelectorAll('button[aria-label="Accept"]')
        if accept_buttons:
            await accept_buttons[0].click()
            await asyncio.sleep(random.uniform(1, 3))  # wait for the click to be processed and for the page to update

        # Get all the links on the page
        links = await self.page.querySelectorAll('a')
        link_hrefs = []
        for link in links:
            href = await self.page.evaluate('(element) => element.getAttribute("href")', link)
            if href:  
                link_hrefs.append(href)

        for href in link_hrefs:
            full_url = urljoin(url, href)
            parsed_url = urlparse(full_url)
            # if there are more than two slashes in the path, then it is a subcategory and we skip
            if parsed_url.path.count('/') > 2:  
                continue
            # await asyncio.sleep(random.uniform(1, 3))
            print(full_url)
            # await asyncio.sleep(2)
            if re.search(r'new', full_url):
                await self.parse_car(full_url, 'new')
            elif re.search(r'used', full_url):
                await self.parse_car(full_url, 'used')
        
        # # Get the 'Next' button and click on it
        # next_button = await self.page.xpath('//a[contains(translate(text(), "NEXT", "next"), "next") or contains(translate(@class, "NEXT", "next"), "next") or contains(translate(@rel, "NEXT", "next"), "next")]')
        # if next_button:
        #     # Click on the button and wait for navigation
        #     await asyncio.gather(
        #         next_button[0].click(),
        #         self.page.waitForNavigation(),
        #     )
        #     # Get the new page's URL
        #     next_page_url = self.page.url
        #     # Parse the new page
        #     await self.parse_page(next_page_url)


    async def parse_car(self, url, condition:str = None):
        # await self.page.setUserAgent('Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0')
        await self.page.goto(url)
        # await asyncio.sleep(random.uniform(1, 5))
        # html_content = await self.page.content()
        # with open('page.html', 'w', encoding='utf-8') as f:
        #     f.write(html_content)

        data_list = []
        div_elements = await self.page.querySelectorAll('div')
        # await asyncio.sleep(random.uniform(1, 5))
        for div_element in div_elements:
            # Get all attribute names of div_element
            attributes = await self.get_all_attributes(div_element)
            vin = img_src = year = model = make = name = price = href = trim = stock = fueltype = type = None
            # await asyncio.sleep(random.uniform(1, 5))
            vin = await self.check_attribute_name(attributes, ['vin'])
            year = await self.check_attribute_name(attributes, ['year'])
            model = await self.check_attribute_name(attributes, ['model'])
            make = await self.check_attribute_name(attributes, ['make'])
            name = await self.check_attribute_name(attributes, ['name'])
            price = await self.check_attribute_name(attributes, ['price'])
            # await asyncio.sleep(random.uniform(1, 5))
            if vin and vin not in self.crawled_vins:  # If VIN found and it's new
                print('vin found')
                self.crawled_vins.add(vin)

                href = await self.get_attribute_from_sub_element(div_element, 'a', 'href')
                img_src = await self.get_attribute_from_sub_element(div_element, 'img', 'src')
                if img_src:
                    img_src = urljoin(url, img_src)
                if img_src or model or make or name or price:  # Any of these attributes is enough
                    data = {
                        'website': urlparse(url).scheme + "://" + urlparse(url).netloc,
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
        
            # non_empty_count = sum(bool(attr) for attr in [vin, year, model, make, name, price])
            # if non_empty_count < 3:
            #     vehicle_data_json = await self.check_attribute_name(attributes, ['data-vehicle'])
            #     await asyncio.sleep(random.uniform(1, 5))
            #     if vehicle_data_json is not None:
            #         print(vehicle_data_json)
            #         vehicle_data = json.loads(vehicle_data_json)
            #         vin = vehicle_data.get('vin', None)
            #         if vin:  # If VIN found, get href and img_src
            #             href = await self.get_attribute_from_sub_element(self.page, div_element, 'a', 'href')
            #             await asyncio.sleep(random.uniform(1, 5))
            #             img_src = await self.get_attribute_from_sub_element(self.page, div_element, 'img', 'src')
            #             await asyncio.sleep(random.uniform(1, 5))
            #             make = vehicle_data.get('make', None)
            #             stock = vehicle_data.get('stock', None)
            #             fueltype = vehicle_data.get('fueltype', None)
            #             type = vehicle_data.get('type', None)
            #             year = vehicle_data.get('year', None)
            #             model = vehicle_data.get('model', None)
            #             trim = vehicle_data.get('trim', None)
            #             price = vehicle_data.get('price', None)
            #             if img_src:
            #                 img_src = urljoin(url, img_src)
            #             if model or make or name or price:  # Any of these attributes is enough
            #                 data = {
            #                     'website': urlparse(url).scheme + "://" + urlparse(url).netloc,
            #                     'vin': vin,
            #                     'img_src': img_src,
            #                     'year': year,
            #                     'model': model,
            #                     'make': make,
            #                     'name': name,
            #                     'price': price,
            #                     'stock': stock,
            #                     'fueltype': fueltype,
            #                     'type': type,
            #                     'trim': trim,
            #                     'href': href
            #                 }
            #             data_list.append(data)

        with jsonlines.open(f'{condition}_car_info.jsonl', mode='a') as writer:
            writer.write_all(data_list)

    async def start(self):
        self.browser = await launch(headless=True)
        # self.browser = await launch(headless=False)
        self.page = await self.browser.newPage()
        
        # specify the user agent to avoid blocking
        # await self.page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; WOW64; rv:68.0) Gecko/20100101 Firefox/68.0')
        await self.page.setUserAgent('Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0')
        for url in self.start_urls:
            await self.parse_page(url)

        # Save crawled_vins to file
        with open('crawled_vins.txt', 'w') as file:
            for vin in self.crawled_vins:
                file.write(vin + '\n')

        await self.browser.close()


start_urls = [
            # 'https://www.toyotaofcorvallis.com/new-vehicles/',
            'https://www.beavertontoyota.com/'
            ]
crawler = MyCrawler(start_urls)
asyncio.run(crawler.start())
