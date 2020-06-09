import datetime


def d2s1(dt: datetime.datetime):
    return dt.strftime("%d/%m/%Y")


def d2s2(dt: datetime.datetime):
    return dt.strftime("%d.%m.%Y")


class RawExchange:
    def __init__(self, date: datetime.datetime, data: dict):
        self.digit = data["NumCode"].strip()
        self.str = data["CharCode"].strip()
        self.name = data["Name"]
        self.convtype = data["Convtype"]
        self.multiply = int(data["Nominal"])
        self.rate = float(data["Value"].replace(",", ".").replace(" ", ""))
        self.date = date

    def __str__(self):
        return f"{self.date.date()}:{self.str}:{self.rate}"


class Exchange:
    def __init__(self, date: datetime.datetime, charname: str, rub_rate: float, usd_rate: float):
        self.date = date
        self.str = charname
        self.rub_rate = rub_rate
        self.usd_rate = usd_rate

    def __str__(self):
        return f"{self.date.date()}:{self.str}:{self.rub_rate}:{self.usd_rate}"

    def to_line(self, sep=","):
        return sep.join((self.str, str(self.date.strftime("%Y-%m-%d")), str(self.usd_rate), str(self.rub_rate))) + "\n"
