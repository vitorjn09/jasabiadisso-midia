# jasabiadisso-midia

Robô de publicação do Já Sabia Disso? para Instagram, Facebook, YouTube e TikTok.

- `agenda/`: os posts agendados, um por pasta (veja `agenda/README.md`).
- `publicador/publicar.py`: publica pelas APIs oficiais da Meta e do YouTube.
- `.github/workflows/publicar.yml`: roda o publicador a cada 15 minutos.

O repositório precisa ser público: o Instagram baixa as imagens pelo link
`raw.githubusercontent.com`. Os vídeos são enviados direto pelo robô.

Segredos (Settings > Secrets and variables > Actions): `META_TOKEN`,
`FB_PAGE_ID`, `IG_USER_ID` (opcional), `YT_CLIENT_ID`, `YT_CLIENT_SECRET`,
`YT_REFRESH_TOKEN`. TikTok: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` e
`SEGREDOS_TOKEN` (token do GitHub com Secrets: Read and write, para o robô
guardar `TIKTOK_REFRESH_TOKEN` sozinho). Veja `docs/conectar-tiktok.md`.

Teste manual: aba Actions > Publicar posts > Run workflow, com modo `conexao`
(confere os acessos) ou `verificar` (confere os posts sem publicar).

## Painel

`painel/index.html` é uma página para usar o robô sem mexer no GitHub: mostra
a agenda e o estado de cada post, deixa adicionar, editar e apagar posts e
rodar o robô (testar conexão, verificar, publicar) com confirmação antes.
Abra o arquivo no navegador, ou ative o GitHub Pages (Settings > Pages >
Deploy from a branch > `main` / root) e use
`https://vitorjn09.github.io/jasabiadisso-midia/painel/`. Para mudar algo,
a página pede um token do GitHub (fine-grained, só este repositório, com
Contents e Actions em Read and write), que fica guardado só no navegador.

## Análises

`.github/workflows/analises.yml` roda `publicador/analises.py` uma vez por dia
(e pelo botão "Atualizar números" do painel). Ele busca seguidores, alcance,
visualizações, interações e os melhores posts do Instagram, a página do
Facebook e o canal do YouTube, e grava tudo cifrado em
`dados/analises.cifrado.json`. Crie o segredo `ANALISES_SENHA` com uma senha
e digite a mesma senha no painel (Conectar > Senha das análises). O token da
Meta precisa das permissões `instagram_manage_insights` e `read_insights`.

## Biblioteca e cronograma

- `biblioteca/<nome>/`: ficha (`ficha.json`) e capa de cada vídeo pronto. O vídeo fica na Release
  `biblioteca`, fora do repositório. Para incluir um vídeo, envie `biblioteca/<nome>/video.mp4`,
  `capa.jpg` e `ficha.json` num ramo `entrada/<nome>`: o workflow `biblioteca.yml` sobe o vídeo
  para a Release, leva a ficha e a capa para a `main` e apaga o ramo.
- `cronograma/cronograma.json`: o plano de conteúdo, editado pela aba Cronograma do painel.
- `relogio.yml`: faz o robô publicar na hora certa, sem depender do cron do GitHub.
