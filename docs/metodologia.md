# Metodologia da análise de sazonalidade de vendas

O estudo investiga como o perfil mensal de vendas varia por produto, preservando a estrutura dos períodos comerciais. A documentação explica as técnicas aplicadas, seus motivos e as evidências que permitem revisar cada resultado.

## Objetivo e unidade de análise

O grão analítico é produto × período × mês. A demonstração contém 3 produtos fictícios, 5 períodos e 12 meses por período, totalizando 180 observações. Cada período vai de março a fevereiro.

O gerador usa contagens Poisson com parâmetros inventados, efeitos mensais artificiais e mudança de escala entre períodos. A seed 2026 fixa a demonstração, sem usar amostras ou parâmetros de dados privados. A distribuição usada para gerar a simulação não é uma distribuição ajustada a vendas reais.

## Técnicas utilizadas e por que foram escolhidas

| Técnica | Aplicação no estudo | Motivo da escolha |
|---|---|---|
| Agregação por grão mensal | Soma por produto, período e mês | Garante que índices e comparações usem uma unidade consistente |
| Validação e cobertura | Verifica campos, meses, valores e completude | Evita confundir ausência de mês com venda zero |
| Normalização dentro do período | Vendas do mês / média mensal do próprio período | Coloca períodos com escalas diferentes na mesma referência |
| Peso igual para períodos elegíveis | Média e mediana dos índices entre períodos | Evita dar mais peso apenas aos períodos de maior volume |
| Média e mediana | Síntese dos índices e dos volumes | Permite examinar o centro por duas medidas, sem confundir mediana com estabilidade |
| Desvio-padrão e quartis | Dispersão dos volumes mensais | Complementa as medidas centrais com variabilidade observada |
| Mapa de calor | Índices por produto, período e mês | Mantém visíveis as observações que formam o resumo |
| Friedman | Comparação dos meses nos mesmos períodos | Usa a estrutura de medidas repetidas, com período como bloco |
| Kendall W | Magnitude da concordância dos rankings mensais | Acrescenta medida de efeito à leitura do teste global |
| Benjamini–Hochberg | Três testes, um por produto | Controla descobertas falsas nas condições do procedimento |

## Passo a passo da normalização

1. Agregar vendas por produto, período e mês, na ordem março–fevereiro.
2. Registrar a cobertura dos 12 meses de cada combinação produto × período.
3. Selecionar períodos completos e com soma de vendas positiva.
4. Calcular a média mensal do próprio período.
5. Dividir cada mês por essa média e resumir seus índices entre períodos elegíveis.

Para produto `p`, período `t` e mês `m`:

`media_periodo(p,t) = soma(vendas dos 12 meses) / 12`

`indice(p,t,m) = vendas(p,t,m) / media_periodo(p,t)`

`indice_medio(p,m) = média dos índices(p,t,m) entre períodos elegíveis`

O índice de 1,00 é a referência do próprio período; 1,20 representa 20% acima dela. Essa referência remove a diferença de escala total entre períodos, mas não ajusta tendências dentro do período, campanhas, feriados ou mudanças de composição.

Na regra implementada, um zero observado permanece zero. Mês ausente permanece ausente: o período aparece nos totais e na cobertura, mas não entra no índice nem no teste. Períodos com soma zero também são excluídos da normalização. A cobertura `periodo_completo` indica presença dos 12 meses, separadamente da regra de soma positiva.

## Média mediana e faixas descritivas

A média resume o centro aritmético; a mediana é menos sensível a extremos. A dispersão é avaliada com quartis, desvio-padrão e observações no mapa. Uma mediana alta, isoladamente, não comprova demanda estável.

| Índice médio | Classificação do código |
|---|---|
| Menor que 0,80 | Abaixo: forte |
| 0,80 até menor que 0,95 | Abaixo: moderado |
| 0,95 até 1,05, inclusive | Próximo da média |
| Maior que 1,05 até 1,20, inclusive | Acima: moderado |
| Maior que 1,20 | Acima: forte |

As faixas são regras descritivas fixas; não representam significância, intervalo de confiança ou garantia de demanda futura.

## Friedman Kendall W e múltiplos testes

Os 12 meses são medidas repetidas em cada período. Friedman compara seus rankings com o período como bloco e sem exigir normalidade. Essa estrutura é o motivo da escolha: as amostras mensais não são tratadas como grupos independentes. O código requer pelo menos três períodos completos com soma positiva.

O teste global pergunta se há diferenças entre os meses. Não identifica os pares diferentes, não comprova causa e não é previsão. O projeto não executa pós-teste de Dunn; esse método não deve aparecer como resultado da implementação.

Kendall W é calculado por `χ² de Friedman / [n × (12 − 1)]`, usando a estatística com correção de empates do SciPy. Valores maiores representam maior concordância dos rankings mensais dentro da amostra. O relatório apresenta W junto de p, sem traduzir automaticamente o efeito em impacto financeiro.

BH ajusta os três p-valores dos produtos em uma família completa. O q do relatório é esse p ajustado. O controle de FDR requer p-valores válidos e as condições de independência ou dependência positiva do procedimento; não corrige viés de coleta nem dependência temporal.

### Critério de interpretação da demonstração

O p-valor de `friedmanchisquare` usa aproximação qui-quadrado. A documentação do SciPy recomenda mais de dez observações por medida e mais de seis medidas repetidas para confiar na aproximação. A demonstração tem cinco períodos e 12 meses; p e q são apresentados como exploratórios. O código permite calcular a estatística, e a documentação mantém a leitura proporcional ao histórico disponível.

O resumo executivo se apoia nos índices, na dispersão e na magnitude observada. q acima de 0,05 não comprova ausência de sazonalidade; q abaixo do limiar não prova previsibilidade, causalidade ou resultado comercial futuro.

## Boas práticas e evidências verificáveis

| Prática | Por que importa | Evidência no projeto |
|---|---|---|
| Grão e janela definidos | Mantém comparações equivalentes | Produto × período × mês; março a fevereiro |
| Zero separado de ausência | Preserva o significado do dado | Cobertura e exclusão de períodos incompletos |
| Normalização documentada | Evita comparar escalas como se fossem padrão sazonal | Índices relativos ao próprio período |
| Teste coerente com o desenho | Respeita a estrutura repetida dos meses | Friedman com período como bloco |
| Estatística com contexto | Dá visibilidade à magnitude e ao histórico | W, p aproximado, q e número de períodos |
| Observações visíveis | Permite conferir o resumo | Mapa com cada índice por mês e período |
| Reprodutibilidade | Permite refazer cada tabela | Seed fixa e relatório gerado por código |
| Proteção da publicação | Confere a origem fictícia das saídas públicas | Verificador do índice, base, imagens, relatório e README |

## Uso dos resultados

Volume absoluto ajuda a dimensionar escala; índice relativo mostra intensidade mensal na referência normalizada. A escolha de antecedência de campanha, estoque ou capacidade depende também de margem, prazo de venda e entrega e orçamento.

O relatório associa cada sugestão a uma evidência e uma validação seguinte. Assim, distingue observação, hipótese e ação proposta, sem apresentar resultados fictícios como desempenho ou impacto de uma empresa real.

## Dicionário e compatibilidade

Entrada CSV ou XLSX com `Produto`, `Período`, `Meses` e `Vendas`. Os nomes são normalizados para `produto`, `periodo`, `mes` e `vendas`; `Ciclo` continua aceito como alias de `Período`. Colunas antigas e atuais juntas são rejeitadas por ambiguidade.

O grão analítico é produto × período × mês. Registros desse grão são somados. Vendas devem ser finitas, numéricas e não negativas.

Cada período representa **março a fevereiro**. Os identificadores `Ciclo 01` a `Ciclo 05` continuam como chaves. Nos gráficos do README aparecem como `01` a `05`, sob o eixo **Período**. Eles não indicam anos civis.

## Saídas e interpretação

- `indices_sazonais.csv`: média, mediana, classificação e `periodos_utilizados`.
- `vendas_por_periodo.csv`: totais por produto e período.
- `cobertura.csv`: meses observados e `periodo_completo`.
- `resumo_testes.csv`: `periodos_completos`, Friedman, p, Kendall W e q ajustado.

Consumidores das saídas anteriores devem trocar `ciclo` por `periodo`, incluindo arquivos e campos derivados. Fórmulas e valores são preservados.

Os índices têm peso igual para cada período completo com soma positiva. O gráfico do índice médio não é intervalo de confiança nem previsão. A classificação por faixas é ilustrativa.


## Reproduzir e revisar

```powershell
python scripts/gerar_dados_sinteticos.py
python scripts/gerar_portfolio.py
python analise_sazonalidade.py
python -m pytest -q
git add .
python scripts/verificar_publicacao.py
```

O script analítico gera saídas locais em `outputs/`; o gerador de portfólio atualiza README, relatório e imagens públicas exclusivamente com a simulação. O verificador compara esses artefatos no índice Git com sua reprodução. Bases e saídas privadas permanecem nas pastas ignoradas; não use `git add -f` para publicá-las.

## Referências técnicas

- [SciPy — controle de falsas descobertas](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.false_discovery_control.html)
- [SciPy — Friedman para medidas repetidas e condições da aproximação](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.friedmanchisquare.html)

As referências documentam os métodos. As funções implementadas e os resultados deste projeto podem ser conferidos no código, nos testes e no [relatório reproduzível](relatorio.md).
