from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import yt_dlp
import io
import uuid
import requests
from bs4 import BeautifulSoup
import json

app = FastAPI()

app.mount("/img", StaticFiles(directory="static/img"), name="img")

@app.get("/")

def ler_index():
    return FileResponse('static/index.html')


armazenamento = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class Dados(BaseModel):
    url: str

# Pega da cifra com base no link


def pega_html(url):
    response = requests.get(url)

    html = response.content

    soup = BeautifulSoup(response.text, 'html.parser')

    return soup

# Tratamento da cifra para o padrão PRK

def faz_cifra(soup):

    article = soup.find("pre")

    result = [str(i) for i in article]

    mapa = ""

    final = ""

    for i in result:

        if i.find("<span") != -1 or i.count("-") > 10:
            continue

        i = i.replace("[", "--- ").replace("]", "")

        if "<" in i or len(i.strip()) == 0:
            mapa += i.replace("<b>", "").replace("</b>", "")
            continue

        pos = i.rfind("\n")

        if pos == 0:
            pos = len(i)

        dif = len(i) - pos
                
        if len(mapa) > 0:
            final += mapa
            amostra = mapa
            mapa = ""
        else:
            amostra = ""

        # if i == result[-1]:
        #     final += i
        #     continue

        i = i[:pos]

        cont = 0
        cont2 = 1

        # print("amostra" + repr(amostra))
        # print("i" + repr(i))

        invalido = True

        suposto = i

        for j in amostra:
            if j == "-" or "---" in  i.strip()[:3]:
                break
            if len(j.strip()) == 0 or j == "!":
                cont += 1
                invalido = False
                continue
            if invalido:
                continue
            cont += cont2

            try:
                if len(i[cont-1].strip()) == 0:
                    continue

            except:
                pass

            suposto = i[:cont] + "|" + i[cont:]
            cont2  = 2
            invalido = True
    
        if not cont >= len(i):
            i = suposto

        final += i + "\n"
        mapa +="!" + (" " * (dif -2))

    final = final[:len(final) -1]

    return(final)


def cria_json(soup, lyrics):

    name = str(soup.find("div", class_="g-side-ad").find('h1').text)
    artist = str(soup.find("div", class_="g-side-ad").find('a').text)
    tom = str(soup.find("div", class_="cifra_cnt g-fix cifra-mono").find('span').find('a').text)
    capo = soup.find(id='cifra_capo').find('a')

    if capo == None:
        capo = 0
    else:
        capo = int(capo.text[0])


    # ydl_opts = {
    #         "quiet": True,
    #         "skip_download": True,
    #         "default_search": "ytsearch1",
    #         "no_warnings": True,
    #     }

    # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #     info = ydl.extract_info(name + " - " + artist, download=False)
    #     if "entries" in info and info["entries"]:
    #         link_youtube = info["entries"][0]["webpage_url"]
    #     else:
    #         link_youtube = ""

    dados = {
    "name": name,
    "artist": artist,
    "to": tom,
    "lyrics": lyrics,
    # "reference_link": link_youtube,
    "capo": capo
    }
    
    return dados


@app.post("/executar")

def executar(dados: Dados):
    if dados.url == "":
        return {"resultado": ""}
    html = pega_html(dados.url)
    lyric = faz_cifra(html)
    file = cria_json(html, lyric)

    file_id = str(uuid.uuid4())
    armazenamento[file_id] = file

    return {"resultado": lyric, "file_id": file_id}


@app.get("/baixar/{file_id}")


def baixar(file_id: str):

    if file_id not in armazenamento:
        raise HTTPException(status_code=404, detail="ID inválido")
    
    conteudo = armazenamento[file_id]

    name_file = "PRK_song_" + armazenamento[file_id]["name"].replace(" ", "_").replace("/", "") + ".json"
    
    del armazenamento[file_id]

    conteudo = json.dumps(conteudo, indent=4, ensure_ascii=False)

    buffer = io.StringIO(conteudo)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={name_file}"
        }
    )