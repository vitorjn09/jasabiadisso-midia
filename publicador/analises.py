#!/usr/bin/env python3
"""Coleta as métricas do perfil para a aba Análises do painel.

Busca números do Instagram, da página do Facebook e do canal do YouTube com os
mesmos segredos do publicador e grava em dados/analises.json. Cada métrica é
pedida separada: se uma falhar (permissão faltando, métrica que a Meta
aposentou), as outras continuam e o erro fica anotado no arquivo.

O arquivo sai cifrado (AES-GCM com chave derivada por PBKDF2 da senha guardada
no segredo ANALISES_SENHA) em dados/analises.cifrado.json: o repositório é
público e só quem souber a senha lê os números no painel. Sem o segredo, nada
é gravado.

Uso:
  python publicador/analises.py
"""

import base64
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publicar import RAIZ, ErroApi, _pedir, get, ig_id, pagina_id, yt_token  # noqa: E402

DADOS = RAIZ / "dados"
CIFRADO = DADOS / "analises.cifrado.json"
FUSO = dt.timezone(dt.timedelta(hours=-3))
DIAS_HISTORICO = 120
ITERACOES = 200_000


def limpar(msg):
    return str(msg)[:300]


def numero(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            return round(float(v), 2)
        except (TypeError, ValueError):
            return None


# ---------------------------------------------------------------- Instagram

def ig_total(conta, metrica, desde, ate, erros):
    """Total de uma métrica da conta no período (metric_type=total_value)."""
    try:
        r = get(f"{conta}/insights", metric=metrica, period="day", metric_type="total_value",
                since=int(desde.timestamp()), until=int(ate.timestamp()))
        for item in r.get("data", []):
            return numero(item.get("total_value", {}).get("value"))
    except ErroApi as e:
        erros.append(f"instagram {metrica}: {limpar(e)}")
    return None


def ig_seguidores_por_dia(conta, erros):
    try:
        agora = dt.datetime.now(dt.timezone.utc)
        r = get(f"{conta}/insights", metric="follower_count", period="day",
                since=int((agora - dt.timedelta(days=29)).timestamp()), until=int(agora.timestamp()))
        valores = r.get("data", [{}])[0].get("values", [])
        return [{"dia": v["end_time"][:10], "novos": numero(v.get("value"))} for v in valores]
    except (ErroApi, IndexError, KeyError) as e:
        erros.append(f"instagram follower_count: {limpar(e)}")
        return []


MET_REEL = ["reach", "views", "likes", "comments", "shares", "saved", "total_interactions", "ig_reels_avg_watch_time"]
MET_FEED = ["reach", "views", "likes", "comments", "shares", "saved", "total_interactions"]


def ig_metricas_post(mid, tipo, erros):
    lista = MET_REEL if tipo == "REELS" else MET_FEED
    saida = {}

    def ler(r):
        for item in r.get("data", []):
            v = item.get("values", [{}])[0].get("value") if item.get("values") else item.get("total_value", {}).get("value")
            saida[item["name"]] = numero(v)

    try:
        ler(get(f"{mid}/insights", metric=",".join(lista)))
    except ErroApi:
        # Uma métrica sem suporte derruba o pedido inteiro: tenta uma a uma.
        for m in lista:
            try:
                ler(get(f"{mid}/insights", metric=m))
            except ErroApi as e:
                if len(erros) < 40:
                    erros.append(f"instagram post {m}: {limpar(e)}")
    return saida


def instagram():
    erros, saida = [], {"erros": erros}
    try:
        conta = ig_id()
        info = get(conta, fields="username,followers_count,follows_count,media_count")
        saida["conta"] = {"usuario": info.get("username"), "seguidores": numero(info.get("followers_count")),
                          "seguindo": numero(info.get("follows_count")), "posts": numero(info.get("media_count"))}
    except ErroApi as e:
        erros.append(f"instagram conta: {limpar(e)}")
        return saida

    hoje = dt.datetime.now(FUSO).replace(hour=0, minute=0, second=0, microsecond=0)
    metricas = ["reach", "views", "profile_views", "accounts_engaged", "total_interactions",
                "likes", "comments", "shares", "saves", "follows_and_unfollows"]
    saida["ontem"] = {m: ig_total(conta, m, hoje - dt.timedelta(days=1), hoje, erros) for m in metricas}
    saida["d7"] = {m: ig_total(conta, m, hoje - dt.timedelta(days=7), hoje, erros) for m in metricas}
    saida["d28"] = {m: ig_total(conta, m, hoje - dt.timedelta(days=28), hoje, erros) for m in metricas}
    saida["seguidores_por_dia"] = ig_seguidores_por_dia(conta, erros)

    posts = []
    try:
        r = get(f"{conta}/media", limit=30, fields="id,caption,media_type,media_product_type,timestamp,permalink,"
                                                  "thumbnail_url,media_url,like_count,comments_count")
        for m in r.get("data", []):
            tipo = m.get("media_product_type") or m.get("media_type")
            met = ig_metricas_post(m["id"], tipo, erros) if tipo != "STORY" else {}
            posts.append({
                "tipo": {"REELS": "reel", "FEED": "carrossel" if m.get("media_type") == "CAROUSEL_ALBUM" else "imagem"}.get(tipo, str(tipo).lower()),
                "quando": m.get("timestamp"),
                "legenda": (m.get("caption") or "")[:160],
                "link": m.get("permalink"),
                "imagem": m.get("thumbnail_url") or (m.get("media_url") if m.get("media_type") != "VIDEO" else None),
                "curtidas": numero(m.get("like_count")) if met.get("likes") is None else met.get("likes"),
                "comentarios": numero(m.get("comments_count")) if met.get("comments") is None else met.get("comments"),
                "alcance": met.get("reach"), "visualizacoes": met.get("views"),
                "salvos": met.get("saved"), "compartilhamentos": met.get("shares"),
                "interacoes": met.get("total_interactions"),
                "tempo_medio_ms": met.get("ig_reels_avg_watch_time"),
            })
    except ErroApi as e:
        erros.append(f"instagram posts: {limpar(e)}")
    saida["posts"] = posts
    return saida


# ---------------------------------------------------------------- Facebook

def facebook():
    erros, saida = [], {"erros": erros}
    try:
        pag = pagina_id()
        info = get(pag, fields="name,followers_count,fan_count")
        saida["conta"] = {"nome": info.get("name"), "seguidores": numero(info.get("followers_count")),
                          "curtidas": numero(info.get("fan_count"))}
    except ErroApi as e:
        erros.append(f"facebook página: {limpar(e)}")
        return saida
    d28 = {}
    for m in ["page_post_engagements", "page_views_total", "page_daily_follows_unique", "page_video_views",
              "page_impressions_unique", "page_media_view"]:
        try:
            r = get(f"{pag}/insights", metric=m, period="days_28")
            vals = r.get("data", [{}])[0].get("values", [])
            if vals:
                d28[m] = numero(vals[-1].get("value"))
        except (ErroApi, IndexError) as e:
            erros.append(f"facebook {m}: {limpar(e)}")
    saida["d28"] = d28
    return saida


# ---------------------------------------------------------------- YouTube

def youtube():
    erros, saida = [], {"erros": erros}
    if not os.environ.get("YT_REFRESH_TOKEN"):
        erros.append("youtube: segredos não configurados")
        return saida
    try:
        cab = {"Authorization": f"Bearer {yt_token()}"}
        api = "https://www.googleapis.com/youtube/v3"
        canal = _pedir("GET", f"{api}/channels", {"part": "snippet,statistics,contentDetails", "mine": "true"}, cabecalhos=cab)
        item = (canal.get("items") or [{}])[0]
        est = item.get("statistics", {})
        saida["conta"] = {"nome": item.get("snippet", {}).get("title"), "inscritos": numero(est.get("subscriberCount")),
                          "visualizacoes": numero(est.get("viewCount")), "videos": numero(est.get("videoCount"))}
        uploads = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        videos = []
        if uploads:
            lista = _pedir("GET", f"{api}/playlistItems", {"part": "contentDetails", "playlistId": uploads, "maxResults": "25"}, cabecalhos=cab)
            ids = ",".join(i["contentDetails"]["videoId"] for i in lista.get("items", []))
            if ids:
                det = _pedir("GET", f"{api}/videos", {"part": "snippet,statistics", "id": ids}, cabecalhos=cab)
                for v in det.get("items", []):
                    s, sn = v.get("statistics", {}), v.get("snippet", {})
                    videos.append({"titulo": sn.get("title"), "quando": sn.get("publishedAt"),
                                   "link": f"https://youtube.com/shorts/{v['id']}",
                                   "imagem": (sn.get("thumbnails", {}).get("medium") or {}).get("url"),
                                   "visualizacoes": numero(s.get("viewCount")), "curtidas": numero(s.get("likeCount")),
                                   "comentarios": numero(s.get("commentCount"))})
        saida["videos"] = videos
    except ErroApi as e:
        erros.append(f"youtube: {limpar(e)}")
    return saida


# ---------------------------------------------------------------- arquivo

def chave(senha, sal):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=sal, iterations=ITERACOES).derive(senha.encode())


def ler_anterior(senha):
    try:
        if CIFRADO.exists():
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            c = json.loads(CIFRADO.read_text())
            b = lambda k: base64.b64decode(c[k])  # noqa: E731
            return json.loads(AESGCM(chave(senha, b("sal"))).decrypt(b("iv"), b("dados"), None))
    except Exception as e:  # senha trocada ou arquivo corrompido: começa o histórico de novo
        print(f"histórico anterior ignorado: {e}")
    return {}


def gravar(dados, senha):
    DADOS.mkdir(exist_ok=True)
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    sal, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(chave(senha, sal)).encrypt(iv, texto.encode(), None)
    e = lambda b: base64.b64encode(b).decode()  # noqa: E731
    CIFRADO.write_text(json.dumps({"v": 1, "iteracoes": ITERACOES, "sal": e(sal), "iv": e(iv), "dados": e(ct)}) + "\n")


def main():
    senha = os.environ.get("ANALISES_SENHA", "")
    if not senha:
        print("Falta o segredo ANALISES_SENHA (Settings > Secrets and variables > Actions). Nada foi gravado.")
        sys.exit(1)
    anterior = ler_anterior(senha)
    ig, fb, yt = instagram(), facebook(), youtube()
    agora = dt.datetime.now(FUSO)
    hoje = agora.date().isoformat()
    foto = {
        "dia": hoje,
        "ig_seguidores": ig.get("conta", {}).get("seguidores"),
        "ig_alcance": (ig.get("ontem") or {}).get("reach"),
        "ig_visualizacoes": (ig.get("ontem") or {}).get("views"),
        "ig_interacoes": (ig.get("ontem") or {}).get("total_interactions"),
        "fb_seguidores": fb.get("conta", {}).get("seguidores"),
        "yt_inscritos": yt.get("conta", {}).get("inscritos"),
        "yt_visualizacoes": yt.get("conta", {}).get("visualizacoes"),
    }
    historico = [h for h in anterior.get("historico", []) if h.get("dia") != hoje] + [foto]
    dados = {"atualizado": agora.isoformat(timespec="minutes"), "instagram": ig, "facebook": fb,
             "youtube": yt, "historico": historico[-DIAS_HISTORICO:]}
    gravar(dados, senha)
    for rede, d in (("Instagram", ig), ("Facebook", fb), ("YouTube", yt)):
        print(f"{rede}: {'ok' if d.get('conta') else 'sem dados'}" + (f" ({len(d['erros'])} aviso(s))" if d["erros"] else ""))
        for e in d["erros"][:6]:
            print(f"  - {e}")
    print("Gravado em dados/analises.cifrado.json (cifrado)")


if __name__ == "__main__":
    main()
