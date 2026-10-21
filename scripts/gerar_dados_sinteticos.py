"""Gera uma base inteiramente fictícia: não utiliza ou ajusta dados empresariais."""
from pathlib import Path
import numpy as np
import pandas as pd

MESES = ["mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez", "jan", "fev"]
FATORES = {
    "Produto A": [0.90, 0.86, 0.98, 1.02, 1.04, 1.01, 1.16, 1.21, 1.13, 1.10, 0.75, 0.84],
    "Produto B": [1.05, 1.10, 1.04, 0.95, 0.82, 0.80, 0.88, 1.04, 1.11, 1.25, 1.18, 1.09],
    "Produto C": [0.98, 1.01, 1.05, 1.02, 1.01, 0.99, 1.04, 1.00, 0.97, 1.02, 0.96, 0.95],
}


def gerar(seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    linhas = []
    for produto, fatores in FATORES.items():
        for i in range(5):
            ciclo = f"Ciclo {i+1:02}"
            escala = 70 * (1 + i * 0.12) * (1 if produto == "Produto A" else 0.75 if produto == "Produto B" else 1.25)
            for mes, fator in zip(MESES, fatores):
                vendas = int(rng.poisson(escala * fator))
                linhas.append({"Produto": produto, "Período": ciclo, "Meses": mes, "Vendas": vendas})
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    destino = Path("data/sazonalidade_sintetica.csv")
    destino.parent.mkdir(exist_ok=True)
    gerar().to_csv(destino, index=False, encoding="utf-8-sig", lineterminator="\n")
    print(f"Base 100% sintética criada: {destino}")
