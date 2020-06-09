import datetime

from lxml.etree import fromstring

from exc_loader.codes import codes


def cbr_usd_xml_parser(xml: str):
    raw = fromstring(xml)
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
            digit = cdata["num_code"]
            chr = codes[cdata["num_code"]]
            raw_excs.append(
                {"NumCode": digit, "CharCode": chr, "Name": chr, "Convtype": int(cdata["dir"]), "Nominal": 1,
                 "date": date})

    return raw_excs


with open("../exc_loader/good_soap.xml", "rb") as f:
    raw = f.read()

print(cbr_usd_xml_parser(raw))
