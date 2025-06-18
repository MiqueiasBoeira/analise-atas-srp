"""
Análise consolidada: todos os itens de todos os pregões com percentual empenhado.
"""
import sys
from pathlib import Path

import pandas as pd

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


def processar_todos_json(input_dir: Path) -> pd.DataFrame:
    """Retorna um DataFrame com uma linha por item (todos os pregões)."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {input_dir}")
    json_files = sorted(p for p in input_dir.iterdir() if p.suffix.lower() == ".json")
    if not json_files:
        raise FileNotFoundError(f"Nenhum .json em {input_dir}")
    linhas = []
    for json_path in json_files:
        ug, nr_pregao = parse_nome_arquivo(json_path)
        itens = carregar_itens_arquivo(json_path)
        for item in itens:
            qnt_hom = converter_quantidade(item.get("qnt_homologada"))
            qnt_emp = converter_quantidade(item.get("qnt_empenhada"))
            valor_unit = converter_valor_monetario(item.get("valor_unitario"))
            percentual = round((qnt_emp / qnt_hom) * 100, 2) if qnt_hom > 0 else 0
            valor_empenhado = round(qnt_emp * valor_unit, 2) if valor_unit is not None else None
            linhas.append({
                "UG": ug,
                "nr_pregao": nr_pregao,
                "numero_item": item.get("numero"),
                "qnt_homologada": qnt_hom,
                "qnt_empenhada": qnt_emp,
                "percentual_empenhado": percentual,
                "valor_unitario": valor_unit,
                "valor_empenhado": valor_empenhado,
                "link": item.get("link"),
                "novo_link": item.get("novo_link"),
            })
    df = pd.DataFrame(linhas)
    if df.empty:
        raise ValueError("Nenhum item carregado.")
    # Média global de percentual empenhado por pregão
    grupo = df.groupby(["UG", "nr_pregao"], dropna=False)["percentual_empenhado"].mean().reset_index()
    grupo = grupo.rename(columns={"percentual_empenhado": "media_global_empenhado"})
    df = df.merge(grupo, on=["UG", "nr_pregao"], how="left")
    for col in ["qnt_homologada", "qnt_empenhada", "percentual_empenhado", "valor_unitario", "valor_empenhado", "media_global_empenhado"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def exportar_resultados(df: pd.DataFrame, output_excel: Path, output_csv: Path) -> None:
    """Exporta para Excel e CSV."""
    output_excel.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="todos_itens")
    df.to_csv(output_csv, index=False, sep=";", encoding="utf-8-sig")


def run(input_dir: Path | None = None, output_excel: Path | None = None, output_csv: Path | None = None) -> pd.DataFrame:
    """Executa o pipeline de análise."""
    input_dir = input_dir or config.DATA_DIR
    output_excel = output_excel or config.OUTPUT_ANALISE_EXCEL
    output_csv = output_csv or config.OUTPUT_ANALISE_CSV
    df = processar_todos_json(input_dir)
    exportar_resultados(df, output_excel, output_csv)
    return df
