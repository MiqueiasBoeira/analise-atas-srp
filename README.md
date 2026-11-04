# Análise de Contratos Públicos

Pipeline em Python para **coleta, processamento e análise** de dados de pregões no portal [contratos.sistema.gov.br](https://contratos.sistema.gov.br).

Ideal para demonstrar automação de dados, web scraping com Selenium, CLI e geração de relatórios — com um fluxo que roda **sem login** a partir de JSONs de exemplo.

> **Acesso ao portal:** a coleta (`collect`) só funciona para quem possui **cadastro no sistema Compras** (gov.br), pois exige login autenticado em [contratos.sistema.gov.br](https://contratos.sistema.gov.br).  
> Uma **nova versão sem necessidade de cadastro** está em desenvolvimento.

---

## Destaques

- **CLI** com três comandos: `collect`, `resumo` e `analyze`
- **Coleta** via Selenium em Chrome já autenticado (remote debugging)
- **Análise offline** com pandas → Excel e CSV
- Configuração centralizada (`config.py` / `.env`)
- Separação clara: scraper · pipeline · utilitários de dados

| Stack | Uso |
|-------|-----|
| Python 3.10+ | runtime |
| Selenium | coleta no portal |
| pandas + openpyxl | consolidação e exportação |
| argparse | interface de linha de comando |

---

## Demo rápida (sem acessar o site)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# ou, com uv:  uv venv && uv pip install -r requirements.txt

python main.py resumo --input-dir data/samples
python main.py analyze --input-dir data/samples
```

Saídas em `output/`:

- `resumo_total_empenhado.xlsx` / `.csv` — totais por pregão
- `analise_pregoes_itens.xlsx` / `.csv` — todos os itens + % empenhado

---

## Coleta no portal

**Pré-requisito:** cadastro ativo no Compras / gov.br. Sem isso, o login no portal não é possível e a coleta não roda. (Versão sem cadastro em desenvolvimento.)

1. Abra o Chrome com depuração remota e faça login no portal:

```bash
# Linux
google-chrome --remote-debugging-port=9223

# Windows
chrome.exe --remote-debugging-port=9223
```

2. Copie `.env.example` → `.env` e ajuste `CHROMEDRIVER_PATH` se necessário.

3. Rode a coleta com a URL da página de itens:

```bash
python main.py collect \
  --url "https://contratos.sistema.gov.br/compras/486754/itens" \
  --output-dir data/json
```

O JSON é salvo no padrão `UG - NUMERO_PREGAO.json`.

---

## Estrutura

```text
.
├── main.py                 # CLI
├── config.py               # paths, Chrome, saídas
├── requirements.txt
├── .env.example
├── data/
│   ├── samples/            # JSONs de exemplo (demo offline)
│   └── json/               # JSONs coletados (não versionados)
├── output/                 # Excel/CSV gerados
├── src/
│   └── data_utils.py       # conversão de valores, parse de arquivos
├── scraper/
│   ├── driver.py           # conexão Selenium
│   └── extractors.py       # XPaths e extração de páginas
└── pipeline/
    ├── collect.py          # coleta → JSON
    ├── resumo.py           # totais por pregão
    └── analise.py          # consolidado por item
```

```text
  [Portal] --collect--> [JSON] --resumo/analyze--> [Excel/CSV]
              Selenium              pandas
```

---

## Formato dos dados

Cada JSON é uma lista de itens:

```json
{
  "numero": "00001",
  "link": "https://contratos.sistema.gov.br/...",
  "novo_link": "https://contratos.sistema.gov.br/...",
  "qnt_homologada": "800",
  "qnt_empenhada": "30.00000",
  "valor_unitario": 11.5
}
```

Arquivo: `UG - NUMERO_PREGAO.json` (ex.: `160368 - 00001_2021.json`).

---

## Observações

- A **coleta** depende de cadastro no Compras; `resumo` e `analyze` funcionam offline com JSONs.
- Uma versão **sem cadastro** no portal está sendo desenvolvida.
- Os XPaths em `scraper/extractors.py` dependem do layout atual do portal.
- O comando `collect` abre uma aba nova no Chrome já logado, sem fechar sua sessão.
- Dados de exemplo em `data/samples` são suficientes para demonstrar o pipeline de análise.

## Licença

MIT — veja [LICENSE](LICENSE).
