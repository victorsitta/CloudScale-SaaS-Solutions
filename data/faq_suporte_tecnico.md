# FAQ de Suporte Tecnico - CloudScale SaaS Solutions

Aqui estao as respostas para as principais duvidas tecnicas dos nossos clientes e parceiros de integracao.

## 1. Como resetar tokens de API
Se o seu token de API expirou ou foi exposto, siga o passo a passo para resetar:
1. Acesse o painel administrativo da CloudScale em `console.cloudscale.com`.
2. Navegue ate **Configuracoes da Conta** > **API & Integracoes**.
3. Localize o token atual e clique no botao **Revogar Token**.
4. Em seguida, clique em **Gerar Novo Token**.
5. Copie a nova chave imediatamente, pois ela nao sera exibida novamente.

## 2. Integracao via Webhooks
A CloudScale envia notificacoes em tempo real via Webhooks sobre eventos de billing e alteracoes de status de servidores.
- **Configuracao**: Va para a secao Webhooks no painel e insira a sua URL de recebimento (Endpoint).
- **Seguranca**: Validamos as chamadas adicionando uma assinatura `X-CloudScale-Signature` no header HTTP de cada requisicao.

## 3. Solucao para Erro HTTP 429 (Too Many Requests)
O erro HTTP 429 ocorre quando a sua aplicacao ultrapassa o limite de requisicoes permitidas por minuto para o seu plano:
- **Plano Starter**: Limite maximo de 60 requisicoes por minuto.
- **Plano Pro**: Limite maximo de 300 requisicoes por minuto.
- **Plano Enterprise**: Limite customizado.
**Como mitigar**: Implemente uma estrategia de retentativa com recuo exponencial (Exponential Backoff) e faça cache de dados estaticos localmente para reduzir as chamadas desnecessarias.
