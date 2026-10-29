# Agenda de posts

Cada post é uma pasta aqui dentro, com um `post.json` e as mídias. O robô
(`.github/workflows/publicar.yml`) roda a cada 15 minutos, publica o que já
passou da hora e grava o resultado em `estado.json` na mesma pasta.

Nome da pasta: `AAAA-MM-DD-tipo-assunto`, por exemplo `2026-11-02-reel-polvo`.

```json
{
  "quando": "2026-11-02T18:00:00-03:00",
  "tipo": "reel",
  "redes": ["instagram", "facebook", "youtube"],
  "legenda": "Texto da legenda com #hashtags",
  "midias": ["video.mp4"],
  "capa": "capa.jpg",
  "titulo_facebook": "Título do reel no Facebook",
  "titulo_youtube": "Título do Short #shorts"
}
```

- `tipo`: `reel`, `carrossel` (2 a 10 imagens), `imagem` ou `story` (1 imagem ou vídeo).
- `redes`: `instagram`, `facebook`, `youtube` (no YouTube só reel). TikTok vai pelo Buffer.
- `capa`, `titulo_facebook`, `titulo_youtube` e `ia` (true se o conteúdo foi gerado por IA) são opcionais.
- O Instagram só aceita imagem em JPG: `python publicador/publicar.py --preparar` converte os PNG.
- Post com mais de 12 horas de atraso não é publicado (fica `atrasado`).
- Story com enquete ou quiz não entra aqui: a figurinha não pode ser posta pela API.

`estado.json` mostra, por rede: `publicado` (com o id), `erro` (tenta de novo
no próximo ciclo), `falhou` (desistiu depois de 3 erros) ou `atrasado`.
Depois de publicado em todas as redes, a pasta pode ser apagada.
