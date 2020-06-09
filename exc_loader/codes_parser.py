import requests
from lxml.html import fromstring

url = "https://www.iban.com/currency-codes"

r = requests.get(url)
page = fromstring(r.content)
sel = "body > div.boxed > div.flat-row.pad-top20px.pad-bottom70px > div > div > div > div > table > tbody > tr"
select = page.cssselect(sel)
c2d = {}
d2c = {}

with open("../codes.csv", "w") as f:
    for elem in select:
        chr = elem[2].text
        dig = elem[3].text
        if chr and dig:
            c2d[chr] = dig
            d2c[dig] = chr
            print(dig, chr)
            line = f"{dig},{chr}\n"
            f.write(line)

print(d2c)
