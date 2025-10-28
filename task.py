import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime

class RiversideSpider(scrapy.Spider):
    name = "riverside_simple"

    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-PK,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://epublic-access.riverside.courts.ca.gov/public-portal/?q=node/378",
    }

    cookies = {
        "has_js": "1",
        "SSESS5dcaf0b317a9ed2ebdfcbc4d2c83708b": "TZwJ0X9Z-di_d0Kze7CnWEfvhBmIb8pue3fkc2ZRZz8",
        "AWSALB": "EB8ShioGovKol9347HgvZKb7tGbSMuV9KGhlZrtki48rljclfMAu72Js0aXFPR1ch8x4VjOSow8oudUffkFO1PZ2XLJqOP1Ai7yv0lwn8btxo0FS2Jv1DhV4UzVt",
        "AWSALBCORS": "EB8ShioGovKol9347HgvZKb7tGbSMuV9KGhlZrtki48rljclfMAu72Js0aXFPR1ch8x4VjOSow8oudUffkFO1PZ2XLJqOP1Ai7yv0lwn8btxo0FS2Jv1DhV4UzVt",
    }

    def start_requests(self):
        url = "https://epublic-access.riverside.courts.ca.gov/public-portal/?q=node/385/3145926"
        yield scrapy.Request(
            url,
            headers=self.custom_headers,
            cookies=self.cookies,
            callback=self.parse_page,
            dont_filter=True
        )

    def parse_page(self, response):
        if any(x in response.text.lower() for x in ["captcha", "verify", "access denied"]):
            self.logger.warning("CAPTCHA restriction detected")
            return

        def clean_text(text):
            if text:
                return " ".join(text.split()).strip()
            return ""

        case_number = clean_text(response.xpath('//b[contains(text(),"PRMC")]/text()').get())
        filed_date_raw = response.xpath('//td[contains(text(), "/20")]/text()').get()
        filed_date = None
        if filed_date_raw:
            try:
                filed_date = datetime.strptime(filed_date_raw.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
            except ValueError:
                filed_date = filed_date_raw.strip()

        case_status = clean_text(response.xpath('//td[normalize-space(text())="Case Status:"]/following-sibling::td/text()').get())
        description = clean_text(response.xpath('//td[contains(text(),"Estate of:")]/text()').get())
        case_type = clean_text(response.xpath('//b[contains(text(),"Probate")]/text()').get())

        party_rows = response.xpath('(//table[contains(@id,"tree_table")])[1]/tbody/tr')
        party1_name = None
        party1_type = None
        party2_name = None
        party2_type = None

        for row in party_rows:
            name = clean_text("".join(row.xpath('./td[2]//text()').getall()))
            role = clean_text("".join(row.xpath('./td[3]//text()').getall()))

            if not name or role == "Judge":
                continue

            if not party1_name and role == "Decedent":
                party1_name = name
                party1_type = role
            elif not party2_name and role == "Administrator":
                party2_name = name
                party2_type = role

        result = {
            "Case Number": case_number,
            "Filed Date": filed_date,
            "Case Type": case_type,
            "Status": case_status,
            "Description": description,
            "Party1 Name": party1_name,
            "Party1 Type": party1_type,
            "Party2 Name": party2_name,
            "Party2 Type": party2_type,
        }

        print("Extracted Data:\n", result)
        yield result

if __name__ == "__main__":
    process = CrawlerProcess({
        "LOG_LEVEL": "INFO", 
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    })

    process.crawl(RiversideSpider)
    process.start()
