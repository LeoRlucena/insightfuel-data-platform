# Profiling — ANP Combustíveis Automotivos

Este documento registra o profiling realizado sobre os arquivos de preços de
combustíveis automotivos da ANP utilizados no projeto InsightFuel.

Foram analisadas seis partições semestrais, correspondentes ao período de 2023
a 2025. O objetivo do profiling foi compreender a estrutura, granularidade e
qualidade dos dados antes da definição das transformações das camadas Silver
e Gold.

## 1. Fonte

[Série Histórica de Preços de Combustíveis e de GLP](https://dados.gov.br/dados/conjuntos-dados/serie-historica-de-precos-de-combustiveis-e-de-glp)

Fonte: Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP).

Arquivos analisados:

- AUTOMOTIVOS_2023.01.csv
- AUTOMOTIVOS_2023.02.csv
- AUTOMOTIVOS_2024.01.csv
- AUTOMOTIVOS_2024.02.csv
- AUTOMOTIVOS_2025.01.csv
- AUTOMOTIVOS_2025.02.csv

## 2. Granularidade identificada

Uma linha representa uma observação de preço coletada pela ANP para determinado
produto, em uma revenda e em uma determinada data.

A revenda pode ser identificada pelo CNPJ e possui informações complementares
de localização, endereço e bandeira.

Durante o profiling foi constatado que uma mesma combinação de:

`CNPJ da Revenda + Produto + Data da Coleta`

pode possuir mais de uma observação. Portanto, essa combinação não representa
uma chave única confiável do dataset.

## 3. Schema da fonte

| Coluna            | Tipo observado na Bronze | Tipo esperado na Silver |
| ----------------- | ------------------------ | ----------------------- |
| Regiao - Sigla    | String                   | String                  |
| Estado - Sigla    | String                   | String                  |
| Municipio         | String                   | String                  |
| Revenda           | String                   | String                  |
| CNPJ da Revenda   | String                   | String                  |
| Nome da Rua       | String                   | String                  |
| Numero Rua        | String                   | String / null           |
| Complemento       | String                   | String / null           |
| Bairro            | String                   | String / null           |
| Cep               | String                   | String                  |
| Produto           | String                   | String                  |
| Data da Coleta    | String                   | Date                    |
| Valor de Venda    | String                   | Decimal / Float         |
| Valor de Compra   | String                   | null / coluna removida  |
| Unidade de Medida | String                   | String                  |
| Bandeira          | String                   | String                  |

CNPJ e CEP devem permanecer como `String`, pois representam identificadores e
não valores destinados a operações matemáticas.

## 4. Características da fonte

- Formato: CSV
- Delimitador: `;`
- Periodicidade dos arquivos utilizados: semestral
- Período analisado: 2023 a 2025
- Data da coleta no formato `dd/mm/yyyy`
- Valores monetários representados com vírgula como separador decimal
- Seis produtos encontrados:
  - DIESEL
  - DIESEL S10
  - ETANOL
  - GASOLINA
  - GASOLINA ADITIVADA
  - GNV
- Unidades encontradas:
  - `R$ / litro`
  - `R$ / m³`
  - `R$ / m3`

A representação `R$ / m3` foi identificada em 2025/2 e representa uma
inconsistência de representação em relação a `R$ / m³`.

## 5. Profiling por partição

| Partição | Registros | Data mínima | Data máxima | Colisões da chave candidata | Duplicatas exatas | Linhas vazias |
| -------- | --------: | ----------- | ----------- | --------------------------: | ----------------: | ------------: |
| 2023/1   |   431.576 | 2023-01-02  | 2023-06-30  |                           0 |                 0 |             0 |
| 2023/2   |   472.424 | 2023-07-03  | 2023-12-29  |                           0 |                 0 |             0 |
| 2024/1   |   477.154 | 2024-01-01  | 2024-06-28  |                          14 |                10 |             0 |
| 2024/2   |   421.382 | 2024-07-01  | 2024-12-31  |                           0 |                 0 |             0 |
| 2025/1   |   429.523 | 2025-01-01  | 2025-06-30  |                           0 |           9.113\* |         9.114 |
| 2025/2   |   384.208 | 2025-07-01  | 2025-12-31  |                           0 |                 0 |             0 |

\* As 9.113 duplicatas exatas identificadas em 2025/1 estão relacionadas às
9.114 linhas completamente vazias presentes no arquivo. Ao aplicar uma operação
de unicidade, uma dessas linhas vazias é preservada e as outras 9.113 são
consideradas redundantes.

## 6. Qualidade dos dados

### 6.1 Valores nulos

#### 2023/1

- Numero Rua: 107
- Complemento: 333.000
- Bairro: 828
- Valor de Compra: 431.576 (100%)

#### 2023/2

- Numero Rua: 140
- Complemento: 362.579
- Bairro: 854
- Valor de Compra: 472.424 (100%)

#### 2024/1

- Numero Rua: 65
- Complemento: 366.324
- Bairro: 868
- Valor de Compra: 477.154 (100%)

#### 2024/2

- Numero Rua: 100
- Complemento: 326.684
- Bairro: 573
- Valor de Compra: 421.382 (100%)

#### 2025/1

O arquivo contém 9.114 linhas completamente vazias.

Como consequência, pelo menos 9.114 valores nulos aparecem em praticamente
todos os atributos. Além disso:

- Numero Rua: 9.172
- Complemento: 332.908
- Bairro: 9.976
- Valor de Compra: 429.523 (100%)

#### 2025/2

- Numero Rua: 24
- Complemento: 297.501
- Bairro: 662
- Valor de Compra: 384.208 (100%)

### 6.2 Valor de Compra

A coluna `Valor de Compra` apresentou 100% de valores nulos nas seis partições
analisadas.

Como não fornece informação utilizável no período selecionado, sua remoção da
camada Silver é uma candidata à regra de transformação.

O arquivo original permanecerá preservado na Bronze, portanto a informação
original da fonte não será perdida.

### 6.3 Campos de endereço

`Complemento` apresenta grande quantidade de valores nulos em todas as
partições. Essa ausência não representa necessariamente um erro de qualidade,
uma vez que diversos endereços não possuem complemento.

Também foram identificados valores ausentes em `Numero Rua` e `Bairro`, porém
em quantidade consideravelmente menor.

Por esse motivo, esses campos não devem ser descartados automaticamente apenas
pela existência de valores nulos.

### 6.4 Linhas completamente vazias

Foram identificadas 9.114 linhas completamente vazias na partição 2025/1.

As demais partições analisadas não apresentaram linhas completamente vazias.

Essas linhas não representam observações de preço e deverão ser descartadas
durante o processamento para a camada Silver.

### 6.5 Unidade de medida

Nas partições analisadas foram encontradas as representações:

- `R$ / litro`
- `R$ / m³`
- `R$ / m3`

A variação `R$ / m3` foi encontrada em 2025/2.

Como `m3` e `m³` representam a mesma unidade, a camada Silver deverá
padronizar essa representação.

## 7. Análise de unicidade

Inicialmente foi considerada como possível chave candidata a combinação:

`CNPJ da Revenda + Produto + Data da Coleta`

A combinação apresentou unicidade nas partições:

- 2023/1
- 2023/2
- 2024/2
- 2025/1, desconsiderando as linhas completamente vazias
- 2025/2

Entretanto, foram identificadas 14 colisões na partição 2024/1.

A investigação dessas colisões mostrou que existem dois casos distintos:

1. registros integralmente idênticos;
2. registros com o mesmo CNPJ, produto e data de coleta, mas com diferenças
   em outros atributos, inclusive no valor de venda.

Isso demonstra que a combinação não constitui uma chave natural única
confiável para os dados da ANP.

Consequentemente, ela poderá continuar sendo utilizada como indicador para
detecção e monitoramento de possíveis colisões, mas não será utilizada
isoladamente como regra de deduplicação.

## 8. Estratégia de deduplicação

A estratégia definida a partir do profiling é conservadora.

A camada Silver poderá remover registros integralmente idênticos, pois eles não
adicionam uma nova observação ao dataset.

Por outro lado, registros que compartilham:

`CNPJ da Revenda + Produto + Data da Coleta`

mas apresentam diferenças em qualquer outro atributo relevante deverão ser
preservados.

Portanto, não será utilizada uma deduplicação baseada somente nessas três
colunas.

Essa decisão evita que observações distintas fornecidas pela própria fonte
sejam descartadas indevidamente.

## 9. Decisões para a camada Silver

A camada Silver será responsável pela limpeza, tipagem, padronização e
validação dos dados provenientes da Bronze.

Com base no profiling das seis partições, foram definidas as seguintes
transformações:

1. **Linhas completamente vazias:** remover registros em que todas as colunas
   estejam nulas.

2. **Duplicatas:** remover apenas registros integralmente idênticos,
   preservando observações que compartilhem CNPJ, produto e data, mas possuam
   diferenças em outros atributos.

3. **CNPJ da Revenda:** remover caracteres de formatação e preservar o valor
   como `String`.

4. **CEP:** padronizar sua representação e preservar o tipo `String`.

5. **Data da Coleta:** converter a representação `dd/mm/yyyy` para um tipo
   `Date`.

6. **Valor de Venda:** converter a representação textual com vírgula decimal
   para um tipo numérico adequado.

7. **Valor de Compra:** remover da Silver, uma vez que apresentou 100% de
   valores nulos em todas as partições analisadas. O atributo continuará
   preservado nos arquivos originais da Bronze.

8. **Unidade de Medida:** normalizar representações equivalentes, em especial
   `R$ / m3` e `R$ / m³`.

9. **Nomes de colunas:** padronizar a nomenclatura para facilitar o
   processamento programático e manter consistência entre as camadas.

10. **Atributos categóricos:** avaliar e aplicar padronizações de representação
    quando necessárias, evitando alterações que modifiquem o significado
    original dos dados.

11. **Chave geográfica:** posteriormente, associar município e UF ao código
    oficial do IBGE para permitir a integração com as fontes externas
    mapeadas pelo projeto.

## 10. Organização da Bronze

Os arquivos originais são mantidos sem alteração na camada Bronze, utilizando
particionamento lógico por ano e semestre:

    data/
    └── bronze/
        └── anp/
            └── automotivos/
                ├── ano=2023/
                │   ├── semestre=1/
                │   └── semestre=2/
                ├── ano=2024/
                │   ├── semestre=1/
                │   └── semestre=2/
                └── ano=2025/
                    ├── semestre=1/
                    └── semestre=2/

Problemas encontrados na fonte, como linhas vazias, duplicatas e
inconsistências de representação, não são corrigidos diretamente na Bronze.

Essa decisão preserva a fidelidade aos dados recebidos e permite que as
transformações posteriores sejam reproduzidas a partir da fonte original.

## 11. Conclusão do profiling

O profiling das seis partições permitiu compreender a estrutura e os principais
problemas de qualidade da fonte ANP antes da construção do pipeline.

O schema permaneceu consistente entre os arquivos analisados, enquanto foram
identificadas algumas anomalias específicas: linhas completamente vazias em
2025/1, duplicatas exatas em 2024/1, colisões na chave inicialmente considerada
candidata e uma diferença de representação da unidade de medida em 2025/2.

Também foi constatado que `Valor de Compra` não contém informação útil no
período analisado, apresentando 100% de valores nulos.

A análise demonstrou ainda que `CNPJ da Revenda + Produto + Data da Coleta`
não pode ser considerada uma chave única do dataset. Dessa forma, a
deduplicação deverá considerar apenas registros integralmente idênticos,
preservando observações distintas fornecidas pela ANP.

Com essas características identificadas, o profiling da fonte ANP para o
período de 2023 a 2025 é considerado concluído. As decisões documentadas aqui
servirão como requisitos para o desenho da arquitetura e para a implementação
posterior das transformações da camada Silver.
