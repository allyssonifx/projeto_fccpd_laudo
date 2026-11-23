import json
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError
from urllib.request import Request, urlopen


LIMITE = 8


def evento(nome, **campos):
    print(json.dumps({
        "utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "evento": nome,
        **campos,
    }), flush=True)


def requisicao(url, metodo="GET"):
    inicio = time.monotonic()
    try:
        resposta = urlopen(Request(url, method=metodo), timeout=0.8)
    except HTTPError as erro:
        resposta = erro
    with resposta:
        dados = json.load(resposta)
        return resposta.status, dados, time.monotonic() - inicio


class ServicoJson(BaseHTTPRequestHandler):
    def responder(self, status, dados):
        corpo = json.dumps(dados).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *_):
        pass
