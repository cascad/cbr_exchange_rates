import datetime

import requests
from lxml import etree

from exc_loader.models import d2s1, RawExchange


def cbr_rub_page_loader(date: datetime.datetime) -> str:
    base_url = "http://www.cbr.ru/scripts/XML_daily_eng.asp?date_req={}"
    dt = d2s1(date)
    url = base_url.format(dt)
    print(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"}

    a = requests.get(url, headers=headers)
    return a.text


def cbr_rub_page_parser(text: str) -> list:
    data = []
    root = etree.fromstring(text.encode("cp1251"))
    for appt in root.getchildren():
        dct = {}
        for elem in appt.getchildren():
            dct[elem.tag] = elem.text
        dct["Convtype"] = 0
        data.append(dct)

    assert len(data) == 34
    return data


if __name__ == "__main__":
    date = datetime.datetime(2020, 1, 1)
    text = cbr_rub_page_loader(date)
    d = cbr_rub_page_parser(text)
    excs = [RawExchange(date, i) for i in d]
    print([str(i) for i in excs])
