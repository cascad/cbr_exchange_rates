import datetime
from pprint import pformat


def curr2dict(fn: str):
    with open(fn, "r") as f:
        lines = f.readlines()

    data = {}
    for line in lines:
        ex, info, usd, rub = line.split(",")
        key = ex + " $ " + info
        data[key] = (rub, usd)

    return data


def cmp(d1, d2):
    keys = set(d1.keys())
    keys.update(d2.keys())

    res = []

    for k in keys:
        d1_data = None
        d2_data = None

        if k in d1:
            d1_data = float(d1[k][0]), float(d1[k][1])
        if k in d2:
            d2_data = float(d2[k][0]), float(d2[k][1])

        if d1_data is None or d2_data is None:
            raise Exception(f"{k} exchange is None in {'d1' if d1_data is None else 'd2'}")
        else:
            if d1_data != d2_data:
                res.append((k, d1_data[0] - d2_data[0], d1_data[1] - d2_data[1], d1_data[0], d2_data[0], d1_data[1],
                            d2_data[1]))

    return res


def get_diff(file1: str, file2: str):
    d1 = curr2dict(file1)
    d2 = curr2dict(file2)
    res = cmp(d1, d2)
    res = sorted(res, key=lambda x: datetime.datetime.strptime(x[0].split(" $ ")[1], "%Y-%m-%d"))
    # pprint(res)
    for i in res:
        if i[1] is None:
            print(i[0], None)
            continue

        curr = i[0]
        drub = abs(round(i[1], 3))
        dusd = abs(round(i[2], 3))
        rub_1 = round(i[3], 3)
        rub_2 = round(i[4], 3)
        usd_1 = round(i[5], 3)
        usd_2 = round(i[6], 3)

        if dusd > 0.05:  # and curr.split(" $ ")[0] != "CUP"
            print(f"{curr} {rub_1} - {rub_2} = {drub} RUB\n{curr} {usd_1} - {usd_2} = {dusd} USD")

    with open("../cmp_res.txt", "w") as f:
        f.write(pformat(res))


if __name__ == "__main__":
    currs = ("../exchange_data/curr_2020-04-21.csv", "../exchange_data/alter_curr_2020-04-21.csv")
    get_diff(currs[0], currs[1])
