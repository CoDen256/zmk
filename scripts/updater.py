import time

import requests
from bs4 import BeautifulSoup


login_url = "https://keycombiner.com/accounts/login/"
collection_url = lambda c: f"https://keycombiner.com/collecting/combinations/{c}/import/"
personal_url = lambda c: f"https://keycombiner.com/collecting/collections/personal/{c}/"
list_url = lambda c: f"https://keycombiner.com/collecting/api/collection/{c}/list/"
del_url = "https://keycombiner.com/collecting/combinations/remove_from_personal/"


def update(file,passw,collnum):

    s = requests.session()
    u = s.get(login_url)

    print("[updater] logging in...", u)
    parsed_html = BeautifulSoup(u.content,features="html.parser")

    v = parsed_html.body.find("input").attrs["value"]
    print("[updater] found token", v)
    r = s.post(login_url, headers= {
        "Referer" : login_url
    }, files=dict(
        csrfmiddlewaretoken=(None, v),
        login=(None,'den.blackshov@gmail.com'),
        password=(None,open(passw, "r").read().strip()),

    ))
    print("[updater] logged in", r)

    personal = personal_url(collnum)
    p = s.get(personal, headers= {
        "Referer" : personal
    })
    print("[updater] fetched personal", p)

    p_content = BeautifulSoup(p.content,features="html.parser")
    x = p_content.body.find("input").attrs["value"]
    print("[updater] token found", x)

    listc = list_url(collnum)
    c = s.get(listc, headers={"Referer" : personal})
    ids = list(map(lambda x : x[0], list(c.json())))
    print("[updater] listed shortcuts", c, ids)

    d = s.post(del_url, headers= {
        "Referer" : personal,
        "X-Csrftoken" : x
    }, json={"ids" : ids})
    print("[updater] deleted shortcuts", d)


    collection = collection_url(collnum)
    c = s.get(collection, headers={"Referer" : collection})
    c_content = BeautifulSoup(c.content,features="html.parser")
    print("[updater] importing", c)
    t = c_content.body.find("input").attrs["value"]
    print("[updater] found token", t)


    result = s.post(collection, headers= {
        "Referer" : collection
    }, files=dict(
        csrfmiddlewaretoken=(None, t),
        file=("keymap.csv", open(file, 'rb'), 'text/csv'),
        separator=(None,'A'),
        quoting=(None,'0'),

    ))
    print("[updater] imported", result)

    print("[updater] done")
    time.sleep(15)