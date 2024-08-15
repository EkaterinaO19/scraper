import random
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

base_url = 'https://vkusvill.ru'
categories_url = f'{base_url}/goods/'  # Adjust as needed to reach the categories list

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x86) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15',
]

def get_random_headers():
    return {
        'User-Agent': random.choice(user_agents)
    }

def scrape_page(url):
    headers = get_random_headers()
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    image_urls = []
    names = []
    prices = []
    weights = []

    for product in soup.find_all('div', class_='ProductCard__content'):
        img_tag = product.find('img', class_='ProductCard__imageImg')
        img_src = img_tag.get('src') if img_tag else 'No image'
        image_urls.append(img_src)

        name_tag = product.find('a',
                                class_='ProductCard__link rtext _desktop-md _mobile-sm gray900 js-datalayer-catalog-list-name')
        name = name_tag.text.strip() if name_tag else 'No name'
        names.append(name)

        price_tag = product.find('span', class_='js-datalayer-catalog-list-price hidden')
        price = price_tag.text.strip() if price_tag else 'No price'
        prices.append(price)

        weight_tag = product.find('div', class_='ProductCard__weight')
        weight = weight_tag.get_text(strip=True) if weight_tag else 'No weight'
        weights.append(weight)

    return pd.DataFrame({
        'Image URL': image_urls,
        'Name': names,
        'Price': prices,
        'Weight': weights
    })

def get_max_pages(soup):
    pagination = soup.find('div', class_='VV_Pager')
    if pagination:
        page_links = pagination.find_all('a', href=True)
        page_numbers = [int(link.get('href').split('PAGEN_1=')[-1]) for link in page_links if
                        'PAGEN_1=' in link.get('href')]
        return max(page_numbers, default=1)
    return 1

def scrape_category(category_url):
    headers = get_random_headers()
    initial_response = requests.get(category_url, headers=headers)
    initial_soup = BeautifulSoup(initial_response.content, 'html.parser')
    max_pages = get_max_pages(initial_soup)

    category_data = pd.DataFrame()

    for page in range(1, max_pages + 1):
        page_url = f"{category_url}?PAGEN_1={page}"
        headers = get_random_headers()  # Rotate the User-Agent for each page request
        try:
            page_data = scrape_page(page_url)
            category_data = pd.concat([category_data, page_data], ignore_index=True)
        except Exception as e:
            print(f"Error scraping {page_url}: {e}")

        temp_filename = f'temp_scraped_data_{int(time.time())}.xlsx'
        category_data.to_excel(temp_filename, index=False)

        time.sleep(1)  # To avoid overwhelming the server

    return category_data

def get_category_links(url):
    headers = get_random_headers()
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    category_links = {link.text.strip(): base_url + link.get('href') for link in
                      soup.find_all('a', class_='VVCatalog2020Menu__Link', href=True)}
    return category_links

category_links = get_category_links(categories_url)
all_data = {}

for category_name, link in category_links.items():
    print(f"Scraping category: {category_name}")
    try:
        category_data = scrape_category(link)
        all_data[category_name] = category_data
    except Exception as e:
        print(f"Error scraping category {category_name}: {e}")

output_file = 'scraped_data_by_category.xlsx'
with pd.ExcelWriter(output_file) as writer:
    for category_name, data in all_data.items():
        data.to_excel(writer, sheet_name=category_name, index=False)

print(f'All data has been scraped and saved to {output_file}')

