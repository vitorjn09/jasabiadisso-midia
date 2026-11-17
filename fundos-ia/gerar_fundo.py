#!/usr/bin/env python3
"""Gera um fundo de IA (cenário realista 9:16) para os vídeos.

Provedores (seletor --provedor ou variável FUNDOS_PROVEDOR):
  gemini      (padrão) API de imagens do Gemini, "Nano Banana". Lê a chave do
              ambiente GEMINI_API_KEY (secret do repositório). Roda pelo
              workflow "Gerar fundo de IA" (.github/workflows/fundos-ia.yml).
  elevenlabs  (reserva) o ElevenLabs não tem chave neste robô: a imagem é feita
              pelo conector do ElevenLabs no chat, como antes
              (gpt-image-2.5-sunburst, 9:16, 2K, qualidade low, 47 créditos).
              O script só lembra o passo a passo e sai.

Cache: se o arquivo de saída já existe, não gera de novo (não gasta nada).
Os fundos prontos ficam em informações/lib/fundos-ia/<pasta>/<nome>.jpg.

O prompt segue o molde de fotógrafo de informações/modelo/modelo-visual.md
(seção 1). Se o texto não trouxer as restrições, elas são acrescentadas.

Só usa a biblioteca padrão do Python (Pillow é opcional, para salvar em JPG).
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta"
API_REVISION = "2026-05-20"

MODELO_PADRAO = "gemini-nano-banana-2.1"

# Preço oficial por imagem (ai.google.dev/gemini-api/docs/pricing, 17/11/2026),
# em dólar, chamada normal. Só para anotar na ficha; a cobrança real é a do Google.
PRECO_USD = {
    ("gemini-nano-banana-2.1", "1K"): 0.0336,
    ("gemini-nano-banana-2.1", "2K"): 0.0504,
    ("gemini-nano-banana-2.1", "4K"): 0.113,
    ("gemini-3.1-flash-image", "1K"): 0.067,
    ("gemini-3.1-flash-image", "2K"): 0.101,
    ("gemini-3.1-flash-image", "4K"): 0.151,
    ("gemini-3.1-flash-lite-image", "1K"): 0.0336,
}

# Restrições fixas do molde realista (modelo-visual.md, itens 5 e 6).
RESTRICOES = (
    "Photographic realism, not an illustration, not a painting, not a 3D render, "
    "no outlines, no flat colors. No readable text, no logos, no close-up faces, "
    "no recognizable landmarks unless named above. Natural film grain, gentle "
    "vignetting, slightly imperfect exposure, real-world muted colors. Keep the "
    "upper 15% sky and the lower 20-25% ground simple."
)
ABERTURA = "Vertical background plate for a short documentary video."


def montar_prompt(texto: str) -> str:
    texto = " ".join(texto.split())
    partes = []
    if "background plate" not in texto.lower():
        partes.append(ABERTURA)
    partes.append(texto)
    if "not an illustration" not in texto.lower():
        partes.append(RESTRICOES)
    return " ".join(partes)


def _post(url: str, corpo: dict, chave: str, extra: dict | None = None) -> dict:
    cab = {"x-goog-api-key": chave, "Content-Type": "application/json"}
    cab.update(extra or {})
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers=cab, method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def _achar_imagens(no, achadas: list) -> None:
    """Procura blocos de imagem em base64 em qualquer formato de resposta."""
    if isinstance(no, dict):
        tipo = str(no.get("mime_type") or no.get("mimeType") or "")
        dado = no.get("data")
        if isinstance(dado, str) and tipo.startswith("image/") and len(dado) > 1000:
            achadas.append((tipo, dado))
        for v in no.values():
            _achar_imagens(v, achadas)
    elif isinstance(no, list):
        for v in no:
            _achar_imagens(v, achadas)


def gerar_gemini(prompt: str, modelo: str, tamanho: str, proporcao: str, chave: str) -> tuple[bytes, str]:
    # 1) API "interactions" (formato atual da documentação).
    corpo = {
        "model": modelo,
        "input": [{"type": "text", "text": prompt}],
        "response_format": {
            "type": "image",
            "mime_type": "image/jpeg",
            "aspect_ratio": proporcao,
            "image_size": tamanho,
        },
    }
    erro_novo = None
    try:
        resp = _post(f"{API}/interactions", corpo, chave, {"Api-Revision": API_REVISION})
        achadas: list = []
        _achar_imagens(resp, achadas)
        if achadas:
            tipo, dado = achadas[-1]
            return base64.b64decode(dado), tipo
        erro_novo = "resposta sem imagem: " + json.dumps(resp)[:600]
    except urllib.error.HTTPError as e:
        erro_novo = f"HTTP {e.code}: {e.read().decode(errors='replace')[:600]}"

    # 2) Reserva: generateContent (formato antigo, ainda aceito por vários modelos).
    corpo2 = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": proporcao, "imageSize": tamanho},
        },
    }
    try:
        resp = _post(f"{API}/models/{modelo}:generateContent", corpo2, chave)
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"Gemini recusou o pedido.\n interactions: {erro_novo}\n generateContent: "
            f"HTTP {e.code}: {e.read().decode(errors='replace')[:600]}"
        )
    achadas = []
    _achar_imagens(resp, achadas)
    if not achadas:
        raise SystemExit("Gemini respondeu sem imagem (pode ter sido bloqueio de conteúdo): "
                         + json.dumps(resp)[:800])
    tipo, dado = achadas[-1]
    return base64.b64decode(dado), tipo


def salvar_jpg(dados: bytes, destino: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image  # opcional
    except ImportError:
        destino.write_bytes(dados)
        return None
    img = Image.open(io.BytesIO(dados)).convert("RGB")
    img.save(destino, "JPEG", quality=92, optimize=True)
    return img.size


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nome", required=True, help="nome do arquivo, sem extensão (ex.: campo-santana-1889)")
    ap.add_argument("--pasta", default="realista", help="subpasta de fundos-ia (padrão: realista)")
    ap.add_argument("--prompt", help="descrição da cena (molde de fotógrafo, em inglês)")
    ap.add_argument("--prompt-arquivo", help="ler o prompt de um arquivo de texto")
    ap.add_argument("--saida", default="saida-fundos", help="pasta raiz onde salvar (padrão: saida-fundos)")
    ap.add_argument("--provedor", default=os.environ.get("FUNDOS_PROVEDOR", "gemini"),
                    choices=["gemini", "elevenlabs"])
    ap.add_argument("--modelo", default=os.environ.get("GEMINI_MODELO_IMAGEM", MODELO_PADRAO))
    ap.add_argument("--tamanho", default="2K", choices=["1K", "2K", "4K"])
    ap.add_argument("--proporcao", default="9:16")
    ap.add_argument("--forcar", action="store_true", help="gera de novo mesmo se já existir")
    a = ap.parse_args()

    texto = a.prompt or (Path(a.prompt_arquivo).read_text(encoding="utf-8") if a.prompt_arquivo else "")
    if not texto.strip():
        ap.error("informe --prompt ou --prompt-arquivo")
    prompt = montar_prompt(texto)

    destino = Path(a.saida) / a.pasta / f"{a.nome}.jpg"
    if destino.exists() and not a.forcar:
        print(f"Já existe no cache, nada gerado: {destino}")
        return 0

    if a.provedor == "elevenlabs":
        print(
            "Reserva ElevenLabs: gerar pelo conector do ElevenLabs no chat, modelo gpt-image-2.5-sunburst, "
            "9:16, 2K, qualidade low (47 créditos), 1 variação, com este prompt:\n\n" + prompt +
            f"\n\nDepois salvar em informações/lib/fundos-ia/{a.pasta}/{a.nome}.jpg e anotar no LEIA.md. "
            "Crédito na tela: 'Cenário: reconstituição gerada com IA (ElevenLabs)'."
        )
        return 2

    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not chave:
        print("Falta o secret GEMINI_API_KEY (Settings > Secrets and variables > Actions).", file=sys.stderr)
        return 1

    t0 = time.time()
    dados, tipo = gerar_gemini(prompt, a.modelo, a.tamanho, a.proporcao, chave)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tam = salvar_jpg(dados, destino)
    seg = round(time.time() - t0, 1)

    ficha = {
        "nome": a.nome,
        "pasta": a.pasta,
        "provedor": "gemini",
        "modelo": a.modelo,
        "tamanho": a.tamanho,
        "proporcao": a.proporcao,
        "pixels": list(tam) if tam else None,
        "mime_original": tipo,
        "custo_estimado_usd": PRECO_USD.get((a.modelo, a.tamanho)),
        "segundos": seg,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "credito_na_tela": "Cenário: reconstituição gerada com IA (Gemini)",
        "etiqueta": "RECONSTITUIÇÃO (IA)",
        "prompt": prompt,
    }
    destino.with_suffix(".json").write_text(json.dumps(ficha, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gerado: {destino} ({tam[0]}x{tam[1]}) em {seg}s" if tam else f"Gerado: {destino} em {seg}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
