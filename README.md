# jasabiadisso-midia

Robô de publicação do Já Sabia Disso? para Instagram, Facebook e YouTube.

- `agenda/`: os posts agendados, um por pasta (veja `agenda/README.md`).
- `publicador/publicar.py`: publica pelas APIs oficiais da Meta e do YouTube.
- `.github/workflows/publicar.yml`: roda o publicador a cada 15 minutos.

O repositório precisa ser público: o Instagram baixa as imagens pelo link
`raw.githubusercontent.com`. Os vídeos são enviados direto pelo robô.

Segredos (Settings > Secrets and variables > Actions): `META_TOKEN`,
`FB_PAGE_ID`, `IG_USER_ID` (opcional), `YT_CLIENT_ID`, `YT_CLIENT_SECRET`,
`YT_REFRESH_TOKEN`.

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
