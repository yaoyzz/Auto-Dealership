import asyncio
import json
import jsonlines
from pyppeteer import launch
from urllib.parse import urljoin, urlparse
import re

def check_attribute_name(attributes, names):
    for attr in attributes:
        for name in names:
            if name in attr.lower():
                return attributes[attr]
    return None

async def get_all_attributes(page, element):
    attributes = await page.evaluate('(element) => { let attrs = {}; for(let i=0; i<element.attributes.length; i++) { let attr = element.attributes[i]; attrs[attr.name] = attr.value; }; return attrs; }', element)
    print(attributes)
    return attributes

async def get_attribute_from_sub_element(page, element, sub_element_tag, attribute_name):
    sub_element = await element.querySelector(sub_element_tag)
    if sub_element:
        attribute_value = await page.evaluate(f'(element) => element.getAttribute("{attribute_name}")', sub_element)
        return attribute_value
    else:
        return None

async def parse_car(page, url):
    await page.goto(url)
    h1_element = await page.querySelector('h1')
    if h1_element:
        text = await page.evaluate('(element) => element.textContent', h1_element)
        print(text)

    data_list = []
    div_elements = await page.querySelectorAll('div')

    for div_element in div_elements:
        # Get all attribute names of div_element
        attributes = await get_all_attributes(page, div_element)
        vin = img_src = year = model = make = name = price = href = trim = stock = fueltype = type = None
        vin = check_attribute_name(attributes, ['vin'])
        year = check_attribute_name(attributes, ['year'])
        model = check_attribute_name(attributes, ['model'])
        make = check_attribute_name(attributes, ['make'])
        name = check_attribute_name(attributes, ['name'])
        price = check_attribute_name(attributes, ['price'])

        if vin:  # If VIN found, get href and img_src
            href = await get_attribute_from_sub_element(page, div_element, 'a', 'href')
            img_src = await get_attribute_from_sub_element(page, div_element, 'img', 'src')
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
                    'href': href
                }
                print(f"Crawled car with vin: {vin}")
                data_list.append(data)
        
        non_empty_count = sum(bool(attr) for attr in [vin, img_src, model, make, name, price])
        if non_empty_count < 3:
            vehicle_data_json = check_attribute_name('data-vehicle', ['vin'])
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

                href = await get_attribute_from_sub_element(page, div_element, 'a', 'href')
                img_src = await get_attribute_from_sub_element(page, div_element, 'img', 'src')
                if vin:  # If VIN found, get href and img_src
                    href = await get_attribute_from_sub_element(page, div_element, 'a', 'href')
                    img_src = await get_attribute_from_sub_element(page, div_element, 'img', 'src')
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
                            'href': href
                        }
                        print(f"Crawled car with vin: {vin}")
                        data_list.append(data)
    
    return data_list

async def main():
    start_urls = ['https://www.zeiglernissanoforlandpark.com/new-vehicles/']  # List of start urls
    crawled_vins = set()
    browser = await launch()
    page = await browser.newPage()

    with jsonlines.open('output.jsonl', mode='w') as writer:
        for url in start_urls:
            data_list = await parse_car(page, url)
            for data in data_list:
                if data['vin'] not in crawled_vins:
                    crawled_vins.add(data['vin'])
                    writer.write(data)
            
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
