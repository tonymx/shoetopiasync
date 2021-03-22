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
    except Exception as ex:
         logger.error("uncaught exception: %s", ex)
         return []

    return result_variants

def update_inventory_shopify(invitemid,qty):
    try:
        levels=shopify.InventoryLevel.find(inventory_item_ids=invitemid)
        #locations=shopify.Location.find(inventory_item_ids=invitemid)
        #print(levels)
        for l in levels:
            #print(l.inventory_item_id,l.location_id,l.available,l.updated_at)
            #Updating inventory qty, missing update price
            inventory_level = shopify.InventoryLevel.set(l.location_id, l.inventory_item_id, qty)
            #print(f"new inventoryQty updated={inventory_level.available}")
    except Exception as ex:
        logger.error("uncaught exception: %s", ex)

def main():
    try:
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
        #print(df_variants_raw)

        df_variants_raw.price=df_variants_raw['price'].astype('float64')
        df_variants_raw.inventory_quantity=df_variants_raw['inventory_quantity'].astype('int64')

        #df_variants_raw.to_csv (r'df_variants.csv', index = False, header=True)

        #Consultar BD intermedia de size &b SIZECOLORS_ENVwith open('./settings.json', 'r') as file:
        with open('./settings.json', 'r') as file:
            config = json.load(file)
            file.close()

        sqlconn=Connection(host=config[Config.SIZECOLORS_ENV]['HOST'],db=config[Config.SIZECOLORS_ENV]['DATABASE'],usr=config[Config.SIZECOLORS_ENV]['USER'],pwd=config[Config.SIZECOLORS_ENV]['PWD'])
        print("Conexion sql abierta")
        qry="select (a.codigo+'-'+b.talla) as sku,b.Cantidad as Qty,ROUND(a.precio - (((a.desc1 * a.precio)/100) + (a.desc2 * (a.precio - ((a.desc1 * a.precio)/100))/100)),0,1) as Price,a.estilo,a.color_base,a.color,a.concepto,a.linea,a.temporada from articulos a JOIN existencias b ON a.codigo=b.codigo"
        #print(qry)
        df_web_lavirs=pd.read_sql_query(qry,sqlconn.conn)
        #df_web_lavirs.to_csv (r'df_sizecolors.csv', index = False, header=True)
        df_web_lavirs.Price=df_web_lavirs['Price'].astype('float64')
        df_web_lavirs.Qty=df_web_lavirs['Qty'].astype('int64')

        #Identificar las diferencias por cantidad
        #Hacer join de ambos dataframes para obtener las diferencias
        df_merged_inner=pd.merge(left=df_web_lavirs,right=df_variants_raw,left_on='sku',right_on='sku')
        df_diff=df_merged_inner[df_merged_inner.Qty != df_merged_inner.inventory_quantity]
        #df_diff.to_csv (r'df_diff.csv', index = False, header=True)

        #Identificar las diferencias por precio
        df_diff_price=df_merged_inner[df_merged_inner.Price != df_merged_inner.price]
        #df_diff_price.to_csv (r'df_diff_price.csv', index = False, header=True)

        #sys.exit(0)

        print("Procesando diferencias en cantidad")
        for row in df_diff.itertuples(index = True, name ='DiferenciasQty'):
            #print (getattr(row, "Qty"), getattr(row, "Price"),getattr(row,"inventory_item_id"),getattr(row,"inventory_quantity"),getattr(row,"price"),getattr(row,"id"))
            inventoryitemid=getattr(row,"inventory_item_id")
            newqty=getattr(row,"Qty")
            inventoryqty=getattr(row,"inventory_quantity")
            print(f"Actualizando inventory_item_id={inventoryitemid},Shopify={inventoryqty} Size&ColorsQty={newqty}")
            update_inventory_shopify(inventoryitemid,newqty)

        print("Procesando diferencias en precio")
        for row in df_diff_price.itertuples(index = True, name ='DiferenciasPrices'):
            sizecolors_price=float(getattr(row, "Price"))
            shopify_price=float(getattr(row, "price"))

            sku=getattr(row,"sku")
            print(f"Los precios son diferentes para {sku}, Shopify={shopify_price} Size&Colors={sizecolors_price}")
            variant = shopify.Variant.find(getattr(row,"id"))
            variant.price = sizecolors_price
            variant.save()

            print("Se procesaron todas las diferencias!")

            # if sizecolors_price!=shopify_price:
            #     sku=getattr(row,"sku")
            #     print(f"Los precios son diferentes para {sku}")
            #     variant = shopify.Variant.find(getattr(row,"id"))
            #     variant.price = float(getattr(row, "Price"))
            #     variant.save()

    except Exception as ex:
         logger.error("uncaught exception: %s", ex)

if __name__ == '__main__':
    main()
