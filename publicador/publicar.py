#!/usr/bin/env python3
"""Publicador do Já Sabia Disso? para Instagram, Facebook e YouTube.

Lê os posts em agenda/<pasta>/post.json, publica os que já chegaram na hora
pelas APIs oficiais (Meta Graph API e YouTube Data API) e grava o resultado em estado.json na
mesma pasta. Roda a cada 15 minutos pelo GitHub Actions.

Uso:
  python publicador/publicar.py              publica o que estiver na hora
  python publicador/publicar.py --verificar  só confere os posts, não publica
  python publicador/publicar.py --conexao    testa o token e mostra as contas
  python publicador/publicar.py --preparar   converte PNG em JPG (Instagram só aceita JPG)

Variáveis de ambiente (segredos do repositório):
  META_TOKEN      token de página (longa duração) com permissão de publicar
  FB_PAGE_ID      id da página do Facebook
  IG_USER_ID      id da conta do Instagram (opcional; é descoberto pela página)
  GRAPH_VERSION   versão da API (padrão v23.0)
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN   acesso ao canal do YouTube
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AGENDA = RAIZ / "agenda"
VERSAO = os.environ.get("GRAPH_VERSION", "v23.0")
GRAPH = f"https://graph.facebook.com/{VERSAO}"
RUPLOAD = "https://rupload.facebook.com"

TIPOS = {"reel", "carrossel", "imagem", "story"}
REDES = {"instagram", "facebook", "youtube"}
EXT_VIDEO = {".mp4", ".mov"}
EXT_IMAGEM = {".jpg", ".jpeg", ".png"}

# Post atrasado demais não sai (um story de ontem não faz sentido hoje).
ATRASO_MAXIMO = dt.timedelta(hours=12)


class ErroApi(Exception):
    pass


# ---------------------------------------------------------------- HTTP

def _pedir(metodo, url, params=None, corpo=None, cabecalhos=None, tentativas=3):
    if params:
        dados = urllib.parse.urlencode(params).encode()
        if metodo == "GET":
            url = f"{url}?{dados.decode()}"
            dados = None
    else:
        dados = corpo
    for tentativa in range(1, tentativas + 1):
        req = urllib.request.Request(url, data=dados, method=metodo, headers=cabecalhos or {})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                texto = resp.read().decode()
                return json.loads(texto) if texto else {}
        except urllib.error.HTTPError as e:
            texto = e.read().decode(errors="replace")
            if e.code >= 500 and tentativa < tentativas:
                time.sleep(5 * tentativa)
                continue
            raise ErroApi(f"{metodo} {url.split('?')[0]} -> {e.code}: {texto}") from None
        except urllib.error.URLError as e:
            if tentativa < tentativas:
                time.sleep(5 * tentativa)
                continue
            raise ErroApi(f"{metodo} {url.split('?')[0]} -> {e}") from None


def token():
    t = os.environ.get("META_TOKEN")
    if not t:
        raise ErroApi("META_TOKEN não configurado nos segredos do repositório")
    return t


def get(caminho, **params):
    params["access_token"] = token()
    return _pedir("GET", f"{GRAPH}/{caminho}", params)


def post(caminho, **params):
    params["access_token"] = token()
    return _pedir("POST", f"{GRAPH}/{caminho}", params)


def enviar_binario(url, arquivo, extra=None):
    """Envia o arquivo direto para o servidor de upload da Meta."""
    conteudo = arquivo.read_bytes()
    cab = {
        "Authorization": f"OAuth {token()}",
        "offset": "0",
        "file_size": str(len(conteudo)),
        "Content-Type": "application/octet-stream",
    }
    cab.update(extra or {})
    return _pedir("POST", url, corpo=conteudo, cabecalhos=cab)


# ---------------------------------------------------------------- contas

def pagina_id():
    p = os.environ.get("FB_PAGE_ID")
    if not p:
        raise ErroApi("FB_PAGE_ID não configurado nos segredos do repositório")
    return p


def ig_id():
    i = os.environ.get("IG_USER_ID")
    if i:
        return i
    dados = get(pagina_id(), fields="instagram_business_account")
    conta = dados.get("instagram_business_account", {}).get("id")
    if not conta:
        raise ErroApi("a página não tem conta do Instagram profissional ligada")
    os.environ["IG_USER_ID"] = conta
    return conta


# ---------------------------------------------------------------- mídia

def url_publica(arquivo):
    """URL do arquivo no repositório público (raw.githubusercontent.com)."""
    repo = os.environ.get("GITHUB_REPOSITORY", "vitorjn09/jasabiadisso-midia")
    ramo = os.environ.get("RAMO_MIDIA", "main")
    rel = arquivo.relative_to(RAIZ).as_posix()
    return f"https://raw.githubusercontent.com/{repo}/{ramo}/{urllib.parse.quote(rel)}"


def e_video(arquivo):
    return arquivo.suffix.lower() in EXT_VIDEO


# ---------------------------------------------------------------- Instagram

def ig_esperar(container, limite=900):
    inicio = time.time()
    while time.time() - inicio < limite:
        st = get(container, fields="status_code,status")
        codigo = st.get("status_code")
        if codigo == "FINISHED":
            return
        if codigo in ("ERROR", "EXPIRED"):
            raise ErroApi(f"Instagram recusou a mídia: {st.get('status')}")
        time.sleep(10)
    raise ErroApi("Instagram demorou demais para processar a mídia")


def ig_video(conta, arquivo, **params):
    """Cria o container de vídeo e envia o arquivo direto (sem depender de URL)."""
    c = post(f"{conta}/media", upload_type="resumable", **params)
    enviar_binario(c["uri"], arquivo)
    return c["id"]


def ig_publicar(p, pasta):
    conta = ig_id()
    midias = [pasta / m for m in p["midias"]]
    legenda = p.get("legenda", "")
    tipo = p["tipo"]

    if tipo == "reel":
        extra = {"caption": legenda, "share_to_feed": "true"}
        if p.get("capa"):
            extra["cover_url"] = url_publica(pasta / p["capa"])
        container = ig_video(conta, midias[0], media_type="REELS", **extra)
    elif tipo == "story":
        m = midias[0]
        if e_video(m):
            container = ig_video(conta, m, media_type="STORIES")
        else:
            container = post(f"{conta}/media", media_type="STORIES", image_url=url_publica(m))["id"]
    elif tipo == "imagem":
        container = post(f"{conta}/media", image_url=url_publica(midias[0]), caption=legenda)["id"]
    else:  # carrossel
        filhos = []
        for m in midias:
            if e_video(m):
                filho = ig_video(conta, m, media_type="VIDEO", is_carousel_item="true")
            else:
                filho = post(f"{conta}/media", image_url=url_publica(m), is_carousel_item="true")["id"]
            ig_esperar(filho)
            filhos.append(filho)
        container = post(f"{conta}/media", media_type="CAROUSEL",
                         children=",".join(filhos), caption=legenda)["id"]

    ig_esperar(container)
    return post(f"{conta}/media_publish", creation_id=container)["id"]


# ---------------------------------------------------------------- Facebook

def fb_video(pagina, arquivo, borda, **finalizar):
    """Fluxo de três etapas usado por reels (video_reels) e stories (video_stories)."""
    inicio = post(f"{pagina}/{borda}", upload_phase="start")
    video = inicio["video_id"]
    enviar_binario(inicio.get("upload_url") or f"{RUPLOAD}/video-upload/{VERSAO}/{video}", arquivo)
    fim = post(f"{pagina}/{borda}", upload_phase="finish", video_id=video, **finalizar)
    return fim.get("post_id") or video


def fb_foto_sem_publicar(pagina, arquivo):
    return post(f"{pagina}/photos", url=url_publica(arquivo), published="false")["id"]


def fb_publicar(p, pasta):
    pagina = pagina_id()
    midias = [pasta / m for m in p["midias"]]
    legenda = p.get("legenda", "")
    tipo = p["tipo"]

    if tipo == "reel":
        extra = {"video_state": "PUBLISHED", "description": legenda}
        if p.get("titulo_facebook"):
            extra["title"] = p["titulo_facebook"]
        return fb_video(pagina, midias[0], "video_reels", **extra)
    if tipo == "story":
        m = midias[0]
        if e_video(m):
            return fb_video(pagina, m, "video_stories")
        foto = fb_foto_sem_publicar(pagina, m)
        return post(f"{pagina}/photo_stories", photo_id=foto).get("post_id", foto)
    # imagem ou carrossel: fotos sem publicar, depois um post no feed com todas
    fotos = [fb_foto_sem_publicar(pagina, m) for m in midias]
    anexos = {f"attached_media[{i}]": json.dumps({"media_fbid": f}) for i, f in enumerate(fotos)}
    return post(f"{pagina}/feed", message=legenda, **anexos)["id"]


# ---------------------------------------------------------------- YouTube

def yt_token():
    faltando = [v for v in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(v)]
    if faltando:
        raise ErroApi(f"faltam segredos do YouTube: {', '.join(faltando)}")
    r = _pedir("POST", "https://oauth2.googleapis.com/token", {
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })
    return r["access_token"]


def yt_publicar(p, pasta):
    """Envia o vídeo como Short público (envio resumível em duas etapas)."""
    video = pasta / p["midias"][0]
    conteudo = video.read_bytes()
    acesso = yt_token()
    titulo = p.get("titulo_youtube") or p.get("legenda", "").split("\n")[0]
    meta = {
        "snippet": {
            "title": titulo[:100],
            "description": p.get("legenda", "")[:5000],
            "categoryId": "27",  # Educação
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": bool(p.get("ia", False)),
        },
    }
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={
            "Authorization": f"Bearer {acesso}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(len(conteudo)),
        })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            destino = resp.headers["Location"]
    except urllib.error.HTTPError as e:
        raise ErroApi(f"YouTube recusou o envio: {e.code} {e.read().decode(errors='replace')}") from None
    r = _pedir("PUT", destino, corpo=conteudo, cabecalhos={
        "Authorization": f"Bearer {acesso}", "Content-Type": "video/mp4"})
    return r["id"]


PUBLICAR = {"instagram": ig_publicar, "facebook": fb_publicar, "youtube": yt_publicar}


# ---------------------------------------------------------------- agenda

def ler_posts():
    for arq in sorted(AGENDA.glob("*/post.json")):
        pasta = arq.parent
        try:
            p = json.loads(arq.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            yield pasta, None, [f"post.json inválido: {e}"]
            continue
        yield pasta, p, validar(p, pasta)


def validar(p, pasta):
    erros = []
    try:
        quando = dt.datetime.fromisoformat(p["quando"])
        if quando.tzinfo is None:
            erros.append("'quando' precisa do fuso, ex.: 2026-11-02T18:00:00-03:00")
    except (KeyError, ValueError):
        erros.append("'quando' ausente ou fora do formato 2026-11-02T18:00:00-03:00")
    if p.get("tipo") not in TIPOS:
        erros.append(f"'tipo' deve ser um de {sorted(TIPOS)}")
    redes = p.get("redes") or []
    if not redes or set(redes) - REDES:
        erros.append(f"'redes' deve ter só {sorted(REDES)}")
    midias = p.get("midias") or []
    if not midias:
        erros.append("'midias' vazio")
    for m in midias + ([p["capa"]] if p.get("capa") else []):
        arq = pasta / m
        if not arq.exists():
            erros.append(f"arquivo não encontrado: {m}")
        elif arq.suffix.lower() not in EXT_VIDEO | EXT_IMAGEM:
            erros.append(f"formato não aceito: {m}")
        elif "instagram" in redes and arq.suffix.lower() == ".png":
            erros.append(f"Instagram só aceita JPG: rode --preparar ({m})")
    tipo = p.get("tipo")
    if "youtube" in redes and tipo != "reel":
        erros.append("no YouTube só sai reel (Short)")
    if tipo == "reel" and midias and not e_video(pasta / midias[0]):
        erros.append("reel precisa de um vídeo")
    if tipo in ("reel", "story", "imagem") and len(midias) > 1:
        erros.append(f"{tipo} leva só uma mídia")
    if tipo == "carrossel" and not 2 <= len(midias) <= 10:
        erros.append("carrossel leva de 2 a 10 mídias")
    return erros


def ler_estado(pasta):
    arq = pasta / "estado.json"
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}


def gravar_estado(pasta, estado):
    (pasta / "estado.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def agora():
    return dt.datetime.now(dt.timezone.utc)


def publicar_pendentes():
    falhas = 0
    for pasta, p, erros in ler_posts():
        nome = pasta.name
        if erros:
            print(f"[{nome}] ignorado: " + "; ".join(erros))
            continue
        quando = dt.datetime.fromisoformat(p["quando"])
        if quando > agora():
            continue
        estado = ler_estado(pasta)
        for rede in p["redes"]:
            atual = estado.get(rede, {})
            if atual.get("status") in ("publicado", "atrasado", "falhou"):
                continue
            if agora() - quando > ATRASO_MAXIMO:
                estado[rede] = {"status": "atrasado", "em": agora().isoformat()}
                print(f"[{nome}] {rede}: passou da hora há mais de 12h, não publicado")
                continue
            try:
                ident = PUBLICAR[rede](p, pasta)
                estado[rede] = {"status": "publicado", "id": ident, "em": agora().isoformat()}
                print(f"[{nome}] {rede}: publicado ({ident})")
            except Exception as e:  # qualquer falha fica registrada e o resto segue
                tentativas = atual.get("tentativas", 0) + 1
                estado[rede] = {"status": "erro", "erro": str(e)[:1000],
                                "tentativas": tentativas, "em": agora().isoformat()}
                # Depois de 3 falhas para de tentar, para não repetir post pela metade.
                if tentativas >= 3:
                    estado[rede]["status"] = "falhou"
                print(f"[{nome}] {rede}: ERRO {e}")
                falhas += 1
            gravar_estado(pasta, estado)
    return falhas


# ---------------------------------------------------------------- utilidades

def verificar():
    total = 0
    for pasta, p, erros in ler_posts():
        total += 1
        estado = ler_estado(pasta)
        if erros:
            print(f"✗ {pasta.name}: " + "; ".join(erros))
        else:
            redes = ", ".join(f"{r}={estado.get(r, {}).get('status', 'aguardando')}" for r in p["redes"])
            print(f"✓ {pasta.name}: {p['tipo']} em {p['quando']} ({redes})")
    print(f"{total} post(s) na agenda")


def conexao():
    if os.environ.get("YT_REFRESH_TOKEN"):
        acesso = yt_token()
        canal = _pedir("GET", "https://www.googleapis.com/youtube/v3/channels",
                       {"part": "snippet", "mine": "true"},
                       cabecalhos={"Authorization": f"Bearer {acesso}"})
        nomes = [c["snippet"]["title"] for c in canal.get("items", [])]
        print(f"YouTube: {', '.join(nomes) or 'nenhum canal'}")
    pag = get(pagina_id(), fields="name,instagram_business_account{username}")
    print(f"Página do Facebook: {pag.get('name')} ({pagina_id()})")
    conta = pag.get("instagram_business_account")
    if conta:
        print(f"Instagram: @{conta.get('username')} ({conta['id']})")
        limite = get(f"{conta['id']}/content_publishing_limit", fields="quota_usage,config")
        print(f"Cota de publicação nas últimas 24h: {json.dumps(limite.get('data'))}")
    else:
        print("Nenhuma conta do Instagram ligada à página")


def preparar():
    from PIL import Image
    for pasta, p, _ in ler_posts():
        if not p or "instagram" not in (p.get("redes") or []):
            continue
        mudou = False
        for chave in ("midias", "capa"):
            itens = p.get(chave)
            lista = itens if isinstance(itens, list) else [itens] if itens else []
            novos = []
            for m in lista:
                arq = pasta / m
                if arq.suffix.lower() == ".png" and arq.exists():
                    jpg = arq.with_suffix(".jpg")
                    Image.open(arq).convert("RGB").save(jpg, "JPEG", quality=92)
                    arq.unlink()
                    m = jpg.name
                    mudou = True
                novos.append(m)
            if lista:
                p[chave] = novos if isinstance(itens, list) else novos[0]
        if mudou:
            (pasta / "post.json").write_text(
                json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{pasta.name}: PNG convertido para JPG")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--conexao", action="store_true")
    g.add_argument("--preparar", action="store_true")
    a = ap.parse_args()
    if a.verificar:
        verificar()
    elif a.conexao:
        conexao()
    elif a.preparar:
        preparar()
    else:
        sys.exit(1 if publicar_pendentes() else 0)


if __name__ == "__main__":
    main()
