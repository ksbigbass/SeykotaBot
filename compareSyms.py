import pandas as pd
import scrapeSyms
import datetime as dt
import AlpacaTrader
from dotenv import load_dotenv
import os
   
load_dotenv()
   
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
base_url = os.getenv('ALPACA_BASE_URL')

sell = []

sdf = pd.DataFrame(scrapeSyms.strongDf)

def create_sell_list(symbols,count):
    for stock in symbols:
        if stock not in scrapeSyms.strong:
            AlpacaTrader.api.submit_order(stock, 1, type='limit',limit_price=1)


def create_count(lst):
    try:
        for stock in lst:
            if stock in scrapeSyms.strong:
                print(stock)

    except:
        print('error')

def get_positions():
        assets = AlpacaTrader.api.list_positions()
        symbols = [asset.symbol for asset in assets]
        count = [asset.qty for asset in assets]
        create_sell_list(symbols,count)



# lst = ['OILU', 'LXU', 'CRGY', 'BPT', 'CHKEL', 'SGML', 'CHKEZ', 'AMR', 'ZETA', 'NRT', 'IPI', 'NRGV', 'CHKEW', 'AR', 'UAN']


get_positions()
 


