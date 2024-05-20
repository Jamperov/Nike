import requests
import json
import traceback
import logging as log
from datetime import datetime

# КОНФИГУРАЦИЯ
# True – парсить категорию
# False – пропустить
PARSER_CONFIG = {
    "us": {
        "Shoes": (True, "https://api.nike.com/cic/browse/v2?queryid=products&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DattributeIds(16633190-45e5-4830-a068-232ac7aea82c)%26anchor%3D{anchor}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D60&language=en&localizedRangeStr=%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D"),
        "Clothing": (True, "https://api.nike.com/cic/browse/v2?queryid=products&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DattributeIds(a00f0bb2-648b-4853-9559-4cd943b7d6c6)%26anchor%3D{anchor}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D60&language=en&localizedRangeStr=%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D"),
        "Accessories": (True, "https://api.nike.com/cic/browse/v2?queryid=products&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DattributeIds(fa863563-4508-416d-bae9-a53188c04937)%26anchor%3D{anchor}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D60&language=en&localizedRangeStr=%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D")
    },
    "gb": {
        "Shoes": (True, "https://api.nike.com/cic/browse/v2?queryid=products&country=gb&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(GB)%26filter%3Dlanguage(en-GB)%26filter%3DattributeIds(16633190-45e5-4830-a068-232ac7aea82c)%26anchor%3D{anchor}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D60&language=en-GB&localizedRangeStr=%7BlowestPrice%7D%E2%80%94%7BhighestPrice%7D"),
        "Clothing": (True, "https://api.nike.com/cic/browse/v2?queryid=products&country=gb&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(GB)%26filter%3Dlanguage(en-GB)%26filter%3DattributeIds(a00f0bb2-648b-4853-9559-4cd943b7d6c6)%26anchor%3D{anchor}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D60&language=en-GB&localizedRangeStr=%7BlowestPrice%7D%E2%80%94%7BhighestPrice%7D"),
        "Accessories": (True, "https://api.nike.com/cic/browse/v2?queryid=products&country=gb&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(GB)%26filter%3Dlanguage(en-GB)%26filter%3DattributeIds(fa863563-4508-416d-bae9-a53188c04937)%26anchor%3D{anchor}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D60&language=en-GB&localizedRangeStr=%7BlowestPrice%7D%E2%80%94%7BhighestPrice%7D")
    },
}

def parse_products(base_url, country, category):
    products_list = []
    anchor = 0

    while True:
        url = base_url.format(anchor=anchor)
        response = requests.get(url)
        data = response.json()
        
        errors = data.get("data", {}).get("products", {}).get("errors", [])
        if errors:
            log.error(f"Error while fetching {url}: {errors[0].get('message')}")
            continue

        products = data["data"]["products"]["products"]
        if not products:
            break
        
        for product in products:
            try:
                parsed_product = parse_product(product, country, category)
                products_list.append(parsed_product)
            except Exception as e:
                log.error(f"Error while parsing {product['title']} ({product['url'].replace('{countryLang}', 'nike.com' if country == 'us' else 'nike.com/gb')}): {e}")
                traceback.print_exc()
                continue

        log.info(f"Total parsed for {country.upper()} {category}: {len(products_list)}")
        anchor += 60

    return products_list

def parse_product(product, country, category):
    title = product["title"]
    link = product["url"].replace("{countryLang}", "nike.com" if country == "us" else "nike.com/gb")
    if product["isLaunch"]:
        type_ = "new"
    elif product["isBestSeller"]:
        type_ = "trending"
    else:
        type_ = "normal"

    description = [
        {"title": "Subtitle", "text": product["subtitle"]},
        {"title": "ID", "text": product["id"]}
    ]

    for colorway in product["colorways"]:
        color_description = {
            "title": "colorway",
            "text": colorway["colorDescription"],
            "table": [
                {"title": "portraitImageURL", "value": str(colorway["images"]["portraitURL"])},
                {"title": "squarishImageURL", "value": str(colorway["images"]["squarishURL"])},
                {"title": "currentPrice", "value": str(colorway["price"]["currentPrice"])},
                {"title": "discounted", "value": str(colorway["price"]["discounted"])},
                {"title": "fullPrice", "value": str(colorway["price"]["fullPrice"])},
                {"title": "cloudProductId", "value": colorway["cloudProductId"]},
                {"title": "inStock", "value": str(colorway["inStock"])},
                {"title": "isBestSeller", "value": str(colorway["isBestSeller"])},
                {"title": "isNew", "value": str(colorway["isNew"])}
            ]
        }
        description.append(color_description)

    additional_description_entries, gender = parse_additional_details(product["cloudProductId"], product["price"]["currentPrice"], country)
    description.extend(additional_description_entries)

    parsed_product = {
        "title": title,
        "store": "Nike",
        "link": link,
        "price": 1,
        "priceOld": 1,
        "type": type_,
        "gender": gender,
        "description": description,
        "category": category,
        "locale": country
    }
    return parsed_product

def parse_additional_details(cloudProductId, currentPrice, country):
    URL = "https://product-proxy-v2.adtech-prod.nikecloud.com/products"
    data = {
        "experienceProducts": [
            {
                "cloudProductId": cloudProductId,
                "currentPrice": currentPrice
            }
        ],
        "country": country
    }
    
    response = requests.post(URL, json=data)
    data = response.json()
    
    if "error" in data:
        log.error(f"API returned an error for product additional request: {data['error']}")
        raise Exception(f"API returned an error for product additional request: {data['error']}")

    product_details = data.get("hydratedProducts", [{}])[0]
    sizes = [{"title": "Size", "value": size_data["size"]} for size_data in product_details.get("skuData", [])]
    genders = product_details.get("genders", [])
    
    if "MEN" in genders and len(genders) == 1:
        gender_value = "man"
    elif "WOMEN" in genders and len(genders) == 1:
        gender_value = "woman"
    elif ("GIRLS" in genders or "BOYS" in genders) and not any(g in genders for g in ["MEN", "WOMEN"]):
        gender_value = "kids"
    else:
        gender_value = "unisex"

    description_entries = [
        {"title": "sizes", "table": sizes},
        {"title": "subcategories", "table": [{"title": "Subcategory", "value": cat} for cat in product_details.get("subCategory", [])]},
        {"title": "genders", "table": [{"title": "Gender", "value": gender} for gender in genders]}
    ]
    
    return description_entries, gender_value

def main():
    current_time = datetime.now().strftime('%Y%m%d_%H%M')
    prefix = "vipavenue_products"
    log.basicConfig(filename=f"{prefix}_{current_time}.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=log.INFO)
    all_products = []

    try:
        for country, categories in PARSER_CONFIG.items():
            for category, config in categories.items():
                try:
                    if config[0]:
                        all_products.extend(parse_products(config[1], country, category))
                        log.info(f"Total parsed: {len(all_products)}")
                except Exception as e:
                    log.error(f"Error while parsing {country.upper()} {category}: {e}")
                    traceback.print_exc()
    except Exception as e:
        log.critical(f"ERROR WHILE PARSING: {e}")
        traceback.print_exc()

    log.info("Done!\nWriting to disk...")

    with open(f"{prefix}_{current_time}.json", "w") as f:
        json.dump(all_products, f)

if __name__ == "__main__":
    main()
