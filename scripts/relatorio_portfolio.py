"""Relatório de sazonalidade reproduzido somente com o gerador fictício."""
from __future__ import annotations

import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from analise_sazonalidade import analisar, MESES
from scripts.gerar_dados_sinteticos import gerar


def fmt(v, casas=2):
    if pd.isna(v):
        return "—"
    return f"{v:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def tabela(cabecalhos, linhas):
    return "\n".join(["| " + " | ".join(cabecalhos) + " |",
                      "|" + "---|"*len(cabecalhos)] +
                     ["| " + " | ".join(map(str, linha)) + " |" for linha in linhas])


def artefatos_relatorio():
    dados = gerar(2026).rename(columns={"Produto":"produto", "Período":"periodo", "Meses":"mes", "Vendas":"vendas"})
    resultado = analisar(dados)
    indices, testes = resultado['indices_sazonais'], resultado['resumo_testes']
    arquivos = {}
    normalizados = []
    for produto,g in dados.groupby('produto'):
        m = g.pivot(index='periodo',columns='mes',values='vendas').reindex(columns=MESES)
        normalizados.append((produto,m.div(m.mean(axis=1),axis=0)))

    with plt.rc_context({"font.family":"DejaVu Sans", "font.size":10}):
        fig, axes = plt.subplots(3,1,figsize=(12,9.5),layout='constrained')
        cmap = LinearSegmentedColormap.from_list('azul_portfolio',['#F1F5FA','#AAC8E5','#2463A6','#143958'])
        for ax,(produto,m) in zip(axes,normalizados):
            imagem = ax.imshow(m.to_numpy(), cmap=cmap, vmin=.4, vmax=1.6, aspect='auto')
            ax.set(title=produto,xticks=range(12),xticklabels=MESES,yticks=range(len(m)),
                   yticklabels=[p.removeprefix('Ciclo ') for p in m.index],ylabel='Período')
            for i,row in enumerate(m.to_numpy()):
                for j,v in enumerate(row):
                    ax.text(j,i,fmt(v),ha='center',va='center',color='white' if v>1.15 else '#18344C',fontsize=9)
        fig.colorbar(imagem,ax=list(axes),label='Índice do mês / média mensal do período',shrink=.8)
        fig.suptitle('Índices por produto, período e mês | dados fictícios',fontsize=15,fontweight='bold')
        buffer=io.BytesIO()
        fig.savefig(buffer,format='png',dpi=160,facecolor='white')
        plt.close(fig)
        arquivos['docs/assets/mapa_periodos.png']=buffer.getvalue()

    linhas = ['# Relatório de sazonalidade de vendas com dados fictícios','',
              'Relatório gerado por código com resumo executivo, análise por produto, métodos e recomendações demonstrativas. '
              'Todos os números e nomes de produtos são fictícios, gerados com seed 2026.','',
              '## Resumo executivo','',
              f'A simulação reúne **{len(dados)} observações mensais**, **3 produtos** e **5 períodos completos por produto**. '
              f'O total é de **{fmt(dados.vendas.sum(),0)} unidades fictícias**, distribuídas de março a fevereiro. '
              'O perfil mensal é comparado após normalizar a escala de cada período.','',
              'O relatório apresenta separadamente volume absoluto, padrão relativo, dispersão e testes exploratórios. '
              'Essa organização permite discutir planejamento comercial sem confundir crescimento do volume com maior intensidade sazonal.','',
              '## Resumo descritivo das vendas mensais','',
              tabela(['Produto','Observações','Total (un.)','Média mensal','Mediana','Desvio-padrão','P25','P75','Mín.','Máx.'],
                     [[p,fmt(len(g),0),fmt(g.vendas.sum(),0),fmt(g.vendas.mean()),fmt(g.vendas.median()),
                       fmt(g.vendas.std()),fmt(g.vendas.quantile(.25)),fmt(g.vendas.quantile(.75)),fmt(g.vendas.min(),0),fmt(g.vendas.max(),0)]
                      for p,g in dados.groupby('produto')]),'',
              '**Método e motivo:** média e mediana resumem posições centrais; desvio-padrão e quartis descrevem dispersão. '
              'A média não é o volume total e a mediana, sozinha, não mede estabilidade. Cada linha reúne 60 meses, '
              'com cinco observações de cada mês do calendário comercial.','',
              '## Volume por período','',
              tabela(['Produto','Período','Vendas (un.)'],[[r.produto,r.periodo,fmt(r.vendas_total,0)] for r in resultado['vendas_por_periodo'].itertuples()]),'',
              '![Totais de vendas por período](assets/vendas_por_periodo.png)','',
              '**Método e motivo:** somar o volume mostra a escala comercial. A comparação do perfil dos meses usa '
              'índices relativos para evitar que um período maior domine a referência. Cada período elegível tem peso igual.','',
              '## Perfil mensal normalizado','',
              '![Índices médios por produto](assets/indices_sazonais.png)','',
              'A normalização usa `índice = vendas do mês / média mensal do próprio período`. Depois calcula média '
              'e mediana desses índices entre os períodos completos. A média é feita sobre índices normalizados, '
              'sem dividir totais de bases diferentes. Um índice de 1,20 significa 20% acima da média mensal daquele período.','',
              tabela(['Produto','Mês','Índice médio','Índice mediano','Faixa descritiva','Períodos utilizados'],
                     [[r.produto,r.mes,fmt(r.indice_medio,3),fmt(r.indice_mediano,3),r.classificacao,fmt(r.periodos_utilizados,0)]
                      for r in indices.itertuples()]),'',
              '**Método e motivo:** apresentar média e mediana permite examinar a sensibilidade aos valores mais altos. '
              'As faixas indicam desvios descritivos da referência 1,00, sem equivaler a significância estatística.','',
              '## Comparação mês a mês entre períodos','',
              '![Mapa dos índices sazonais com cada período e mês](assets/mapa_periodos.png)','',
              '**Método e motivo:** o mapa mantém visíveis os cinco índices de cada mês, permitindo conferir '
              'se o resumo médio representa padrões recorrentes ou observações concentradas em um período. '
              'Todos os painéis usam a mesma escala de cor; os valores são mostrados nas células.','',
              '## Testes exploratórios e tamanho de efeito','',
              tabela(['Produto','Períodos completos','Friedman χ²','p aproximado','q BH','Kendall W'],
                     [[r.produto,fmt(r.periodos_completos,0),fmt(r.friedman_chi2,3),fmt(r.p_valor,6),fmt(r.q_valor_fdr,6),fmt(r.kendall_w,3)]
                      for r in testes.itertuples()]),'',
              '**Friedman:** compara os 12 meses como medidas repetidas nos mesmos períodos. O período é o bloco; '
              'a associação entre observações do mesmo período é respeitada na estrutura da comparação. '
              'O código requer ao menos três períodos completos e soma positiva.','',
              '**Kendall W:** `χ² / [n × (12 − 1)]` descreve a magnitude da concordância dos rankings mensais. '
              'A medida acompanha o p-valor para dar contexto à intensidade do padrão observado.','',
              '**Benjamini–Hochberg:** ajusta a família completa de três testes, um por produto. O q apresentado '
              'é o p ajustado pelo procedimento BH. A escolha atende ao objetivo exploratório de controlar a taxa '
              'de descobertas falsas nas condições do método.','',
              '**Critério de leitura:** p e q usam aproximação qui-quadrado. Com cinco períodos, são demonstrações '
              'exploratórias; a documentação do SciPy recomenda mais de dez observações por medida e mais de seis '
              'medidas repetidas para confiar nessa aproximação. A interpretação combina índices, dispersão e W. '
              'Um teste global não identifica quais pares de meses diferem, e q acima de 5% não prova ausência de sazonalidade.','',
              '## Leitura executiva por produto','',
              '| Produto | Maior índice médio | Menor índice médio | Aplicação comercial possível |','|---|---|---|---|']
    for produto,g in indices.groupby('produto'):
        maior,menor=g.loc[g.indice_medio.idxmax()],g.loc[g.indice_medio.idxmin()]
        linhas.append(f'| {produto} | {maior.mes}: {fmt(maior.indice_medio)} ({fmt((maior.indice_medio-1)*100,1)}% acima da referência) '
                      f'| {menor.mes}: {fmt(menor.indice_medio)} | Investigar demanda em {maior.mes} e antecipar planejamento de capacidade |')
    linhas += ['', 'O quadro traduz a simulação em perguntas para planejamento. Antecedência de campanhas, estoque ou '
               'capacidade deve considerar prazo de venda, margem, orçamento e entrega, informações que precisam ser '
               'levantadas antes de transformar um padrão descritivo em decisão operacional.','',
               '## Cobertura e qualidade','',
               tabela(['Produto','Período','Meses observados','Completo'],
                      [[r.produto,r.periodo,fmt(r.meses_observados,0),'Sim' if r.periodo_completo else 'Não'] for r in resultado['cobertura'].itertuples()]),'',
               'A simulação tem 15 combinações produto × período, todas com os 12 meses. Na entrada de uso geral, '
               'vendas devem ser numéricas, finitas e não negativas; produto, período e mês devem estar preenchidos. '
               'Meses desconhecidos e cabeçalhos ambíguos são rejeitados. Registros repetidos no grão mensal são somados '
               'pela regra de agregação, sem afirmar que toda repetição é uma duplicata indevida.','',
               'Períodos incompletos permanecem nos totais e na cobertura; ficam fora dos índices e do teste. '
               'Um zero observado é um valor válido; ausência de mês permanece ausência. Períodos com soma zero '
               'também ficam fora da normalização.','',
               '## Recomendações demonstrativas','',
               '| Aplicação | Evidência a examinar | Próxima validação |','|---|---|---|',
               '| Planejamento de demanda | Índices médios e medianos por mês | Conferir repetição no mapa e ampliar histórico |',
               '| Capacidade de operação | Volume absoluto e dispersão mensal | Levantar prazo de entrega, capacidade e nível de serviço |',
               '| Planejamento comercial | Meses relativamente mais intensos por produto | Relacionar campanhas e prazos sem atribuir causalidade ao calendário |',
               '| Monitoramento | Novos períodos completos e cobertura | Atualizar índices e conferir mudanças de mix e cadastro |','',
               'Essas ações exemplificam uso de dados; não representam implantação, previsão ou ganho financeiro realizado.','',
               '## Reprodutibilidade','', '```powershell','python scripts/gerar_dados_sinteticos.py',
               'python analise_sazonalidade.py','python scripts/gerar_portfolio.py','python -m pytest -q','```','',
               'Este relatório e o mapa são regenerados com dados fictícios pelo mesmo comando do portfólio. '
               'A base, as imagens e o relatório são conferidos no índice Git antes do commit.','',
               '[Metodologia e justificativas](metodologia.md) · [Voltar ao README](../README.md)']
    arquivos['docs/relatorio.md']=('\n'.join(linhas)+'\n').encode('utf-8')
    return arquivos
