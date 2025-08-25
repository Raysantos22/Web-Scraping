import random
import requests
from parsel import Selector
import csv
from datetime import date
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time

today = date.today().strftime('%Y%m%d')

# with open(f'temu_long_eta_{today}.csv', 'w', newline='', encoding='utf8') as f:
#     writer = csv.writer(f)
#     writer.writerow(['sku', 'free_delivery_eta', 'fastest_delivery_eta', 'delivery_provider', 'scrape_date'])

def start_requests():
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
    # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    # "Accept-Language": "en-US,en;q=0.5",
    # "Accept-Encoding": "gzip, deflate, br, zstd",
    # "Alt-Used": "www.amazon.com.au",
    # "Connection": "keep-alive",
    # "Cookie": "session-id=357-1590114-9512065; session-id-time=2082787201l; i18n-prefs=AUD; csm-hit=tb:5HK74SQR4GTD0AF2C6KX+s-R08XHRA2B9KDNFDMD62Y|1750815698258&t:1750815698258&adb:adblk_no; ubid-acbau=355-3973666-7178701; lc-acbau=en_AU; x-acbau=VoGe5PQhhkRDF2aGnyjSmWSRhpB1s70v0OCM4CxbfNMhRheNdexMU9LePyV22pt8; at-acbau=Atza|IwEBIB75zXov0oM2R4RtEiTvqq7ZQWnb_A4RNzUCDXx87pjttQszi_X0W2cF6rDjtpXroTPWVKDR0Pp63fAVghPQq3wC3x5C41Z9HzyQD5iWjJcNgGQ_IvjWE9hDNUxqA8BC0vMdfmG-oRCACVSkvVMKF_jban-bdPJuL_qgyombdwmccwNtACTtQbuSgi7-jvh2pew1kkFT1ZXGCTPqeISKVmdOAqUYCvDidMuAUzSTKhIWmWmWKvI1XFbyhdymsbTMmmivACcHurio7R9yss-Vicb8yozfRrV02h69uPt2tUsFkA; sess-at-acbau=\"8wGJBFwqSG5YHJqpRflV+C8PvCNgl0bByMdIzm4Rths=\"; sst-acbau=Sst1|PQHoa6rh0v1fgk2YYDYNf2kiCUi5mMJXyWzgX_S5LjiihX4ik31VVeoUgQ2LMSJV3TWo_3fKB3t2Ue1tCGzBHZhJYzg8qn3c3zlQ713oXEcsIcloXOST4ePynt233OSnKyOC-N_Dg835yj71vrxOHRNWiwtZUwtb0FMikC9aox7cM1BoWNLvU1CjAXqDSVm651O9Jz7CAyqhA0JBt6udd7PeIRliF1faOoAeZsQJuHDpTyFor-SaaoobU8LgCjb2VNio20q-_5yjdDzWv8jlxzKXoDXT4KEEiIuKqGgWwjge6vA; sid=\"XOdYOmal+lQu+zLAsFjODw==|ALi9b/Focn14uCDHrQWHPvvSEogTb9Tb7iv8cESUWSI=\"; ph_phc_tGCcl9SINhy3N0zy98fdlWrc1ppQ67KJ8pZMzVZOECH_posthog={\"distinct_id\":\"amzn1.account.ocid.A1MB91EOM8XDDZ\",\"$sesid\":[1747642014940,\"0196e794-dcdc-74aa-b56e-de87659a2ce5\",1747642014940],\"$epp\":true}; session-token=\"y2oSFINZ4I80/+aMFZHs6AbVAw1vBHscBEY8EpMllhU0rVHhFQ1B/dEX2ttp1OA25cMWE7+aN32P+EGtU8F7qZ3dv/5H971yZJTg5qGDFRwCWfRyhBba5fwrZweBy8vH2C37YTRnhG3rm/AJBTmWEIommPVKU3059+29770a8NJGKIETD5EkAHRj/wfTN5zwhBcGiT/qEk2enhYwtpzntI/If/yqAn0pvgJU5UghQa98og+MrTPIp/FSwuMBxIuJ4MXsE6f+X/4ipQHxUERINdaMWVGGe0Y4yQx0oIgrPuJ+GFHp7jbq7aOfKKeja0MoyXQLXX6IK7pr5xKcoo8GxbXrsfLWbnHRkfrt9Ktv3FZmwZoOrFa3nu0VNdUmu/H5vxPZAhouAbw=\"",
    # "Upgrade-Insecure-Requests": "1",
    # "Sec-Fetch-Dest": "document",
    # "Sec-Fetch-Mode": "navigate",
    # "Sec-Fetch-Site": "none",
    # "Sec-Fetch-User": "?1",
    # "Priority": "u=0, i",
    # "TE": "trailers"
    }

    proxy_user = 'amazonemega'
    proxy_pass = 'VQd40aV1joC7rizcab'
    proxy_host = 'au.decodo.com'
    proxy_port = '30000'

    proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

    # HTTP or HTTPS proxy (example)
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    session = requests.Session()
    session.headers.update(headers)
    session.proxies.update(proxies)
    return session
 
def start_scrape(to_check):
    session = start_requests()
    print(len(to_check))
    for sku in to_check:
        try:
            url = f"https://www.amazon.com.au/dp/{sku}?th=1&rh=p_n_shipping_option-bin%3A3242350011B0CBLQQQTZ"
            response = session.get(url)
            # print(response.text)c:\Users\MochF\Downloads\20250805.zip
            if response.status_code == 200:
                selector = Selector(text=response.text)
                # Extract the title of the page
                free_delivery_eta = (selector.xpath('//*[@data-csa-c-delivery-price="FREE"]/span/text()').get() or '').strip().replace('"', '')
                fastest_delivery_eta = (selector.xpath('//*[@data-csa-c-delivery-price="fastest"]/span/text()').get() or '').strip()

                # delivery_to = selector.xpath('//*[@id="contextualIngressPtLabel_deliveryShortLine"]/span/text()').getall() or ''
                # if len(delivery_to) > 1:
                #     delivery_to = delivery_to[1].strip()
                # else:
                #     delivery_to = delivery_to[0].strip() if delivery_to else ''
                # print(delivery_to)

                delivery_provider = selector.xpath('//*[@data-csa-c-content-id="desktop-fulfiller-info"]/div/span[contains(@class, "offer-display-feature-text-message")]/text()').get() or ''

                # print(f"Free Delivery ETA: {free_delivery_eta}")
                # print(f"Fastest Delivery ETA: {fastest_delivery_eta}")
                # print(f"Delivery Provider: {delivery_provider}")

                with open(f'temu_long_eta_{today}.csv', 'a', newline='', encoding='utf8') as f:
                    writer = csv.writer(f)
                    writer.writerow([sku, free_delivery_eta, fastest_delivery_eta, delivery_provider, today])

                print(f"Processed SKU: {sku}")
            else:
                print(f"Failed to retrieve data for SKU: {sku}, Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error processing SKU {sku}: {e}")
            with open(f'temu_long_eta_{today}.csv', 'a', newline='', encoding='utf8') as f:
                writer = csv.writer(f)
                writer.writerow([sku, '', '', '', today])

        time.sleep(random.uniform(2, 3))  # Sleep to avoid hitting the server too hard
    
if __name__ == "__main__":
    df = pd.read_csv('temu_to_check_20250805.csv', encoding='utf8')
    to_check = df['SKU'].tolist()
    to_check = to_check[421:]
    # to_check = [to_check]
    print(f"Total SKUs to check: {len(to_check)}")

    print(len(to_check))

    num_threads = 1
    chunk_size = len(to_check) // num_threads + 1
    sku_chunks = [to_check[i:i + chunk_size] for i in range(0, len(to_check), chunk_size)]

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(start_scrape, sku_chunks)