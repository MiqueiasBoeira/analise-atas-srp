import os
import json
import re
from pathlib import Path

import pandas as pd


# ============================
# CONFIGURAÇÕES
# ============================

# Pasta onde estão TODOS os JSON finais (um por contratação/pregão)
# ex.: "C:/Users/PC/Documents/json_pregoes"
INPUT_DIR = Path("C:/Users/PC/PycharmProjects/Script análise gcalc/Análise 27NOV25/")

# Arquivos de saída
OUTPUT_EXCEL = Path("analise_pregoes_itens.xlsx")
OUTPUT_CSV = Path("analise_pregoes_itens.csv")


# ============================
# FUNÇÕES AUXILIARES
# ============================

def converter_quantidade(valor):
    """
    Converte strings de QUANTIDADE para número, tratando o ponto como decimal.

    Exemplos:
        "28"       -> 28
        "1.00000"  -> 1
        "3.000"    -> 3
        "" / None  -> 0

    Aqui NÃO removemos '.', apenas trocamos vírgula por ponto,
    pois as quantidades vieram do sistema como "1.00000" = 1.00000 (não mil).
    """
    if valor is None:
        return 0

    if isinstance(valor, (int, float)):
        return valor

    s = str(valor).strip()
    if s == "":
        return 0

    # Para quantidade: vírgula como ponto, ponto permanece como decimal
    s = s.replace(",", ".")
    try:
        num = float(s)
        return int(num) if num.is_integer() else num
    except ValueError:
        return 0


def converter_moeda(valor):
    """
    Converte strings de VALOR MONETÁRIO em número (float),
    aceitando formatos:
        "4,50"
        "1.234,56"
        "1234.56"

    Aqui SIM removemos '.' como separador de milhar e usamos vírgula como decimal.
    """
    if valor is None:
        return 0

    if isinstance(valor, (int, float)):
        return valor

    s = str(valor).strip()
    if s == "":
        return 0

    # remove separador de milhar ".", troca vírgula por ponto
    s = s.replace(".", "").replace(",", ".")
    try:
        num = float(s)
        return int(num) if num.is_integer() else num
    except ValueError:
        return 0


def parse_nome_arquivo(json_path: Path):
    """
    A partir de um nome de arquivo no formato:
        '160377 - 00005_2022.json'
    extrai:
        UG = '160377'
        nr_pregao = '00005_2022'

    Se não bater o padrão, retorna algo razoável.
    """
    nome = json_path.name  # ex.: "160377 - 00005_2022.json"
    padrao = r"(\d+)\s*-\s*(.+)\.json$"
    m = re.match(padrao, nome)
    if m:
        ug = m.group(1).strip()
        nr_pregao = m.group(2).strip()
    else:
        # fallback: tudo antes da extensão
        ug = ""
        nr_pregao = json_path.stem.strip()

    return ug, nr_pregao


def carregar_itens_arquivo(json_path: Path):
    """
    Lê um arquivo JSON e retorna a lista de itens.
    Suporta dois formatos:
      1) Lista direta de itens: [ {...}, {...}, ... ]
      2) Dict contendo uma lista em 'dados': { "dados": [ {...}, ... ] }
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # tentar achar uma chave que contenha a lista de itens
        if "dados" in data and isinstance(data["dados"], list):
            return data["dados"]
        elif "itens" in data and isinstance(data["itens"], list):
            return data["itens"]
        else:
            # última tentativa: se o dict não está no formato esperado
            # vamos considerar que não há itens
            return []
    else:
        return []


# ============================
# PIPELINE PRINCIPAL
# ============================

def processar_todos_json(input_dir: Path) -> pd.DataFrame:
    """
    Lê todos os arquivos .json da pasta input_dir, processa e retorna
    um DataFrame consolidado com todos os itens de todos os pregões.
    """

    if not input_dir.exists():
        raise FileNotFoundError(f"Pasta '{input_dir}' não encontrada.")

    json_files = sorted([p for p in input_dir.iterdir() if p.suffix.lower() == ".json"])

    if not json_files:
        raise FileNotFoundError(f"Nenhum arquivo .json encontrado em '{input_dir}'.")

    linhas = []

    for json_path in json_files:
        ug, nr_pregao = parse_nome_arquivo(json_path)
        itens = carregar_itens_arquivo(json_path)

        for item in itens:
            numero_item = item.get("numero")

            # Quantidades: tratar ponto como decimal, não como milhar
            qnt_homologada = converter_quantidade(item.get("qnt_homologada"))
            qnt_empenhada = converter_quantidade(item.get("qnt_empenhada"))

            # Valores monetários: remover separador de milhar, etc.
            valor_unitario = converter_moeda(item.get("valor_unitario"))

            # percentual empenhado (%)
            if qnt_homologada > 0:
                percentual_empenhado = round((qnt_empenhada / qnt_homologada) * 100, 2)
            else:
                percentual_empenhado = 0

            # valor total empenhado = qnt_empenhada x valor_unitario
            valor_empenhado = None
            if valor_unitario is not None:
                valor_empenhado = round(qnt_empenhada * valor_unitario, 2)

            linha = {
                "UG": ug,
                "nr_pregao": nr_pregao,
                "numero_item": numero_item,
                "qnt_homologada": qnt_homologada,
                "qnt_empenhada": qnt_empenhada,
                "percentual_empenhado": percentual_empenhado,
                "valor_unitario": valor_unitario,
                "valor_empenhado": valor_empenhado,
                "link": item.get("link"),
                "novo_link": item.get("novo_link"),
            }

            linhas.append(linha)

    df = pd.DataFrame(linhas)

    if df.empty:
        raise ValueError("Nenhum item foi carregado a partir dos JSON.")

    # Calcular média global de percentual empenhado por pregão (UG + nr_pregao)
    grupo = (
        df.groupby(["UG", "nr_pregao"], dropna=False)["percentual_empenhado"]
        .mean()
        .reset_index()
    )
    grupo = grupo.rename(columns={"percentual_empenhado": "media_global_empenhado"})

    # Mesclar de volta no df
    df = df.merge(grupo, on=["UG", "nr_pregao"], how="left")

    return df


def exportar_resultados(df: pd.DataFrame, output_excel: Path, output_csv: Path):
    """
    Exporta o DataFrame consolidado para Excel (aba única) e CSV.
    """

    # Excel
    output_excel.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="todos_itens")

    # CSV (padrão ; para facilitar abertura no Excel em PT-BR)
    df.to_csv(output_csv, index=False, sep=";", encoding="utf-8-sig")


# ============================
# EXECUÇÃO
# ============================

def main():
    print(f"Lendo JSONs da pasta: {INPUT_DIR.resolve()}")
    df = processar_todos_json(INPUT_DIR)

    print(f"Total de linhas (itens) carregadas: {len(df)}")
    print("Exemplo de colunas:", list(df.columns))

    print(f"Exportando para Excel: {OUTPUT_EXCEL.resolve()}")
    print(f"Exportando para CSV:   {OUTPUT_CSV.resolve()}")


    cols_numericas = [
    "qnt_homologada",
    "qnt_empenhada",
    "percentual_empenhado",
    "valor_unitario",
    "valor_empenhado",
    "media_global_empenhado",
]

    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    exportar_resultados(df, OUTPUT_EXCEL, OUTPUT_CSV)

    print("Concluído.")


if __name__ == "__main__":
    main()
