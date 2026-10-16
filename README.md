# Parquet to Star Schema

> 🧪 Projeto de portfólio que transforma a camada Parquet de uma landing zone em um modelo estrela pronto para consultas de negócio.

## 🎯 O problema

Quando cada relatório lê arquivos de origem e aplica as próprias regras de junção, a empresa perde uma definição comum para os indicadores. Duas equipes podem responder de modo diferente à mesma pergunta sobre cobertura, categoria ou localidade.

Este projeto constrói uma camada analítica sobre o Parquet criado em [S3 Raw JSON to Parquet](https://github.com/brunomartins94/s3-raw-to-parquet). Em vez de inventar vendas que não existem na fonte, ele modela a cobertura de cervejarias por tipo, localização e data de snapshot.

## 🏗️ Modelo analítico

```text
              dim_date
                 │
dim_brewery ─ fact_brewery_snapshot ─ dim_brewery_type
                 │
            dim_location
```

**Grão da fato:** uma cervejaria observada em uma data de ingestão.

| Tabela | Responsabilidade |
| --- | --- |
| `dim_date` | Data do snapshot e chave de calendário. |
| `dim_brewery` | Identidade e nome da cervejaria. |
| `dim_brewery_type` | Categoria da cervejaria, como `micro` ou `brewpub`. |
| `dim_location` | Cidade, estado/província e país. |
| `fact_brewery_snapshot` | Contagem por cervejaria, status de fechamento e chaves das dimensões. |

## ✅ O que demonstra

- Modelagem dimensional com grão documentado.
- Chaves determinísticas para dimensões e fato.
- Leitura de Parquet no Amazon S3 e escrita de marts em Parquet.
- Consultas de negócio com DuckDB sobre fato e dimensões.
- Reexecução idempotente por data e tabela.
- Desenvolvimento e testes em Docker.

## 💼 Aplicabilidade

| Caminho comum | Problema | Modelo estrela |
| --- | --- | --- |
| Cada dashboard consulta o arquivo de origem | Regras e métricas divergem entre consumidores | Dimensões reutilizáveis e fato com grão definido |
| Uma tabela ampla para tudo | Junções e regras ficam implícitas | Entidades de negócio ficam explícitas |
| Métricas sem data de referência | Não há clareza sobre o momento observado | Snapshot permite comparar cargas ao longo do tempo |

Esse padrão se aplica a catálogo de fornecedores, cobertura de lojas, rastreamento logístico, eventos de produto e dados públicos: qualquer caso em que consumidores precisam de métricas consistentes sobre entidades, categorias, locais e períodos.

## 🐳 Execução com Docker

1. Crie o arquivo local de configuração:

   ```powershell
   copy .env.example .env
   ```

2. Informe no `.env` o bucket já utilizado nos dois projetos anteriores, as credenciais locais e os prefixos. Não versione esse arquivo.

3. Confirme as credenciais:

   ```powershell
   docker compose run --rm aws sts get-caller-identity
   ```

4. Execute os testes:

   ```powershell
   docker compose run --build --rm test
   ```

5. Crie o modelo para a data já presente na camada processed:

   ```powershell
   docker compose run --build --rm pipeline --ingested-date 2026-09-26
   ```

6. Consulte a fato com as dimensões:

   ```powershell
   docker compose run --build --rm analysis --ingested-date 2026-09-26
   ```

Na segunda execução da pipeline, as cinco tabelas Parquet já existentes são mantidas. O log deve retornar `written_models: 0`.

## ⚙️ Configuração

| Variável | Descrição | Padrão |
| --- | --- | --- |
| `SOURCE_BUCKET` | Bucket da camada processed | obrigatório |
| `TARGET_BUCKET` | Bucket que receberá os marts | obrigatório |
| `AWS_REGION` | Região AWS | `us-east-2` |
| `PROCESSED_PREFIX` | Prefixo do Parquet de origem | `processed/open_brewery_db` |
| `MART_PREFIX` | Prefixo do modelo analítico | `marts/brewery_directory` |

## 🔗 Continuidade do laboratório

- [Projeto anterior: S3 Raw JSON to Parquet](https://github.com/brunomartins94/s3-raw-to-parquet)
- Os rascunhos de LinkedIn e blog deste projeto ficarão em `../roadmap/parquet-to-star-schema/` ao final.
