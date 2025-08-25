from parsel import Selector
import csv
from concurrent.futures import ThreadPoolExecutor
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
from selenium.webdriver.chrome.service import Service
import logging
import time

d = date.today().strftime('%Y%m%d')

def driver_setup():
    options = ChromeOptions()

    # Set up the WebDriver
    # service = Service(ChromeDriverManager().install())
    service = Service()
    options.add_argument("--headless")  # Enable headless mode
    options.add_argument("--disable-gpu")
    driver = Chrome(service=service, options=options)

    # Enable network tracking to be able to modify headers
    driver.execute_cdp_cmd('Network.enable', {})

    headers = {
        'Cookie': 'session-id=357-1590114-9512065; session-id-time=2082787201l; i18n-prefs=AUD; csm-hit=tb:R1J5DFW499CN3ST63XPJ+s-R1J5DFW499CN3ST63XPJ|1736097268168&t:1736097268168&adb:adblk_no; ubid-acbau=355-3973666-7178701; lc-acbau=en_AU; session-token="w87V+6F2Gep/TjAVJxbcM0p2e9ZDvRnsLqA+2+hSrP04Zw2IHwAWjosOVBWvNHwNW8IfKDYHjF3uuFpfqtl0V6PQrun234vGqCBPcLsIkY34ZK6PaIX93z6jUF1I82gUVtoHtv+Y5ujN3P/WTxKpZBElGC/jxWEX2jiinWeI138owQIDda4vZIIwVYycb2hiF1JEGlhApPlbb8mqqphuxBtJcxu/8xPugenwQ27JEuiPp0VBSTHU9nB1IfomsotykuY2LUMSQV+iKUUodhd3KsPuV8P2A0anVIL5rxAyCPkaf+msqBNHJdypjHExXNvIvuBX4TBFeH7nuqzmXI+ukFclLTdr+Lj3oRglkpGC11s="',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    # def set_custom_headers(headers):
    #     for header in headers:
    #         driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': headers})

    # set_custom_headers(headers)

    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {"headers": headers})

    return driver

def get_subcat(urls, driver):
    for url in urls:
        cat_name = url[0]
        url = url[1]
        driver.get(url)

        response = Selector(driver.page_source)
        subcats = response.xpath('//ul[@role="group"]/li/span/a/@href').getall()
        print(subcats)
        for subcat in subcats:
            url = f"https://www.amazon.com.au{subcat}"
            get_subsubcat(url, driver, cat_name)
        
def get_subsubcat(url, driver, cat_name):
    driver.get(url)

    response = Selector(driver.page_source)
    subsubcats = response.xpath('//ul[@role="group"]/li/span/a/@href').getall()
    for subsubcat in subsubcats:
        url = f"https://www.amazon.com.au{subsubcat}"
        get_details(url, driver, cat_name)

def get_details(url, driver, cat_name):
    driver.get(url)
    try:

        more = True
        while more == True:
            cards = driver.find_elements(By.XPATH, '//ol[contains(@class, "p13n-gridRow")]/li')
            total = len(cards)
            print(total)
            # print('a')
            # for i in cards:
            #     print(i)
            # wait = WebDriverWait(driver, 5)
            # wait.until(EC.element_to_be_clickable((By.XPATH, '//li[@class="a-last"]')))
            # time.sleep(1.5)

            # wait = WebDriverWait(driver, 10)  # 10 seconds timeout
            # last_card = wait.until(EC.visibility_of_element_located((By.XPATH, '//ol[contains(@class, "p13n-gridRow")]/li[last()]')))
            # # last_card = driver.find_elements(By.XPATH, '//ol[contains(@class, "p13n-gridRow")]/li')
            # # last_card = last_card[-1]
            # print(f'last card: {last_card}')

            # driver.execute_script("arguments[0].scrollIntoView(true);", last_card)
            # actions = ActionChains(driver)
            # actions.move_to_element(last_card).perform()
            # print('action done')

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # wait = WebDriverWait(driver, 10)
            # wait.until(EC.element_to_be_clickable((By.XPATH, '//ol[contains(@class, "p13n-gridRow")]/li')))
            time.sleep(2.5)
            cards = driver.find_elements(By.XPATH, '//ol[contains(@class, "p13n-gridRow")]/li')
            new_total = len(cards)
            print(new_total)
    
            if total == new_total:
                more = False

        # time.sleep(50)

        response = Selector(driver.page_source)
        asin = response.xpath('//ol[contains(@class, "p13n-gridRow")]/li/span/div/div/div/@data-asin').getall()

        for sku in asin:
            with open(f'best_seller_{cat_name}_{d}.csv', 'a', newline='', encoding='utf8', errors='ignore') as f:
            # with open(f'test.csv', 'a', newline='', encoding='utf8', errors='ignore') as f:
                writer = csv.writer(f)
                writer.writerow([sku])

        next_page = response.xpath('//ul/li[@class="a-last"]/a/@href').get()
        if next_page is not None:
            next_url = f"https://www.amazon.com.au{next_page}"

            get_details(next_url, driver, cat_name)
    except Exception as e:
        logging.error("Selenium Error: %s", e)

# url = "https://www.amazon.com.au/gp/bestsellers/home/ref=zg_bs_home_sm"
url_list = [
    # ['device_and_accessories', 'https://www.amazon.com.au/gp/bestsellers/amazon-devices/ref=zg_bs_nav_amazon-devices_0'],
    # ['amazon_launchpad', 'https://www.amazon.com.au/gp/bestsellers/boost/ref=zg_bs_nav_boost_0'],
    # ['amazon_renewed', 'https://www.amazon.com.au/gp/bestsellers/amazon-renewed/ref=zg_bs_nav_amazon-renewed_0'],
    # ['Apps_and_games', 'https://www.amazon.com.au/gp/bestsellers/mobile-apps/ref=zg_bs_nav_mobile-apps_0'], 
    # ['Audible_books','https://www.amazon.com.au/gp/bestsellers/audible/ref=zg_bs_nav_audible_0'],
    # ['Automotive', 'https://www.amazon.com.au/gp/bestsellers/automotive/ref=zg_bs_nav_automotive_0'],
    ['Baby', 'https://www.amazon.com.au/gp/bestsellers/baby-products/ref=zg_bs_nav_baby-products_0'], 
    ['Beauty', 'https://www.amazon.com.au/gp/bestsellers/beauty/ref=zg_bs_nav_beauty_0'],
    ['Books', 'https://www.amazon.com.au/gp/bestsellers/books/ref=zg_bs_nav_books_0'],
    ['Clothing_shoes_accesories', 'https://www.amazon.com.au/gp/bestsellers/fashion/ref=zg_bs_nav_fashion_0'], 
    ['Computers', 'https://www.amazon.com.au/gp/bestsellers/computers/ref=zg_bs_nav_computers_0'], 
    ['Electronics', 'https://www.amazon.com.au/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0'],
    ['Garden', 'https://www.amazon.com.au/gp/bestsellers/garden/ref=zg_bs_nav_garden_0'],
    ['Gift_Cards', 'https://www.amazon.com.au/gp/bestsellers/gift-cards/ref=zg_bs_nav_gift-cards_0'], 
    ['Health_household_personal_care', 'https://www.amazon.com.au/gp/bestsellers/health/ref=zg_bs_nav_health_0'],
    ['Home', 'https://www.amazon.com.au/gp/bestsellers/home/ref=zg_bs_nav_home_0'],
    ['Home_improvement', 'https://www.amazon.com.au/gp/bestsellers/home-improvement/ref=zg_bs_nav_home-improvement_0'],
    ['Kindle_store', 'https://www.amazon.com.au/gp/bestsellers/digital-text/ref=zg_bs_nav_digital-text_0'],
    ['Kitchen_and_dining', 'https://www.amazon.com.au/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0'],
    ['Lighting', 'https://www.amazon.com.au/gp/bestsellers/lighting/ref=zg_bs_nav_lighting_0'],
    ['Movies_and_tv', 'https://www.amazon.com.au/gp/bestsellers/movies-and-tv/ref=zg_bs_nav_movies-and-tv_0'],
    ['Music', 'https://www.amazon.com.au/gp/bestsellers/music/ref=zg_bs_nav_music_0'],
    ['Musical_intruments', 'https://www.amazon.com.au/gp/bestsellers/musical-instruments/ref=zg_bs_nav_musical-instruments_0'],
    ['Pantry_food_and_drinks', 'https://www.amazon.com.au/gp/bestsellers/grocery/ref=zg_bs_nav_grocery_0'],
    ['Pet_supplies', 'https://www.amazon.com.au/gp/bestsellers/pet-supplies/ref=zg_bs_nav_pet-supplies_0'], 
    ['Software', 'https://www.amazon.com.au/gp/bestsellers/software/ref=zg_bs_nav_software_0'], 
    ['Sports_fitness_outdoors', 'https://www.amazon.com.au/gp/bestsellers/sporting-goods/ref=zg_bs_nav_sporting-goods_0'],
    ['stationary_and_office', 'https://www.amazon.com.au/gp/bestsellers/office-products/ref=zg_bs_nav_office-products_0'],
    ['toys_and_games', 'https://www.amazon.com.au/gp/bestsellers/toys/ref=zg_bs_nav_toys_0'],
    ['Video_games', 'https://www.amazon.com.au/gp/bestsellers/videogames/ref=zg_bs_nav_videogames_0']
]

num_of_threads = 3

new_url_list = []
steps = len(url_list) // num_of_threads
for i in range(0,len(url_list),steps):
    sub_url_list = url_list[i:i+steps] if i+steps < len(url_list) else url_list[i:]
    new_url_list.append(sub_url_list)

print(len(url_list))
print(steps)
print(len(new_url_list))

drivers = [driver_setup() for _ in range(num_of_threads)]

with ThreadPoolExecutor(max_workers=num_of_threads) as executor:
    executor.map(get_subcat, new_url_list, drivers)

# for [cat_name, url] in cats:
#     with open(f'best_seller_{cat_name}.csv', 'a', newline='', encoding='utf8', errors='ignore') as f:
#         writer = csv.writer(f)
#         writer.writerow(['sku'])
#     get_details(url, driver_setup(), cat_name)