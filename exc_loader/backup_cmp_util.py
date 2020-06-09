import datetime
from pprint import pprint, pformat


def curr2dict(fn: str):
    with open(fn, "r", encoding="utf8") as f:
        lines = f.readlines()

    data = {}
    for line in lines:
        sdate, convert, exc, rate, nominal, direct = line.split(",")
        key = ",".join((exc, sdate, convert, nominal, direct))
        data[key] = rate

    return data


def cmp(d1, d2):
    keys = set(d1.keys())
    keys.update(d2.keys())

    res = []

    for k in keys:
        d1_data = None
        d2_data = None

        if k in d1:
            d1_data = float(d1[k])
        if k in d2:
            d2_data = float(d2[k])

        if d1_data is None or d2_data is None:
            raise Exception(f"{k} not in {'d1' if d1_data is None else 'd2'}")
        else:
            if d1_data != d2_data:
                res.append((k, d1_data, d2_data, abs(d1_data - d2_data)))

    return res


def get_diff(file1: str, file2: str):
    d1 = curr2dict(file1)
    d2 = curr2dict(file2)
    res = cmp(d1, d2)
    res = sorted(res, key=lambda x: datetime.datetime.strptime(x[0].split(",")[1], "%Y-%m-%d"))
    srt = []

    for i in res:
        exc, sdate, convert, nominal, direct = i[0].split(",")

        if convert == "to_usd" and i[3] > 0.01:
            # print(i)
            z = (i[0], round(i[1], 3), round(i[2], 3), round(i[3], 3))
            srt.append(z)

    srt = sorted(srt, key=lambda x: x[3])
    pprint(srt)


if __name__ == "__main__":
    currs = ("../backup/bad_backup_2020-04-20.csv", "../backup/backup_2020-04-20.csv")
    get_diff(currs[0], currs[1])
