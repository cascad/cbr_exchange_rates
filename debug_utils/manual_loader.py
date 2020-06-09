import datetime

import requests

from base.utils import is_correct_data
from exc_loader.models import d2s2


def load(date: datetime.datetime):
    base_url = "https://www.cbr.ru/hd_base/seldomc/sc_daily/"
    dt = d2s2(date)
    post_data = {"UniDbQuery.Posted": "True", "UniDbQuery.To": dt}
    body = f"UniDbQuery.Posted=True&UniDbQuery.ToDate={dt}"
    a = requests.post(base_url, data=post_data)  # , headers=headers
    return a.text


base_url = "https://www.cbr.ru/hd_base/seldomc/sc_daily/"

# s = requests.session()
# s.headers.update(H)
# r = s.get(base_url)
# print(s.headers, s.cookies)
# print(r.status_code)
# cookie_val = dict(_ym_uid=1586965843231132748, _ym_d=1586965843, _ym_isad=1, accept=1, _ym_visorc_5774506='b')
# for k, v in cookie_val.items():
#     if not isinstance(v, str):
#         cookie_val[k] = str(v)
#     requests.utils.add_dict_to_cookiejar(s.cookies,
#                                          cookie_val)


dt = datetime.datetime(2019, 12, 27)
print(is_correct_data(dt, load(dt)))
