import numpy as np
import pandas as pd
import pytest
from analise_sazonalidade import analisar, carregar_dados, ajustar_fdr, MESES


def dados_exemplo():
    return pd.DataFrame([
        {"produto": "Produto A", "ciclo": f"Ciclo {n}", "mes": m, "vendas": 100 if m != "jan" else 50}
        for n in range(1, 5) for m in MESES
    ])


def test_indice_respeita_referencia_de_ciclo():
    resultado = analisar(dados_exemplo())
    tabela = resultado["indices_sazonais"]
    assert len(tabela) == 12
    assert tabela["indice_medio"].mean() == pytest.approx(1)
    assert float(tabela.loc[tabela["mes"] == "jan", "indice_medio"].iloc[0]) < 1


def test_ciclos_incompletos_ficam_fora_do_teste():
    df = dados_exemplo()
    df = df[~((df["ciclo"] == "Ciclo 4") & (df["mes"] == "jan"))]
    resultado = analisar(df)
    assert int(resultado["resumo_testes"]["periodos_completos"].iloc[0]) == 3
    assert resultado["cobertura"]["periodo_completo"].sum() == 3


def test_sem_dados_suficientes_nao_inventa_p_valor():
    df = dados_exemplo().query('ciclo == "Ciclo 1"')
    saida = analisar(df)["resumo_testes"]
    assert np.isnan(saida["p_valor"].iloc[0])


def test_bh_fdr_preserva_nulos():
    x = ajustar_fdr(pd.Series([0.01, 0.02, np.nan, 0.40]))
    assert np.isnan(x.iloc[2])
    assert x.iloc[0] <= x.iloc[1] <= x.iloc[3]


def test_dados_invalidos_rejeitados(tmp_path):
    caminho = tmp_path / "teste.csv"
    pd.DataFrame([{"Produto": "X", "Ciclo": "C1", "Meses": "mes13", "Vendas": 10}]).to_csv(caminho, index=False)
    with pytest.raises(ValueError, match="Meses não reconhecidos"):
        carregar_dados(caminho)
