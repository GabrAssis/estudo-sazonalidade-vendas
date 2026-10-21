import pandas as pd
import pytest

from analise_sazonalidade import carregar_dados, analisar
from scripts.gerar_dados_sinteticos import gerar


def test_periodo_e_ciclo_produzem_mesmos_indices(tmp_path):
    novo = gerar().rename(columns={"Ciclo": "Período"})
    legado = novo.rename(columns={"Período": "Ciclo"})
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    novo.to_csv(a, index=False)
    legado.to_csv(b, index=False)
    d1, d2 = carregar_dados(a), carregar_dados(b)
    pd.testing.assert_frame_equal(d1, d2)
    assert "periodo" in d1
    for nome, tabela in analisar(d1).items():
        pd.testing.assert_frame_equal(tabela, analisar(d2)[nome])


def test_rejeita_periodo_e_ciclo_juntos(tmp_path):
    df = gerar().rename(columns={"Ciclo": "Período"})
    df["Ciclo"] = df["Período"]
    arquivo = tmp_path / "ambiguo.csv"
    df.to_csv(arquivo, index=False)
    with pytest.raises(ValueError, match="duplicad"):
        carregar_dados(arquivo)
