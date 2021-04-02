import os
import json

# basedir = os.path.abspath(os.path.dirname(__file__))
# basedir=basedir+'\db'
# print(basedir)

class Config(object):
    API_URL_SHOP = os.environ.get('API_URL_SHOP') or 'https://shoetopia-mx.myshopify.com/admin'
    API_USER_SHOPIFY = os.environ.get('API_USER_SHOPIFY') or 'c742b47cbd793681bb46a01ef4e84a58'
    API_PASS_SHOPIFY = os.environ.get('API_PASS_SHOPIFY') or '1225427a3c2adef95587c943a539dabb'
    MAX_ATTEMPTS_SHOPIFY = os.environ.get('MAX_ATTEMPTS_SHOPIFY') or 10
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['consultormid@gmail.com']
    SIZECOLORS_ENV = os.environ.get('SIZECOLORS_ENV') or "PRODUCCION"
    RESOURCES_PER_PAGE = os.environ.get('RESOURCES_PER_PAGE') or 250
    # GOOGLE_CLIENT_ID= os.environ.get('GOOGLE_CLIENT_ID')
    # GOOGLE_CLIENT_SECRET= os.environ.get('GOOGLE_CLIENT_SECRET')
    # GOOGLE_REFRESH_TOKEN = os.environ.get('GOOGLE_REFRESH_TOKEN')
    # RECIPIENTS = ['consultormid@gmail.com']
    # SENDER_EMAIL = os.environ.get('SENDER_EMAIL') or 'info.ingenieux@gmail.com'
    with open('./settings.json', 'r') as file:
        config = json.load(file)
        file.close()

    SLEEP= int(config[SIZECOLORS_ENV]['SLEEP'])
