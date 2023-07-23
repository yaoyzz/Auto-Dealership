import json
import asyncio
from pyppeteer import launch

class MyClass:
    async def parse_test(self, response, page):
        await page.goto(response['test'])  # Here's the modification

        # Wait for the element to be visible
        await page.waitForXPath('/html/body/div[2]/section/div[4]/div[2]/div[1]/h3')

        # Note: The response.xpath line has been commented out as it's unclear what it does.
        # test1 = await response.xpath('/html/body/div[2]/div[2]/a/div/div/div/h3/text()')
        test2_element = await page.xpath('/html/body/div[2]/div[2]/a/div/div/div/h3')
        test2 = await page.evaluate('(element) => element.textContent', test2_element[0])
        test3_element = await page.xpath('/html/body/div[2]/section/div[4]/div[2]/div[1]/h3')
        test3 = await page.evaluate('(element) => element.textContent', test3_element[0])

        data = {
            'test2': test2,
            'test3': test3
        }

        filename = 'test.json'

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)



# Example usage
response = {
            'test': 'https://www.beavertontoyota.com/searchnew.aspx',
        }
obj = MyClass()

async def main():
    browser = await launch(headless=True)
    page = await browser.newPage()
    await obj.parse_test(response, page)
    await browser.close()

# Set up asyncio event loop
loop = asyncio.get_event_loop()
# Schedule your async function to run on the event loop
loop.run_until_complete(main())
