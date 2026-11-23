param([string]$Destino = 'tmp/reproducao')

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-Location $PSScriptRoot
$null = New-Item -ItemType Directory -Force -Path $Destino
if (Get-ChildItem -LiteralPath $Destino -Force) {
    throw "Use um diretório vazio para preservar as evidências anteriores: $Destino"
}

$projeto = "escobar-sre-$PID"
$modoAnterior = $env:MODO
try {
    foreach ($modo in @('base', 'mitigado')) {
        $env:MODO = $modo
        try {
            docker compose -p $projeto --ansi never up --abort-on-container-exit --exit-code-from sonda 2>&1 |
                Tee-Object -FilePath (Join-Path $Destino "$modo.compose.log")
            $resultado = $LASTEXITCODE
            foreach ($servico in @('publicador', 'proxy', 'sonda')) {
                docker compose -p $projeto logs --no-color --no-log-prefix $servico |
                    Set-Content -Encoding utf8 (Join-Path $Destino "$modo.$servico.jsonl")
                if ($LASTEXITCODE -ne 0) { throw "Falha ao coletar o log de $servico" }
            }
            if ($resultado -ne 0) { throw "A execução em modo $modo terminou com código $resultado" }
        } finally {
            docker compose -p $projeto down
        }
    }
    python lab/resumir.py $Destino | Tee-Object -FilePath (Join-Path $Destino 'resumo.log')
    if ($LASTEXITCODE -ne 0) { throw 'As evidências da execução estão incompletas' }
} finally {
    $env:MODO = $modoAnterior
}
