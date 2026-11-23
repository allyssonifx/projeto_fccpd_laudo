import os
from http.server import HTTPServer

from comum import ServicoJson, evento


# Duas listas de metadados com nomes iguais, como duas tabelas em bancos distintos.
metadados = ["campo_" + str(i) for i in range(5)]
versoes = {
    "valida": metadados,
    "duplicada": metadados + metadados,
    "rollback": metadados,
}
ativa = "valida"


class Publicador(ServicoJson):
    def do_GET(self):
        if self.path == "/config":
            self.responder(200, {"versao": ativa, "features": versoes[ativa]})
        elif self.path == "/origem":
            self.responder(200, {"origem": "ok"})
        else:
            self.responder(404, {"erro": "rota desconhecida"})

    def do_POST(self):
        global ativa
        nova = self.path.removeprefix("/publicar/")
        if nova not in ("duplicada", "rollback"):
            self.responder(404, {"erro": "versao desconhecida"})
            return
        ativa = nova
        dados = {"versao": ativa, "features": len(versoes[ativa])}
        evento("publicacao", **dados)
        self.responder(200, dados)


if __name__ == "__main__":
    evento("publicacao", versao=ativa, features=len(versoes[ativa]))
    HTTPServer((os.getenv("BIND", "0.0.0.0"), 8001), Publicador).serve_forever()
