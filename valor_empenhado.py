import json
import re
from pathlib import Path

import pandas as pd


# ============================
# CONFIGURAÇÕES
# ============================

# PASTA COM OS JSONS
PASTA_JSON = Path(r"C:/Users/PC/PycharmProjects/Script análise gcalc/Análise 27NOV25/")

# ARQUIVOS DE SAÍDA
OUTPUT_EXCEL = Path("resumo_total_empenhado.xlsx")
OUTPUT_CSV = Path("resumo_total_empenhado.csv")


# ============================
# FUNÇÕES AUXILIARES
# ============================

def converter_qtd(valor):
    """
    Converte quantidades no formato dos JSONs:

      - "545.99360"        -> 545.9936
      - "1,543.00000"      -> 1543.0
      - "100.00000"        -> 100.0
      - "0.00000"          -> 0.0

    Regra: remove APENAS vírgulas (milhar), mantém o ponto como decimal.
    """
    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    if isinstance(valor, str):
        s = valor.strip()
        if s == "":
            return 0.0
        s = s.replace(",", "")  # remove milhar
        try:
            return float(s)
        except ValueError:
            return 0.0

    return 0.0


def converter_valor(valor):
    """
    Converte valores monetários no formato dos JSONs:

      - "1748.48"     -> 1748.48
      - "4.5"         -> 4.5
      - "1,234.56"    -> 1234.56

    Regra: remove vírgulas, mantém ponto.
    """
    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    if isinstance(valor, str):
        s = valor.strip()
        if s == "":
            return 0.0
        s = s.replace(",", "")  # remove milhar
        try:
            return float(s)
        except ValueError:
            return 0.0

    return 0.0


def parse_nome_arquivo(json_path: Path):
    """
    Extrai UG e número do pregão a partir do nome do arquivo:

        '160368 - 00001_2021.json'
        '160368 - Pregão  000072023_atualizado.json'
    """
    nome = json_path.name
    padrao = r"(\d+)\s*-\s*(.+)\.json$"
    m = re.match(padrao, nome)
    if m:
        ug = m.group(1).strip()
        nr_pregao = m.group(2).strip()
    else:
        ug = ""
        nr_pregao = json_path.stem.strip()

    return ug, nr_pregao


def carregar_itens_arquivo(json_path: Path):
    """Lê o JSON e retorna a lista de itens."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("dados"), list):
            return data["dados"]
        if isinstance(data.get("itens"), list):
            return data["itens"]
    return []


# ============================
# PIPELINE PRINCIPAL
# ============================

def processar_pasta(pasta_json: Path) -> pd.DataFrame:
    if not pasta_json.exists():
        raise FileNotFoundError(f"Pasta '{pasta_json}' não encontrada.")

    arquivos = sorted([p for p in pasta_json.iterdir() if p.suffix.lower() == ".json"])

    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo .json encontrado em '{pasta_json}'.")

    linhas = []

    for json_path in arquivos:
        ug, nr_pregao = parse_nome_arquivo(json_path)
        itens = carregar_itens_arquivo(json_path)

        total_empenhado = 0.0
        total_homologado = 0.0
        qtd_itens = 0

        for item in itens:
            qnt_empenhada = converter_qtd(item.get("qnt_empenhada"))
            qnt_homologada = converter_qtd(item.get("qnt_homologada"))
            valor_unitario = converter_valor(item.get("valor_unitario"))

            # valor empenhado do item
            valor_empenhado_item = qnt_empenhada * valor_unitario

            # valor homologado do item  (NOVO)
            valor_homologado_item = qnt_homologada * valor_unitario

            total_empenhado += valor_empenhado_item
            total_homologado += valor_homologado_item
            qtd_itens += 1

        linha = {
            "arquivo": json_path.name,
            "UG": ug,
            "nr_pregao": nr_pregao,
            "qtd_itens": qtd_itens,
            "total_homologado": round(total_homologado, 2),
            "total_empenhado": round(total_empenhado, 2),
        }
        linhas.append(linha)

    df = pd.DataFrame(linhas)

    # Garante tipos numéricos
    df["qtd_itens"] = pd.to_numeric(df["qtd_itens"], errors="coerce")
    df["total_empenhado"] = pd.to_numeric(df["total_empenhado"], errors="coerce")
    df["total_homologado"] = pd.to_numeric(df["total_homologado"], errors="coerce")

    return df


def exportar(df: pd.DataFrame, output_excel: Path, output_csv: Path):
    df.to_excel(output_excel, index=False, sheet_name="resumo", engine="openpyxl")

    df.to_csv(
        output_csv,
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )


# ============================
# EXECUÇÃO
# ============================

def main():
    print(f"Lendo JSONs da pasta: {PASTA_JSON.resolve()}")
    df = processar_pasta(PASTA_JSON)

    print(df.head())
    print(f"\nTotal de arquivos processados: {len(df)}")

    print(f"\nSalvando Excel em: {OUTPUT_EXCEL.resolve()}")
    print(f"Salvando CSV em:   {OUTPUT_CSV.resolve()}")

    exportar(df, OUTPUT_EXCEL, OUTPUT_CSV)

    print("\nConcluído.")


if __name__ == "__main__":
    main()
