"""Gera gráficos e tabelas públicos exclusivamente com a simulação de seed 2026."""
from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analise_sazonalidade import analisar, MESES
from scripts.gerar_dados_sinteticos import gerar
from scripts.relatorio_portfolio import artefatos_relatorio

INICIO, FIM = "<!-- RESULTADOS:SINTETICOS:INICIO -->", "<!-- RESULTADOS:SINTETICOS:FIM -->"
CORES = {"Produto A": "#2463A6", "Produto B": "#B15A16", "Produto C": "#667C32"}


def numero(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def png(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=160, facecolor="white")
    plt.close(fig)
    return buffer.getvalue()


def artefatos():
    """Sem parâmetro de entrada externa: somente dados inventados pelo gerador."""
    dados = gerar(2026).rename(columns={"Produto": "produto", "Período": "periodo", "Meses": "mes", "Vendas": "vendas"})
    resultado = analisar(dados)
    indices = resultado["indices_sazonais"]
    totais = resultado["vendas_por_periodo"].pivot(index="periodo", columns="produto", values="vendas_total")
    imagens = {}
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(11, 5))
        for (produto, grupo), marcador in zip(indices.groupby("produto"), ["o", "s", "^"]):
            h = grupo.set_index("mes").reindex(MESES)
            ax.plot(MESES, h.indice_medio, marker=marcador, color=CORES[produto], label=produto, linewidth=2)
        ax.axhline(1, linestyle="--", color="#555555", linewidth=1, label="Média do período = 1")
        ax.set(ylim=(.5, 1.5), xlabel="Mês | período de março a fevereiro", ylabel="Índice médio relativo",
               title="Perfil sazonal por produto | média de cinco períodos")
        ax.grid(axis="y", alpha=.18)
        ax.legend(ncol=2, loc="lower right", frameon=False)
        fig.text(.5, .02, "Dados 100% fictícios • cada mês é dividido pela média mensal de seu próprio período", ha="center", fontsize=9)
        fig.tight_layout(rect=(0, .05, 1, 1))
        imagens["docs/assets/indices_sazonais.png"] = png(fig)

        fig, ax = plt.subplots(figsize=(11, 5))
        x = np.arange(len(totais))
        for i, produto in enumerate(totais.columns):
            ax.bar(x+(i-1)*.25, totais[produto], width=.25, color=CORES[produto], label=produto)
        ax.set(xticks=x, xticklabels=[p.removeprefix("Ciclo ") for p in totais.index],
               xlabel="Período", ylabel="Vendas simuladas (unidades)",
               title="Volume por produto e período")
        ax.legend(frameon=False)
        ax.grid(axis="y", alpha=.18)
        ax.set_axisbelow(True)
        fig.text(.5, .02, "Dados 100% fictícios • totais em unidades, sem conversão em faturamento", ha="center", fontsize=9)
        fig.tight_layout(rect=(0, .05, 1, 1))
        imagens["docs/assets/vendas_por_periodo.png"] = png(fig)

    linhas = ["## Resultados da demonstração", "",
              f"**{numero(len(dados))} observações fictícias · 3 produtos · 5 períodos · 12 meses por período.**", "",
              "### Índices sazonais", "",
              "![Índices mensais relativos por produto, com referência igual a um](docs/assets/indices_sazonais.png)", "",
              "Índice `1,00` equivale à média mensal do próprio período; `1,20` equivale a 20% acima dessa referência.", "",
              "| Mês | Produto A | Produto B | Produto C |", "|---|---:|---:|---:|"]
    matriz = indices.pivot(index="mes", columns="produto", values="indice_medio").reindex(MESES)
    for mes, row in matriz.iterrows():
        linhas.append(f"| {mes} | " + " | ".join(numero(v, 2) for v in row) + " |")
    linhas += ["", "### Volume e meses de maior/menor índice", "",
               "![Totais de vendas simuladas por produto e período](docs/assets/vendas_por_periodo.png)", "",
               "| Produto | Vendas simuladas (unidades) | Maior índice | Menor índice |", "|---|---:|---:|---:|"]
    for produto, grupo in indices.groupby("produto"):
        alto, baixo = grupo.loc[grupo.indice_medio.idxmax()], grupo.loc[grupo.indice_medio.idxmin()]
        total = dados.loc[dados.produto.eq(produto), "vendas"].sum()
        linhas.append(f"| {produto} | {numero(total)} | {alto.mes}: {numero(alto.indice_medio, 2)} | {baixo.mes}: {numero(baixo.indice_medio, 2)} |")
    linhas += ["", "### Leitura de negócio", ""]
    for produto, grupo in indices.groupby("produto"):
        alto = grupo.loc[grupo.indice_medio.idxmax()]
        linhas.append(f"- Na simulação, **{produto}** tem seu maior índice em **{alto.mes}**, {numero((alto.indice_medio-1)*100, 1)}% acima da referência mensal normalizada.")
    linhas += ["- O volume por período mostra a evolução da escala; os índices permitem comparar o perfil dos meses após essa normalização.",
               "- Em uma aplicação comercial, esses recortes apoiariam a investigação de janelas de demanda e o planejamento de capacidade.", "",
               "Fonte: `scripts/gerar_dados_sinteticos.py`, seed `2026`; reproduza com `python scripts/gerar_portfolio.py`. "
               "Resultados inteiramente fictícios: demonstram análise exploratória e não constituem previsão de vendas."]
    imagens.update(artefatos_relatorio())
    return imagens, "\n".join(linhas)


def main():
    imagens, trecho = artefatos()
    for nome, conteudo in imagens.items():
        destino = ROOT/nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
    caminho = ROOT/"README.md"
    texto = caminho.read_text(encoding="utf-8")
    if texto.count(INICIO) != 1 or texto.count(FIM) != 1:
        raise ValueError("README precisa conter um par de marcadores de resultados.")
    antes, restante = texto.split(INICIO)
    _, depois = restante.split(FIM)
    caminho.write_text(antes+INICIO+"\n"+trecho+"\n"+FIM+depois, encoding="utf-8")
    print("README, relatório e imagens atualizados usando exclusivamente dados fictícios.")


if __name__ == "__main__":
    main()
