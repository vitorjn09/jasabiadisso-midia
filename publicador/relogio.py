#!/usr/bin/env python3
"""Relógio do robô: diz quanto falta para o próximo post da agenda.

O cron do GitHub (a cada 15 min) costuma atrasar horas. O workflow
relogio.yml usa este script para dormir até a hora exata do próximo post e
então chamar o publicador.

Imprime linhas KEY=valor para o GITHUB_OUTPUT:
  espera   segundos até o próximo post futuro (vazio se não houver)
  alvo     nome da pasta do próximo post
  vencidos quantos posts já passaram da hora e ainda não saíram
"""

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publicar import ATRASO_MAXIMO, agora, ler_estado, ler_posts  # noqa: E402

FINAIS = ("publicado", "atrasado", "falhou")


def main():
    proximo, alvo, vencidos = None, "", 0
    for pasta, p, erros in ler_posts():
        if erros or not p:
            continue
        estado = ler_estado(pasta)
        if all(estado.get(r, {}).get("status") in FINAIS for r in p["redes"]):
            continue
        quando = dt.datetime.fromisoformat(p["quando"])
        if quando <= agora():
            if agora() - quando <= ATRASO_MAXIMO:
                vencidos += 1
        elif proximo is None or quando < proximo:
            proximo, alvo = quando, pasta.name
    espera = int((proximo - agora()).total_seconds()) + 20 if proximo else ""
    print(f"espera={espera}")
    print(f"alvo={alvo}")
    print(f"vencidos={vencidos}")


if __name__ == "__main__":
    main()
