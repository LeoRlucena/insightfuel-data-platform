# Arquitetura da Plataforma de Dados — InsightFuel

## 1. Visão Geral

A plataforma de dados InsightFuel foi projetada para realizar a ingestão, tratamento, integração e disponibilização analítica de dados relacionados ao mercado brasileiro de combustíveis.

A principal fonte utilizada é a Série Histórica de Preços de Combustíveis disponibilizada pela Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP). A arquitetura também prevê a integração de fontes complementares, como dados geográficos, demográficos, socioeconômicos e macroeconômicos, necessários para responder às questões analíticas propostas pelo projeto.

A plataforma segue uma arquitetura de dados em três camadas — Bronze, Silver e Gold — separando a preservação dos dados de origem, o tratamento e padronização dos registros e a construção dos produtos destinados ao consumo analítico. Isso reflete a arquitetura Medallion, apresentada durante as aulas.

O Apache Airflow é utilizado como ferramenta de orquestração, sendo responsável pelo controle das dependências e da ordem de execução das etapas do pipeline. As regras de negócio e transformações permanecem implementadas em módulos Python independentes da DAG, permitindo que sejam executadas e testadas fora do ambiente do Airflow, promovendo reprodutibilidade.

A implementação foi desenvolvida com foco em reprodutibilidade, qualidade, incrementalidade e idempotência. Dessa forma, novas partições podem ser incorporadas ao conjunto de dados sem a necessidade de reconstrução manual de todo o histórico, enquanto reexecuções do pipeline evitam duplicações ou acúmulo indevido de registros. Isso bate justamente com um dos requisitos propostos pelo trabalho final da disciplina.


## 2. Arquitetura em Camadas

A arquitetura utiliza três camadas principais de armazenamento: Bronze,Silver e Gold. Cada camada possui responsabilidades distintas dentro do ciclo de processamento dos dados.

### 2.1 Bronze

A camada Bronze representa os dados em sua forma mais próxima possível da fonte original, completamente crua, da maneira que é baixada.

No caso da ANP, os arquivos semestrais são obtidos automaticamente a partir dos recursos oficiais disponibilizados pela ANP. Os arquivos compactados são baixados e os CSVs originais são armazenados em partições organizadas por ano e semestre.

Exemplo:

    data/bronze/anp/automotivos/
    ├── ano=2023/
    │   ├── semestre=1/
    │   └── semestre=2/
    ├── ano=2024/
    │   ├── semestre=1/
    │   └── semestre=2/
    └── ano=2025/
        ├── semestre=1/
        └── semestre=2/

A Bronze não tem como objetivo corrigir problemas encontrados na fonte. Situações como linhas vazias, registros duplicados, diferenças de representação e valores ausentes são preservadas nessa etapa. Isso permite manter rastreabilidade sobre o dado recebido e possibilita o reprocessamento posterior caso as regras de transformação sejam alteradas.

A organização por ano e semestre acompanha a granularidade de publicação da fonte da ANP e permite que novas partições sejam incorporadas incrementalmente, conforme solicitado. 


### 2.2 Silver

A camada Silver contém dados tipados, padronizados e validados, adequados para integração com outras fontes e para a construção dos produtos analíticos.

Durante a transformação dos dados da ANP são realizadas operações como:

- remoção de linhas completamente vazias;
- remoção exclusivamente de registros integralmente duplicados;
- padronização dos nomes das colunas;
- conversão da data de coleta para tipo de data;
- conversão do valor de venda para representação numérica;
- normalização do CNPJ e do CEP;
- padronização das unidades de medida;
- seleção dos atributos relevantes para as etapas posteriores.

A deduplicação não utiliza a combinação CNPJ da revenda, produto e data da coleta como chave única. Durante o profiling foram identificadas observações distintas que compartilham essa combinação, inclusive com diferentes valores de venda. Por esse motivo, apenas duplicatas integralmente idênticas são removidas, evitando a perda de observações legítimas.

Os dados tratados são armazenados em formato Parquet e continuam particionados por ano e semestre:

    data/silver/anp/automotivos/
    └── ano=YYYY/
        └── semestre=N/
            └── dados.parquet

A dimensão de municípios proveniente do IBGE também é materializada na Silver. Ela disponibiliza, entre outros atributos, o código oficial do município, município (nome), unidade federativa e região, permitindo a utilização do código IBGE como chave geográfica de integração.

Essa separação evita que chamadas a serviços externos sejam realizadas repetidamente durante cada transformação analítica.

### 2.3 Gold

A camada Gold é destinada aos produtos de dados preparados para análise e resposta às questões de negócio do projeto.

Diferentemente da Silver, a Gold não representa apenas dados limpos. Nessa camada são construídas agregações e combinações orientadas às necessidades analíticas.

O primeiro produto implementado é a série mensal de preços de combustíveis por município e produto, cuja granularidade é:

    ano_mes + codigo_ibge + produto

Para cada combinação são calculadas métricas como:

- preço médio;
- preço mediano;
- preço mínimo;
- preço máximo;
- desvio padrão;
- quantidade de coletas.

Os dados são enriquecidos com a dimensão oficial de municípios do IBGE antes da agregação, utilizando o código IBGE como identificador geográfico.

O produto é armazenado em Parquet e particionado por ano:

    data/gold/anp/precos_mensais_municipio/
    ├── ano=2023/
    │   └── dados.parquet
    ├── ano=2024/
    │   └── dados.parquet
    └── ano=2025/
        └── dados.parquet

A arquitetura permite a criação de múltiplos produtos Gold independentes. Dessa forma, análises futuras de volatilidade, relação entre etanol e gasolina, comportamento por bandeira, preços reais corrigidos pela inflação e indicadores socioeconômicos podem possuir conjuntos de dados específicos, sem a necessidade de concentrar todas as análises em uma única tabela.


## 3. Tecnologias e Justificativas

### Python

Python foi adotado como linguagem principal da plataforma por oferecer um ecossistema consolidado para engenharia e análise de dados e por permitir que as regras de transformação sejam implementadas independentemente da ferramenta de orquestração.

A lógica de negócio é organizada em módulos próprios do projeto, enquanto o Airflow permanece responsável principalmente pela orquestração das etapas.

### Polars

Polars é utilizado para leitura, transformação, validação e agregação dos dados.

A biblioteca oferece processamento orientado a colunas, suporte nativo a tipos de dados e integração direta com formatos colunares como Parquet. Para o volume de dados utilizado no projeto, permite executar as transformações localmente sem a necessidade de introduzir uma infraestrutura distribuída.

A razão da preferência por Polars ao Pandas se dá ao fato de eu já ter tido contato prévio com Polars para outros projetos e testes pessoais.

### Apache Parquet

Parquet foi escolhido como formato de armazenamento das camadas Silver e Gold.

Por ser um formato colunar, permite leitura seletiva das colunas necessárias, mantém informações de tipos e oferece compressão eficiente. Essas características são adequadas para cargas analíticas realizadas por ferramentas como Polars e DuckDB.

A Bronze permanece em CSV para preservar o formato disponibilizado pela fonte.

### Apache Airflow

Apache Airflow é utilizado como ferramenta de orquestração do pipeline.

A DAG define as dependências entre aquisição, transformação, integração e construção da camada Gold, enquanto as regras de processamento permanecem fora da definição da DAG.

A execução principal atualmente possui o seguinte fluxo:

    baixar_anp ──> processar_anp ──┐
                                   ├──> construir_gold
                 processar_ibge ───┘

Essa organização permite observar individualmente o estado de cada etapa, reexecutar tarefas em caso de falha e impedir que produtos dependentes sejam construídos quando uma etapa anterior não for concluída com sucesso.

### HTTPX

HTTPX é utilizado para comunicação HTTP com as fontes externas.

Na ingestão da ANP, o download dos arquivos é realizado em streaming, evitando a necessidade de carregar o arquivo compactado integralmente em memória antes de sua persistência e extração.

A escolha por `httppx`ao invés de `requests` se dá ao fato da biblioteca escolhida suportar chamadas assíncronas nativamente. Como pretendo tornar disso um trabalho para meu portfólio, isso pode vir a ser útil no futuro. 

### DuckDB

DuckDB é previsto como mecanismo de consulta analítica sobre os arquivos Parquet produzidos pela plataforma.

Sua utilização permite consultar diretamente os produtos Silver e Gold sem a necessidade de manter, nesta etapa do projeto, um servidor de banco de dados analítico dedicado.

### uv

O uv é utilizado para gerenciamento do ambiente Python e das dependências do projeto.

As dependências declaradas no `pyproject.toml` e resolvidas no `uv.lock` permitem reproduzir o ambiente de desenvolvimento com versões conhecidas dos pacotes utilizados.

### Docker

Docker é utilizado para fornecer um ambiente reproduzível para a execução do Apache Airflow e da aplicação Python.

A imagem utilizada pelo Airflow instala o pacote Python do próprio projeto, permitindo que as DAGs utilizem diretamente as funções implementadas nos módulos de ingestão, transformação, validação, armazenamento e agregação.

## 4. Arquitetura de Ingestão das Fontes

A plataforma foi projetada para receber dados de múltiplas fontes de forma independente. Cada fonte possui seu próprio processo de aquisição, persistência e tratamento antes de participar da construção dos produtos analíticos.

Essa separação evita o acoplamento entre as fontes. Uma atualização nos dados da ANP, por exemplo, não exige que os dados socioeconômicos ou geográficos sejam novamente obtidos caso suas respectivas versões permaneçam válidas.

A arquitetura geral de ingestão pode ser representada da seguinte forma:

```text
                    FONTES EXTERNAS
                          │
          ┌───────────────┼───────────────────┐
          │               │                   │
          ▼               ▼                   ▼
         ANP             IBGE          Outras fontes
    preços combust.   municípios      socioeconômicas
          │               │             e econômicas
          ▼               ▼                   ▼
    ┌───────────┐    ┌───────────┐      ┌───────────┐
    │  Bronze   │    │  Bronze*  │      │  Bronze   │
    │    ANP    │    │   IBGE    │      │ por fonte │
    └─────┬─────┘    └─────┬─────┘      └─────┬─────┘
          │                │                  │
          ▼                ▼                  ▼
    ┌───────────┐    ┌───────────┐      ┌───────────┐
    │  Silver   │    │  Silver   │      │  Silver   │
    │    ANP    │    │   IBGE    │      │ por fonte │
    └─────┬─────┘    └─────┬─────┘      └─────┬─────┘
          │                │                  │
          └──────────┬─────┴──────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │    Gold     │
              │  produtos   │
              │ analíticos  │
              └──────┬──────┘
                     │
                     ▼
             Consulta e análise
              Polars / DuckDB

* A persistência do retorno bruto da API do IBGE na camada Bronze
  encontra-se prevista como evolução da implementação.
```

## 5. Pipeline Lógico

O pipeline foi estruturado como um conjunto de etapas com responsabilidades bem definidas. Cada tarefa possui entradas e saídas identificáveis, permitindo que falhas sejam isoladas e que etapas concluídas não precisem ser desnecessariamente repetidas.

Os SLAs apresentados nesta seção representam objetivos de disponibilidade dos dados e não limites rígidos de duração computacional das tarefas. Essa escolha considera que o tempo de execução pode variar de acordo com o tamanho dos arquivos, velocidade de rede e recursos disponíveis no ambiente de execução.

| Ordem | Task | Entrada | Saída | Testes e validações | SLA | Observações |
|---|---|---|---|---|---|---|
| 1 | `baixar_anp` | Arquivos ZIP oficiais da ANP | CSV original particionado na Bronze | Status HTTP, validade do ZIP e presença do CSV esperado | Até 24h após disponibilização da nova partição | Download em streaming. Partições já existentes são reutilizadas. |
| 2 | `processar_anp` | CSVs da Bronze ANP | Parquet particionado na Silver ANP | Schema de entrada, campos obrigatórios, tipos, valores válidos, CNPJ, UF, produtos e unidades | Até 24h após disponibilidade da Bronze | Remove linhas vazias e somente duplicatas integralmente idênticas. |
| 3 | `processar_ibge` | API de Localidades do IBGE | Dimensão de municípios em Parquet na Silver | Schema, ausência de nulos nos campos obrigatórios e unicidade do `codigo_ibge` | Antes da construção de produtos Gold dependentes da dimensão | Produz a dimensão geográfica utilizada para integração das demais fontes. |
| 4 | `construir_gold` | Silver ANP + Silver Municípios IBGE | Parquet Gold mensal por município e produto | Schema, unicidade da granularidade, métricas positivas, consistência mínimo/máximo e quantidade de coletas | Até 24h após atualização das Silver dependentes | Enriquece os registros com `codigo_ibge`, agrega mensalmente e publica partições anuais. |

### 5.1 Fluxo lógico

O fluxo atualmente implementado pode ser representado pelo seguinte pseudo-DAG:

    baixar_anp
        │
        ▼
    processar_anp ──────────────┐
                                │
    processar_ibge ─────────────┤
                                ▼
                         construir_gold
                                │
                                ▼
                     produtos analíticos

`baixar_anp` e `processar_anp` possuem uma relação sequencial, pois a transformação depende da existência dos arquivos da camada Bronze.

A dimensão de municípios do IBGE é processada de forma independente dos dados da ANP. Dessa forma, as duas ramificações podem ser executadas independentemente até o momento em que seus resultados são necessários para a construção da Gold.

A tarefa `construir_gold` somente pode ser executada após a disponibilidade das duas entradas Silver necessárias. Essa dependência impede que o produto analítico seja publicado sem que seus dados de origem e sua dimensão geográfica estejam disponíveis.

### 5.2 Entradas e saídas das etapas

As tarefas do Airflow não transportam os conjuntos de dados completos entre si. Os resultados intermediários são materializados nas respectivas camadas de armazenamento, e as tarefas subsequentes consomem esses artefatos.

Dessa forma, o fluxo físico dos dados pode ser resumido como:

    ANP
     │
     │ ZIP
     ▼
    [baixar_anp]
     │
     │ CSV
     ▼
    Bronze ANP
     │
     ▼
    [processar_anp]
     │
     │ Parquet
     ▼
    Silver ANP ────────────────┐
                               │
    API IBGE                   │
       │                       │
       ▼                       │
    [processar_ibge]           │
       │                       │
       ▼                       │
    Silver Municípios ─────────┤
                               ▼
                       [construir_gold]
                               │
                               ▼
                         Gold Parquet

O XCom do Airflow é utilizado apenas para resultados leves, como caminhos de arquivos produzidos pelas tarefas. DataFrames e arquivos completos não são transportados pelo mecanismo de comunicação entre tarefas.

Essa estratégia reduz o acoplamento entre as etapas e permite que os artefatos intermediários sejam inspecionados, reutilizados e reprocessados independentemente.

## 6. Orquestração com Apache Airflow

O Apache Airflow é utilizado como camada de orquestração da plataforma,
sendo responsável por definir a ordem de execução, as dependências e o
estado das diferentes etapas do pipeline.

A DAG principal, denominada `insightfuel_pipeline`, coordena atualmente
quatro tarefas:

- `baixar_anp`: aquisição das partições semestrais da ANP e persistência
  dos arquivos na camada Bronze;
- `processar_anp`: transformação e validação dos dados da Bronze para a
  Silver;
- `processar_ibge`: obtenção, transformação e persistência da dimensão
  oficial de municípios do IBGE;
- `construir_gold`: integração das fontes necessárias e construção do
  produto analítico mensal da camada Gold.

As dependências implementadas na DAG podem ser representadas por:

    baixar_anp ──> processar_anp ──┐
                                   ├──> construir_gold
                 processar_ibge ───┘

A dependência entre `baixar_anp` e `processar_anp` garante que a
transformação somente seja iniciada após a disponibilização da respectiva
entrada Bronze.

O processamento da dimensão de municípios do IBGE não depende da ingestão
dos dados da ANP e, portanto, constitui uma ramificação independente do
pipeline. A tarefa `construir_gold`, por sua vez, depende das duas entradas
Silver necessárias para realizar a integração e agregação dos dados.

### 6.1 Separação entre orquestração e regras de negócio

As regras de transformação não são implementadas diretamente no arquivo da DAG. A lógica de ingestão, transformação, validação, armazenamento e agregação é organizada em módulos Python pertencentes ao pacote `insightfuel_data_platform`.

O Airflow atua principalmente como coordenador dessas operações.

Essa separação permite executar e testar as funções do pipeline independentemente do Airflow, reduz o acoplamento com a ferramenta de orquestração e facilita a manutenção do projeto.

A organização lógica pode ser resumida como:

Airflow DAG
    │
    ▼
pipeline/coordenadores
    │
    ├── ingestion
    ├── transformation
    ├── validation
    ├── aggregation
    └── storage

Dessa forma, uma alteração em uma regra de transformação não exige que essa regra seja reimplementada na definição da DAG.

### 6.2 Persistência entre tarefas

Os conjuntos de dados processados não são transferidos integralmente entre as tarefas por meio do Airflow.

Cada etapa materializa seus resultados na camada correspondente do armazenamento, enquanto o XCom é utilizado somente para informações leves, como os caminhos dos artefatos produzidos.

Por exemplo:

    processar_anp
          │
          ▼
    Silver Parquet
          │
          ▼
    construir_gold

Essa abordagem evita utilizar o mecanismo de comunicação do orquestrador como transporte de grandes volumes de dados e torna os resultados intermediários persistentes e reutilizáveis.

### 6.3 Observabilidade e controle de execução

A interface do Airflow permite acompanhar individualmente o estado de cada tarefa e da execução completa da DAG.

Uma falha em uma etapa pode ser identificada sem que seja necessário tratar o pipeline como um único processo monolítico. As dependências da DAG também impedem que tarefas posteriores sejam executadas quando uma entrada obrigatória não foi produzida com sucesso.

A execução atualmente pode ser disparada manualmente, característica adequada à fase de desenvolvimento e validação do projeto. A arquitetura permite posteriormente associar a DAG a um agendamento ou mecanismo de detecção de novas partições sem alterar as regras de transformação.

### 6.4 Reexecução e idempotência

As tarefas foram projetadas considerando a possibilidade de reexecução.

Na ingestão da ANP, uma partição Bronze já existente é reutilizada, evitando o download desnecessário do mesmo arquivo. Na transformação para a Silver, partições já materializadas podem ser identificadas e reutilizadas.

Na construção da Gold, as partições anuais são reconstruídas de forma determinística, evitando que uma nova execução simplesmente acrescente registros aos resultados anteriores.

Esse comportamento reduz o risco de duplicação decorrente de reexecuções e permite recuperar o pipeline após falhas sem necessariamente reconstruir todo o histórico.

## 7. Contratos e Qualidade dos Dados

A plataforma aplica validações entre as diferentes etapas do pipeline para evitar que dados estruturalmente inválidos sejam promovidos para as camadas seguintes.

As validações são tratadas como contratos de dados. Esses contratos definem quais atributos são necessários para que uma partição possa ser processada, quais características são esperadas na saída e quais alterações da fonte podem ser toleradas sem interromper todo o pipeline.

A estratégia diferencia problemas que inviabilizam o processamento de alterações que apenas reduzem a disponibilidade de determinados atributos analíticos.

### 7.1 Classificação dos atributos da fonte ANP

Os atributos da ANP são classificados em três grupos de acordo com sua importância para o pipeline.

| Categoria | Exemplos | Comportamento esperado |
|---|---|---|
| Críticos | Estado, Município, CNPJ da Revenda, Produto, Data da Coleta, Valor de Venda e Unidade de Medida | A ausência impede a promoção da partição para a Silver |
| Analíticos | Região, Revenda e Bandeira | A ausência não inviabiliza o núcleo do processamento, mas pode limitar determinadas análises |
| Complementares | Endereço, número, complemento, bairro, CEP e Valor de Compra | Utilizados para rastreabilidade, profiling ou verificações auxiliares e não constituem requisitos do núcleo analítico |

Os campos críticos representam as informações mínimas necessárias para identificar geograficamente a observação, identificar o estabelecimento e produto, determinar o momento da coleta e interpretar corretamente o preço observado.

Por exemplo, a ausência de `Valor de Venda` impede a construção dos indicadores de preço e, portanto, é tratada como erro. Nesse caso, a partição não deve ser promovida para a Silver.

A ausência de um atributo analítico, por outro lado, pode não inviabilizar todas as análises. Caso `Bandeira` não seja fornecida em determinada partição, ainda é possível calcular preços por município e produto, embora análises relacionadas à comparação entre bandeiras fiquem comprometidas.

### 7.2 Contrato da camada Silver

A camada Silver possui um schema controlado e independente de pequenas variações ocorridas na fonte.

Para os dados da ANP, o contrato atualmente contém os seguintes atributos:

    regiao
    uf
    municipio
    revenda
    cnpj_revenda
    cep
    produto
    data_coleta
    valor_venda
    unidade_medida
    bandeira

Durante a transformação são aplicadas regras de tipagem e padronização, incluindo:

- `data_coleta` convertida para tipo de data;
- `valor_venda` convertido para representação decimal;
- CNPJ normalizado para conter somente dígitos;
- CEP normalizado para conter somente dígitos;
- unidades de medida padronizadas;
- nomes de colunas convertidos para o padrão interno da plataforma.

A estabilidade desse contrato é importante para evitar que consumidores da Silver precisem se adaptar automaticamente a cada pequena alteração da fonte.

Quando um atributo opcional utilizado pelo contrato Silver está ausente na fonte, a coluna correspondente pode ser criada com o tipo esperado e valores nulos. Dessa forma, o schema da Silver permanece estável, ao mesmo tempo em que a indisponibilidade da informação é preservada explicitamente.

Esse comportamento foi validado simulando a ausência do campo `Bandeira`. A transformação permaneceu válida e produziu a coluna `bandeira` como `String`, com valores nulos para a partição testada.

### 7.3 Validações da camada Silver

Após a transformação, a partição é submetida a verificações de qualidade antes de ser considerada válida para consumo pelas etapas seguintes.

Entre as verificações aplicadas estão:

- presença das colunas previstas no contrato;
- tipos de dados esperados;
- presença dos campos obrigatórios;
- validade dos valores de venda;
- produtos conhecidos;
- unidades de medida conhecidas;
- formato esperado do CNPJ;
- validade das siglas de unidades federativas.

Essas verificações possuem objetivo diferente do profiling exploratório realizado inicialmente. O profiling foi utilizado para compreender as características e anomalias da fonte, enquanto as validações do pipeline transformam parte desse conhecimento em regras executáveis.

### 7.4 Qualidade da dimensão de municípios

A dimensão de municípios proveniente do IBGE também possui contrato próprio.

São esperados os atributos:

    codigo_ibge
    municipio
    uf
    regiao
    municipio_match

A validação verifica a presença desses atributos, ausência de valores nulos nos campos obrigatórios e unicidade de `codigo_ibge`.

O código IBGE é utilizado como identificador geográfico canônico para integrações posteriores.

A associação dos registros da ANP com essa dimensão é realizada por unidade federativa e nome normalizado do município. Nos dados utilizados pelo projeto, o processo de associação foi validado para as partições analisadas, permitindo utilizar o código oficial do IBGE na construção da Gold.

### 7.5 Validações da camada Gold

A camada Gold também possui validações próprias, direcionadas à granularidade e às métricas produzidas.

Para o produto de preços mensais por município e produto, a granularidade esperada é:

    ano_mes + codigo_ibge + produto

Essa combinação deve ser única no produto final.

Também são verificadas condições como:

- presença e tipos das colunas previstas;
- valores positivos para as métricas de preço;
- preço mínimo menor ou igual ao preço máximo;
- quantidade de coletas maior que zero;
- unicidade da granularidade analítica.

O campo `desvio_padrao` admite valores nulos quando existe apenas uma observação no grupo. Nesse caso, o valor ausente possui significado estatístico legítimo e não é substituído artificialmente por zero.

### 7.6 Níveis de tratamento de problemas

Conceitualmente, os resultados das verificações podem ser classificados em três níveis:

    OK
    └── contrato atendido e processamento permitido

    WARNING
    └── alteração ou ausência não crítica;
        processamento pode continuar com limitação conhecida

    ERROR
    └── violação de requisito crítico;
        partição não deve ser promovida

Essa distinção evita dois extremos: aceitar silenciosamente qualquer alteração da fonte ou interromper todo o pipeline por mudanças que não comprometem o produto analítico principal.

Uma coluna crítica ausente é tratada como erro. Esse comportamento foi validado removendo experimentalmente `Valor de Venda` de uma partição, o que resultou no bloqueio da transformação antes da geração da Silver.

Já a ausência de uma coluna opcional, como `Bandeira`, pode ser absorvida mantendo o contrato estrutural da Silver e representando a informação indisponível por valores nulos.

## 8. Estratégia de Deduplicação

A estratégia de deduplicação foi definida a partir do profiling das seis partições semestrais da ANP utilizadas no projeto, correspondentes ao período de 2023 a 2025.

Inicialmente foi avaliada como possível chave natural a combinação:

    CNPJ da Revenda + Produto + Data da Coleta

Essa combinação representa, intuitivamente, uma observação de determinado produto em um estabelecimento em uma data específica. Entretanto, a análise dos dados demonstrou que ela não constitui uma chave única confiável para a fonte.

### 8.1 Avaliação da chave candidata

Nas partições de 2023 e na maior parte das demais partições analisadas, a combinação candidata não apresentou colisões. Entretanto, na partição referente ao primeiro semestre de 2024 foram encontrados 14 grupos em que mais de um registro possuía o mesmo CNPJ, produto e data de coleta.

A investigação desses registros mostrou dois comportamentos distintos.

Em alguns casos, os registros eram integralmente idênticos. Esses casos representam duplicações que podem ser removidas sem perda de informação.

Em outros casos, entretanto, registros com a mesma combinação de CNPJ, produto e data apresentavam diferenças em outros atributos, inclusive no valor de venda.

Por exemplo, foram encontradas observações pertencentes à mesma combinação de estabelecimento, produto e data com valores de venda distintos.

Isso demonstra que:

    CNPJ + Produto + Data da Coleta

não pode ser utilizado como chave de deduplicação.

Caso o pipeline mantivesse arbitrariamente apenas um registro para cada combinação, observações distintas presentes na própria fonte seriam descartadas.

### 8.2 Critério adotado

A camada Silver remove exclusivamente duplicatas exatas.

Uma duplicata é considerada exata quando todos os atributos do registro original são iguais aos de outro registro da mesma partição.

A deduplicação é realizada antes da seleção das colunas que compõem o schema da Silver. Essa ordem é importante porque atributos que posteriormente não são utilizados na Silver ainda podem diferenciar duas observações na fonte.

O fluxo pode ser representado por:

    registro Bronze
          │
          ▼
    comparação da linha completa
          │
          ├── integralmente igual ──> remove repetição
          │
          └── alguma diferença ─────> preserva observação
          │
          ▼
    seleção e transformação Silver

Dessa forma, a transformação reduz redundâncias comprovadas sem assumir uma chave primária que não é garantida pela fonte.

### 8.3 Evidências encontradas no profiling

O profiling identificou comportamentos diferentes entre as partições.

| Partição | Colisões na chave candidata | Duplicatas exatas redundantes | Linhas completamente vazias |
|---|---:|---:|---:|
| 2023/1 | 0 | 0 | 0 |
| 2023/2 | 0 | 0 | 0 |
| 2024/1 | 14 grupos | 10 | 0 |
| 2024/2 | 0 | 0 | 0 |
| 2025/1 | 0* | 9.113 | 9.114 |
| 2025/2 | 0 | 0 | 0 |

\* A análise da chave candidata desconsidera registros em que os componentes
da chave são nulos.

A partição 2024/1 apresentou 477.154 registros na Bronze. Após a remoção das
10 duplicatas exatas redundantes, foram preservados 477.144 registros.

A partição 2025/1 apresentou um comportamento diferente. Foram identificadas
9.114 linhas completamente vazias ao final do arquivo. Como todas essas
linhas são idênticas entre si, uma operação de deduplicação isolada manteria
uma delas e removeria apenas 9.113 repetições.

Por esse motivo, linhas completamente vazias e duplicatas exatas são tratadas como problemas distintos no processo de transformação.

### 8.4 Ordem das operações

A transformação da Bronze para a Silver aplica inicialmente:

    Bronze
      │
      ▼
    remoção de linhas completamente vazias
      │
      ▼
    remoção de duplicatas exatas
      │
      ▼
    seleção e padronização das colunas
      │
      ▼
    Silver

A remoção das linhas vazias antes da deduplicação garante que registros sem qualquer informação não sejam mantidos apenas porque a operação de deduplicação preservaria uma ocorrência de cada linha distinta.

No caso de 2025/1:

    429.523 registros Bronze
              │
              ├── 9.114 linhas completamente vazias
              ▼
    420.409 registros válidos para continuidade

Após a aplicação das regras de limpeza e deduplicação, a partição resultante possui 420.409 registros.

### 8.5 Preservação das observações da fonte

A estratégia adotada privilegia a preservação das observações quando não há evidência suficiente para classificá-las como duplicadas.

Portanto, duas linhas que compartilhem CNPJ, produto e data da coleta, mas possuam valores de venda diferentes, permanecem na Silver.

Essa decisão evita introduzir uma regra de negócio não fornecida pela ANP, como escolher o maior preço, o menor preço, o primeiro registro ou o último registro.

Caso uma fonte futura forneça um identificador oficial único para cada observação, esse identificador poderá ser incorporado ao contrato e a estratégia de deduplicação poderá ser revisada.

## 9. Incrementalidade e Idempotência

## 10. Tratamento de Schema Drift

## 11. Estratégia de Falhas e Reprocessamento

## 12. Organização Física e Particionamento

## 13. Produtos Analíticos da Camada Gold

## 14. Evoluções da Arquitetura