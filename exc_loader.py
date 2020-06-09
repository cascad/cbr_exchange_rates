import asyncio
import datetime
import os

from exc_loader.cbr_get_rub import cbr_rub_page_loader, cbr_rub_page_parser
from exc_loader.cbr_get_usd import cbr_usd_xml_loader, cbr_usd_xml_parser
from exc_loader.models import RawExchange, Exchange
from exc_loader.other_exc_loader import Collector
from exc_loader.ranges import get_days

EXCHANGE_DATA_DIRECTORY = os.path.join(os.getcwd(), "exchange_data")
BACKUP_DATA_DIRECTORY = os.path.join(os.getcwd(), "backup")


def load_exc(start: datetime.datetime, end: datetime.datetime, filename: str, append: bool):
    data = {}

    backup = "backup_" + datetime.datetime.now().strftime("%Y-%m-%d") + ".csv"
    backup = os.path.join(BACKUP_DATA_DIRECTORY, backup)
    dirname = os.path.dirname(backup)
    print(dirname)

    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    with open(filename, "w" if not append else "a") as f, open(backup, "w" if not append else "a",
                                                               encoding="utf8") as b:
        last_correct_usd_raw_records = None
        last_correct_usd_date = None

        for day in get_days(start, end):
            text = cbr_rub_page_loader(day)
            d = cbr_rub_page_parser(text)

            if len(d) != 34:
                raise Exception(f"{len(d)} on {day} RUB currents")

            rub_excs = [RawExchange(day, i) for i in d]

            u2r_rate = None
            for i in rub_excs:
                if i.str == "USD":
                    u2r_rate = i

            if u2r_rate is None:
                raise Exception(f"empty first USD date {day.date()}")

            for exc in rub_excs:
                rub_rate = exc.rate / exc.multiply
                usd_rate = rub_rate / u2r_rate.rate

                e = Exchange(day, exc.str, rub_rate, usd_rate)
                f.write(e.to_line())
                back = ",".join((day.strftime("%Y-%m-%d"), "to_rub", exc.str, str(exc.rate), str(exc.multiply),
                                 "Прямая" if exc.convtype == 0 else "Обратная"))
                b.write(back + "\n")
                data[(e.str, e.date)] = str(e)

            text = cbr_usd_xml_loader(day)
            xml_date, d = cbr_usd_xml_parser(text)

            rec_count = len(d)

            if rec_count > 0 and rec_count != 113:
                raise Exception(f"{rec_count} on {d} rare currents - error")

            if rec_count == 0:
                if last_correct_usd_raw_records is None:
                    raise Exception(
                        f"Page on first date {day} for load exchanges has no data. Please, use too early date.")
                else:
                    print(f"Page on {day} has no data. Used previous date {last_correct_usd_date}.")
                    d = last_correct_usd_raw_records

            if xml_date.date() != day.date():
                raise Exception(f"Page on {day} has data on {xml_date}.")

            last_correct_usd_raw_records = d
            last_correct_usd_date = day

            usd_excs = [RawExchange(day, i) for i in d]

            for exc in usd_excs:
                if day != exc.date:
                    print(f"bad date on u2r {exc.date}")
                if exc.convtype == 0:
                    usd_rate = 1 / exc.rate
                    rub_rate = usd_rate * u2r_rate.rate
                else:
                    usd_rate = exc.rate
                    rub_rate = exc.rate * u2r_rate.rate

                e = Exchange(day, exc.str, rub_rate, usd_rate)
                f.write(e.to_line())
                back = ",".join((day.strftime("%Y-%m-%d"), "to_usd", exc.str, str(exc.rate), str(exc.multiply),
                                 "Прямая" if exc.convtype == 0 else "Обратная"))
                b.write(back + "\n")
                data[(e.str, e.date)] = str(e)

            print(f"Complete: {day.date()}")


if __name__ == "__main__":
    start = datetime.datetime(2020, 1, 20)
    end = datetime.datetime(2020, 5, 10)
    now = datetime.datetime.now()
    # fake = datetime.datetime(2020, 3, 3)

    for p in (EXCHANGE_DATA_DIRECTORY, BACKUP_DATA_DIRECTORY):
        if not os.path.isdir(p):
            os.makedirs(p)

    outfile_path = os.path.join(EXCHANGE_DATA_DIRECTORY, f"curr_{now.strftime('%Y-%m-%d')}.csv")

    load_exc(start, end, outfile_path, False)
    c = Collector(outfile_path)
    currs = {"MMK": (start, end)}
    asyncio.get_event_loop().run_until_complete(c.download(currs))
