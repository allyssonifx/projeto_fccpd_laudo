import os
import time

from comum import evento, requisicao


PUBLICADOR = os.getenv("PUBLICADOR", "http://publicador:8001")
PROXY = os.getenv("PROXY", "http://proxy:8000")
INTERVALO = 0.2
TOTAL = 60
MUDANCAS = {11: "duplicada", 41: "rollback"}


def sondar(url):
    try:
        return requisicao(url)
    except OSError as erro:
        return 0, {"erro": str(erro)}, None


def aguardar_proxy():
    prazo = time.monotonic() + 20
    while time.monotonic() < prazo:
        status, dados, _ = sondar(PROXY + "/")
        if status == 200 and dados["versao"] == "valida":
            return
        time.sleep(INTERVALO)
    raise SystemExit("A versao valida nao ficou disponivel a tempo")


def medir():
    aguardar_proxy()
    evento("inicio_amostragem", intervalo_s=INTERVALO, amostras=TOTAL)
    inicio = time.monotonic()
    for numero in range(1, TOTAL + 1):
        if numero in MUDANCAS:
            versao = MUDANCAS[numero]
            status, dados, _ = requisicao(PUBLICADOR + "/publicar/" + versao, "POST")
            if status != 200:
                raise SystemExit(f"Falha ao publicar {versao}: HTTP {status}")
            evento("publicacao_confirmada", t_s=round(time.monotonic() - inicio, 6), **dados)
        status, dados, latencia = sondar(PROXY + "/")
        tempo_resposta = round(time.monotonic() - inicio, 6)
        origem, _, _ = sondar(PUBLICADOR + "/origem")
        evento("amostra", n=numero, t_s=tempo_resposta,
               status=status, origem_status=origem, versao=dados.get("versao"),
               latencia_ms=round(latencia * 1000, 3) if latencia is not None else None,
               detalhe=dados.get("erro"))
        time.sleep(max(0, inicio + numero * INTERVALO - time.monotonic()))
    evento("fim_amostragem")


if __name__ == "__main__":
    medir()
