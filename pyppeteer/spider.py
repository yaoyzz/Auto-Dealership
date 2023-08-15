import asyncio
import pyppeteer
from pyppeteer import launch
from urllib.parse import urljoin, urlparse
import json
import jsonlines
import re
import random
from util.bypass import *
import os

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
    async def check_listeners(self):
        # Gather both tasks and execute them concurrently
        results = await asyncio.gather(
            self.page.waitForSelector('a[data-dotagging-element-title="Next"]', timeout=7500),
            self.page.waitForNavigation(timeout=7500),
            return_exceptions=True
        )

        # Check results to identify which listener was waited
        if not isinstance(results[0], Exception):
            print("waitForSelector was fulfilled.")
            return True
        if not isinstance(results[1], Exception):
            print("waitForNavigation was fulfilled.")
            return True
        return False
    async def navigate_next_page(self):
        next_button = None 
        next_button = await self.page.querySelector('a[data-dotagging-element-title="Next"]:not([disabled])')
        if next_button is None:
            next_buttons = await self.page.querySelectorAll('a:not([disabled])')
            for button in next_buttons:
                text = await self.page.evaluate('(element) => element.textContent', button)
                class_name = await self.page.evaluate('(element) => element.className', button)
                rel = await self.page.evaluate('(element) => element.rel', button)
                
                if 'next' in text.lower() or 'next' in class_name.lower() or 'next' in rel.lower():
                    next_button = button
                    break
        # Click the 'Next' button and navigate to the next page if the button is present and clickable
        if next_button:
            try:
                # await next_button.click()
                await self.page.evaluate('(btn) => btn.click()', next_button)
                print('Clicked the next button.')
                # after clicking the next button, check if new page loaded
                if not await self.check_listeners():
                    return False
                # Add a delay before processing the next page to mimic human-like browsing behavior
                await asyncio.sleep(random.uniform(1, 3))
                return True
            except (pyppeteer.errors.ElementHandleError, pyppeteer.errors.TimeoutError) as e:
                print(f'Error: {e}.Navigation failed - The "Next" button is either not visible, not an HTMLElement, or the page took too long to load.')

        return False

    async def navigate(self, url):
        if url in self.visited_urls:  # Skip if the URL was already visited
            return
        try:
            await self.page.goto(url, timeout=10000)  # Set timeout to 10000 milliseconds (10 seconds)
        except pyppeteer.errors.TimeoutError:
            print(f"Navigation to {url} failed due to timeout. Continuing...")
            return  
        await asyncio.sleep(random.uniform(5, 5))
        self.visited_urls.add(url)
        # Check for the presence of the 'Accept' button and click it if it exists
        accept_buttons = await self.page.querySelectorAll('button[aria-label="Accept"]')
        if accept_buttons:
            await accept_buttons[0].click()
            await asyncio.sleep(random.uniform(1, 3))  # wait for the click to be processed and for the page to update

        # Pass the page to the parse_page method
        await self.parse_page()
    async def parse_page(self):
        # Get all the links on the page
        links = await self.page.querySelectorAll('a')
        link_hrefs = []
        for link in links:
            href = await self.page.evaluate('(element) => element.getAttribute("href")', link)
            if href:
                link_hrefs.append(href)
        for href in link_hrefs:
            full_url = urljoin(self.page.url, href)
            if full_url in self.visited_urls:
                continue
            parsed_url = urlparse(full_url)
            if parsed_url.path.count('/') > 2:  # if there are more than two slashes in the path, then it is a subcategory and we skip
                continue
            if "=" in full_url and not re.search(r'=\d+', full_url): # If '=' is present in the URL, but not followed by one or more digits, skip the URL
                continue
            # if re.search(r'contact|about', full_url) and "#" not in full_url:
            #     await self.parse_contact(full_url)
            #     self.visited_urls.add(full_url)
            #     await asyncio.sleep(random.uniform(1, 3))

            if re.search(r'new', full_url):
                await self.parse_car(full_url, 'new', False)
                self.visited_urls.add(full_url)
                await asyncio.sleep(random.uniform(1, 3))
            
            if re.search(r'used', full_url):
                await self.parse_car(full_url, 'used', False)
                self.visited_urls.add(full_url)
                await asyncio.sleep(random.uniform(1, 3))

            # await self.navigate_next_page()

    async def parse_contact(self, url):
        await self.page.setUserAgent(generate_random_user_agent())
        try:
            await self.page.goto(url, timeout=10000)  # Set timeout to 10000 milliseconds (10 seconds)
        except pyppeteer.errors.TimeoutError:
            print(f"Navigation to {url} failed due to timeout. Continuing...")
            return  
        await asyncio.sleep(random.uniform(1, 3))
        
        contact_info = await self.page.evaluate('''() => {
            let info = {};
            let lis = Array.from(document.querySelectorAll('li'));
            let spans = Array.from(document.querySelectorAll('span'));
            let headerDivs = Array.from(document.querySelectorAll('header div'));
            
            lis.forEach(li => {
                if (['main', 'sales', 'service', 'parts', 'body shop'].some(word => li.className.toLowerCase().includes(word))) {
                    let [number_type, number] = li.textContent.split(':');
                    info[number_type.trim()] = number.trim();
                }
            });
            headerDivs.forEach(div => {
                if (div.className.toLowerCase().includes('info')) {
                    let addressText = div.textContent.trim();
                    if (/.*\d{5}$/.test(addressText)) {
                        addressText = addressText.replace(/\s+/g, ' ');
                        info['location'] = addressText;
                    }
                }
            });
            if (!info['location']) {
                spans.forEach(span => {
                    if (span.className.toLowerCase().includes('location')) {
                        info['location'] = span.textContent.trim().replace(/\s+/g, ' ');
                    }
                    else if (span.className.toLowerCase().includes('address')) {
                        let addressSpan = span.querySelector('a');
                        if (addressSpan) {
                            info['location'] = addressSpan.textContent.trim().replace(/\s+/g, ' ');
                        } else {
                            info['location'] = span.textContent.trim().replace(/\s+/g, ' ');
                        }
                    }
                })
            };
            
            return info;
        }''')
        # when at least two pieces of info were found, save the data
        if len(contact_info) > 2:
            contact_info['website'] = urlparse(url).scheme + "://" + urlparse(url).netloc
            existing_data = []
            existing_data_dict = {}
            try:
                with jsonlines.open('dealer_contact.jsonl', mode='r') as file:
                    for line in file:
                        existing_data.append(line)
                        if 'website' in line:
                            existing_data_dict[line['website']] = line
            except FileNotFoundError:
                pass  

            if contact_info['website'] in existing_data_dict:
                existing_line = existing_data_dict[contact_info['website']]
                existing_line.update(contact_info)  # Update the line with new contact info
            else:
                existing_data.append(contact_info)

            with jsonlines.open('dealer_contact.jsonl', mode='w') as writer:
                writer.write_all(existing_data)
    async def parse_car_archive(self, url, condition:str = None, on_page = False):
        if not on_page:
            await self.page.setUserAgent(generate_random_user_agent())
            try:
                await self.page.goto(url, timeout=10000)  # Set timeout to 10000 milliseconds (10 seconds)
            except pyppeteer.errors.TimeoutError:
                print(f"Navigation to {url} failed due to timeout. Continuing...")
                return  
            await asyncio.sleep(random.uniform(2, 5))
        # html_content = await self.page.content()
        # with open('page.html', 'w', encoding='utf-8') as f:
        #     f.write(html_content)

        data_list = []
        div_elements = await self.page.querySelectorAll('div')
        for div_element in div_elements:
            # Get all attribute names of div_element
            attributes = await self.get_all_attributes(div_element)
            vin = img_src = year = model = make = name = price = href = trim = stock = fueltype = type = None
            vin = await self.check_attribute_name(attributes, ['vin'])
            year = await self.check_attribute_name(attributes, ['year'])
            model = await self.check_attribute_name(attributes, ['model'])
            make = await self.check_attribute_name(attributes, ['make'])
            name = await self.check_attribute_name(attributes, ['name'])
            price = await self.check_attribute_name(attributes, ['price'])
            trim = await self.check_attribute_name(attributes, ['trim'])
            fueltype = await self.check_attribute_name(attributes, ['fuel'])
            non_empty_count = sum(bool(attr) for attr in [vin, year, model, make, name, price])
            if non_empty_count >=3: 
                if vin and vin not in self.crawled_vins:  # If VIN found and it's new
                    print(f'vin - {vin} found')
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
                            'trim': trim,
                            'fueltype': fueltype,
                            'href': href
                        }
                        data_list.append(data)
            else:
                vehicle_data_json = await self.check_attribute_name(attributes, ['data-vehicle'])
                if vehicle_data_json is not None:
                    try:
                        vehicle_data = json.loads(vehicle_data_json)
                    except json.JSONDecodeError as e:
                        print(f"{vehicle_data_json} value stored in vehicle-data is not a json. Error: {e}")
                        continue
                    vin = vehicle_data.get('vin', None)
                    if vin and vin not in self.crawled_vins:
                        print(f'vin - {vin} found')
                        self.crawled_vins.add(vin)
                        href = await self.get_attribute_from_sub_element(div_element, 'a', 'href')
                        img_src = await self.get_attribute_from_sub_element(div_element, 'img', 'src')
                        make = vehicle_data.get('make', None)
                        stock = vehicle_data.get('stock', None)
                        fueltype = vehicle_data.get('fueltype', None)
                        type = vehicle_data.get('type', None)
                        year = vehicle_data.get('year', None)
                        model = vehicle_data.get('model', None)
                        trim = vehicle_data.get('trim', None)
                        price = vehicle_data.get('price', None)
                        if img_src:
                            img_src = urljoin(url, img_src)
                        if model or make or name or price:  # Any of these attributes is enough
                            data = {
                                'website': urlparse(url).scheme + "://" + urlparse(url).netloc,
                                'vin': vin,
                                'img_src': img_src,
                                'year': year,
                                'model': model,
                                'make': make,
                                'name': name,
                                'price': price,
                                'stock': stock,
                                'fueltype': fueltype,
                                'type': type,
                                'trim': trim,
                                'href': href
                            }
                        data_list.append(data)

        with jsonlines.open(f'{condition}_car_info.jsonl', mode='a') as writer:
            writer.write_all(data_list)

        navigated = await self.navigate_next_page()
        if navigated:
            await self.parse_car(url, condition, True)  # Recursively call parse_car() if navigated to the next page
    async def parse_car(self, url, condition:str = None, on_page = False):
        if not on_page:
            await self.page.setUserAgent(generate_random_user_agent())
            try:
                await self.page.goto(url, timeout=10000)  # Set timeout to 10000 milliseconds (10 seconds)
            except pyppeteer.errors.TimeoutError:
                print(f"Navigation to {url} failed due to timeout. Continuing...")
                return  
            await asyncio.sleep(random.uniform(2, 5))

        data_list = []
        try:
            div_elements = await self.page.querySelectorAll('div')
        except pyppeteer.errors.NetworkError:
            print("Navigation occurred before the operation could complete. Skipping current operation and continuing...")
            try:
                div_elements = await self.page.querySelectorAll('div')  
            except pyppeteer.errors.NetworkError:
                print("Navigation occurred before the operation could complete. Skipping current operation and continuing...")
                return
        for div_element in div_elements:
            # Get all attribute names of div_element
            attributes = await self.get_all_attributes(div_element)
            
            vehicle_data_json = await self.check_attribute_name(attributes, ['data-vehicle'])
            vehicle_data = None
            if vehicle_data_json is not None:
                try:
                    vehicle_data = json.loads(vehicle_data_json)
                except json.JSONDecodeError as e:
                    # print(f"{vehicle_data_json} value stored in vehicle-data is not a json. Error: {e}")
                    print(f"Value stored in vehicle-data is not a json. Error: {e}")
            # vehicle_data is the json stored and atrieved from the attribute
            if vehicle_data is not None:
                vin = vehicle_data.get('vin', None)
                if vin and vin not in self.crawled_vins:
                    print(f'vin - {vin} found')
                    self.crawled_vins.add(vin)
                    href = await self.get_attribute_from_sub_element(div_element, 'a', 'href')
                    img_src = await self.get_attribute_from_sub_element(div_element, 'img', 'src')
                    make = vehicle_data.get('make', None)
                    stock = vehicle_data.get('stock', None)
                    fueltype = vehicle_data.get('fueltype', None)
                    type = vehicle_data.get('type', None)
                    year = vehicle_data.get('year', None)
                    model = vehicle_data.get('model', None)
                    trim = vehicle_data.get('trim', None)
                    price = vehicle_data.get('price', None)
                    if img_src:
                        img_src = urljoin(url, img_src)
                    if model or make or name or price:  # Any of these attributes is enough
                        data = {
                            'website': urlparse(url).scheme + "://" + urlparse(url).netloc,
                            'vin': vin,
                            'img_src': img_src,
                            'year': year,
                            'model': model,
                            'make': make,
                            'name': name,
                            'price': price,
                            'stock': stock,
                            'fueltype': fueltype,
                            'type': type,
                            'trim': trim,
                            'href': href
                        }
                    data_list.append(data)
            else:
                vin = img_src = year = model = make = name = price = href = trim = stock = fueltype = type = None
                vin = await self.check_attribute_name(attributes, ['vin'])
                year = await self.check_attribute_name(attributes, ['year'])
                model = await self.check_attribute_name(attributes, ['model'])
                make = await self.check_attribute_name(attributes, ['make'])
                name = await self.check_attribute_name(attributes, ['name'])
                price = await self.check_attribute_name(attributes, ['price'])
                trim = await self.check_attribute_name(attributes, ['trim'])
                fueltype = await self.check_attribute_name(attributes, ['fuel'])
                non_empty_count = sum(bool(attr) for attr in [vin, year, model, make, name, price])
                if non_empty_count >=3: 
                    if vin and vin not in self.crawled_vins:  # If VIN found and it's new
                        print(f'vin - {vin} found')
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
                                'trim': trim,
                                'fueltype': fueltype,
                                'href': href
                            }
                            data_list.append(data)

        with jsonlines.open(f'{condition}_car_info.jsonl', mode='a') as writer:
            writer.write_all(data_list)

        navigated = await self.navigate_next_page()
        if navigated:
            await self.parse_car(url, condition, True)
            
    async def start(self):
        # self.browser = await launch(headless=True)
        self.browser = await launch(headless=False)
        self.page = await self.browser.newPage()
        
        for url in self.start_urls:
            await self.navigate(url)

        # Save crawled_vins to file
        with open('crawled_vins.txt', 'w') as file:
            for vin in self.crawled_vins:
                file.write(vin + '\n')

        await self.browser.close()


start_urls = [
# 'https://www.beavertonhonda.com/',
# 'https://www.toyotaofcorvallis.com/',
# 'https://www.mercedesbenzbeaverton.com/',
# 'https://www.zeiglernissanoforlandpark.com/',
# 'https://www.kiefermazda.com/',
# 'https://www.northhollywoodtoyota.com/',

# 'https://www.mypowerhonda.com/',
'https://www.carltonmb.com/', # take long to to navigate url/?model=xxxmake=xxx
'https://www.greshamtoyota.com/',
'https://www.vancouvertoyota.com/',
'https://www.bmwofslo.com/',

# 'https://www.malonetoyota.com/', # take long to to navigate url/?year=xxxmake=xxx			
# 'https://www.mercedesbenzofbellevue.com/', ## take long to to navigate url/?year=xxxmake=xxx # older browser

# 'https://www.tonkinwilsonvillenissan.com/', # data-vehicle issue, navigated to irs
# 'https://www.claremonttoyota.com/', # nothing is parsed

# 'https://www.mbscottsdale.com/', # nothing is parsed
# 'https://www.jpauleytoyota.com/', # nothing is parsed

# 'https://www.siamaks.com/', # nothing is parsed
# 'https://www.prestigeautopdx.com/', # nothing is parsed

# 'https://www.foxtoyotaofelpaso.com/', # Error: vin = vehicle_data.get('vin', None) AttributeError: 'int' object has no attribute 'get'
# 'https://www.marianoriverahonda.com/', # new match news

# 'https://www.dublinnissan.com/', 
# 'https://www.crestmontcadillac.com/' # nothing is parsed
            
]
# There is a must to accept cookies
crawler = MyCrawler(start_urls)
asyncio.run(crawler.start())
