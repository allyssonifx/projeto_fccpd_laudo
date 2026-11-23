import os
import threading
import time
from http.server import HTTPServer

from comum import LIMITE, ServicoJson, evento, requisicao


PUBLICADOR = os.getenv("PUBLICADOR", "http://publicador:8001")
MODO = os.getenv("MODO", "base")
INTERVALO_CONFIG = 0.4
ativa = None


def atualizar_config():
    global ativa
    vista = None
    while True:
        try:
            _, dados, _ = requisicao(PUBLICADOR + "/config")
        except OSError as erro:
            evento("config_indisponivel", erro=str(erro))
        else:
            versao = dados["versao"]
            if versao != vista:
                vista = versao
                features = len(dados["features"])
                excedeu = features > LIMITE
                if excedeu and MODO == "mitigado":
                    evento("config_rejeitada", versao=versao, features=features,
                           limite=LIMITE, mantida=ativa[0] if ativa else None)
                else:
                    ativa = (versao, excedeu)
                    evento("limite_excedido" if excedeu else "config_ativada",
                           versao=versao, features=features, limite=LIMITE)
        time.sleep(INTERVALO_CONFIG)


class Proxy(ServicoJson):
    def do_GET(self):
        if self.path != "/":
            self.responder(404, {"erro": "rota desconhecida"})
            return
        config = ativa
        if config is None:
            self.responder(503, {"erro": "aguardando config"})
            return
        versao, excedeu = config
        if excedeu:
            self.responder(500, {"erro": "limite excedido", "versao": versao})
            return
        try:
            status, dados, _ = requisicao(PUBLICADOR + "/origem")
        except OSError:
            self.responder(502, {"erro": "origem indisponivel", "versao": versao})
        else:
            self.responder(status, {"versao": versao, **dados})


if __name__ == "__main__":
    if MODO not in ("base", "mitigado"):
        raise SystemExit("MODO deve ser base ou mitigado")
    evento("proxy_iniciado", modo=MODO, limite=LIMITE, consulta_s=INTERVALO_CONFIG)
    threading.Thread(target=atualizar_config, daemon=True).start()
    HTTPServer((os.getenv("BIND", "0.0.0.0"), 8000), Proxy).serve_forever()
