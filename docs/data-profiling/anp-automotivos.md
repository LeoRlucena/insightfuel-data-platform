# Profiling — ANP Combustíveis Automotivos

Analisando o arquivo do primeiro semestre de 2023 em busca de mais informações sobre o dataset e como prosseguir no pipeline.

## 1. Fonte

[Série Histórica de Preços de Combustíveis e de GLP](https://dados.gov.br/dados/conjuntos-dados/serie-historica-de-precos-de-combustiveis-e-de-glp)

## 2. Granularidade identificada

Uma linha representa uma observação de preço coletada pela ANP para determinado produto, em uma revenda específica e em uma determinada data. A revenda pode ser identificada pelo CNPJ e possui informações de localização, endereço e bandeira.

## 3. Schema da fonte

| Coluna | Tipo observado na Bronze | Tipo Esperado |
| ----------- | ----------- | ----------- |
| Região | String | String |
| Estado | String | String |
| Município | String | String |
| Revenda | String | String |
| CNPJ | String | String |
| Rua | String | String |
| Número | String | String |
| Complemento | String | String / null |
| Bairro | String | String |
| CEP | String | String |
| Produto | String | String |
| Data Coleta | String | Date |
| Valor de Venda | String | Decimal/Float |
| Valor de Compra | String | Decimal/Float/null |
| Unidade | String | String |
| Bandeira | String | String |

## 4. Características da fonte:

- Formato: .csv
- Delimitador usado: `;`
- Periodicidade dos arquivos: semestral
- Data da coleta no formato `dd/mm/yyyy`
- Valores monetários com vírgula como separador decimal

## 5. Profiling por partição

| Partição | Registros | Data mínima | Data máxima | Duplicidades |
|----------|----------:|-------------|-------------|-------------:|
| 2023/1   | 431.576   | 2023-01-02  | 2023-06-30  | 0 |
| 2023/2   | —         | —           | —           | — |
| 2024/1   | —         | —           | —           | — |
| 2024/2   | —         | —           | —           | — |
| 2025/1   | —         | —           | —           | — |
| 2025/2   | —         | —           | —           | — |

## 6. Qualidade dos dados

### 2023/1
- Numero Rua: 107 nulos (0,02%)
- Complemento: 333.000 nulos (77,16%)
- Bairro: 828 nulos (0,19%)
- Valor de Compra: 431.576 nulos (100%)

### Demais partições
A validar.

## 7. Chave candidata
CNPJ da Revenda + Produto + Data da Coleta

Validada em:
- [x] 2023/1
- [ ] 2023/2
- [ ] 2024/1
- [ ] 2024/2
- [ ] 2025/1
- [ ] 2025/2

## 8. Decisões preliminares para Silver

A camada Silver será responsável pela padronização, tipagem e validação dos dados provenientes da Bronze. Até o momento foram identificadas as seguintes transformações candidatas:

1. **CNPJ da Revenda:** remoção de caracteres de formatação, preservando
   o valor como `String`, por se tratar de um identificador.

2. **CEP:** padronização da representação, preservando o tipo `String`.

3. **Data da Coleta:** conversão de `String`, no formato `dd/mm/yyyy`,
   para um tipo de data.

4. **Valor de Venda:** conversão da representação textual com vírgula
   decimal para um tipo numérico adequado.

5. **Valor de Compra:** sua permanência na Silver será avaliada após o
   profiling das demais partições, visto que apresenta 100% de valores
   nulos em 2023/1.

6. **Nomes de colunas e atributos categóricos:** serão avaliadas
   padronizações de nomenclatura e representação para facilitar o
   processamento e as análises.

7. **Unicidade:** a combinação `CNPJ da Revenda + Produto + Data da
   Coleta` será validada nas demais partições antes de ser adotada como
   regra de unicidade. Eventuais colisões serão investigadas antes da
   definição de uma estratégia de deduplicação.