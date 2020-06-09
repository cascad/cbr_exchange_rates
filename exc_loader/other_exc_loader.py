import asyncio
import datetime
import os

import aiohttp
import lxml
import requests
import tqdm
from lxml.html.clean import Cleaner

BACKUP_DATA_DIRECTORY = os.path.join("D:\\repo\\taxes_calc", "backup")

RUS = ["AUD",
       "AZN",
       "GBP",
       "AMD",
       "BYN",
       "BGN",
       "BRL",
       "HUF",
       "HKD",
       "DKK",
       "USD",
       "EUR",
       "INR",
       "KZT",
       "CAD",
       "KGS",
       "CNY",
       "MDL",
       "NOK",
       "PLN",
       "RON",
       "XDR",
       "SGD",
       "TJS",
       "TRY",
       "TMT",
       "UZS",
       "UAH",
       "CZK",
       "SEK",
       "CHF",
       "ZAR",
       "KRW",
       "JPY",
       ]


def check_date(curr: str, dt: datetime.datetime, page):
    text = f"This {curr} currency table offers current and historic"
    root = lxml.html.fromstring(page)
    sel = "#contentL > div.module.clearfix > p.historicalRateTable-date"
    # xpath = '//*[@id="contentL"]/div[1]' # /p[1]
    r = root.cssselect(sel)
    # r = root.xpath(xpath)
    dt_from_page = datetime.datetime.strptime(r[0].text.split(" ")[0], "%Y-%m-%d")
    # dt_from_page = dateutil.parser.parse(r[0].text)
    return dt_from_page.date() == dt.date() and text in page


def no_data_checker(page):
    bad_text = "Build current and historic rate tables with your chosen base currency with XE Currency Tables. For commercial purposes, get an automated currency feed through the XE Currency Data API."
    return bad_text in page


def parse(page: str):
    ex = {}
    root = lxml.html.fromstring(page)
    sel = "#historicalRateTbl > tbody"
    r = root.cssselect(sel)
    for row in r[0]:
        if not isinstance(row, lxml.html.HtmlComment):
            # print(dir(row[0]))
            code = row[0].text_content()
            val = float(row[2].text)
            ex[code] = val
    return ex


def gen_dates(start, end):
    c = start
    while end >= c:
        yield c
        c = c + datetime.timedelta(days=1)


class MockResult:
    def __init__(self, params: dict, code: int, res):
        self._mdata = params
        self._code = code
        self._resp = res

    @property
    def mdata(self):
        return self._mdata

    def result(self):
        return self._code, self._resp


class Collector:
    def __init__(self, filename: str):
        self.waiter = None
        self.pool = []
        self.base = "https://www.xe.com/currencytables/"
        self.out = filename
        self.session = None
        self.last_page = {}
        self.last_page_date = {}

        fn = "backup_xe_" + datetime.datetime.now().strftime("%Y-%m-%d") + ".csv"
        self.backup_filename = os.path.join(BACKUP_DATA_DIRECTORY, fn)

    async def _get_session(self):
        if self.session is not None:
            if not self.session.closed:
                return self.session
        connector = aiohttp.TCPConnector(keepalive_timeout=10 * 60)
        # self.session = aiohttp.ClientSession(connector=connector)
        self.session = await aiohttp.ClientSession(connector=connector).__aenter__()
        return self.session

    def _sync_download(self, url, params: dict):
        resp = requests.get(url, data=params)
        if resp.status_code != 200:
            err = "response: {} -> {}".format(resp.status_code, resp.url)
            return resp.status_code, err
        return resp.status_code, resp.text

    async def close_connections(self):
        if self.session is not None:
            if not self.session.closed:
                await self.session.__aexit__(None, None, None)
        self.session = None

    async def async_download(self, url, params: dict):
        session = await self._get_session()
        if session.closed:
            raise Exception("session was closed")
        # async with session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                err = "response: {} -> {}".format(resp.status, resp.url)
                return resp.status, err

            return resp.status, await resp.text()

    def sync_download(self, currs: dict):
        print(f"loads currencies {list(currs.keys())} from {self.base}")
        total = sum([len(list(gen_dates(*i))) for i in currs.values()])
        pbar = tqdm.tqdm(total=total)
        counter = 0
        for curr, st in currs.items():
            for date in gen_dates(*st):
                sdate = date.strftime("%Y-%m-%d")
                params = {"from": curr, "date": sdate}

                code, resp = self._sync_download(self.base, params)
                mdata = {"curr": curr, "date": date}
                task = MockResult(mdata, code, resp)
                self.pool.append(task)
                pbar.update(1)
                counter += 1

                if counter > 1000:
                    self.parse(self.out)
                    self.pool.clear()
                    counter = 0

            print(f"\nComplete {curr} on range {currs[curr][0]}:{currs[curr][1]}")
        pbar.close()
        self.parse(self.out)

    async def download(self, currs: dict):
        print(f"loads currencies {list(currs.keys())} from {self.base}")
        total = sum([len(list(gen_dates(*i))) for i in currs.values()])
        pbar = tqdm.tqdm(total=total)

        for curr, st in currs.items():
            for date in gen_dates(*st):
                sdate = date.strftime("%Y-%m-%d")
                params = {"from": curr, "date": sdate}

                task = asyncio.create_task(self.async_download(self.base, params))
                task.mdata = {"curr": curr, "date": date}
                self.pool.append(task)

                if len(self.pool) >= 50:
                    await asyncio.wait(self.pool)
                    self.parse(self.out)
                    self.pool.clear()

                pbar.update(1)

        await asyncio.wait(self.pool)
        self.parse(self.out)
        pbar.close()
        self.pool.clear()

        await self.close_connections()

    def parse(self, filename: str):

        with open(filename, "a") as f, open(self.backup_filename, "a") as b:
            for r in self.pool:
                status, page = r.result()

                if status == 200:
                    curr = r.mdata["curr"]
                    date = r.mdata["date"]
                    sdate = date.strftime("%Y-%m-%d")

                    if no_data_checker(page):
                        if self.last_page.get(curr) is None:
                            raise Exception(
                                f"{curr} page on first date {sdate} for load exchanges has no data. Please, use too early date.")
                        else:
                            print(f"{curr} page on {date} has no data. Used previous date {self.last_page_date[curr]}.")
                            page = self.last_page[curr]
                    else:
                        if not check_date(curr, date, page):
                            raise Exception("Bad check {curr} on {dt}")
                        self.last_page[curr] = page
                        self.last_page_date[curr] = date

                    data = parse(page)
                    line = "{},{},{},{}\n".format(curr, sdate, data["USD"], data["RUB"])
                    f.write(line)

                    back = ",".join((sdate, "to_rub", curr, str(data["RUB"]), "1", "Обратная"))
                    b.write(back + "\n")
                    back = ",".join((sdate, "to_usd", curr, str(data["USD"]), "1", "Обратная"))
                    b.write(back + "\n")

    async def fake_download(self, currs: dict, fake_dt: datetime.datetime):
        print(f"loads currencies {list(currs.keys())} from {self.base}")
        total = sum([len(list(gen_dates(*i))) for i in currs.values()])
        pbar = tqdm.tqdm(total=total)

        for curr, st in currs.items():
            for date in gen_dates(*st):
                if curr not in RUS:
                    date = fake_dt
                sdate = date.strftime("%Y-%m-%d")
                params = {"from": curr, "date": sdate}

                task = asyncio.create_task(self.async_download(self.base, params))
                task.mdata = {"curr": curr, "date": date}
                self.pool.append(task)

                if len(self.pool) >= 50:
                    await asyncio.wait(self.pool)
                    self.fake_parse(self.out)
                    self.pool.clear()

                pbar.update(1)

        await asyncio.wait(self.pool)
        self.fake_parse(self.out)
        pbar.close()
        self.pool.clear()

    def fake_parse(self, filename: str):
        with open(filename, "a", encoding="utf8") as f:
            for r in self.pool:
                status, page = r.result()

                if status == 200:
                    curr = r.mdata["curr"]
                    date = r.mdata["date"]
                    sdate = date.strftime("%Y-%m-%d")

                    if no_data_checker(page):
                        if self.last_page.get(curr) is None:
                            raise Exception(
                                f"{curr} page on first date {sdate} for load exchanges has no data. Please, use too early date.")
                        else:
                            print(f"{curr} page on {date} has no data. Used previous date {self.last_page_date[curr]}.")
                            page = self.last_page[curr]
                    else:
                        if not check_date(curr, date, page):
                            raise Exception("Bad check {curr} on {dt}")
                        self.last_page[curr] = page
                        self.last_page_date[curr] = date

                    data = parse(page)
                    line = "{},{},{},{}\n".format(curr, sdate, data["USD"], data["RUB"])
                    f.write(line)

    def manual(self):
        lines = []
        for r in self.pool:
            status, page = r.result()

            if status == 200:
                curr = r.mdata["curr"]
                date = r.mdata["date"]
                sdate = date.strftime("%Y-%m-%d")

                data = parse(page)

                line = "{},{},{},{}\n".format(curr, sdate, data["USD"], data["RUB"])
                lines.append(line)
        return lines


if __name__ == "__main__":
    start = datetime.datetime(2019, 12, 25, 0, 0)
    end = datetime.datetime(2020, 4, 17, 0, 0)
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    outfile = f"D:\\repo\\taxes_calc\\exchange_data/alter_curr_{now}.csv"
    # if os.path.isfile(outfile):
    #     os.remove(outfile)

    c = Collector(outfile)

    with open("all_currs.txt", "r") as f:
        lines = f.readlines()

    all_currs = [i.strip() for i in lines]
    currs = {i: (start, end) for i in all_currs}
    # fake_dt = datetime.datetime(2020, 3, 3)
    # asyncio.run(c.fake_download(currs, fake_dt))
    asyncio.get_event_loop().run_until_complete(c.download(currs))
