import os
import sys
import shopify
import json
import pandas as pd
from config import Config
from sqlserverdatabase import Connection
from pandas import ExcelWriter
import datetime
from time import time,ctime
import time
import dateutil.parser
import logging
import logging.config

def get_variants_shopify(logger):
    lastid=0
    result_variants = []
    page_v = 1
    total_intentos = 5
    num_intentos = 0
    try:
        total_variantes = shopify.Variant.count()
        #print(total_variantes)
        count_max_request = (total_variantes // Config.RESOURCES_PER_PAGE) + 2
        print(f"count_max_request = {count_max_request}")
        while page_v <= count_max_request:
            print(f"page_v={page_v}")
            print(f"lastid={lastid}")

            try:
                #variants = shopify.Variant.find(page=page_v, limit=Config.RESOURCES_PER_PAGE)
                variants = shopify.Variant.find(since_id=lastid)
                if variants:
                    num_intentos = 0
                    page_v += 1
                    for v in variants:
                        result_variants.append([v.sku, v.id, v.inventory_quantity, v.price,dateutil.parser.parse(v.updated_at,ignoretz=True),v.inventory_item_id])
                        #print(result_variants)
                    lastid=v.id
                else:
                    break
            except Exception as ex:
                print(ex)
                num_intentos += 1
                if num_intentos >= total_intentos:
                    logger.error("Reach the maximum attempts shopify request for page: %s. Variants incomplete",page_v)
                    raise Exception("Reach the maximum attempts shopify request for page")
    except:
         logger.error("uncaught exception: %s", traceback.format_exc())
         return []

    return result_variants


def main():
    logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
    logging.Formatter.converter = time.gmtime
    logger = logging.getLogger(__name__)

    #print(logger)
    shopify.ShopifyResource.set_user(Config.API_USER_SHOPIFY)
    shopify.ShopifyResource.set_password(Config.API_PASS_SHOPIFY)
    shopify.ShopifyResource.set_site(Config.API_URL_SHOP)
    max_attempts=Config.MAX_ATTEMPTS_SHOPIFY
    attempts=0
    while attempts < max_attempts:
          print(f"Geeting Shopify Info attempt # {attempts}")
          variants=get_variants_shopify(logger)
          if not variants:
              attempts+=1
              continue
          else:
              print("Se obtuvo toda la info de shopify")
              break

    print(f'Attempts={attempts}')
    print(f'max_attempts={max_attempts}')
    if attempts==max_attempts:
        logger.error("Reach the global maximum attempts to get variants from shopify")
        raise Exception("Reach the global maximum attempts to get variants from shopify")

    #print("Creando Dataframe con info de shopify")
    df_variants_raw=pd.DataFrame(variants,columns=['sku','id','inventory_quantity','price','updated_at','inventory_item_id'])
    print(df_variants_raw)
    df_variants_raw.to_csv (r'df_variants.csv', index = False, header=True)


if __name__ == '__main__':
    main()
