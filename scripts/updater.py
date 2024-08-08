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

    parsed_html = BeautifulSoup(u.content)

    v = parsed_html.body.find("input").attrs["value"]

    r = s.post(login_url, headers= {
        "Referer" : login_url
    }, files=dict(
        csrfmiddlewaretoken=(None, v),
        login=(None,'den.blackshov@gmail.com'),
        password=(None,open(passw, "r").read().strip()),

    ))

    personal = personal_url(collnum)
    p = s.get(personal, headers= {
        "Referer" : personal
    })

    p_content = BeautifulSoup(p.content)
    x = p_content.body.find("input").attrs["value"]


    listc = list_url(collnum)
    c = s.get(listc, headers={"Referer" : personal})
    ids = list(map(lambda x : x[0], list(c.json())))


    d = s.post(del_url, headers= {
        "Referer" : personal,
        "X-Csrftoken" : x
    }, json={"ids" : ids})


    collection = collection_url(collnum)
    c = s.get(collection, headers={"Referer" : collection})
    c_content = BeautifulSoup(c.content)
    t = c_content.body.find("input").attrs["value"]


    result = s.post(collection, headers= {
        "Referer" : collection
    }, files=dict(
        csrfmiddlewaretoken=(None, t),
        file=("keymap.csv", open(file, 'rb'), 'text/csv'),
        separator=(None,'A'),
        quoting=(None,'0'),

    ))
    time.sleep(15)