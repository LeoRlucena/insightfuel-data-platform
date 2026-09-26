# Arquitetura da Plataforma de Dados --- InsightFuel

## 1. Visão Geral

A plataforma de dados InsightFuel foi projetada para realizar a ingestão, tratamento, integração e disponibilização analítica de dados relacionados ao mercado brasileiro de combustíveis.

A principal fonte utilizada é a Série Histórica de Preços de Combustíveis da Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP). A arquitetura também prevê a integração de fontes geográficas, demográficas, socioeconômicas e macroeconômicas necessárias às questões analíticas do projeto.

A solução utiliza uma arquitetura em três camadas --- Bronze, Silver e Gold --- seguindo o modelo Medallion apresentado durante a disciplina. O Apache Airflow é utilizado para orquestrar as etapas, enquanto as regras de ingestão, transformação, validação e agregação permanecem implementadas em módulos Python independentes da DAG.

A implementação foi desenvolvida com foco em reprodutibilidade, qualidade, incrementalidade e idempotência.

## 2. Arquitetura em Camadas

### 2.1 Bronze

A Bronze representa os dados em sua forma mais próxima possível da fonte original. No caso da ANP, os arquivos semestrais são obtidos automaticamente dos recursos oficiais, descompactados e armazenados como CSV.

Problemas encontrados na fonte, como linhas vazias, duplicações e valores ausentes, não são corrigidos nessa etapa. Essa preservação permite rastreabilidade e reprocessamento caso as regras de transformação sejam alteradas.

Os dados da ANP são particionados por ano e semestre, acompanhando a própria periodicidade de publicação da fonte.

### 2.2 Silver

A Silver contém dados tipados, padronizados e validados. Na transformação da ANP são realizadas, entre outras operações:

-   remoção de linhas completamente vazias;
-   remoção somente de registros integralmente duplicados;
-   padronização dos nomes das colunas;
-   conversão de datas e valores;
-   normalização de CNPJ, CEP e unidades de medida;
-   validação do contrato de dados.

Os arquivos são armazenados em Parquet e mantêm o particionamento por ano e semestre.

A dimensão de municípios do IBGE também é materializada na Silver, disponibilizando código IBGE, município, UF e região. O `codigo_ibge` passa a ser o identificador geográfico utilizado nas integrações posteriores.

### 2.3 Gold

A Gold contém produtos preparados para consumo analítico. Diferentemente da Silver, seus dados podem ser integrados e agregados de acordo com a necessidade de cada análise.

O primeiro produto implementado é a série mensal de preços por município e produto, com granularidade:

    ano_mes + codigo_ibge + produto

São calculados preço médio, mediano, mínimo, máximo, desvio padrão e quantidade de coletas. Outros produtos Gold podem ser criados posteriormente para análises de bandeiras, volatilidade, paridade etanol/gasolina, inflação e indicadores socioeconômicos.

## 3. Tecnologias e Justificativas

  -----------------------------------------------------------------------
  Tecnologia                          Utilização no projeto
  ----------------------------------- -----------------------------------
  Python                              Linguagem principal para ingestão,
                                      transformação, validação e
                                      agregação.

  Polars                              Processamento dos DataFrames. Foi
                                      escolhido pelo suporte a
                                      processamento colunar, tipos de
                                      dados e Parquet, além de
                                      experiência prévia do autor com a
                                      biblioteca.

  Parquet                             Armazenamento das camadas Silver e
                                      Gold em formato colunar, tipado e
                                      comprimido.

  Apache Airflow                      Orquestração das tarefas e controle
                                      das dependências do pipeline.

  HTTPX                               Comunicação HTTP com as fontes
                                      externas e download em streaming
                                      dos arquivos da ANP.

  uv                                  Gerenciamento do ambiente Python e
                                      das dependências por meio de
                                      `pyproject.toml` e `uv.lock`.

  Docker                              Ambiente reproduzível para execução
                                      do Airflow e instalação do pacote
                                      Python do projeto.

  DuckDB                              Previsto para consultas analíticas
                                      diretamente sobre os arquivos
                                      Parquet, sem necessidade de um
                                      servidor analítico dedicado nesta
                                      etapa.
  -----------------------------------------------------------------------

A Bronze permanece em CSV no caso da ANP para preservar o formato recebido da fonte.

## 4. Arquitetura de Ingestão das Fontes

As fontes são tratadas de forma independente antes de participarem dos produtos analíticos. Isso reduz o acoplamento entre elas: uma nova partição da ANP, por exemplo, não exige nova aquisição de uma fonte socioeconômica cuja versão permaneça válida.

``` text
                    FONTES EXTERNAS
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
            ANP          IBGE       Outras fontes
             │            │            │
             ▼            ▼            ▼
          Bronze       Bronze*       Bronze
             │            │            │
             ▼            ▼            ▼
          Silver       Silver        Silver
             └────────────┼────────────┘
                          ▼
                         Gold
                          │
                          ▼
                  Consulta e análise
```

\* Na implementação atual, o retorno bruto da API de Localidades do IBGE ainda não é persistido na Bronze. Essa persistência é uma evolução prevista.

Na ANP, o ZIP é baixado em streaming e o CSV é armazenado na partição correspondente. A dimensão de municípios do IBGE é padronizada e persistida na Silver. A associação entre as duas fontes utiliza UF e nome normalizado do município, passando posteriormente a utilizar o código IBGE como chave geográfica.

## 5. Pipeline Lógico

O pipeline foi dividido em tarefas com entradas, saídas e validações definidas. Os SLAs abaixo representam objetivos de disponibilidade dos dados, e não limites rígidos de duração das tarefas.

  ---------------------------------------------------------------------------------------
  Ordem       Task               Entrada       Saída       Principais      SLA /
                                                           validações      observação
  ----------- ------------------ ------------- ----------- --------------- --------------
  1           `baixar_anp`       ZIP oficial   CSV Bronze  HTTP, ZIP e CSV Até 24h após
                                 ANP                       esperado        nova partição;
                                                                           arquivos
                                                                           existentes são
                                                                           reutilizados

  2           `processar_anp`    CSV Bronze    Parquet     Schema, campos  Até 24h após
                                               Silver      obrigatórios,   Bronze
                                                           tipos, valores, 
                                                           CNPJ, UF,       
                                                           produtos e      
                                                           unidades        

  3           `processar_ibge`   API           Dimensão    Schema, nulos   Deve estar
                                 Localidades   Silver      obrigatórios e  disponível
                                 IBGE                      unicidade do    antes da Gold
                                                           código IBGE     dependente

  4           `construir_gold`   Silver ANP +  Gold mensal Schema,         Até 24h após
                                 IBGE                      granularidade   atualização
                                                           única e         das entradas
                                                           consistência    
                                                           das métricas    
  ---------------------------------------------------------------------------------------

O fluxo implementado é:

``` text
baixar_anp ──> processar_anp ──┐
                                ├──> construir_gold
              processar_ibge ───┘
```

Os conjuntos de dados completos não são transferidos entre tarefas pelo Airflow. Cada etapa materializa sua saída na camada correspondente, e o XCom é utilizado apenas para informações leves, como caminhos de arquivos.

## 6. Orquestração com Apache Airflow

A DAG `insightfuel_pipeline` coordena atualmente quatro tarefas: `baixar_anp`, `processar_anp`, `processar_ibge` e `construir_gold`.

O Airflow é responsável pela ordem, dependências e estado das tarefas. As regras de negócio permanecem no pacote `insightfuel_data_platform`, separadas da DAG. Dessa forma, funções de ingestão, transformação, validação, armazenamento e agregação podem ser executadas e testadas
fora do orquestrador.

A interface do Airflow permite acompanhar o estado de cada etapa e impede que tarefas dependentes sejam executadas quando seus pré-requisitos falham. Na fase atual do projeto, a DAG é disparada manualmente; um agendamento automático pode ser adicionado posteriormente.

## 7. Contratos e Qualidade dos Dados

As validações funcionam como contratos entre as etapas do pipeline. Para a ANP, os atributos são separados de acordo com sua importância:

  -----------------------------------------------------------------------
  Categoria               Exemplos                Tratamento
  ----------------------- ----------------------- -----------------------
  Críticos                Estado, Município,      Ausência bloqueia a
                          CNPJ, Produto, Data da  promoção para Silver
                          Coleta, Valor de Venda  
                          e Unidade de Medida     

  Analíticos              Região, Revenda e       Ausência pode limitar
                          Bandeira                análises, mas não
                                                  inviabiliza o núcleo do
                                                  processamento

  Complementares          Endereço, número,       Utilizados para
                          complemento, bairro,    profiling,
                          CEP e Valor de Compra   rastreabilidade ou
                                                  verificações auxiliares
  -----------------------------------------------------------------------

O contrato atual da Silver ANP contém `regiao`, `uf`, `municipio`, `revenda`, `cnpj_revenda`, `cep`, `produto`, `data_coleta`, `valor_venda`, `unidade_medida` e `bandeira`.

Colunas opcionais ausentes podem ser criadas com o tipo esperado e valores nulos, mantendo o schema da Silver estável. Esse comportamento foi testado removendo `Bandeira`: a transformação continuou e produziu a coluna `bandeira` como `String` com valores nulos. Em contrapartida, a remoção experimental de `Valor de Venda`, campo crítico, interrompeu corretamente a transformação.

A Silver também valida tipos, valores de venda, produtos, unidades, formato do CNPJ e UFs. A dimensão de municípios do IBGE verifica schema, campos obrigatórios e unicidade de `codigo_ibge`.

Na Gold, a combinação `ano_mes + codigo_ibge + produto` deve ser única. Também são verificadas condições como preços positivos, mínimo menor ou igual ao máximo e quantidade de coletas maior que zero. O desvio padrão pode ser nulo quando existe apenas uma observação no grupo.

## 8. Estratégia de Deduplicação

Durante o profiling foi avaliada como possível chave natural a combinação:

    CNPJ da Revenda + Produto + Data da Coleta

Entretanto, no primeiro semestre de 2024 foram encontrados 14 grupos com a mesma combinação. Parte deles era integralmente duplicada, mas outros possuíam diferenças em atributos como o valor de venda. Portanto, essa combinação não pode ser utilizada como chave única sem risco de eliminar observações legítimas.

A estratégia adotada é remover **somente duplicatas exatas**, considerando a linha completa da fonte antes da seleção das colunas da Silver.

  -----------------------------------------------------------------------
  Partição        Colisões na chave  Duplicatas exatas      Linhas vazias
                          candidata        redundantes 
  -------------- ------------------ ------------------ ------------------
  2023/1                          0                  0                  0

  2023/2                          0                  0                  0

  2024/1                  14 grupos                 10                  0

  2024/2                          0                  0                  0

  2025/1                        0\*              9.113              9.114

  2025/2                          0                  0                  0
  -----------------------------------------------------------------------

\* A análise da chave candidata desconsidera registros cujos componentes da chave são nulos.

Em 2024/1, 477.154 registros da Bronze resultaram em 477.144 após a remoção das 10 duplicatas exatas. Em 2025/1, foram encontradas 9.114 linhas completamente vazias. Elas são removidas antes da deduplicação, resultando em 420.409 registros válidos para continuidade.

Assim, registros com o mesmo CNPJ, produto e data, mas com alguma diferença nos demais atributos, são preservados.

## 9. Incrementalidade e Idempotência

Incrementalidade e idempotência resolvem problemas diferentes. A primeira permite incorporar novas partições sem processar novamente todo o histórico; a segunda evita efeitos duplicados quando uma etapa é reexecutada.

Na ANP, cada semestre é tratado como uma partição independente. O downloader verifica se o CSV da partição já está presente na Bronze e, nesse caso, reutiliza o arquivo. A Silver segue a mesma lógica de reutilização de partições já materializadas.

A Gold possui comportamento diferente: por ser derivada das camadas Silver, suas partições anuais podem ser reconstruídas de forma determinística. Assim, uma nova execução não realiza append dos mesmos indicadores ao resultado anterior.

  -----------------------------------------------------------------------
  Conceito                Problema tratado        Estratégia
  ----------------------- ----------------------- -----------------------
  Incrementalidade        Evitar reprocessar todo Partições por ano e
                          o histórico             semestre

  Idempotência            Evitar duplicação por   Reutilização de
                          reexecução              partições e
                                                  reconstrução
                                                  determinística

  Deduplicação            Remover repetições      Somente linhas
                          existentes na própria   integralmente idênticas
                          fonte                   
  -----------------------------------------------------------------------

Uma limitação atual é que a existência do arquivo não detecta uma eventual correção retroativa publicada pela fonte. Como evolução, podem ser registrados metadados e checksums por partição para identificar alterações de conteúdo e disparar o reprocessamento necessário.

## 10. Tratamento de Schema Drift

Como as fontes externas podem adicionar, remover ou renomear colunas, a plataforma diferencia mudanças críticas de alterações que podem ser absorvidas.

A Bronze preserva a estrutura recebida da fonte, enquanto a Silver representa o contrato interno da plataforma. Assim, uma mudança externa não precisa ser propagada automaticamente para os consumidores.

  -----------------------------------------------------------------------
  Alteração                           Tratamento
  ----------------------------------- -----------------------------------
  Coluna crítica removida             Bloqueia a promoção para Silver

  Coluna opcional removida            Mantém a coluna Silver com valores
                                      nulos

  Nova coluna adicionada              Permanece na Bronze e não entra
                                      automaticamente no contrato Silver

  Coluna crítica renomeada            É inicialmente tratada como ausente
                                      até que a mudança seja analisada

  Tipo ou formato incompatível        Falha na transformação ou validação
  -----------------------------------------------------------------------

Esse comportamento foi validado com dois testes: a ausência de `Bandeira` foi absorvida com valores nulos, enquanto a ausência de `Valor de Venda` bloqueou a transformação.

Essa política permite que mudanças da fonte sejam avaliadas antes de alterar o contrato utilizado pelas etapas seguintes.

## 11. Estratégia de Falhas e Reprocessamento

As camadas são persistidas separadamente, de forma que uma falha em uma etapa não invalide os dados já publicados nas anteriores.

  -----------------------------------------------------------------------
  Falha                               Comportamento esperado
  ----------------------------------- -----------------------------------
  Download da ANP                     A partição não é disponibilizada na
                                      Bronze e as etapas dependentes não
                                      prosseguem

  Schema crítico inválido             A partição não é promovida para
                                      Silver

  Falha na validação Silver           Os dados inválidos não são
                                      utilizados na Gold

  Falha no IBGE                       Produtos dependentes da dimensão
                                      geográfica não são construídos

  Falha na Gold                       Bronze e Silver já publicadas
                                      permanecem disponíveis
  -----------------------------------------------------------------------

Uma Gold com falha pode, por exemplo, ser reconstruída utilizando as Silver já materializadas, sem repetir necessariamente o download das fontes.

Falhas transitórias de rede ou indisponibilidade de APIs podem futuramente utilizar políticas de retry. Já falhas de qualidade, como ausência de uma coluna crítica, exigem análise em vez de simples repetição. A DAG atual ainda não possui política explícita de retries e alertas.

## 12. Organização Física e Particionamento

A organização principal dos dados é:

``` text
data/
├── bronze/
│   └── anp/automotivos/
│       └── ano=YYYY/semestre=N/arquivo.csv
├── silver/
│   ├── anp/automotivos/
│   │   └── ano=YYYY/semestre=N/dados.parquet
│   └── ibge/municipios/dados.parquet
└── gold/
    └── anp/precos_mensais_municipio/
        └── ano=YYYY/dados.parquet
```

Bronze e Silver ANP são particionadas por ano e semestre, acompanhando a publicação da fonte. A Gold é particionada por ano, mantendo `ano_mes` como atributo da granularidade analítica e evitando fragmentação excessiva em arquivos mensais pequenos.

## 13. Produtos Analíticos da Camada Gold

A Gold é organizada em produtos específicos, em vez de concentrar todas as análises em uma única tabela.

O produto atualmente implementado é:

    gold/anp/precos_mensais_municipio/

Sua granularidade é `ano_mes + codigo_ibge + produto`, com preço médio, mediano, mínimo, máximo, desvio padrão e quantidade de coletas.

A partir das demais fontes e transformações previstas, poderão ser construídos produtos para análises por bandeira, paridade etanol/gasolina, volatilidade, preços corrigidos pela inflação, contexto socioeconômico e detecção de anomalias.

## 14. Evoluções da Arquitetura

As principais evoluções identificadas são a persistência dos retornos brutos das APIs externas na Bronze, uso de checksums para detectar alterações retroativas, configuração de retries e alertas no Airflow e automatização da descoberta de novas partições da ANP.

Também está prevista a integração das demais fontes mapeadas, como população e PIB municipal, dados geográficos, indicadores socioeconômicos e IPCA. O DuckDB poderá ser utilizado para consultas sobre os arquivos Parquet e os produtos Gold poderão posteriormente alimentar ferramentas de visualização, como Power BI.

Essas evoluções complementam a implementação atual sem alterar a separação estabelecida entre as camadas da plataforma.
