import datetime


def get_days(start, end):
    if start > end:
        raise Exception(f"{start} > {end}")

    curr = start
    while curr.date() <= end.date():
        yield curr
        curr = curr + datetime.timedelta(days=1)


def test_ranges():
    d1 = (datetime.datetime(2019, 12, 29), datetime.datetime(2020, 2, 4))
    r1 = list(get_days(*d1))
    assert r1[0] == d1[0]
    assert r1[-1] == d1[1]

    d2 = (datetime.datetime(2019, 12, 31), datetime.datetime(2020, 1, 2))
    r2 = list(get_days(*d2))
    assert r2[0] == d2[0]
    assert r2[-1] == d2[1]

    d = (datetime.datetime(2019, 9, 6), datetime.datetime(2019, 9, 6))
    r = list(get_days(*d))
    assert len(r) == 1
    assert r[0] == d[0]

    d = (datetime.datetime(2019, 9, 6), datetime.datetime(2019, 9, 7))
    r = list(get_days(*d))
    assert len(r) == 2
    assert r[0] == d[0]
    assert r[-1] == d[1]


if __name__ == "__main__":
    test_ranges()
