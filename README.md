# Estudo de confiabilidade do proxy

Laboratório e laudo sobre o incidente da Cloudflare em novembro de 2025. A miniatura mede o impacto de um arquivo interno acima do limite de features e verifica se o proxy mantém o tráfego ao preservar a última versão válida. [Post-mortem oficial](https://blog.cloudflare.com/18-november-2025-outage/).

- [Laudo em PDF](output/pdf/laudo-cloudflare.pdf)
- [Registro de uso de IA](IA.md)
- [Evidências](logs/)

## Reprodução

Para a execução automatizada, use Docker com Compose V2 ou posterior, contêineres Linux, PowerShell 7 e Python 3 no PATH. Abra um terminal na raiz do repositório. A primeira execução pode baixar a imagem `python:3.12-alpine`. A miniatura usa duas redes internas. A sonda acessa o proxy pelo alias `proxy-trafego` na rede `trafego` e o publicador pela rede `config`.

```powershell
docker version
docker compose config --quiet
pwsh -File ./rodar.ps1
```

O script roda os modos base e mitigado em sequência, encerra cada rodada quando a sonda termina, coleta a saída e remove os contêineres. Por padrão usa `tmp/reproducao`. Para repetir, informe uma pasta vazia com `-Destino tmp/reproducao-2`. Se `pwsh` estiver fora do PATH, abra o script pelo caminho completo do executável do PowerShell 7. O modo Bash está abaixo.

Use `python lab/resumir.py logs/rodada-grupo` para recalcular os números do laudo a partir dos logs do grupo. A pasta `logs/execucao` contém a validação anterior do Codex.

### Execução manual com Bash

Esta sequência grava os eventos por serviço. Execute na raiz, com o Docker em funcionamento e escolha uma pasta nova para cada teste.

```bash
set -e
destino=$(mktemp -d ./reproducao.XXXXXX)
projeto="escobar-sre-$$"
trap 'docker compose -p "$projeto" down' EXIT
for modo in base mitigado; do
  MODO="$modo" docker compose -p "$projeto" --ansi never up \
    --abort-on-container-exit --exit-code-from sonda > "$destino/$modo.compose.log" 2>&1
  for servico in publicador proxy sonda; do
    docker compose -p "$projeto" logs --no-color --no-log-prefix "$servico" \
      > "$destino/$modo.$servico.jsonl"
  done
  docker compose -p "$projeto" down
done
trap - EXIT
python3 lab/resumir.py "$destino" | tee "$destino/resumo.log"
```

## O que observar

O publicador começa com uma versão válida. Depois de a sonda confirmar que o proxy está pronto, ela amostra o tráfego, publica a versão duplicada e pede a volta à versão válida anterior. O proxy consulta a configuração em intervalo próprio. A sonda aciona cada troca no mesmo número de amostra nos dois modos. Os tempos observados e a contagem de erros do modo base podem variar conforme o instante em que o proxy consulta o publicador.

- Em `base.proxy.jsonl`, procure `limite_excedido`. Em `base.sonda.jsonl`, procure HTTP 500 com `versao: duplicada` e eventual retorno do HTTP 200 com `versao: rollback`.
- Em `mitigado.proxy.jsonl`, procure `config_rejeitada` e `mantida: valida`. O status da sonda indica se o tráfego permaneceu disponível enquanto o publicador oferecia a configuração inválida.
- `origem_status` é o status de uma consulta direta por amostra. A análise usa como erro somente a requisição que passa pelo proxy. Os tempos são observados no fim de cada amostra, com resolução prática limitada pela cadência da sonda e pela consulta periódica do proxy.
- Os arquivos `*.compose.log` preservam a saída agregada do Compose. `*.jsonl` guardam os eventos emitidos pelos serviços. `resumo.log` registra o cálculo. `cloudflare-fonte.log` documenta a fonte histórica.
