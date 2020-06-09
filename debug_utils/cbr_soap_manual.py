import requests

endpoint = "http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx"

body = """<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <GetReutersCursOnDateXML xmlns="http://web.cbr.ru/">
      <On_date>2020-03-30</On_date>
    </GetReutersCursOnDateXML>
  </soap12:Body>
</soap12:Envelope>"""

body = body.encode('utf-8')
session = requests.session()
session.headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
session.headers.update({"Content-Length": str(len(body))})
response = session.post(url=endpoint, data=body, verify=False)
print(response.text)
print(response.status_code)
# with open("bad_soap.html", "wb") as f:
#     f.write(response.content)
