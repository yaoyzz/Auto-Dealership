import asyncio
from pyppeteer import launch

async def get_attribute_from_sub_element(page, element, sub_element_tag, attribute_name):
    sub_element = await page.querySelector(sub_element_tag)
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

    div_element = await page.querySelector('div')
    href = await get_attribute_from_sub_element(page, div_element, 'a', 'href')

    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
