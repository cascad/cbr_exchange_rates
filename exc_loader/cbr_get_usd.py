import datetime

import lxml.html
import requests
from lxml.etree import fromstring

from exc_loader.codes import codes
from exc_loader.models import d2s2, RawExchange

POS = {0: "NumCode", 1: "CharCode", 2: "Name", 3: "Convtype", 4: "Value"}


def cbr_usd_page_loader(date: datetime.datetime) -> str:
    base_url = "https://www.cbr.ru/hd_base/seldomc/sc_daily/"
    dt = d2s2(date)
    post_data = {"UniDbQuery.Posted": "True", "UniDbQuery.To": dt}
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"}

    a = requests.post(base_url, data=post_data, headers={"Referrer": base_url})  # , headers=headers
    return a.text


def cbr_usd_xml_loader(date: datetime.datetime) -> str:
    endpoint = "http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx"

    template = """<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <GetReutersCursOnDateXML xmlns="http://web.cbr.ru/">
          <On_date>{dt}</On_date>
        </GetReutersCursOnDateXML>
      </soap12:Body>
    </soap12:Envelope>"""

    sdate = date.strftime("%Y-%m-%d")
    body = template.format(dt=sdate).encode("utf8")

    headers = {"Content-Type": "application/soap+xml; charset=utf-8", "Content-Length": str(len(body))}
    response = requests.post(url=endpoint, data=body, headers=headers, verify=False)
    if response.status_code != 200:
        raise Exception(response.text)
    return response.text


def cbr_usd_xml_parser(xml: str):
    raw = fromstring(xml.encode("utf8"))
    header = raw.xpath("//ReutersValutesData")
    # print(dir(header[0]))
    sdate = header[0].get("OnDate")
    date = datetime.datetime.strptime(sdate, "%Y%m%d")
    print(date)

    currencies = raw.xpath("//ReutersValutesData/Currency")
    raw_excs = []
    for curr in currencies:
        cdata = {}
        for child in curr:
            cdata[child.tag] = child.text

        raw_excs.append(
            {"Value": cdata["val"], "NumCode": cdata["num_code"], "CharCode": codes[cdata["num_code"]],
             "Name": codes[cdata["num_code"]], "Convtype": int(cdata["dir"]), "Nominal": 1})

    return date, raw_excs


def cbr_usd_page_parser(text: str):
    data = []
    root = lxml.html.fromstring(text)
    sel = "#content > div > div > div > div.table-wrapper > div.table > table"  # > tbody
    r = root.cssselect(sel)
    if len(r) == 0:
        raise Exception(text)

    for row in r[0][1:]:
        dct = {}
        for i, td in enumerate(row):
            dct[POS[i]] = td.text

        if dct["Convtype"] not in ("Прямая", "Обратная"):
            raise Exception(dct["Convtype"])

        dct["Convtype"] = 0 if dct["Convtype"] == "Прямая" else 1
        dct["Nominal"] = 1
        data.append(dct)
        # if not isinstance(row, lxml.html.HtmlComment):
        #     print(row[0])
        # print(dir(row[0]))
        # code = row[0].text_content()
        # val = float(row[2].text)
        # ex[code] = val
    if len(data) < 100 or len(data) > 120:
        raise Exception(f"{len(data)}, rates: {[i['Value'] for i in data]}")
    return data


if __name__ == "__main__":
    date = datetime.datetime(2020, 1, 1)
    text = cbr_usd_page_loader(date)
    d = cbr_usd_page_parser(text)
    excs = [RawExchange(date, i) for i in d]
    print([str(i) for i in excs])
