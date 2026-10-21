# Estudo de Sazonalidade de Vendas por Produto

> Projeto de portfólio de análise exploratória de sazonalidade. **TODOS OS DADOS PÚBLICOS SÃO FICTÍCIOS**, gerados artificialmente por código, sem qualquer amostra ou parâmetro derivado de dados privados.

## Questão de negócio
Como identificar meses relativamente fortes e fracos em diferentes produtos, sem confundir crescimento anual com sazonalidade?

## Método
- Ciclo comercial de **março a fevereiro**; agregação por produto, ciclo e mês.
- Para cada ciclo completo com vendas positivas, divide as vendas mensais pela média mensal do próprio ciclo. Assim, `1,00` representa o nível médio daquele ciclo.
- Resume os índices normalizados por média e mediana, com faixas **ilustrativas**, não estatísticas.
- Teste **Friedman** (meses comparados nos mesmos ciclos), com ao menos três ciclos completos. **Kendall W** descreve o tamanho de efeito do ranking; BH-FDR corrige comparações entre produtos.
- Meses ausentes **não viram zeros**. Ciclos incompletos aparecem na tabela de cobertura, mas não são usados no teste/índice.

**Limitações:** apenas 5 ciclos na amostra fictícia. Teste exploratório de baixa potência; valores de p não estabelecem causas, magnitude comercial ou previsões. O bloqueio por ciclo não elimina efeitos de campanhas, feriados ou mudanças de mix. Índices só são comparáveis após verificar consistência dos dados de origem.

## Estrutura
```
analise_sazonalidade.py
scripts/gerar_dados_sinteticos.py
data/sazonalidade_sintetica.csv   # 100% sintético
requirements.txt
tests/test_sazonalidade.py
.gitignore
```

## Execução no VS Code (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/gerar_dados_sinteticos.py
python analise_sazonalidade.py --input data/sazonalidade_sintetica.csv
python -m pytest -q
```

Resultados CSV e gráficos são gerados em `outputs/`, pasta excluída do Git.

## Executar localmente em dados privados
Copie o arquivo para `private_data/minha_base.xlsx` (diretório ignorado pelo Git), mantendo campos `Produto`, `Ciclo`, `Meses`, `Vendas` (ou equivalentes minúsculos). Rode:
```powershell
python analise_sazonalidade.py --input private_data/minha_base.xlsx
```
**Não suba a base, gráficos ou tabelas produzidos com dados reais.** Confira alterações com `git status` antes do `git push`.

## Próximas evoluções
- Intervalos de confiança com bootstrap por ciclo, caso haja volume histórico suficiente.
- Avaliação explícita de tendências temporais, feriados e promoções.
- Integração de testes de qualidade de dados em CI.

## Ética e reprodutibilidade
Este repositório não contém clientes, faturamentos, nomes de produtos internos, dados corporativos, URLs do Colab ou credenciais. A base demonstrativa é inteiramente simulada, e **não representa resultados de empresas reais**.

## Publicação segura no GitHub

Na pasta do projeto, use este fluxo (substitua o endereço remoto pelo seu repositório vazio):

```powershell
git init
git branch -M main
git add .
python scripts/verificar_publicacao.py
git diff --cached --stat
git diff --cached --name-only
git commit -m "Publica estudo com dados sinteticos e testes"
git remote add origin https://github.com/SEU-USUARIO/NOME-DO-REPOSITORIO.git
git push -u origin main
```

**Se a verificação bloquear, não faça o commit/push.** Ela compara a versão staged
(o índice do Git) do CSV com os bytes esperados do gerador e impede arquivos fora
da lista aprovada. Ainda assim, auditoria humana do código/documentação é necessária:
detecção automática não garante identificar todo tipo de informação confidencial.
