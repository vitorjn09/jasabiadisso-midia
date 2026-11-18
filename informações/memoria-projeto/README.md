# Memória do projeto (Já Sabia Disso? / @jasabiadisso.br)

Regras finais do projeto, gravadas em 17/11/2026 a pedido do Vitor. Aqui fica só a regra que vale hoje, com a data e quem decidiu. O detalhe de cada assunto continua no arquivo apontado em cada seção.

**Como usar:** leia este índice e abra só a seção do assunto da tarefa. Quando este arquivo e um arquivo mais antigo discordarem, vale este (a lista de arquivos desatualizados está na seção 12). Quando o Vitor decidir algo novo, atualize a seção e a data.

Onde as coisas ficam:
- **Repositório** (este): robô de publicação, agenda, painel, biblioteca de vídeos prontos.
- **Pasta do projeto** (`/mnt/project-files/`): `informações/` (modelos, guias, lib), `produção/`, `reels/`, `storys/`, `carrosseis/`, `cronograma/`.
- **Skills da conta do Vitor:** `videos-animados`, `linguagem-tv-cinema`, `kits-videos`.

## Índice

1. [Agendamento e publicação](#1-agendamento-e-publicação)
2. [Produção (fluxo de cada vídeo)](#2-produção-fluxo-de-cada-vídeo)
3. [Custo e créditos](#3-custo-e-créditos)
4. [Os 3 quadros e os temas](#4-os-3-quadros-e-os-temas)
5. [Roteiro](#5-roteiro)
6. [Voz e duração](#6-voz-e-duração)
7. [Visual](#7-visual)
8. [Trilha e som](#8-trilha-e-som)
9. [Direitos de imagem e citação de terceiros](#9-direitos-de-imagem-e-citação-de-terceiros)
10. [Stories, carrosséis, cronograma e pastas](#10-stories-carrosséis-cronograma-e-pastas)
11. [Robô, contas e tokens (sem segredos)](#11-robô-contas-e-tokens-sem-segredos)
12. [Onde está cada skill e modelo](#12-onde-está-cada-skill-e-modelo)
13. [Pendências que dependem do Vitor](#13-pendências-que-dependem-do-vitor)

---

## 1. Agendamento e publicação

- Instagram, Facebook e YouTube saem só pelo robô deste repositório (`agenda/`). TikTok sai pelo Metricool; o robô para TikTok foi descartado (PR #32). (Vitor)
- Nunca agendar nem publicar sem pedido explícito do Vitor, e só o item que ele pediu. Horário só para os itens pedidos; sem horário fixo no cronograma nem nos lembretes. Na dúvida sobre item ou horário, confirmar antes. (Vitor, instruções do projeto)
- Vídeos novos vão para a biblioteca sem precisar de aprovação: ramo `entrada/<nome>` com `git add -f biblioteca/<nome>/video.mp4`, `capa.jpg` e `ficha.json` (o workflow `biblioteca.yml` cuida do resto). (Vitor)
- Post feito à mão também tem que aparecer em "Publicados" no painel. (Vitor)
- Antes de reenviar um post, conferir se há execução do robô em andamento ou na fila, para não postar duas vezes. (lição de 17/11/2026, PR #59)

## 2. Produção (fluxo de cada vídeo)

- Um vídeo de cada vez. Sempre informar quanto tempo a produção levou. (Vitor)
- Render na nuvem. Rodar `qa-video.py` antes de todo upload. (Vitor)
- Imagina se em 3D: alvo de render de cerca de 8 min. (Vitor)
- Animatic antes do render final (guia, parte 9). Equipe virtual de 15 cargos aprova ou devolve, com uma linha por cargo no registro do vídeo (guia, parte 12). (Vitor, 14/11/2026)
- Não mexer no vídeo do metrô. (Vitor)

## 3. Custo e créditos

- Voz ElevenLabs: gerar sem esperar aprovação; só perguntar se o custo sair fora do comum. Uma tomada só (`generations_count=1`). Conferir a voz inteira até o último quadro, sem corte. (Vitor)
- Método misto: fundos de IA da ElevenLabs + movimento em código (zoom, parallax, poeira). Sem plano em vídeo gerado (LTX), imagem em qualidade "low" (47 créditos), reaproveitar `informações/lib/fundos-ia/`. Zoom travado: nunca passa da borda da imagem. (Vitor, 13-14/11/2026; caiu de 2.895 para 1.123 créditos por vídeo)
- Flash, Turbo e v4 custam igual nesta conta (1 crédito por letra): a voz só fica mais barata com texto mais curto.
- Gerador de fundos pelo Gemini descartado (sem conta paga). ElevenLabs segue como gerador; PR #57 fica aberto sem merge. (Vitor, 17/11/2026)
- vidIQ sem créditos até 08/12/2026: usar a web e o painel do robô para pesquisa.

## 4. Os 3 quadros e os temas

- 3 reels por dia: **Ninguém te contou**, **Você já sabia** e **Imagina se**, na mesma área do dia, com assunto próprio em cada. (Vitor)
- Temas adultos e adolescentes, sérios; nada "bestinha" (o bocejo foi considerado bestinha). (Vitor, reforçado 17/11/2026)
- Lista de 63 temas: `informações/modelo/temas-adultos.md`. Tema novo passa pelo Vitor antes. (Vitor)
- Em alta (17/11/2026): revista The Economist "The World Ahead 2027" como pauta.
- Datas comemorativas sempre têm vídeo no dia ou perto. (instruções do projeto)
- Títulos novos: "Curiosidade do dia", sem número. (instruções do projeto)
- **Imagina se** = "imagina se você precisasse construir X": explica como funciona de verdade, o boneco faz certo e o vídeo mostra a evolução. Detalhe em `informações/modelo/modelo-imagina-se.md`. (Vitor)
- **Ninguém te contou**: ícones flat no fundo branco, legenda karaokê, troca a cada 1-2 s, sem ícone sobreposto, crédito OpenMoji. (Vitor)
- **Você já sabia** adulto: foto real ou número gigante, moldura dourada, sem rostinhos, trilha grave. (Vitor)

## 5. Roteiro

Regra completa: `informações/modelo/modelo-roteiro.md` (obrigatório em todo roteiro). (Vitor, 17/11/2026)

- Estrutura pelas métricas: gancho em até 3 s (conflito + número), pergunta aberta até 8 s, virada a cada 5-8 s, "e daí?" até 20 s, revelação, motivo de envio, fecho com pergunta que divide opinião ("comente X") e loop com o começo.
- Analítico e com enredo: uma dúvida no ar que prende até o fim. (Vitor, 17/11/2026)
- Tom: uma voz pensando alto, humor seco, fatos checáveis com fonte. Sem diálogo encenado e sem "teoria 1, teoria 2". (Vitor, 17/11/2026)
- Pausas entre as falas; nunca acelerar a voz. O diálogo do Economist foi aprovado, mas a troca de falas ficou rápida demais. (Vitor, 17/11/2026)
- Todo vídeo termina com "Você já sabia disso?", gravado no mesmo texto da narração (`regra-fecho.md`). (Vitor, 24/10/2026)
- Reescrita dos temas: lote 1 em `informações/modelo/roteiros-v2/lote-01.md`, aguardando OK do Vitor; depois lotes de 10.

## 6. Voz e duração

- Voz padrão: ElevenLabs "Antonio de Jesus", modelo eleven_v4, texto puro sem tags de direção (`regra-voz.md`). (Vitor, 24/10/2026)
- Duração livre: os 63 s **não** são mais regra. Pode passar disso, sem acelerar a voz nem cortar texto à força; o vídeo acaba quando a curiosidade acaba. (Vitor, 17/11/2026)

## 7. Visual

Regra completa: `informações/modelo/modelo-visual.md` (checklist obrigatório) e guia `informações/modelo/guia-roteiro-edicao-camera.md`.

- Paleta Pedra do Mar + dourado, legenda amarela em y=1600, fonte Anton, texto dentro da área visível. Sem emojis, sem rostinhos, sem "recriação ilustrativa". (Vitor)
- Estímulo visual a cada 1,5-2 s; nenhum plano parado por mais de 5 s. (Vitor)
- Fundo de IA realista (prompt de fotógrafo, qualidade low) com a etiqueta "RECONSTITUIÇÃO (IA)". (Vitor, 17/11/2026)
- Nunca uma foto sozinha por quadro: imagens reais ligadas por relação (versão x realidade, prova, antes/depois, linha do tempo) e animação que liga (círculo, linha, marca-texto, ponte entre planos). Fotos reais com crédito, nunca em fundo liso. (Vitor, 17/11/2026)
- Estilo aprovado (animatic-depois-v2): câmera na mão, fundo que reage, lupa, pessoas recortadas, pouso com mola, borrão de movimento, som por toque. Recorte de papel só como complemento opcional. (Vitor, 17/11/2026)
- Variar os tipos de animação; Imagina se com cerca de 47% 3D, 38% telas 2D e 15% fotos, nunca mais de 4 s seguidos no mesmo tipo. Capa do Imagina se com foto real na moldura dourada. Nada de listras ou letras piscando (`render-sem-pisca`). (Vitor)
- Capa = primeiro quadro do vídeo, já montado em t=0 (`regra-capa.md`). (Vitor, 24/10/2026)

## 8. Trilha e som

- A trilha casa com o tom do vídeo: padrão clima "curioso", mistério só se o tema pedir; vídeo sério não leva música animadinha, mas nada pesado demais. (Vitor, 13/11/2026)
- Volume cerca de 5 dB abaixo do antigo (guia: música 18-22 dB abaixo da voz, mix em -14 LUFS). (Vitor)
- Mixkit sem crédito; Kevin MacLeod exige crédito. Música famosa ou protegida não, nem com crédito (Content ID). (Vitor, 13/11/2026)

## 9. Direitos de imagem e citação de terceiros

- **Permitido (Vitor, 17/11/2026):** usar trecho, frame ou imagem de série, filme, produto ou marca (ex.: cena dos Simpsons, logo da Samsung ou NVIDIA, capa de revista) como recorte de referência, porque dá identidade e familiaridade.
- Sempre com crédito "Reprodução: <dono>" e etiqueta de fonte, ligado ao fato por animação.
- Trecho curto, só o necessário, como citação para comentário ou notícia. Nunca a música da obra, nunca como se a marca fosse do canal, nunca logo no lugar da marca do canal.
- Isso substitui a regra antiga de não usar obra de terceiros e de desenhar referências no estilo do canal.

## 10. Stories, carrosséis, cronograma e pastas

Regra completa: instruções do projeto e `informações/skill/SKILL.md`.

- Semana: segunda, quarta, sexta e domingo com 3 stories; carrossel na segunda e na sexta; reels todos os dias; um cronograma em imagem por semana. (instruções do projeto)
- Stories completos na imagem, sem enquete, quiz ou figurinha; o 3º é o teaser de amanhã e só sai depois do reel do dia. (Vitor, 01/11/2026)
- Carrossel: no máximo 3 a 4 slides, é um informativo do vídeo que vem depois; carrossel que não será usado é apagado. (instruções do projeto)
- Pastas: um item pronto vai para a pasta do dia em que sai; quando o dia passa, vai para "já postados". Nada pronto fica em `informações/`. (instruções do projeto)

## 11. Robô, contas e tokens (sem segredos)

Nenhum valor de token fica neste arquivo. O repositório é público.

- Instagram e YouTube usam o app antigo da Meta (token de página que não vence). Facebook usa o app novo, já publicado, pelo segredo `FB_PAGE_TOKEN` (vence por volta de 16/01/2027 ou se a senha do Facebook mudar). Ficam os dois apps; migrar o Instagram só se o Vitor quiser. (Vitor, 17/11/2026)
- Segredos são salvos sem espaço nem Enter no fim; o robô limpa e esconde tokens nos erros (PR #58).
- Revogar o app antigo = removê-lo nas Integrações comerciais do Facebook, nunca o app novo.
- Reels antigos do Facebook com 0 views ficam escondidos; reenviar só se o Vitor pedir.
- Painel do robô: comentários por post (PR #46), métricas e botão Imagina se (PR #47).

## 12. Onde está cada skill e modelo

Abra o arquivo só quando a tarefa precisar dele.

| O quê | Onde | Para quê |
|---|---|---|
| Skill `videos-animados` | skill da conta (no tamanho máximo) | fluxo geral de qualquer vídeo |
| Skill `linguagem-tv-cinema` | skill da conta (salva 14/11, seções 2.1 e 7 em 17/11) | linguagem de TV, equipe de 15 cargos, métricas, estilo visual aprovado |
| Skill `kits-videos` | skill da conta (salva 17/11) | kits e ferramentas grátis, QA |
| Skill do perfil | pasta do projeto: `informações/skill/SKILL.md` | stories, carrosséis, cronograma, pastas |
| Modelo de roteiro | `informações/modelo/modelo-roteiro.md` | roteiro pelas métricas, checklist |
| Modelo visual | `informações/modelo/modelo-visual.md` | fundo realista, relação de imagens, checklist |
| Modelo Imagina se | `informações/modelo/modelo-imagina-se.md` | quadro Imagina se |
| Guia completo | `informações/modelo/guia-roteiro-edicao-camera.md` (partes 1-13) | ler só a parte necessária |
| Voz, fecho, capa, narração | `informações/modelo/regra-voz.md`, `regra-fecho.md`, `regra-capa.md`, `regra-narracao.md` | detalhes da voz e da capa |
| Temas | `informações/modelo/temas-adultos.md`, `regra-temas-e-comentarios.md` | lista e famílias de temas |
| Bibliotecas de código | `informações/lib/` (kit-cena.js, modelos3d, fundos-ia, capa-foto.js, extras/) | montar cenas |
| Robô e painel | este repositório: `README.md`, `agenda/README.md`, `publicador/`, `painel/` | publicação e análises |

**Arquivos desatualizados** (não foram alterados; vale este documento):
- `informações/modelo/regra-duracao.md`: fala em 63 s fixos. Hoje a duração é livre (seção 6).
- `informações/modelo/regra-fotos-de-arquivo.md`: só domínio público. Hoje a citação com crédito é permitida (seção 9).
- `informações/skill/SKILL.md`: diz para não gastar créditos sem aprovar tema e roteiro. Hoje a voz e os vídeos da biblioteca saem sem aprovação; só tema novo passa pelo Vitor (seções 3 e 4).

## 13. Pendências que dependem do Vitor

- Cardápio de estilos variados (pelo menos 4 linguagens por vídeo, 3 tipos de texto animado, 4 transições), com teste de 15 s.
- Lote 1 dos roteiros v2.
- Merge dos PRs #48 a #57 (o #55 é o que ativa o app novo no Facebook).
- Cartões de melhoria das skills `kits-videos` e `linguagem-tv-cinema` (revisor externo, pré-visualização, cortes pela batida, zona segura de 310 px).
- Método misto como padrão oficial.
- Trilha dos 3 vídeos de GTA 6; volume da trilha do vídeo do apagão.
- Regra de modelo por tipo de tarefa (para economizar tokens).
