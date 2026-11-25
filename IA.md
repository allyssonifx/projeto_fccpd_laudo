# Registro de uso de IA

O Codex consultou a fonte, escreveu a implementação e o laudo e fez uma rodada de validação registrada em `logs/execucao/`. Depois, o grupo executou os dois cenários no próprio terminal e gerou os arquivos em `logs/rodada-grupo/`. O Codex recalculou as métricas a partir desses logs e atualizou o laudo com os resultados da execução do grupo.

## Prompts e decisões registradas

As citações são trechos de quatro mensagens distintas enviadas ao Codex. As decisões abaixo foram confirmadas pelo grupo após a execução e a conferência dos resultados.

| Trecho do prompt | O que o grupo aceitou, mudou ou descartou |
| --- | --- |
| “Reproduzir em miniatura, com Docker Compose, o mecanismo central do incidente.” | Aceitamos dividir a miniatura em publicador, proxy e sonda e usar HTTP 500 para representar o efeito da falha no tráfego. O Codex implementou a miniatura. |
| “Avalie se o que foi pedido foi entregue e se o projeto está dentro das regras do uso de IA.” | Aceitamos os ajustes de rastreabilidade na auditoria. Corrigimos a identificação do projeto da disciplina e descartamos o parecer sobre o projeto que havia sido analisado inicialmente. O Codex refez o parecer para este repositório e atualizou as métricas com os logs da nossa rodada. |
| “O que faltar pra fechar a entrega faça, simule tudo que for preciso” | Aceitamos trocar o nome genérico `proxy` pelo alias `proxy-trafego`, exclusivo da rede `trafego`. O Codex aplicou a correção e repetiu a validação. Depois, conferimos a diferença nas duas configurações do Compose. |
| “pwsh : O termo 'pwsh' não é reconhecido como nome de cmdlet, função, arquivo de script ou programa operável.” | Reportamos o erro e usamos a solução proposta pelo Codex, que localizou o executável de PowerShell 7 na máquina. Usamos o caminho completo para rodar os dois cenários e gerar os logs do laudo. |

## Erros da IA verificados pelo grupo

1. **Comando de execução incompatível com o terminal usado.** Ao seguir a instrução do Codex, o grupo recebeu `CommandNotFoundException` porque `pwsh` estava fora do `PATH`. A correção foi chamar o executável do PowerShell 7 pelo caminho completo. Os logs em `logs/rodada-grupo/` registram a conclusão dos dois cenários após a correção.

   Trecho da tentativa original relatada pelo grupo:

   ```text
   pwsh -File ./rodar.ps1 -Destino logs/rodada-grupo
   FullyQualifiedErrorId : CommandNotFoundException
   ```

2. **A configuração original deixava indefinida a rede de acesso ao proxy.** O diagrama produzido pelo Codex indicava `trafego`, mas a sonda usava o nome genérico `proxy`, e os dois serviços compartilhavam também a rede `config`. O Codex definiu `PROXY=http://proxy-trafego:8000` para a sonda em `docker-compose.yml` e registrou o alias exclusivamente em `trafego`. O grupo executou o teste de comparação das duas configurações resolvidas com `docker compose config` e reportou a saída abaixo. As métricas do laudo vieram da rodada do grupo.

```text
Antes: sonda e proxy compartilhavam config e trafego; PROXY não estava definido no Compose.
Depois: PROXY=http://proxy-trafego:8000; o alias existe somente na rede trafego.
```

## Erros da IA verificados e corrigidos pelo Codex

1. **Hora da amostra incluía a consulta de controle.** Na versão piloto de `lab/sonda.py`, o Codex calculava `t_s` depois de consultar também a origem. Durante a conferência da saída piloto, foi detectado que a marca misturava o fim da resposta do proxy com o de uma segunda requisição. A versão final guarda `tempo_resposta` logo que o proxy responde, antes de consultar a origem. Os dois cenários foram executados novamente e as métricas finais foram recalculadas.
2. **Diagrama sobreposto ao texto no primeiro PDF.** A rotina de desenho definia a altura do diagrama na classe, mas a inicialização do ReportLab zerava a altura na instância. A primeira renderização mostrou a figura por cima do título e do parágrafo. A correção foi definir largura e altura depois da inicialização e renderizar as quatro páginas novamente.
