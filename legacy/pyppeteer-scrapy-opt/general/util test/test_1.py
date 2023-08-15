import asyncio
from pyppeteer import launch
from urllib.parse import urljoin

async def get_all_attributes(page, element):
    attributes = await page.evaluate('(element) => { let attrs = {}; for(let i=0; i<element.attributes.length; i++) { let attr = element.attributes[i]; attrs[attr.name] = attr.value; }; return attrs; }', element)
    print(attributes)
    return attributes

async def get_attribute_from_sub_element(page, element, sub_element_tag, attribute_name):
    sub_element = await element.querySelector(sub_element_tag)
    if sub_element:
        attribute_value = await page.evaluate(f'(element) => element.getAttribute("{attribute_name}")', sub_element)
        print(attribute_value)
        return attribute_value
    else:
        print(None)
        return None


async def main():
    browser = await launch()
    page = await browser.newPage()
    await page.goto('https://www.beavertontoyota.com/searchnew.aspx')

    div_element = await page.querySelector('div.vehicle-card')
    attributes = await get_all_attributes(page, div_element)

    href = await get_attribute_from_sub_element(page, div_element, 'a', 'href')
    img_src = await get_attribute_from_sub_element(page, div_element, 'img', 'src')

    # Use urljoin to combine the base URL with the extracted href and img_src (if they exist)
    if href:
        href = urljoin('https://www.beavertontoyota.com', href)
        print(f'Full href: {href}')
    if img_src:
        img_src = urljoin('https://www.beavertontoyota.com', img_src)
        print(f'Full img_src: {img_src}')

    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
