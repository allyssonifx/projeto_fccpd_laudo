"""Calcula os indicadores somente a partir dos eventos brutos da sonda e do proxy."""

import json
import sys
from pathlib import Path


def ler(pasta, modo, servico):
    arquivo = pasta / f"{modo}.{servico}.jsonl"
    return [json.loads(linha) for linha in arquivo.read_text(encoding="utf-8-sig").splitlines()
            if linha.strip()]


def resumir(pasta, modo):
    sonda = ler(pasta, modo, "sonda")
    proxy = ler(pasta, modo, "proxy")
    publicador = ler(pasta, modo, "publicador")
    publicacoes = {e["versao"]: e for e in sonda if e["evento"] == "publicacao_confirmada"}
    inicio = next(e for e in sonda if e["evento"] == "inicio_amostragem")
    amostras = [e for e in sonda if e["evento"] == "amostra"]
    assert len(amostras) == inicio["amostras"] and sonda[-1]["evento"] == "fim_amostragem"
    assert [a["n"] for a in amostras] == list(range(1, len(amostras) + 1))
    duplicada = publicacoes["duplicada"]["t_s"]
    rollback = publicacoes["rollback"]["t_s"]
    assert [e["versao"] for e in publicador if e["evento"] == "publicacao"] == [
        "valida", "duplicada", "rollback"]
    assert amostras[0]["versao"] == "valida" and amostras[-1]["versao"] == "rollback"

    erros = [a for a in amostras if not 200 <= a["status"] < 300]
    recuperada = next(a for a in amostras if a["versao"] == "rollback" and a["status"] == 200)
    janela = [a for a in amostras if duplicada <= a["t_s"] < rollback]
    primeiro_apos_publicacao = janela[0]
    primeiro_apos_rollback = next(a for a in amostras if a["t_s"] >= rollback)
    falha = erros[0] if erros else None
    excesso = next(e for e in proxy if e["evento"] ==
                   ("limite_excedido" if modo == "base" else "config_rejeitada"))
    assert all(a["origem_status"] == 200 for a in amostras)
    assert all(a["status"] == 500 and a["versao"] == "duplicada" for a in erros)
    assert bool(erros) == (modo == "base")
    assert sum(e["evento"] == "proxy_iniciado" for e in proxy) == 1
    return {
        "modo": modo,
        "amostras": len(amostras),
        "origem_200": sum(a["origem_status"] == 200 for a in amostras),
        "proxy_200": sum(a["status"] == 200 for a in amostras),
        "erros": len(erros),
        "erro_pct": round(100 * len(erros) / len(amostras), 2),
        "limite": excesso["limite"],
        "features_por_versao": {e["versao"]: e["features"] for e in publicador},
        "intervalo_sonda_s": inicio["intervalo_s"],
        "intervalo_proxy_s": next(e["consulta_s"] for e in proxy if e["evento"] == "proxy_iniciado"),
        "publicacao_confirmada_s": duplicada,
        "rollback_confirmado_s": rollback,
        "primeira_falha_amostra": falha["n"] if falha else None,
        "primeira_falha_s": falha["t_s"] if falha else None,
        "tempo_ate_falha_s": round(falha["t_s"] - duplicada, 3) if falha else None,
        "primeiro_200_rollback_amostra": recuperada["n"],
        "primeiro_200_rollback_s": recuperada["t_s"],
        "tempo_ate_recuperacao_s": round(recuperada["t_s"] - falha["t_s"], 3) if falha else None,
        "tempo_rollback_ate_200_s": round(recuperada["t_s"] - rollback, 3),
        "primeira_amostra_apos_publicacao": {k: primeiro_apos_publicacao[k] for k in
                                               ("n", "status", "versao")},
        "primeira_amostra_apos_rollback": {k: primeiro_apos_rollback[k] for k in
                                             ("n", "status", "versao")},
    }


if __name__ == "__main__":
    pasta = Path(sys.argv[1])
    for modo in ("base", "mitigado"):
        print(json.dumps(resumir(pasta, modo), ensure_ascii=False))
