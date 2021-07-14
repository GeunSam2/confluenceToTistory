import html2text
from bs4 import BeautifulSoup as bs

with open('output.html', 'r') as f:
    html = f.read()

soup = bs(html, 'html.parser')
#print (soup.tr.td.p)
Tds = soup.find_all('td', 'confluenceTd')
Ths = soup.find_all('td', 'confluenceTh')

def unwrapTds(soups):
    for item in soups:
        item.p.unwrap()

unwrapTds(Tds)
unwrapTds(Ths)

print (str(soup))

md = html2text.html2text(str(soup))
with open ('result.md', 'w') as f:
    f.write(md)

print ('---- end ----')
