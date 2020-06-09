import asyncio
import datetime
import os

import click
import dateutil.parser
from dateutil.parser import ParserError

from exc_loader.cbr_get_rub import cbr_rub_page_loader, cbr_rub_page_parser
from exc_loader.cbr_get_usd import cbr_usd_xml_loader, cbr_usd_xml_parser
from exc_loader.models import RawExchange, Exchange
from exc_loader.other_exc_loader import Collector
from exc_loader.ranges import get_days


def load_exc(start: datetime.datetime, end: datetime.datetime, output_filename: str, backup: str, append: bool):
    data = {}

    with open(output_filename, "w" if not append else "a") as f, open(backup, "w" if not append else "a",
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


@click.group()
def cli():
    pass


@cli.command()
@click.option('--output', default=os.path.join(os.getcwd(), "exchange_data"), help='Output directory')
@click.option('--backup', default=os.path.join(os.getcwd(), "backup"), help='Backup data directory')
@click.argument('start_date')
@click.argument('end_date')
def run(output: str, backup: str, start_date: str, end_date: str):
    """Example: `python run app.py 2019.01.01 2020.01.01`"""
    for path in (output, backup):
        if not os.path.isdir(path):
            os.makedirs(path)

    try:
        start = dateutil.parser.parse(start_date)
        end = dateutil.parser.parse(end_date)
    except ParserError as e:
        click.echo(e)
        return

    now = datetime.datetime.now()
    # fake = datetime.datetime(2020, 3, 3)

    output_path = os.path.join(output, f"curr_{now.strftime('%Y-%m-%d')}.csv")
    backup_filename = "backup_" + datetime.datetime.now().strftime("%Y-%m-%d") + ".csv"
    backup_path = os.path.join(backup, backup_filename)

    click.echo(f" [x] Output: [{output_path}]. Backup: [{backup_path}]")

    load_exc(start, end, output_path, backup_path, False)
    c = Collector(output_path)
    currs = {"MMK": (start, end)}
    asyncio.get_event_loop().run_until_complete(c.download(currs))
    click.echo('Complete')


if __name__ == "__main__":
    cli()
