import requests
from bs4 import BeautifulSoup
import json

def pega_html(url):
    response = requests.get(url)

    html = response.content

    soup = BeautifulSoup(response.text, 'html.parser')

    return soup

def faz_cifra(soup):

    article = soup.find("pre")

    result = [str(i) for i in article]

    mapa = ""

    final = ""

    for i in result:

        i = i.replace("[", "--- ").replace("]", "")

        if "<" in i or len(i.strip()) == 0:
            mapa += i.replace("<b>", "").replace("</b>", "").replace("""<span class="cnt">""", "").replace("</span>", "").replace("""<span class="tablatura">""", "")
            continue
        
        if len(mapa) > 0:
            final += mapa
            mapa = ""

        pos = i.rfind("\n")
        dif = len(i) - pos

        if i == result[-1]:
            final += i
            continue
        final += i[:pos] + "\n"
        mapa +="!" + (" " * (dif -2))

    return(final)


def cria_json(soup, lyrics):

    name = str(soup.find("div", class_="g-side-ad").find('h1').text)
    artist = str(soup.find("div", class_="g-side-ad").find('a').text)
    tom = str(soup.find("div", class_="cifra_cnt g-fix cifra-mono").find('span').find('a').text)

    dados = {
        "name": name,
        "artist": artist,
        #"to": tom,
        "lyrics": lyrics
    }

    name_file = "PRK_song_" + name.replace(" ", "_").replace("/", "") + ".json"

    with open(name_file, 'w', encoding='utf-8') as file:
        json.dump(dados, file, indent=4, ensure_ascii=False)

    return(name_file)


html = pega_html(input("Cole aqui a url da cifra da musica: "))

lyric = faz_cifra(html)

print(lyric)

result = cria_json(html, lyric)

print(f"O arquivo {result} foi criado com sucesso!")