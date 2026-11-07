"""TikTok pelo robô: envia o reel como rascunho para a caixa de entrada do TikTok.

Usa a Content Posting API, modo Upload (escopo video.upload). O vídeo chega
como notificação no app do TikTok; o Vitor abre, cola a legenda e toca em
Publicar. A API de rascunho não aceita legenda.

Segredos do repositório:
  TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET   do app em developers.tiktok.com
  TIKTOK_REFRESH_TOKEN                      gravado sozinho pelo modo tiktok_login
  SEGREDOS_TOKEN   token do GitHub (fine-grained, só este repositório, permissão
                   Secrets: Read and write). Serve para o robô guardar o
                   TIKTOK_REFRESH_TOKEN, que o TikTok às vezes troca.

O token de acesso vale 24 h e é renovado a cada uso; o de renovação vale 365 dias.
"""

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://open.tiktokapis.com/v2"
MB = 1024 * 1024
# Regras do envio em partes: cada parte de 5 a 64 MB, a última pode ter até 128 MB.
PARTE = 10 * MB
INTEIRO_ATE = 64 * MB


class ErroTikTok(Exception):
    pass


def configurado():
    return bool(os.environ.get("TIKTOK_CLIENT_KEY") and os.environ.get("TIKTOK_CLIENT_SECRET"))


def _http(metodo, url, dados=None, cabecalhos=None, tentativas=3):
    for tentativa in range(1, tentativas + 1):
        req = urllib.request.Request(url, data=dados, method=metodo, headers=cabecalhos or {})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                texto = resp.read().decode()
                return resp.status, (json.loads(texto) if texto.strip().startswith("{") else {})
        except urllib.error.HTTPError as e:
            texto = e.read().decode(errors="replace")
            if e.code >= 500 and tentativa < tentativas:
                time.sleep(5 * tentativa)
                continue
            raise ErroTikTok(f"{metodo} {url.split('?')[0]} -> {e.code}: {texto[:500]}") from None
        except urllib.error.URLError as e:
            if tentativa < tentativas:
                time.sleep(5 * tentativa)
                continue
            raise ErroTikTok(f"{metodo} {url.split('?')[0]} -> {e}") from None


def _api(metodo, caminho, acesso, corpo=None):
    cab = {"Authorization": f"Bearer {acesso}"}
    dados = None
    if corpo is not None:
        cab["Content-Type"] = "application/json; charset=UTF-8"
        dados = json.dumps(corpo).encode()
    _, r = _http(metodo, f"{API}/{caminho}", dados, cab)
    erro = r.get("error") or {}
    if erro.get("code") not in (None, "ok"):
        raise ErroTikTok(f"{caminho}: {erro.get('code')} {erro.get('message', '')}")
    return r.get("data") or {}


def _token(params):
    params = {"client_key": os.environ["TIKTOK_CLIENT_KEY"],
              "client_secret": os.environ["TIKTOK_CLIENT_SECRET"], **params}
    _, r = _http("POST", f"{API}/oauth/token/", urllib.parse.urlencode(params).encode(),
                 {"Content-Type": "application/x-www-form-urlencoded"})
    if "access_token" not in r:
        raise ErroTikTok(f"o TikTok não deu o token: {r.get('error')} {r.get('error_description', '')}".strip())
    return r


# ---------------------------------------------------------------- segredo no GitHub

def guardar_segredo(nome, valor):
    """Grava um segredo do repositório pela API do GitHub (cifrado com a chave do repo)."""
    gh = os.environ.get("SEGREDOS_TOKEN")
    if not gh:
        raise ErroTikTok("falta o segredo SEGREDOS_TOKEN para guardar o acesso do TikTok")
    from nacl import encoding, public  # pip install pynacl

    repo = os.environ.get("GITHUB_REPOSITORY", "vitorjn09/jasabiadisso-midia")
    base = f"https://api.github.com/repos/{repo}/actions/secrets"
    cab = {"Authorization": f"Bearer {gh}", "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}
    _, chave = _http("GET", f"{base}/public-key", cabecalhos=cab)
    caixa = public.SealedBox(public.PublicKey(chave["key"].encode(), encoding.Base64Encoder()))
    cifrado = base64.b64encode(caixa.encrypt(valor.encode())).decode()
    corpo = json.dumps({"encrypted_value": cifrado, "key_id": chave["key_id"]}).encode()
    _http("PUT", f"{base}/{nome}", corpo, {**cab, "Content-Type": "application/json"})
    os.environ[nome] = valor


def acesso():
    """Troca o token de renovação por um de acesso e guarda o novo, se o TikTok mudar."""
    atual = os.environ.get("TIKTOK_REFRESH_TOKEN")
    if not atual:
        raise ErroTikTok("TikTok ainda não conectado: use Conectar TikTok no painel")
    r = _token({"grant_type": "refresh_token", "refresh_token": atual})
    novo = r.get("refresh_token")
    if novo and novo != atual:
        guardar_segredo("TIKTOK_REFRESH_TOKEN", novo)
    return r["access_token"]


def login(codigo, redirect_uri):
    """Primeira conexão: troca o código que volta do TikTok pelo token e guarda."""
    if not codigo:
        raise ErroTikTok("faltou o código do TikTok")
    r = _token({"grant_type": "authorization_code", "code": codigo, "redirect_uri": redirect_uri})
    escopos = r.get("scope", "")
    if "video.upload" not in escopos:
        raise ErroTikTok(f"a conta não liberou o envio de vídeos (escopos: {escopos})")
    guardar_segredo("TIKTOK_REFRESH_TOKEN", r["refresh_token"])
    return conta(r["access_token"])


def conta(acesso_token=None):
    dados = _api("GET", "user/info/?fields=open_id,display_name", acesso_token or acesso())
    return dados.get("user", {}).get("display_name") or "(sem nome)"


# ---------------------------------------------------------------- envio

def _partes(tamanho):
    """Tamanho de cada parte e quantas são, seguindo as regras do TikTok."""
    if tamanho <= INTEIRO_ATE:
        return tamanho, 1
    return PARTE, tamanho // PARTE  # a sobra entra na última parte


def enviar_rascunho(video):
    """Manda o vídeo para a caixa de entrada do TikTok. Devolve o publish_id."""
    if video.suffix.lower() not in (".mp4", ".mov", ".webm"):
        raise ErroTikTok(f"o TikTok não aceita {video.suffix}")
    conteudo = video.read_bytes()
    total = len(conteudo)
    parte, qtd = _partes(total)
    tok = acesso()
    dados = _api("POST", "post/publish/inbox/video/init/", tok, {
        "source_info": {"source": "FILE_UPLOAD", "video_size": total,
                        "chunk_size": parte, "total_chunk_count": qtd}})
    url, ident = dados["upload_url"], dados["publish_id"]
    tipo = {".mov": "video/quicktime", ".webm": "video/webm"}.get(video.suffix.lower(), "video/mp4")
    for i in range(qtd):
        ini = i * parte
        fim = total if i == qtd - 1 else ini + parte
        pedaco = conteudo[ini:fim]
        _http("PUT", url, pedaco, {"Content-Type": tipo, "Content-Length": str(len(pedaco)),
                                   "Content-Range": f"bytes {ini}-{fim - 1}/{total}"})
    return ident, _esperar(tok, ident)


def _esperar(tok, ident, limite=180):
    """Confere se o vídeo chegou na caixa de entrada. Devolve o último status."""
    inicio, st = time.time(), ""
    while time.time() - inicio < limite:
        d = _api("POST", "post/publish/status/fetch/", tok, {"publish_id": ident})
        st = d.get("status", "")
        if st in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            return st
        if st == "FAILED":
            raise ErroTikTok(f"o TikTok recusou o vídeo: {d.get('fail_reason', 'sem motivo')}")
        time.sleep(10)
    return st or "PROCESSING"
