# Ligar o TikTok ao robô

Com isso, cada reel agendado com a rede TikTok vai sozinho para a caixa de
entrada do seu TikTok, na hora marcada. Você recebe uma notificação no app,
abre o rascunho, cola a legenda e toca em **Publicar**. Leva uns 20 segundos.

O Metricool continua no TikTok até o teste abaixo funcionar.

## Por que rascunho e não post direto

Conferi as regras atuais do TikTok for Developers (novembro de 2026):

- Um app que não passou pela auditoria do TikTok só consegue postar direto como
  **privado** (só você vê), e a conta precisa estar no modo privado.
- A auditoria e a revisão do app recusam apps "para uso pessoal". As regras
  citam como exemplo de recusa "uma ferramenta para subir conteúdo nas contas
  que você ou sua equipe administram", que é exatamente o nosso robô. Por isso
  não vale pedir a auditoria.
- O caminho que sobra é o **modo sandbox** (teste) do app com o envio de
  **rascunho** (escopo `video.upload`). Ele não precisa de revisão e pode ter
  até 10 contas suas. O limite é de 5 rascunhos pendentes a cada 24 horas, o
  que dá folga para 1 reel por dia.
- O rascunho não leva legenda pela API: a legenda você cola no app.

## Passo a passo (uma vez só, uns 15 minutos)

### 1. Criar o app

1. Entre em <https://developers.tiktok.com> com a conta do TikTok do perfil
   (Log in, no canto de cima).
2. Abra **Manage apps** e toque em **Connect an app**. Escolha conta
   individual se perguntar. Dê o nome **Já Sabia Disso**.
3. Em cima da página do app, mude de **Production** para **Sandbox** e toque
   em **Create Sandbox**. Nome: `robo`. Tudo daqui para baixo é feito dentro
   do sandbox.

### 2. Configurar o sandbox

1. **App details**: preencha o que for obrigatório. Em **Platforms**, marque
   **Web** e use o site `https://painel-robo-sabia-dessa.vercel.app/`.
2. **Products** > **Add products**: adicione **Login Kit** e **Content Posting API**.
3. Em **Login Kit** > **Redirect URI** > Web, cole exatamente:
   `https://painel-robo-sabia-dessa.vercel.app/`
4. Em **Content Posting API**, deixe **Direct Post** desligado.
5. Em **Scopes**, confira que estão `user.info.basic` e `video.upload`.
6. Toque em **Apply changes**.
7. Em **Sandbox settings** > **Target users**, adicione a conta do TikTok do
   perfil (ele pede para entrar com ela). Pode levar até 1 hora para aparecer.
8. Em **Credentials** (do sandbox), copie a **Client key** e o
   **Client secret**.

### 3. Guardar as chaves no GitHub

Em <https://github.com/vitorjn09/jasabiadisso-midia/settings/secrets/actions>,
**New repository secret**, crie:

| Nome | Valor |
| --- | --- |
| `TIKTOK_CLIENT_KEY` | a Client key do sandbox |
| `TIKTOK_CLIENT_SECRET` | o Client secret do sandbox |
| `SEGREDOS_TOKEN` | um token novo do GitHub (veja abaixo) |

O `SEGREDOS_TOKEN` deixa o robô guardar sozinho o acesso do TikTok (o TikTok
às vezes troca esse acesso, e o robô precisa salvar o novo). Para criar:
<https://github.com/settings/personal-access-tokens/new>, nome `robo-segredos`,
validade a maior possível, **Only select repositories** >
`jasabiadisso-midia`, e em **Repository permissions** > **Secrets** escolha
**Read and write**. Mais nada. Gere e cole o valor no segredo.

### 4. Conectar pelo painel

1. Abra o painel (<https://painel-robo-sabia-dessa.vercel.app>) > aba **Robô**
   > **Conectar TikTok**.
2. Na primeira vez ele pede a **Client key** (a mesma do passo 2.8).
3. O TikTok abre e pede para autorizar. Autorize com a conta do perfil.
4. Você volta para o painel, que pergunta se pode rodar **Conectar TikTok**.
   Confirme. Em um minuto aparece `TikTok conectado: <nome da conta>`.
5. Rode **Testar conexão**: a linha do TikTok deve mostrar o nome da conta.

### 5. Primeiro teste

Me peça no chat para mandar um reel de teste para o TikTok. Ele chega como
rascunho e só sai se você tocar em Publicar, então dá para testar sem postar
nada. Se funcionar, os reels novos já saem com TikTok marcado e o Metricool
deixa de ser usado.

## Se der erro

- `TikTok ainda não conectado`: falta o passo 4.
- `falta o segredo SEGREDOS_TOKEN`: falta o passo 3.
- `invalid_grant` ou `refresh_token` inválido: o acesso venceu (dura 1 ano) ou
  foi revogado. Repita o passo 4.
- `scope_not_authorized`: no passo 4, a caixa de envio de vídeos ficou
  desmarcada. Repita o passo 4.
- `spam_risk_too_many_pending_share`: já há 5 rascunhos esperando no app.
  Publique ou apague os rascunhos antigos.
- Se o sandbox não aceitar o envio, o TikTok volta para o Metricool e eu procuro
  outro caminho.
