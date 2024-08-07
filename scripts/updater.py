import requests
from bs4 import BeautifulSoup

file = 'C:\\dev\\zmk-config\\shortcuts\\keymap.csv'
passw = 'C:\\dev\\zmk-config\\scripts\\pass'
collnum = 33922

login_url = "https://keycombiner.com/accounts/login/"
collection_url = lambda c: f"https://keycombiner.com/collecting/combinations/{c}/import/"
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
