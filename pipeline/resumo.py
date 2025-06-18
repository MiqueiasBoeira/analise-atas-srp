"""
Gera resumo por pregão: totais empenhado e homologado a partir dos JSONs.
"""
import sys
from pathlib import Path

import pandas as pd

# Permitir rodar de qualquer lugar com o projeto na path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import config
from src.data_utils import (
    carregar_itens_arquivo,
    converter_quantidade,
    converter_valor_monetario,
    parse_nome_arquivo,
)


def processar_pasta(pasta_json: Path) -> pd.DataFrame:
    """Lê todos os JSON da pasta e retorna DataFrame com uma linha por pregão."""
    if not pasta_json.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta_json}")
    arquivos = sorted(p for p in pasta_json.iterdir() if p.suffix.lower() == ".json")
    if not arquivos:
        raise FileNotFoundError(f"Nenhum .json em {pasta_json}")
    linhas = []
    for json_path in arquivos:
        ug, nr_pregao = parse_nome_arquivo(json_path)
        itens = carregar_itens_arquivo(json_path)
        total_empenhado = 0.0
        total_homologado = 0.0
        for item in itens:
            qtd_emp = converter_quantidade(item.get("qnt_empenhada"))
            qtd_hom = converter_quantidade(item.get("qnt_homologada"))
            valor_unit = converter_valor_monetario(item.get("valor_unitario"))
            total_empenhado += qtd_emp * valor_unit
            total_homologado += qtd_hom * valor_unit
        linhas.append({
            "arquivo": json_path.name,
            "UG": ug,
            "nr_pregao": nr_pregao,
            "qtd_itens": len(itens),
            "total_homologado": round(total_homologado, 2),
            "total_empenhado": round(total_empenhado, 2),
        })
    df = pd.DataFrame(linhas)
    for col in ["qtd_itens", "total_empenhado", "total_homologado"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def exportar(df: pd.DataFrame, output_excel: Path, output_csv: Path) -> None:
    """Exporta para Excel e CSV."""
    output_excel.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_excel, index=False, sheet_name="resumo", engine="openpyxl")
    df.to_csv(output_csv, index=False, sep=";", decimal=",", encoding="utf-8-sig")


def run(input_dir: Path | None = None, output_excel: Path | None = None, output_csv: Path | None = None) -> pd.DataFrame:
    """Executa o pipeline de resumo. Usa config se paths não forem passados."""
    input_dir = input_dir or config.DATA_DIR
    output_excel = output_excel or config.OUTPUT_RESUMO_EXCEL
    output_csv = output_csv or config.OUTPUT_RESUMO_CSV
    df = processar_pasta(input_dir)
    exportar(df, output_excel, output_csv)
    return df
