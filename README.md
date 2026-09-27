# InsightFuel Data Platform

Plataforma de dados desenvolvida para análise dos preços de combustíveis no Brasil a partir dos dados públicos disponibilizados pela Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP).

O projeto foi desenvolvido como parte da disciplina de **Tecnologia de Armazenamento de Dados** e implementa um pipeline de dados utilizando Apache Airflow, Python, Polars e Parquet.

## Objetivo

Construir um pipeline de dados capaz de realizar a ingestão, transformação, validação e agregação dos dados históricos de preços de combustíveis, preparando-os para consumo analítico.

A implementação processa os dados de preços de combustíveis automotivos da ANP entre **2023 e 2025** e utiliza a API de Localidades do IBGE para identificação padronizada dos municípios por meio do código IBGE.

## Arquitetura

O projeto utiliza uma arquitetura de dados dividida em três camadas:

### Bronze

Armazena os arquivos obtidos da fonte original, preservando os dados brutos para rastreabilidade e reprocessamento.

Os arquivos da ANP são organizados por ano e semestre:

```text
data/bronze/anp/automotivos/
├── ano=2023/
│   ├── semestre=1/
│   └── semestre=2/
├── ano=2024/
└── ano=2025/
```

### Silver

Contém os dados tratados e padronizados.

Entre as principais transformações realizadas estão:

- remoção de linhas completamente vazias;
- remoção de duplicatas exatas;
- validação de colunas críticas;
- tratamento de colunas opcionais;
- normalização de CNPJ e CEP;
- conversão das datas;
- conversão e tipagem dos valores de venda;
- padronização das unidades de medida;
- padronização dos municípios para integração com o IBGE.

Os dados municipais do IBGE também são tratados e armazenados na camada Silver, permitindo utilizar o `codigo_ibge` como chave de integração.

### Gold

Contém dados agregados para consumo analítico.

A principal tabela produzida possui granularidade:

```text
mês + município + produto
```

São calculadas as seguintes métricas:

- preço médio;
- preço mediano;
- preço mínimo;
- preço máximo;
- desvio-padrão;
- quantidade de coletas.

Os arquivos são armazenados em formato Parquet e particionados por ano.

## Pipeline

O pipeline é orquestrado pelo **Apache Airflow**.

```text
baixar_anp ──> processar_anp ──┐
                               ├──> construir_gold
             processar_ibge ───┘
```

### Etapas

**`baixar_anp`**

Realiza o download automático dos arquivos históricos de preços de combustíveis disponibilizados pela ANP.

**`processar_anp`**

Carrega os arquivos da camada Bronze, realiza as transformações e validações e publica os dados tratados na camada Silver.

**`processar_ibge`**

Consulta a API de Localidades do IBGE e produz uma base padronizada de municípios utilizada para integração geográfica.

**`construir_gold`**

Integra os dados tratados da ANP com os municípios do IBGE, realiza as agregações mensais e publica os datasets analíticos da camada Gold.

## Estrutura do projeto

```text
insightfuel-data-platform/
├── dags/                       # DAGs do Apache Airflow
├── data/
│   ├── bronze/                 # Dados brutos
│   ├── silver/                 # Dados tratados
│   └── gold/                   # Dados analíticos
├── docker/                     # Configuração da imagem do Airflow
├── notebooks/                  # Profiling, desenvolvimento e análises
├── scripts/
│   ├── setup.sh                # Inicialização do ambiente
│   └── check.sh                # Testes e análise estática
├── src/
│   └── insightfuel_data_platform/
│       ├── aggregation/
│       ├── ingestion/
│       ├── pipelines/
│       ├── profiling/
│       ├── storage/
│       ├── transformation/
│       ├── utils/
│       └── validation/
├── tests/                      # Testes automatizados
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

## Tecnologias

O projeto utiliza:

- **Python 3.12**
- **Polars** para processamento dos dados;
- **Apache Airflow** para orquestração;
- **DuckDB** para consultas analíticas;
- **Apache Parquet** para armazenamento;
- **HTTPX** para consumo das fontes HTTP;
- **PyArrow** para interoperabilidade com Parquet;
- **Docker / Docker Compose** para execução do Airflow;
- **uv** para gerenciamento do ambiente e dependências;
- **pytest** para testes automatizados;
- **Ruff** para análise estática e qualidade do código;
- **Matplotlib** para visualizações analíticas.

## Como executar

### Pré-requisitos

É necessário possuir:

- Git;
- Docker;
- Docker Compose;
- uv.

### Clonar o projeto

```bash
git clone https://github.com/LeoRlucena/insightfuel-data-platform.git
cd insightfuel-data-platform
```

### Inicializar o ambiente

O projeto possui um script responsável por sincronizar o ambiente Python, construir a imagem do Airflow, realizar sua inicialização e subir os serviços:

```bash
./scripts/setup.sh
```

O script executa o equivalente a:

```bash
uv sync
docker compose build
docker compose run --rm airflow-init
docker compose up -d
```

Após a inicialização, o estado dos containers pode ser consultado com:

```bash
docker compose ps
```

## Execução do pipeline

Com o ambiente em execução, a DAG principal pode ser acionada pelo Apache Airflow.

A DAG executa o fluxo completo:

```text
Download ANP
    ↓
Bronze
    ↓
Transformação ANP ──── Integração IBGE
          \              /
           \            /
            ↓          ↓
             Gold
              ↓
        Análises
```

O pipeline foi desenvolvido para permitir reprocessamento sem gerar duplicações nos resultados.

Arquivos Bronze já existentes são reutilizados e as camadas derivadas são reconstruídas de forma determinística.

## Qualidade e testes

O projeto possui testes automatizados para as principais regras de transformação e agregação.

Entre os cenários testados estão:

- normalização dos campos da ANP;
- normalização das unidades de medida;
- detecção de ausência de colunas críticas;
- tratamento de colunas opcionais;
- remoção de duplicatas exatas;
- preservação de observações distintas;
- cálculo das métricas mensais;
- separação entre produtos;
- validação da camada Gold;
- detecção de violações de granularidade.

Todos os testes e verificações de qualidade podem ser executados com:

```bash
./scripts/check.sh
```

O script executa:

```bash
uv run pytest -v
uv run ruff check .
```

## Dados e processamento

A implementação utiliza os arquivos semestrais de preços de combustíveis automotivos da ANP referentes aos anos de **2023, 2024 e 2025**.

Durante o profiling foram identificadas situações relevantes para o tratamento dos dados, incluindo:

- linhas completamente vazias;
- registros exatamente duplicados;
- unidades de medida representadas de formas diferentes;
- campos com alta quantidade de valores nulos;
- combinações de CNPJ, produto e data que não constituem uma chave natural única.

Por esse motivo, a estratégia de deduplicação remove apenas registros completamente idênticos, preservando observações que compartilham CNPJ, produto e data, mas possuem informações diferentes.

## Análises

Os dados produzidos pelo pipeline podem ser consultados utilizando DuckDB.

O notebook de análise explora algumas das questões propostas pelo projeto, incluindo:

- diferenças regionais nos preços dos combustíveis;
- dispersão dos preços por região e produto;
- relação entre os preços de etanol e gasolina.

Entre 2023 e 2025, os dados analisados mostram diferenças persistentes nos níveis de preços entre as regiões brasileiras.

Na análise da relação Etanol/Gasolina, são comparados os preços médios dos dois produtos para o mesmo município e mês, permitindo avaliar a ocorrência da relação inferior ao limiar de referência de `0,70`.

## Reprodutibilidade e idempotência

O pipeline foi desenvolvido considerando reprocessamento e rastreabilidade.

A camada Bronze preserva os arquivos obtidos da fonte original, enquanto as camadas Silver e Gold podem ser reconstruídas a partir dos dados persistidos.

A execução repetida do pipeline sobre as mesmas entradas produz os mesmos dados derivados e não adiciona registros duplicados aos datasets existentes.

## Limitações

A implementação atual possui algumas limitações conhecidas:

- o período processado está definido entre 2023 e 2025;
- a detecção de alterações nos arquivos de origem não utiliza checksum;
- o download considera um arquivo existente na Bronze como já obtido;
- nem todas as fontes complementares previstas na arquitetura foram implementadas;
- análises que dependem de população, renda, PIB, distância das capitais ou inflação exigem integração das respectivas fontes externas;
- a análise de dispersão implementada utiliza o desvio-padrão das coletas dentro de cada município-mês e não representa diretamente volatilidade temporal;
- a dimensão de tamanho populacional dos municípios prevista na análise de volatilidade depende da integração dos dados populacionais do IBGE.

Essas integrações fazem parte da arquitetura proposta e podem ser incorporadas em evoluções posteriores da plataforma.