import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os.path
import datetime as dt

URL = "https://www.eseykota.com/TT/PHP_TT/TT_charts/stocks/myList.txt"
r = requests.get(URL)

soup = BeautifulSoup(r.content, 'html.parser')
raw = soup.prettify()
tag = (str(soup.encode_contents()))

r = re.compile('[A-Z]')
special_char = '@_!#$%^&*()<>?/\|}{~:;.[]rn'

date = pd.DataFrame({'year': [2022, 2023],
                     'month': [1, 2],
                     'day': [5, 6]})
modSyms = []

for w in tag.split('\\n'):
    modSyms.append(w)

modSyms = list(filter(r.match, modSyms))

cleanSyms = [''.join(x for x in string if not x in special_char)
             for string in modSyms]

strong = [x for x in cleanSyms[0:15]]  # make the strong list 0-14
strongDf = pd.DataFrame(strong, columns=['sym'])
strongDf['count'] = 1
strongDf['date'] = dt.date.today()

weak = [x for x in cleanSyms[15:]]  # make the weak list 15-30
weakDf = pd.DataFrame(weak, columns=['sym'])
weakDf['count'] = 0
weakDf['date'] = dt.date.today()



# print(strong)
#print(strongDf)
print(weakDf)