from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.linextractors import LinkExtractor


class CrawlingSpider(CrawlSpider):
    name = "spider_beavertontoyota"
    start_urls = ['https://www.beavertontoyota.com/']

    def parse(self, response):
        logo_url = response.xpath('/html/body/div[1]/header/div/div[1]/div[1]/ul/li[2]/a/img/@src').get()
        yield {
            'logo_url': logo_url
        }
        