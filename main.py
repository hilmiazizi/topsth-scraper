import requests
import shelve
import json
import copy
from urllib.parse import quote
from datetime import date
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
import concurrent.futures


skus = []
def get_product_list(cat_data, pbar):
    cat_id = cat_data['cat_id']
    path = cat_data['path']
    page = 0
    products = []
    while True:
        headers = {
            'Host': 'l7mux9u4cp-dsn.algolia.net',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/619.25 (KHTML, like Gecko) Version/10.6.76 Mobile/5NQ4FI Safari/619.25',
            'Accept': '*/*',
            'Accept-Language': 'id,en-US;q=0.7,en;q=0.3',
            'X-Algolia-Api-Key': '74c36eaa211b83d1a2575f9d7bdbf5dc',
            'X-Algolia-Application-Id': 'L7MUX9U4CP',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.tops.co.th',
            'Referer': 'https://www.tops.co.th/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Connection': 'keep-alive',
        }

        query = f'["categories.level2","brand_name","promotions.cluster_1.type","country_of_product","lifestyle_and_benefit"]&filters=category_uids:"{cat_id}" AND visibility_search=1 AND visibility_catalog=1 AND stock.CFR432.is_in_stock:true AND cluster:cluster_1'+f'&highlightPostTag=__/ais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=15&maxValuesPerFacet=1000&page={page}&tagFilters=&facetFilters=["visibility_search:1"]'
        data = '{"requests":[{"indexName":"tops_en_products_recommened_sort_order_desc","params":"clickAnalytics=true&facets='+quote(query,safe="&=")+'"}]}'
        response = requests.post(
            'https://l7mux9u4cp-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.5.1)%3B%20Browser%3B%20instantsearch.js%20(4.44.0)%3B%20JS%20Helper%20(3.10.0)',
            headers=headers,
            data=data,
        )
        result = json.loads(response.content.decode('utf-8'))
        result = result['results'][0]['hits']
        if len(result) == 0:
            break
        else:
            for line in result:
                finalized_data = product_handler(line)
                
                if finalized_data:
                    pbar.write(f"{finalized_data['product_name']} --> Scraped!")
                    products.append(finalized_data)
        page+=1
    
    jsonl_file_path = os.path.join(path, "data.jsonl")
    with open(jsonl_file_path, "a", encoding="utf-8") as file:
        for data in products:
            json.dump(data, file, ensure_ascii=False)
            file.write("\n")
            file.flush()

    complete_path = os.path.join('result','complete_products.jsonl')
    with open(complete_path, "a", encoding="utf-8") as file:
        for data in products:
            json.dump(data, file, ensure_ascii=False)
            file.write("\n")
            file.flush()
    return str(len(products))
    
def product_handler(data):
    global skus
    if data['objectID'] in skus:
        return None
    url = 'https://tops.co.th/en/'+data['url_key']
    details = detail_fetcher(url)
    product_data = {
            'product_name' : data['name'],
            'image_url': 'https://assets.tops.co.th//'+data['image_url'],
            'quantity': data['name'].split(' ')[-1].replace('.',''),
            'product_details': details if details else None,
            'barcode': data['objectID'],
            'price': data['final_price'],
            'labels': data['product_badge'],
            'promotion': data['promotions'],
            'date_scraped': date.today().isoformat()
        }
    return product_data
def detail_fetcher(url):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,id;q=0.8,jv;q=0.7,de;q=0.6,zh-CN;q=0.5,zh;q=0.4,ja;q=0.3',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://www.tops.co.th/en/mom-and-kids/baby-personal-care/baby-shampoo',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    }

    response = requests.get('https://www.tops.co.th/en/johnson-baby-shampoo-800ml-9556006000502', headers=headers)
    soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
    product_details = soup.find("div", {
        "id": "panelsStayOpen-collapseOne",
        "class": ["accordion-collapse", "collapse", "show"],
        "aria-labelledby": "panelsStayOpen-headingOne"
    })
    if product_details:
        text_content = " ".join(product_details.get_text(separator=" ", strip=True).split())
        return text_content
    else:
        return None
    
def data_saver(data, level, name=None):
    if level == 2:
        with shelve.open("cache_shelve") as db:
            categories = db.get("category", {}) 
            cat_dict = {
                        'MzQ3MTk4' : {
                                'category_name':'Mom & Kids',
                                'category_id':'MzQ3MTk4'
                            }
                        }
            if 'MzQ3MTk4' not in categories:
                categories.update(cat_dict)
                db["category"] = categories
                
        for line in data['hits']:
            if line['level'] == level:
                with shelve.open("cache_shelve") as db:
                    categories = db.get("category", {}) 
                    cat_dict = {
                                line['category_uid']: {
                                    'category_name': line['name'],
                                    'category_id': line['category_uid']
                                    }
                                }
                    
                    if line['category_uid'] not in categories:
                        categories.update(cat_dict)
                        db["category"] = categories
    
    if level == 3:
        with shelve.open("cache_shelve") as db:
            category = db.get('category',{})
            index = category[name['category_id']]
            index['sub_category'] = {}
            for line in data['hits']:
                if line['level'] == level:
                    temp = {
                        line['category_uid'] : {
                            'parent_category_uid': data['hits'][0]['category_uid'],
                            'sub_categrory_name': line['name'],
                            'sub_category_id': line['category_uid']
                        }
                    }
                    if line['category_uid'] not in index['sub_category']:
                        index['sub_category'].update(temp)
                db["category"] = category
    
    if level == 4:
        with shelve.open("cache_shelve") as db:
            category = db.get('category',{})
            temp_data = category[name['parent_category_uid']]
            temp_data = temp_data['sub_category']
            temp_data = temp_data[name['sub_category_id']]
            temp_data['final_category'] = {}
            for line in data['hits']:
                if line['level'] == level:
                    temp = {
                        line['category_uid'] : {
                            'parent_category_uid': data['hits'][0]['category_uid'],
                            'final_category_name': line['name'],
                            'final_category_id': line['category_uid']
                        }
                    }
                    
                    if line['category_uid'] not in temp_data['final_category']:
                        temp_data['final_category'].update(temp)
                db["category"] = category
            

def get_category(query):
    headers = {
        'Host': 'l7mux9u4cp-dsn.algolia.net',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/618.29.10 (KHTML, like Gecko) Version/10.6 Mobile/UND8KD Safari/618.29.10',
        'Accept': '*/*',
        'Accept-Language': 'id,en-US;q=0.7,en;q=0.3',
        'X-Algolia-Api-Key': '74c36eaa211b83d1a2575f9d7bdbf5dc',
        'X-Algolia-Application-Id': 'L7MUX9U4CP',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.tops.co.th',
        'Referer': 'https://www.tops.co.th/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Connection': 'keep-alive',
    }
    data = json.dumps(query)
    response = requests.post(
        'https://l7mux9u4cp-dsn.algolia.net/1/indexes/tops_en_categories/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.5.1)%3B%20Browser%3B%20instantsearch.js%20(4.44.0)',
        headers=headers,
        data=data,
    )
    data = json.loads(response.content.decode('utf-8'))
    return data


def final_scrape():
    product_dict = {}
    with shelve.open("cache_shelve") as db:
        complete = db.get('category')
    for first_cat in complete.keys():
        level1 = complete[first_cat]['sub_category']
        level1_name = complete[first_cat]['category_name']
        for second_cat in level1.keys():
            level2 = level1[second_cat]['final_category']
            level2_name = level1[second_cat]['sub_categrory_name']
            
            product_dict[level2_name] = []
            for third_cat in level2.keys():
                level3 = level2[third_cat]['final_category_id']
                level3_name = level2[third_cat]['final_category_name']

                folder_path = os.path.join('result',level1_name, level2_name, level3_name)
                os.makedirs(folder_path, exist_ok=True)
                if level3 not in product_dict:
                    final_data = {
                            'cat_id': level3,
                            'cat_name': level3_name,
                            'path': folder_path
                        }
                    product_dict[level2_name].append(final_data)
    total_data = len(product_dict.keys())
    pbar = tqdm(total=total_data, desc=f"Scraping all products from categories", colour="red")
    for data in product_dict.keys():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(get_product_list, x, pbar) for x in product_dict[data]]
            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)

def scrape_category():
    query = {"query":"","facetFilters":[]}

    # getting second category
    print('Fething 2nd category..')
    data_saver(get_category(query), 2)
    with shelve.open("cache_shelve") as db:
        level2 = db.get('category')
    print('Fething 2nd done')

    # getting third category
    print('Fething 3rd category..')
    for line in level2.keys():
        cat_id = level2[line]
        query_copy = copy.deepcopy(query)
        query_copy['facetFilters'].append([f"category_uid:{line}", f"parent_uid:{line}"])
        data_saver(get_category(query_copy), 3, cat_id)
    print('Fething 3rd done')

    with shelve.open("cache_shelve") as db:
        level2 = db.get('category')

    print('Fething 4th category..')
    # getting forth category
    for line in level2.keys():
        level3 = level2[line]['sub_category']
        for x in level3.keys():
            cat_id = level3[x]
            query_copy = copy.deepcopy(query)
            query_copy['facetFilters'].append([f"category_uid:{x}", f"parent_uid:{x}"])
            data_saver(get_category(query_copy), 4, cat_id)
    print('Fething 4th done')

    with shelve.open("cache_shelve") as db:
        complete = db.get('category')
    with open("category.json", "w", encoding="utf-8") as f:
        json.dump(level2, f, indent=4, ensure_ascii=False) 

scrape_category()
final_scrape()