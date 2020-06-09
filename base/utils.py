import datetime
import re


def no_data_finder(text):
    """Raw page checker for no-info-page"""
    if "За выбранный вами период нет информации" in text:
        return True
    return False


def is_correct_data(dt, text):
    """Raw page checker on correct date."""
    # "Данные на 27.12.2019."
    found = re.search(r'(Данные на \d+\.\d+\.\d+)\.', text)
    if found is None:
        raise Exception(f"Not found text about date: \"Данные на %d.%m.%Y.\"")
    # 27.12.2019 format here
    text = found.group()
    raw_date = text.rstrip(".").split("Данные на ")[1]
    try:
        date = datetime.datetime.strptime(raw_date, "%d.%m.%Y")
    except Exception:
        print(f"Invalid date {raw_date}. Text: {text}")
        raise
    else:
        return dt.date() == date.date()
