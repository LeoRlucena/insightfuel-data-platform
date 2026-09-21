# Mapeamento de Fontes de Dados - InsightFuel Analytics

## 1. Objetivo

O projeto InsightFuel Analytics busca construir uma plataforma de dados capaz de integrar informações de preços de combustível em conjunto com dados geográficos, demográficos, socioeconômicos e macroeconômicos dos municípios brasileiros.

A base será composta pelos dados históricos de preços de combustíveis disponibilizados pela Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP). Esses dados serão enriquecidos por fontes externas, permitindo análises que se relacionam com fatores como renda, atividade econômica, distância das capitais e inflação.

A seleção de fontes externas levou em consideração as perguntas e hipóteses norteadores com enunciado da atividade propostas para o projeto.

---

## 2. ANP - Série Histórica de Preços de Combustíveis

**Fonte**: Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP).

**Dataset**: Série histórica de preços de combustíveis e de GLP.

**Acesso**: Portal de dados abertos da ANP / Portal Brasileiro de Dados Abertos.

**Formato utilizado**: CSV.

**Periodicidade dos arquivos utilizados**: semestral, contendo observações do levantamento periódico de preços.

**Período selecionado para o projeto**: 2023 a 2025.

### Dados de interesse

Os seguintes atributos são disponibilizados:

* Região;
* Unidade de Federação;
* Município;
* Nome da Revenda;
* CNPJ da Revenda;
* Endereço;
* Produto;
* Data da Coleta;
* Valor de Venda;
* Valor de Compra;
* Unidade de Medida;
* Bandeira;

### Justificativa

A ANP constitui a fonte principal do projeto, fornecendo as observações necessárias para construir séries temporais de preços de combustíveis.

Com essa fonte, podemos calcular preços médios e medianos, dispersão e volatilidade, paridade entre etanol e gasolina, diferenças regionais, comportamento por bandeira e detectar variações atípicas.

### Integração

A fonte não fornece código IBGE do município, o que implica em termos que relacionar os campos de município e UF da ANP com o cadastro oficial de municípios do IBGE, o que nos permite obter um identificador geográfico padronizado para os enriquecimentos posteriores.

---

## 3. IBGE - Cadastro de Localidades

**Fonte**: Instituto Brasileiro de Geografia e Estatística (IBGE).

**Serviço**: API de localidades / Registro de Referência de Municípios.

**Formato**: JSON via API REST.

**Granularidade**: Município.

### Dados de interesse

* Código IBGE do Município;
* Nome do Município;
* Unidade da Federação;
* Região;
* Demais hierarquias territoriais disponibilizadas pelo serviço;

### Justificativa

A API de localidades será utilizada para associar cada município presente nos dados da ANP ao respectivo código oficial do IBGE, que funcionará como chave geográfica padronizada para relacionar dados de combustíveis com população, PIB, indicadores socioeconômicos e informações geográficas, dessa forma enriquecendo a dimensão da análise.

### Chave de Integração Prevista

Inicialmente:

`Município + UF -> Código IBGE`

Após o enriquecimento, o código do IBGE passa a ser a principal chave para relacionar as demais fontes municipais.

---

## 4. IBGE - Estimativas da População

**Fonte**: Instituto Brasileiro de Geografia e Estatística (IBGE).

**Dataset**: Estimativas da População Residente para os Municípios e Unidades da Federação.

**Periodicidade**: Anual.

**Granularidade**: Município/Ano.

### Dados de interesse

* Código do município;

* População estimada;

* Ano de referência.

### Justificativa

A população municipal será utilizada para indicar o porte dos mercados locais, um enriquecimento que permitirá comparar o comportamento de preços entre municípios de diferentes tamanhos, investigando se mercados menores possuem maior volatilidade ou preços diferentes dos encontrados em centros urbanos maiores.

Além disso, também poderá ser utilizada para criar categorias de porte populacional, como municípios pequenos, médios e grandes.

### Chave de integração prevista

`Código IBGE + Ano`

---

## 5. IBGE - Produto Interno Bruto dos Municípios

**Fonte**: Instituto Brasileiro de Geografia e Estatística (IBGE).

**Dataset**: Produto Interno Bruto dos Municípios.

**Granularidade**: Município/Ano.

### Dados de interesse

* Código do município;
* PIB Municipal;
* PIB per capita;
* Ano de referência.

### Justificativa

O PIB per capita será utilizado como uma proxy de condição econômica do município, permitindo investigar a existência de associação entre condições econômicas locais e os preços praticados nos postos.

Além disso, também poderá compor modelos utilizados para estimar o preço esperado de determinado município, podendo tornar possível a construção do **Fuel Value Index**.

### Limitação Temporal

Existe uma diferença entre o perídio de preços da ANP e a disponibilidade do PIB Municipal.

Os dados ANP utilizados no projeto abrangem 2023 - 2025, enquanto os dados municipais de PIB do IBGE atualmente disponíveis chegam até 2023.

Portanto, o PIB não deverá ser tratado como uma variável contemporânea anual para todas as observações de 2024 e 2025.

### Chave de integração prevista

`Código IBGE + Ano de Referência`

---

## 6. IBGE - Malhas Territoriais

**Fonte**: Instituto Brasileiro de Geografia e Estatística (IBGE).

**Dataset/Serviço**: Malhas territoriais e municipais.

**Granularidade**: Município.

### Dados de interesse

* Código IBGE;
* Geometria Municipal;
* Limites territoriais;
* Informações geográficas para derivação de coordenadas ou centroides.

### Justificativa

A informação geográfica será utilizada principalmente para construir a variável de distância entre um município e a capital de sua respectiva Unidade da Federação.

### Limitação

A distância calculada dessa maneira representa uma aproximação geográfica e não necessariamente a distância logística ou rodoviária efetivamente percorrida no transporte dos combustíveis.

Portanto, a distância será tratada como uma proxy de isolamento ou custo logístico, e essa limitação deverá ser considerada na interpretação dos resultados.

### Chave de integração prevista

`Código IBGE`

---

## 7. Atlas do Desenvolvimento Humano / Base dos Dados - IDHM

**Fonte**: Atlas do Desenvolvimento humano no Brasil / PNUD.

**Fonte de acesso prevista**: Base dos dados.

**Granularidade**: Município/período de referência.

### Dados de interesse

* Código do município;
* IDHM;
* IDHM Renda;
* Outros componentes socioeconômicos que possam ser relevantes.

### Justificativa

O IDHM e, particularmente, o componente de renda podem ser utilizados como indicadores estruturais das condições socioeconômicas dos municípios, complementando o PIB per capita.

### Limitação Temporal

O IDHM municipal tradicionalmente utilizado pelo Atlas está associado aos dados dos Censos de 1991, 2000 e 2010. Dessa forma, o indicador não representa diretamente a condição socioeconômica dos municípios no período 2023–2025 analisado pela ANP.

Por esse motivo, o IDHM deverá ser tratado como uma característica estrutural histórica do município e não como uma variável anual contemporânea.

Para análises diretamente relacionadas ao período estudado, indicadores econômicos mais recentes, como o PIB per capita disponível, deverão receber prioridade.

### Chave de integração prevista

`Código IBGE`

---

## 8. Banco Central do Brasil - IPCA

**Fonte**: Banco Central do Brasil (BCB), utilizando dados provenientes do IPCA calculado pelo IBGE.

**Sistema**: Sistema Gerenciador de Séries Temporais (SGS).

**Série Prevista**: IPCA geral — código SGS 433.

**Granularidade**: Mês.

**Peridiocidade**: Mensal.

### Dados de interesse

* Mês/Ano;
* Variação Percentual Mensal do IPCA.

### Justificativa

Os valores de venda encontrados na ANP são preços nominais. Uma comparação direta entre preços observados em diferentes anos pode misturar alterações específicas do mercado de combustíveis com a perda geral do poder de compra da moeda.

A série mensal do IPCA permitirá construir um índice acumulado e converter os preços nominais para valores reais em uma mesma data-base.

### Chave de integração prevista

`Ano + Mês`

---

## 9. Matriz de Rastreabilidade

| Pergunta/Hipótese | Principais variáveis | Fontes |
| ----------- | ----------- | ----------- |
| Q1 - Variação regional | preço. produto, região, população, indicadores econômicos | ANP + IBGE |
| Q2 / H1 - Distância de capital | preço municipal e distância geográfica | ANP + IBGE + Localidades + Malhas |
| Q3 / H2 - Renda e preços | preço, PIB per capita e IDHM/IDHM Renda | ANP + IBGE PIB + Atlas/BD |
| Q4 / H3 - Volatilidade e porte | série temporal, produto, região e população | ANP + IBGE População |
| Q5 / H4 - Paridade etanol/gasolina | preço de etanol, gasolina e localização | ANP + IBGE Localidades |
| Q6 - Fuel Value Index | preço, bandeira, população e condições socioeconômicas | ANP + IBGE + Atlas/BD |
| Q7 - Porte populacional | preço e população municipal | ANP + IBGE População |
| Q8 - Anomalias | série temporal de preços | ANP |
| H5 - Bandeiras | preço e bandeira | ANP |
| H6 - Preços reais | preço nominal e IPCA mensal | ANP + BCB/IBGE |

---

## 10. Estratégia de Integração

O código de município do IBGE será o principal identificador geográfico entre as diferentes fontes, com o seguinte fluxo previsto:

`ANP -> padronização Município/UF -> API de Localidades -> Código IBGE`

A partir desse identificador teremos:

* `Código IBGE -> População`;
* `Código IBGE -> PIB / PIB per capita`;
* `Código IBGE -> IDHM`;
* `Código IBGE -> Malha geográfica`.

O IPCA será relacionado temporalmente aos preços por meio do ano e mês derivados da Data de Coleta da ANP:

* `Data da Coleta -> Ano/Mês -> IPCA`.

Com essa estratégia, reduzimos a dependência de relacionamentos baseados em nomes textuais de município, estabelecendo uma chave comum entre os dados e um maior enriquecimento.

---

## 11. Considerações sobre temporalidade

As fontes aqui selecionados apresentam diferentes frequências e períodos de atualização.

Os preços da ANP, por exemplo, possuem alta granularidade temporal e vão ser agregados para análises mensais. Já população possui referência anual, enquanto PIB municipal tem maior defasagem de divulgação. O IDHM possui caráter estrutural e histórico. Já o IPCA é de periodicidade mensal.

Por conta disso, não pode-se considerar que todas as variáveis sejam observadas simultaneamente em enriquecimentos. Dessa forma, o pipeline deverá preservar o ano ou período de referência de cada indicador, permitindo também identificar a temporalidade de cada informação utilizada nas análises.

---

## 12. Conclusão

As fontes selecionadas nos permitem cobrir os principais eixos analíticos propostos para o InsightFuel, sem introduzir fontes externas desnecessárias.

O núcleo transacional e temporal relacionado à preços gira em torno da ANP. O IBGE fornece a estrutura territorial, demográfica e econômica para caracterizar os municípios. O Atlas do Desenvolvimento Humano acrescenta características socioeconômicas estruturais, enquanto o IPCA permitirá comparar preços em termos reais.

Integrar todas essas fontes possibilitará construir uma camada analítica mensal enriquecida.

As principais limitações identificadas nesta etapa são a defasagem temporal do PIB municipal, a natureza histórica do IDHM e o uso de distância geográfica como proxy de distância logística, devendo sempre ser consideradas nas interpretações das análises.

---

## Referências das Fontes de Dados

**AGÊNCIA NACIONAL DO PETRÓLEO, GÁS NATURAL E BIOCOMBUSTÍVEIS (ANP).** Série Histórica de Preços de Combustíveis e de GLP. Portal Brasileiro de Dados Abertos. Disponível em:
https://dados.gov.br/dados/conjuntos-dados/serie-historica-de-precos-de-combustiveis-e-de-glp
Acesso em: 20 set. 2026.

**INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE).** API de Localidades. Serviço de Dados do IBGE. Disponível em:
https://servicodados.ibge.gov.br/api/docs/localidades#api-Municipios
Acesso em: 20 set. 2026.

**INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE).** Estimativas da População. Disponível em:
https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html
Acesso em: 20 set. 2026.

**INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE).** Produto Interno Bruto dos Municípios. Disponível em:
https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html
Acesso em: 20 set. 2026.

**INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE).** API de Malhas Geográficas. Serviço de Dados do IBGE. Disponível em:
https://servicodados.ibge.gov.br/api/docs/malhas?versao=4
Acesso em: 20 set. 2026.

**INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE).** Metadados Estatísticos do IBGE. Catálogo de APIs Governamentais. Disponível em:
https://www.gov.br/conecta/catalogo/apis/metadados-estatisticos-do-ibge
Acesso em: 20 set. 2026.

**PROGRAMA DAS NAÇÕES UNIDAS PARA O DESENVOLVIMENTO (PNUD); IPEA; FUNDAÇÃO JOÃO PINHEIRO.** Atlas do Desenvolvimento Humano no Brasil. Dados disponibilizados por meio da Base dos Dados. Disponível em:
https://basedosdados.org/dataset/cbfc7253-089b-44e2-8825-755e1419efc8?table=2b704f11-2b3a-485d-a492-71f86c7ea21a
Acesso em: 20 set. 2026.

**BANCO CENTRAL DO BRASIL (BCB).** Sistema Gerenciador de Séries Temporais (SGS). Série 433 — Índice Nacional de Preços ao Consumidor Amplo (IPCA), variação percentual mensal. Disponível em:
https://www3.bcb.gov.br/sgspub/consultarvalores/consultarValoresSeries.do?method=consultarSeries&series=433
Acesso em: 20 set. 2026.

**BANCO CENTRAL DO BRASIL (BCB).** Portal de Dados Abertos do Banco Central do Brasil. Disponível em:
https://dadosabertos.bcb.gov.br/
Acesso em: 20 set. 2026.
