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

# Comentários: só leitura, para dar ideias de temas. O robô não responde nada.
# Guarda só o texto, a data e as curtidas (sem o nome de quem comentou) e tira
# os comentários do próprio perfil.
COMENT_POR_POST = 100
COMENT_TAMANHO = 500


def paginar(r, maximo=300):
    """Junta as páginas da Graph API (segue paging.next) para pegar todos os posts."""
    itens = list(r.get("data", []))
    while len(itens) < maximo and (r.get("paging") or {}).get("next"):
        r = _pedir("GET", r["paging"]["next"])
        itens += r.get("data", [])
    return itens


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


def comentario(texto, quando, curtidas=None, respostas=None):
    return {"texto": str(texto or "").strip()[:COMENT_TAMANHO], "quando": quando,
            "curtidas": numero(curtidas), "respostas": numero(respostas)}


def recentes_primeiro(lista):
    return sorted((c for c in lista if c["texto"]), key=lambda c: c.get("quando") or "", reverse=True)


def aviso_comentarios(erros, rede, e, falta):
    erros.append(f"{rede} comentários: {limpar(e)} (falta {falta})")


# ---------------------------------------------------------------- Instagram

def ig_comentarios(mid, meu_usuario):
    r = get(f"{mid}/comments", fields="text,username,timestamp,like_count,replies.limit(0).summary(true)", limit=50)
    lista = []
    for c in paginar(r, COMENT_POR_POST):
        if meu_usuario and (c.get("username") or "").lower() == meu_usuario.lower():
            continue
        lista.append(comentario(c.get("text"), c.get("timestamp"), c.get("like_count"),
                                ((c.get("replies") or {}).get("summary") or {}).get("total_count")))
    return recentes_primeiro(lista)[:COMENT_POR_POST]


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
        dados = r.get("data") or []
        if not dados:  # a Meta só libera esse dado para contas com 100 seguidores ou mais
            return []
        valores = dados[0].get("values", [])
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
    erros = []; saida = {"erros": erros}
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
        r = get(f"{conta}/media", limit=100, fields="id,caption,media_type,media_product_type,timestamp,permalink,"
                                                  "thumbnail_url,media_url,like_count,comments_count")
        for m in paginar(r):
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
                "id": m["id"],
            })
    except ErroApi as e:
        erros.append(f"instagram posts: {limpar(e)}")
    sem_acesso = False
    for x in posts:
        mid = x["id"]
        if sem_acesso or not x.get("comentarios"):
            continue
        try:
            x["comentarios_lista"] = ig_comentarios(mid, saida["conta"].get("usuario"))
        except ErroApi as e:
            aviso_comentarios(erros, "instagram", e, "a permissão instagram_manage_comments no META_TOKEN")
            sem_acesso = True
    saida["posts"] = posts
    return saida


# ---------------------------------------------------------------- Facebook

def facebook():
    erros = []; saida = {"erros": erros}
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
              "page_media_view"]:
        try:
            r = get(f"{pag}/insights", metric=m, period="days_28")
            vals = r.get("data", [{}])[0].get("values", [])
            if vals:
                d28[m] = numero(vals[-1].get("value"))
        except (ErroApi, IndexError) as e:
            erros.append(f"facebook {m}: {limpar(e)}")
    saida["d28"] = d28
    saida["posts"] = fb_posts(pag, erros)
    return saida


def fb_posts(pag, erros):
    posts = []
    try:
        r = get(f"{pag}/posts", limit=100, fields="id,message,created_time,permalink_url,full_picture,shares,"
                                                  "reactions.summary(total_count).limit(0),comments.summary(total_count).limit(0)")
    except ErroApi as e:
        erros.append(f"facebook posts: {limpar(e)}")
        return posts
    aviso = sem_acesso = False
    for m in paginar(r):
        reacoes = numero((m.get("reactions") or {}).get("summary", {}).get("total_count"))
        coment = numero((m.get("comments") or {}).get("summary", {}).get("total_count"))
        compart = numero((m.get("shares") or {}).get("count")) or 0
        views = None
        try:
            ins = get(f"{m['id']}/insights", metric="post_media_view")
            vals = (ins.get("data") or [{}])[0].get("values", [])
            views = numero(vals[-1].get("value")) if vals else None
        except (ErroApi, IndexError) as e:
            if not aviso:
                erros.append(f"facebook visualizações dos posts: {limpar(e)}")
                aviso = True
        item = {
            "quando": m.get("created_time"), "legenda": (m.get("message") or "")[:160],
            "link": m.get("permalink_url"), "imagem": m.get("full_picture"),
            "visualizacoes": views, "reacoes": reacoes, "comentarios": coment, "compartilhamentos": compart,
            "interacoes": (reacoes or 0) + (coment or 0) + compart,
            "id": m.get("id"),
        }
        if coment and not sem_acesso:
            try:
                item["comentarios_lista"] = fb_comentarios(m["id"], pag)
            except ErroApi as e:
                aviso_comentarios(erros, "facebook", e, "a permissão pages_read_user_content no META_TOKEN")
                sem_acesso = True
        posts.append(item)
    return posts


def fb_comentarios(post_id, pag):
    r = get(f"{post_id}/comments", fields="message,created_time,like_count,comment_count,from{id}",
            filter="toplevel", order="reverse_chronological", limit=50)
    lista = []
    for c in paginar(r, COMENT_POR_POST):
        if (c.get("from") or {}).get("id") == str(pag):
            continue
        lista.append(comentario(c.get("message"), c.get("created_time"), c.get("like_count"), c.get("comment_count")))
    return recentes_primeiro(lista)[:COMENT_POR_POST]


# ---------------------------------------------------------------- YouTube

def youtube():
    erros = []; saida = {"erros": erros}
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
            ids_todos, pag_token = [], None
            while len(ids_todos) < 500:
                params = {"part": "contentDetails", "playlistId": uploads, "maxResults": "50"}
                if pag_token:
                    params["pageToken"] = pag_token
                lista = _pedir("GET", f"{api}/playlistItems", params, cabecalhos=cab)
                ids_todos += [i["contentDetails"]["videoId"] for i in lista.get("items", [])]
                pag_token = lista.get("nextPageToken")
                if not pag_token:
                    break
            itens_det = []
            for k in range(0, len(ids_todos), 50):
                det = _pedir("GET", f"{api}/videos", {"part": "snippet,statistics", "id": ",".join(ids_todos[k:k + 50])}, cabecalhos=cab)
                itens_det += det.get("items", [])
            if ids_todos:
                for v in itens_det:
                    s, sn = v.get("statistics", {}), v.get("snippet", {})
                    videos.append({"titulo": sn.get("title"), "quando": sn.get("publishedAt"),
                                   "link": f"https://youtube.com/shorts/{v['id']}",
                                   "imagem": (sn.get("thumbnails", {}).get("medium") or {}).get("url"),
                                   "visualizacoes": numero(s.get("viewCount")), "curtidas": numero(s.get("likeCount")),
                                   "comentarios": numero(s.get("commentCount")), "id": v["id"]})
        meu_canal = item.get("id")
        sem_acesso = False
        for x in videos:
            vid = x.get("id")
            if sem_acesso or not x.get("comentarios"):
                continue
            try:
                x["comentarios_lista"] = yt_comentarios(api, cab, vid, meu_canal)
            except ErroApi as e:
                aviso_comentarios(erros, "youtube", e, "a permissão youtube.force-ssl no YT_REFRESH_TOKEN")
                sem_acesso = True
        saida["videos"] = videos
    except ErroApi as e:
        erros.append(f"youtube: {limpar(e)}")
    return saida


def yt_comentarios(api, cab, vid, meu_canal):
    lista, pag_token = [], None
    while len(lista) < COMENT_POR_POST:
        params = {"part": "snippet", "videoId": vid, "maxResults": "100", "order": "time", "textFormat": "plainText"}
        if pag_token:
            params["pageToken"] = pag_token
        r = _pedir("GET", f"{api}/commentThreads", params, cabecalhos=cab)
        for t in r.get("items", []):
            sn = t.get("snippet", {})
            c = (sn.get("topLevelComment") or {}).get("snippet", {})
            if meu_canal and (c.get("authorChannelId") or {}).get("value") == meu_canal:
                continue
            lista.append(comentario(c.get("textDisplay"), c.get("publishedAt"), c.get("likeCount"), sn.get("totalReplyCount")))
        pag_token = r.get("nextPageToken")
        if not pag_token:
            break
    return recentes_primeiro(lista)[:COMENT_POR_POST]


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
