"""Estudo exploratório de sazonalidade em períodos comerciais (março a fevereiro).

Uso: python analise_sazonalidade.py --input data/sazonalidade_sintetica.csv
A amostra pública foi gerada artificialmente; nenhuma base comercial real é incluída.
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # executar também em servidores sem interface gráfica
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare

MESES = ["mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez", "jan", "fev"]
COLUNAS = {"produto", "periodo", "mes", "vendas"}


def nome_normalizado(valor: object) -> str:
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", texto.strip().lower()).strip("_")


def parse_numero(valor: object) -> float:
    """Aceita valores numéricos, formatos 1234.56 e 1.234,56; não infere moeda."""
    if pd.isna(valor) or not str(valor).strip():
        return float("nan")
    if isinstance(valor, (int, float, np.number)):
        return float(valor)
    texto = str(valor).strip().replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return float(texto)


def carregar_dados(caminho: str | Path) -> pd.DataFrame:
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".csv":
        origem = pd.read_csv(caminho, sep=None, engine="python", dtype=str)
    elif caminho.suffix.lower() in {".xlsx", ".xlsm"}:
        origem = pd.read_excel(caminho, dtype=object)
    else:
        raise ValueError("Formato não aceito: use CSV ou XLSX.")

    aliases = {"meses": "mes", "mes": "mes", "vendas": "vendas",
               "produto": "produto", "periodo": "periodo", "ciclo": "periodo"}
    origem.columns = [aliases.get(nome_normalizado(c), nome_normalizado(c)) for c in origem.columns]
    if not origem.columns.is_unique:
        raise ValueError("Colunas duplicadas após normalizar cabeçalhos.")
    if not COLUNAS.issubset(origem.columns):
        raise ValueError(f"Colunas obrigatórias: {sorted(COLUNAS)}")

    df = origem[list(sorted(COLUNAS))].copy()
    df["produto"] = df["produto"].astype("string").str.strip()
    df["periodo"] = df["periodo"].astype("string").str.strip()
    df["mes"] = df["mes"].astype("string").map(nome_normalizado).str[:3]
    invalidos = sorted(set(df["mes"].dropna()) - set(MESES))
    if invalidos:
        raise ValueError(f"Meses não reconhecidos: {invalidos}")
    if df[["produto", "periodo", "mes"]].isna().any().any() or (df["produto"] == "").any() or (df["periodo"] == "").any():
        raise ValueError("Produto, período e mês devem estar preenchidos.")
    try:
        df["vendas"] = df["vendas"].map(parse_numero)
    except ValueError as exc:
        raise ValueError("Há valores de vendas que não puderam ser convertidos em números.") from exc
    if df["vendas"].isna().any() or not np.isfinite(df["vendas"]).all() or (df["vendas"] < 0).any():
        raise ValueError("Vendas devem ser numéricas, finitas e não negativas.")
    if df.empty:
        raise ValueError("Arquivo sem registros.")
    return df


def ajustar_fdr(p_valores: pd.Series) -> pd.Series:
    """Benjamini–Hochberg, com valores ausentes preservados."""
    p = pd.to_numeric(p_valores, errors="coerce")
    saida = pd.Series(np.nan, index=p.index, dtype=float)
    validos = p.dropna().sort_values()
    n = len(validos)
    if n:
        ranks = np.arange(1, n + 1)
        q = np.minimum.accumulate((validos.to_numpy() * n / ranks)[::-1])[::-1]
        saida.loc[validos.index] = np.clip(q, 0, 1)
    return saida


def classificar_indice(indice: float) -> str:
    """Faixas ilustrativas de desvio relativo; não são testes de significância."""
    if pd.isna(indice):
        return "Sem dados"
    if indice < .80:
        return "Abaixo: forte"
    if indice < .95:
        return "Abaixo: moderado"
    if indice <= 1.05:
        return "Próximo da média"
    if indice <= 1.20:
        return "Acima: moderado"
    return "Acima: forte"


def analisar(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Um período completo contribui uma vez por mês, reduzindo viés de tendência.

    O teste de Friedman é exploratório e bloqueia por período. Não demonstra causa.
    Meses faltantes NÃO são assumidos como zero: períodos incompletos são excluídos
    do índice sazonal e do teste, mas permanecem nos totais e na cobertura.
    """
    df = df.rename(columns={"ciclo": "periodo"}).copy()
    if not df.columns.is_unique:
        raise ValueError("Colunas duplicadas após normalizar cabeçalhos.")
    mensal = (df.groupby(["produto", "periodo", "mes"], as_index=False,
                         observed=True)["vendas"].sum())
    totais_periodos = (mensal.groupby(["produto", "periodo"], as_index=False)["vendas"]
                    .sum().rename(columns={"vendas": "vendas_total"}))
    tabelas_indices = []
    testes = []
    cobertura = []

    for produto, bloco in mensal.groupby("produto", sort=True):
        matriz = bloco.pivot(index="periodo", columns="mes", values="vendas").reindex(columns=MESES)
        for periodo, linha in matriz.iterrows():
            cobertura.append({"produto": produto, "periodo": periodo,
                              "meses_observados": int(linha.notna().sum()),
                              "periodo_completo": bool(linha.notna().all())})
        completos = matriz.dropna(axis=0)
        completos = completos.loc[completos.sum(axis=1) > 0]
        n = len(completos)

        if n:
            indices_por_periodo = completos.div(completos.mean(axis=1), axis=0)
            for mes in MESES:
                x = indices_por_periodo[mes]
                tabelas_indices.append({"produto": produto, "mes": mes,
                                        "indice_medio": float(x.mean()),
                                        "indice_mediano": float(x.median()),
                                        "classificacao": classificar_indice(float(x.mean())),
                                        "periodos_utilizados": n})
        estatistica = p = w = np.nan
        situacao = "Insuficiente: requer >=3 períodos completos com vendas positivas"
        if n >= 3:
            assert len(MESES) == 12
            if np.allclose(indices_por_periodo.to_numpy(), 1.0):
                estatistica, p, w = 0.0, 1.0, 0.0
            else:
                resultado = friedmanchisquare(*(indices_por_periodo[m].to_numpy() for m in MESES))
                estatistica, p = float(resultado.statistic), float(resultado.pvalue)
                w = estatistica / (n * (len(MESES) - 1)) if np.isfinite(estatistica) else np.nan
            situacao = "Testado" if np.isfinite(p) else "Teste não identificável (dados constantes)"
        testes.append({"produto": produto, "periodos_completos": n,
                       "friedman_chi2": estatistica, "p_valor": p,
                       "kendall_w": w, "situacao": situacao})

    resumo = pd.DataFrame(testes)
    resumo["q_valor_fdr"] = ajustar_fdr(resumo["p_valor"])
    resumo["interpretacao"] = np.where(
        resumo["q_valor_fdr"].isna(), "Sem evidência avaliável",
        np.where(resumo["q_valor_fdr"] < .05,
                 "Diferenças entre meses (exploratório)",
                 "Sem diferenças detectadas no limiar de 5%")
    )
    return {"resumo_testes": resumo,
            "indices_sazonais": pd.DataFrame(tabelas_indices, columns=[
                "produto", "mes", "indice_medio", "indice_mediano", "classificacao", "periodos_utilizados"]),
            "vendas_por_periodo": totais_periodos,
            "cobertura": pd.DataFrame(cobertura)}


def criar_graficos(indices: pd.DataFrame, pasta: Path) -> None:
    for numero, (produto, grupo) in enumerate(indices.groupby("produto", sort=True), start=1):
        dados = grupo.set_index("mes").reindex(MESES)
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.plot(MESES, dados["indice_medio"].to_numpy(), marker="o", label="Índice médio")
        ax.plot(MESES, dados["indice_mediano"].to_numpy(), linestyle="--", marker=".", label="Índice mediano")
        ax.axhline(1, linewidth=1, color="gray", label="Referência = 1")
        ax.set(xlabel="Mês (período mar–fev)", ylabel="Índice relativo", title=f"Sazonalidade exploratória | {produto}")
        ax.legend()
        fig.tight_layout()
        fig.savefig(pasta / f"indice_produto_{numero:02}.png", dpi=160)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Análise exploratória de sazonalidade por produto")
    parser.add_argument("--input", default="data/sazonalidade_sintetica.csv", help="CSV/XLSX de entrada")
    parser.add_argument("--output", default="outputs", help="Pasta local ignorada pelo Git")
    args = parser.parse_args()
    entrada = Path(args.input)
    if not entrada.is_file():
        parser.error(f"Arquivo não encontrado: {entrada}. Rode: python scripts/gerar_dados_sinteticos.py")
    df = carregar_dados(entrada)
    resultados = analisar(df)
    pasta = Path(args.output)
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, tabela in resultados.items():
        tabela.to_csv(pasta / f"{nome}.csv", index=False, encoding="utf-8-sig")
    criar_graficos(resultados["indices_sazonais"], pasta)
    print(f"Concluído: {len(df)} registros; resultados em {pasta.resolve()}")
    print(resultados["resumo_testes"].to_string(index=False))
    print("ATENÇÃO: análise exploratória; significância não prova causalidade nem prevê vendas.")


if __name__ == "__main__":
    main()
