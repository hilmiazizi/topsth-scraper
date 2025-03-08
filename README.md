
# ScrapeMonster.tech - Big C Web Scraping Assignment
![Runtime Banner](https://github.com/hilmiazizi/topsth-scraper/blob/main/runtime.png)
## 1. Approach Used

Im always trying to find hidden API first rather than relying on the HTML. So i checked the web with my Burpsuite and found this 2 endpoint:


#### (Endpoint A) Endpoint to fetch category based on category:
```
https://l7mux9u4cp-dsn.algolia.net/1/indexes/tops_en_categories/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.5.1)%3B%20Browser%3B%20instantsearch.js%20(4.44.0)
```

#### (Endpoint B) Endpoint to fetch product list based on category:
```
https://l7mux9u4cp-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.5.1)%3B%20Browser%3B%20instantsearch.js%20(4.44.0)%3B%20JS%20Helper%20(3.10.0)
```


#### Endpoint A
---
From what i know, there is 3 level of category, for example:
- Mom & Kids
  - Baby Personal Care
    - Baby Soap
    - Powder
    - Baby Lotion & Oil
    - Toothpaste
    - Toothbrush
    - Baby Shampoo

First of all, i need to get all the category to its deepest point, how to do that? do this request:
```
curl --path-as-is \
-X POST \
-H "Accept-Language: id,en-US;q=0.7,en;q=0.3" \
-H "X-Algolia-Api-Key: 74c36eaa211b83d1a2575f9d7bdbf5dc" \
-H "X-Algolia-Application-Id: L7MUX9U4CP" \
-H "Content-Type: application/x-www-form-urlencoded" \
-H "Origin: https://www.tops.co.th" \
-H "Referer: https://www.tops.co.th/" \
--data-binary '{"query": "", "facetFilters": [["category_uid:MzQ3MTk4", "parent_uid:MzQ3MTk4"]]}' \
"https://l7mux9u4cp-dsn.algolia.net/1/indexes/tops_en_categories/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.5.1);%20Browser;%20instantsearch.js%20(4.44.0)"
```
Just need to adjust the `category_uid` and `parent_uid`. But both of that param can be filled with the same `category_id`. The output is all the child category of the given `category_id` so you can build the hierarchy of each category by using this endpoint. You can see the complete hierarchy here: https://github.com/hilmiazizi/topsth-scraper/blob/main/category.json

How to get the highest level category to start with? i just send the empty query like this:
```
{"query":"","facetFilters":[]}
```
But there is a problem, `Fruit & Vegetables`,  `Meat & Seafood`, `Pet Food` and `Mom & Kids` is not included in the response so i just manually add it using the value i found from burp.

Using this method i can build the entire hierarchy of all categories.


#### Endpoint B
---
This endpoint is used to get all products from the deepest category, here the request:
```
curl --path-as-is -X POST "https://l7mux9u4cp-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.5.1)%3B%20Browser%3B%20instantsearch.js%20(4.44.0)%3B%20JS%20Helper%20(3.10.0)" \
-H "Accept-Language: id,en-US;q=0.7,en;q=0.3" \
-H "X-Algolia-Api-Key: 74c36eaa211b83d1a2575f9d7bdbf5dc" \
-H "X-Algolia-Application-Id: L7MUX9U4CP" \
-H "Content-Type: application/x-www-form-urlencoded" \
-H "Origin: https://www.tops.co.th" \
-H "Referer: https://www.tops.co.th/" \
--data-binary '{
  "requests": [
    {
      "indexName": "tops_en_products_recommened_sort_order_desc",
      "params": "clickAnalytics=true&facets=[\"categories.level2\",\"brand_name\",\"promotions.cluster_1.type\",\"country_of_product\",\"lifestyle_and_benefit\"]&filters=category_uids:\"MzQ3MzU0\" AND visibility_search=1 AND visibility_catalog=1 AND stock.CFR432.is_in_stock:true AND cluster:cluster_1&highlightPostTag=__/ais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=15&maxValuesPerFacet=1000&page=0&tagFilters=&facetFilters=[\"visibility_search:1\"]"
    }
  ]
}'
```


As you can see on the POST data, you just need to pass the `category_uids`. It can also handle pagination by adjusting the `page`. At this point, i can't rely on product count that provided by Endpoint A so i just bruteforce it until the last page by:
```
if len(data['results']['hits']) == 0:
  break
else:
  page+=1
```

Here is the response example:
```
{
   "sku":"9556006000502",
   "algoliaLastUpdateAtCET":"2025-03-06 18:09:48",
   "final_price":{
      "THB":{
         "cluster_1":209,
         "cluster_2":209,
         "cluster_3":209,
         "cluster_4":209,
         "cluster_5":209,
         "cluster_6":null
      }
   },
   "price":{
      "THB":{
         "cluster_1":209,
         "cluster_2":209,
         "cluster_3":209,
         "cluster_4":null,
         "cluster_5":null,
         "cluster_6":null
      }
   },
   "discount_amount":{
      "THB":{
         "cluster_1":0,
         "cluster_2":0,
         "cluster_3":0,
         "cluster_4":0,
         "cluster_5":0,
         "cluster_6":0
      }
   },
   "entity_id":674285,
   "name":"Johnson Baby Shampoo 800ml.",
   "url_key":"johnson-baby-shampoo-800ml-9556006000502",
   "url":"https://mcprod.tops.co.th/johnson-baby-shampoo-800ml-9556006000502",
   "type_id":"simple",
   "categories":{
      "level0":["Redacted because too long and not relevant"],
      "level1":["Redacted because too long and not relevant"],
      "level2":["Redacted because too long and not relevant"]
   },
   "categories_without_path":["Redacted because too long and not relevant"],
   "category_uids":["Redacted because too long and not relevant"],
   "categoryIds":["Redacted because too long and not relevant"],
   "category_tokenized":["Redacted because too long and not relevant"],
   "rating_summary":0,
   "rating_count":0,
   "min_sale_qty":1,
   "max_sale_qty":199,
   "rule_ids":["Redacted because too long and not relevant"],
   "overlay":[],
   "cluster":[
      "cluster_1",
      "cluster_2",
      "cluster_3",
      "cluster_4"
   ],
   "promotions":{
      "cluster_1":[
         {
            "promotion_no":"4400036444",
            "start_date":"2025-02-18 17:00:00",
            "start_date_unixtime":1739898000,
            "end_date":"2025-03-04 16:59:59",
            "end_date_unixtime":1741107599,
            "type":"sale",
            "amount":"0.0000",
            "has_promotion_of_week":1
         }
      ],
      "cluster_2":[
         {
            "promotion_no":"4400036444",
            "start_date":"2025-02-18 17:00:00",
            "start_date_unixtime":1739898000,
            "end_date":"2025-03-04 16:59:59",
            "end_date_unixtime":1741107599,
            "type":"sale",
            "amount":"0.0000",
            "has_promotion_of_week":1
         }
      ],
      "cluster_3":[
         {
            "promotion_no":"4400036444",
            "start_date":"2025-02-18 17:00:00",
            "start_date_unixtime":1739898000,
            "end_date":"2025-03-04 16:59:59",
            "end_date_unixtime":1741107599,
            "type":"sale",
            "amount":"0.0000",
            "has_promotion_of_week":1
         }
      ]
   },
   "name_tokenized":["Redacted because too long and not relevant"],
   "installment_plans_ids":[],
   "package_uom":"PMIL",
   "consumer_unit":"btls",
   "campaign_name":"none",
   "local_import":"FMT-Unique TD in CFM Stores",
   "item_type_indicator":"CFG - Credit Item",
   "country_of_product":"USA",
   "thumbnail_url":"JOHNSON-JohnsonBabyShampoo800ml-9556006000502-1",
   "image_url":"JOHNSON-JohnsonBabyShampoo800ml-9556006000502-1",
   "image":"JOHNSON-JohnsonBabyShampoo800ml-9556006000502-1",
   "bestseller_count":55,
   "thumbnail":"JOHNSON-JohnsonBabyShampoo800ml-9556006000502-1",
   "visibility":"Catalog, Search",
   "visibility_search":1,
   "visibility_catalog":1,
   "is_nyb":0,
   "recommended":0,
   "is_seasonal":0,
   "is_new_arrivals":0,
   "marketplace_seller":"",
   "brand_option_id":134828,
   "brand_id":null,
   "allow_product_review":0,
   "product_name_special":0,
   "allow_storage_at_warehouse":0,
   "hide_discount_price_tag_discount":0,
   "hide_t1c_redeemable_amount":0,
   "official_brand":0,
   "featured_brand":0,
   "only_central":0,
   "brand_tier":null,
   "brand_name":"JOHNSON",
   "brand_name_tokenized":[
      "JOHNSON",
      "จอห์น สัน"
   ],
   "the1card_point":150,
   "the1card_startdate":"2020-11-11 00:00:00",
   "the1card_startdate_unixtime":1605052800,
   "shipping_methods_code":[],
   "shipping_methods":[],
   "shop_ids":[],
   "created_at":"2023-12-19 13:30:16",
   "ranking":0,
   "stock":["Redacted because too long and not relevant"],
   "cluster_1":209,
   "cluster_2":209,
   "cluster_3":209,
   "gtm_data":{
      "category_en":"Mom & Kids > Baby Health Care > Baby Shampoo",
      "product_name_en":"Johnson Baby Shampoo 800ml.",
      "brand_name_en":"JOHNSON",
      "category_id_level_two":"MzQ3MzEy",
      "category_id":"MzQ3MTk4",
      "category_uid":"MzQ3MTk4"
   },
   "product_remark":null,
   "product_badge":{
      
   },
   "campaign_categories":"promotion-hbc-discount-17-23-nov-2024",
   "objectID":"9556006000502",
   "_highlightResult":{
      "sku":{
         "value":"9556006000502",
         "matchLevel":"none",
         "matchedWords":[
            
         ]
      },
      "name":{
         "value":"Johnson Baby Shampoo 800ml.",
         "matchLevel":"none",
         "matchedWords":[
            
         ]
      },
      "categories":{
         "level0":["Redacted because too long and not relevant"],
         "level1":["Redacted because too long and not relevant"],
         "level2":["Redacted because too long and not relevant"]
      },
      "category_tokenized":["Redacted because too long and not relevant"],
      "brand_name":{
         "value":"JOHNSON",
         "matchLevel":"none",
         "matchedWords":[
            
         ]
      },
      "brand_name_tokenized":["Redacted because too long and not relevant"]
   }
}
```

From that response i got this formula:
```
url = https://tops.co.th/en/+url_key
name = name
image = https://assets.tops.co.th//+image_url
quantity = name.split(' ')[-1]
barcode = objectID
details = ???
price = final_price
labels = product_badge
promotion = promotions
date scrape = date.time()
```
What left is just product details which i scrape from the product url and extract it using bs4


#### Notes
---
This code is shit honestly, i was really sick and had to finish this in 5 days so it is what it is, you got the idea



## 2. Total Product Count

- Total products listed on the website: idk, there is no reliable source, for example the product count from API is 28 while the actual is only 8.

- Total products successfully scraped: 41242

## 3. Duplicate Handling Logic

From what i understand, this is a one time scrape, the way i get all the products is to go from each category, there is possibility that a certain product being listed on multiple category. How do i make sure that there is no duplicate on the jsonl? i have a variable that store all SKU and make sure that the SKU is unique before writen to the jsonl

Describe how you handle updates to existing products (e.g., price changes)?
There is no instruction about this, but i have found the hidden API, just fetch it right away.

## 4.  Dependencies

    beautifulsoup4==4.13.3
    requests==2.25.0
    tqdm==4.67.1

## 5. How to Run the Script

    pip install -r requirements.txt
    python3 main.py

## 6. Challenges Faced & Solutions

- Labels and Label, i have no idea what the difference is so i just put 1 label
- Barcode Number. I found no information about the EAN/UPC other than SKU, some SKU is a valid EAN/UPC. I decided not to validate it because SKU should be attached anyway, validation should be processed on different script
- OTOP & Only At Tops. I have no idea about OTOP, there is no reference. But Only At Tops is just simply the master of all category.

## 7. Sample Output (First 3 Products)

```
{"product_name": "Johnson Baby Shampoo 800ml.", "image_url": "https://assets.tops.co.th//JOHNSON-JohnsonBabyShampoo800ml-9556006000502-1", "quantity": "800ml", "product_details": "Properties : The product received may be subject to package modification and quantity from the manufacturer. We reserve the right to make any changes without prior notice. *The images used are for advertising purposes only. Ingredients : Water, Sodium Methyl Cocoyl Taurate, Disodium EDTA, Polyquaternium-10, Fragrance, PEG-150 Distearate, Citric Acid, Glycerin, Sodium Benzoate, Sodium Cocoyl Isethionate, PEG-80 Sorbitan Laurate, Cocamidopropyl Betaine, Decyl Glucoside Usage : Remove safety seal to open. Apply to wet hair, gently lather and rinse. For best results, use with Johnson's ® bath or lotion. WARNING: Use under adult supervision. SAFETY TIP: Keep out of reach of children. STORAGE: Store in dry cool place and away from direct sunlight.", "barcode": "9556006000502", "price": {"THB": {"cluster_1": 209, "cluster_2": 209, "cluster_3": 209, "cluster_4": 209, "cluster_5": 209, "cluster_6": null}}, "labels": {}, "promotion": {"cluster_1": [{"promotion_no": "4400036444", "start_date": "2025-02-18 17:00:00", "start_date_unixtime": 1739898000, "end_date": "2025-03-04 16:59:59", "end_date_unixtime": 1741107599, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_2": [{"promotion_no": "4400036444", "start_date": "2025-02-18 17:00:00", "start_date_unixtime": 1739898000, "end_date": "2025-03-04 16:59:59", "end_date_unixtime": 1741107599, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_3": [{"promotion_no": "4400036444", "start_date": "2025-02-18 17:00:00", "start_date_unixtime": 1739898000, "end_date": "2025-03-04 16:59:59", "end_date_unixtime": 1741107599, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}]}, "date_scraped": "2025-03-07"}
{"product_name": "Kodomo Original Baby Shampoo 400ml.", "image_url": "https://assets.tops.co.th//KODOMO-KodomoOriginalBabyShampoo400ml-8850002012554-1?$JPEG$", "quantity": "400ml", "product_details": "Properties : The product received may be subject to package modification and quantity from the manufacturer. We reserve the right to make any changes without prior notice. *The images used are for advertising purposes only. Ingredients : Water, Sodium Methyl Cocoyl Taurate, Disodium EDTA, Polyquaternium-10, Fragrance, PEG-150 Distearate, Citric Acid, Glycerin, Sodium Benzoate, Sodium Cocoyl Isethionate, PEG-80 Sorbitan Laurate, Cocamidopropyl Betaine, Decyl Glucoside Usage : Remove safety seal to open. Apply to wet hair, gently lather and rinse. For best results, use with Johnson's ® bath or lotion. WARNING: Use under adult supervision. SAFETY TIP: Keep out of reach of children. STORAGE: Store in dry cool place and away from direct sunlight.", "barcode": "8850002012554", "price": {"THB": {"cluster_1": 75, "cluster_2": 75, "cluster_3": 75, "cluster_4": 96, "cluster_5": 96, "cluster_6": null}}, "labels": {}, "promotion": {"cluster_1": [{"promotion_no": "4400036615", "start_date": "2025-03-04 17:00:00", "start_date_unixtime": 1741107600, "end_date": "2025-03-18 16:59:59", "end_date_unixtime": 1742317199, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_3": [{"promotion_no": "4400036615", "start_date": "2025-03-04 17:00:00", "start_date_unixtime": 1741107600, "end_date": "2025-03-18 16:59:59", "end_date_unixtime": 1742317199, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_2": [{"promotion_no": "4400036615", "start_date": "2025-03-04 17:00:00", "start_date_unixtime": 1741107600, "end_date": "2025-03-18 16:59:59", "end_date_unixtime": 1742317199, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}]}, "date_scraped": "2025-03-07"}
{"product_name": "Kodomo Gentle Soft Kids Shampoo 400ml.", "image_url": "https://assets.tops.co.th//KODOMO-KodomoGentleSoftKidsShampoo400ml-8850002011892-1", "quantity": "400ml", "product_details": "Properties : The product received may be subject to package modification and quantity from the manufacturer. We reserve the right to make any changes without prior notice. *The images used are for advertising purposes only. Ingredients : Water, Sodium Methyl Cocoyl Taurate, Disodium EDTA, Polyquaternium-10, Fragrance, PEG-150 Distearate, Citric Acid, Glycerin, Sodium Benzoate, Sodium Cocoyl Isethionate, PEG-80 Sorbitan Laurate, Cocamidopropyl Betaine, Decyl Glucoside Usage : Remove safety seal to open. Apply to wet hair, gently lather and rinse. For best results, use with Johnson's ® bath or lotion. WARNING: Use under adult supervision. SAFETY TIP: Keep out of reach of children. STORAGE: Store in dry cool place and away from direct sunlight.", "barcode": "8850002011892", "price": {"THB": {"cluster_1": 75, "cluster_2": 75, "cluster_3": 75, "cluster_4": 89, "cluster_5": 89, "cluster_6": null}}, "labels": {}, "promotion": {"cluster_1": [{"promotion_no": "4400036615", "start_date": "2025-03-04 17:00:00", "start_date_unixtime": 1741107600, "end_date": "2025-03-18 16:59:59", "end_date_unixtime": 1742317199, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_3": [{"promotion_no": "4400036615", "start_date": "2025-03-04 17:00:00", "start_date_unixtime": 1741107600, "end_date": "2025-03-18 16:59:59", "end_date_unixtime": 1742317199, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_2": [{"promotion_no": "4400036615", "start_date": "2025-03-04 17:00:00", "start_date_unixtime": 1741107600, "end_date": "2025-03-18 16:59:59", "end_date_unixtime": 1742317199, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}]}, "date_scraped": "2025-03-07"}
{"product_name": "Johnson Active Shiny Drops Kids Shampoo 500ml.", "image_url": "https://assets.tops.co.th//JOHNSON-JohnsonActiveShinyDropsKidsShampoo500ml-8850007040378-1", "quantity": "500ml", "product_details": "Properties : The product received may be subject to package modification and quantity from the manufacturer. We reserve the right to make any changes without prior notice. *The images used are for advertising purposes only. Ingredients : Water, Sodium Methyl Cocoyl Taurate, Disodium EDTA, Polyquaternium-10, Fragrance, PEG-150 Distearate, Citric Acid, Glycerin, Sodium Benzoate, Sodium Cocoyl Isethionate, PEG-80 Sorbitan Laurate, Cocamidopropyl Betaine, Decyl Glucoside Usage : Remove safety seal to open. Apply to wet hair, gently lather and rinse. For best results, use with Johnson's ® bath or lotion. WARNING: Use under adult supervision. SAFETY TIP: Keep out of reach of children. STORAGE: Store in dry cool place and away from direct sunlight.", "barcode": "8850007040378", "price": {"THB": {"cluster_1": 169, "cluster_2": 169, "cluster_3": 169, "cluster_4": 169, "cluster_5": 178, "cluster_6": null}}, "labels": {}, "promotion": {"cluster_2": [{"promotion_no": "4400036240", "start_date": "2025-01-28 17:00:00", "start_date_unixtime": 1738083600, "end_date": "2025-02-04 16:59:59", "end_date_unixtime": 1738688399, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_1": [{"promotion_no": "4400036240", "start_date": "2025-01-28 17:00:00", "start_date_unixtime": 1738083600, "end_date": "2025-02-04 16:59:59", "end_date_unixtime": 1738688399, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_3": [{"promotion_no": "4400036240", "start_date": "2025-01-28 17:00:00", "start_date_unixtime": 1738083600, "end_date": "2025-02-04 16:59:59", "end_date_unixtime": 1738688399, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}]}, "date_scraped": "2025-03-07"}
{"product_name": "Johnson Active Kids Strong&Healthy Shampoo 500ml.", "image_url": "https://assets.tops.co.th//JOHNSON-JohnsonActiveKidsStrongHealthyShampoo500ml-4801010525202-1", "quantity": "500ml", "product_details": "Properties : The product received may be subject to package modification and quantity from the manufacturer. We reserve the right to make any changes without prior notice. *The images used are for advertising purposes only. Ingredients : Water, Sodium Methyl Cocoyl Taurate, Disodium EDTA, Polyquaternium-10, Fragrance, PEG-150 Distearate, Citric Acid, Glycerin, Sodium Benzoate, Sodium Cocoyl Isethionate, PEG-80 Sorbitan Laurate, Cocamidopropyl Betaine, Decyl Glucoside Usage : Remove safety seal to open. Apply to wet hair, gently lather and rinse. For best results, use with Johnson's ® bath or lotion. WARNING: Use under adult supervision. SAFETY TIP: Keep out of reach of children. STORAGE: Store in dry cool place and away from direct sunlight.", "barcode": "4801010525202", "price": {"THB": {"cluster_1": 169, "cluster_2": 169, "cluster_3": 169, "cluster_4": 169, "cluster_5": 178, "cluster_6": null}}, "labels": {}, "promotion": {"cluster_2": [{"promotion_no": "4400036240", "start_date": "2025-01-28 17:00:00", "start_date_unixtime": 1738083600, "end_date": "2025-02-04 16:59:59", "end_date_unixtime": 1738688399, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_3": [{"promotion_no": "4400036240", "start_date": "2025-01-28 17:00:00", "start_date_unixtime": 1738083600, "end_date": "2025-02-04 16:59:59", "end_date_unixtime": 1738688399, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}], "cluster_1": [{"promotion_no": "4400036240", "start_date": "2025-01-28 17:00:00", "start_date_unixtime": 1738083600, "end_date": "2025-02-04 16:59:59", "end_date_unixtime": 1738688399, "type": "sale", "amount": "0.0000", "has_promotion_of_week": 1}]}, "date_scraped": "2025-03-07"}
```
