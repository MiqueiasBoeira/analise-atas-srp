"""
Utilitários compartilhados para conversão de valores, parsing de nomes de arquivo
e carregamento de itens a partir de JSONs de pregão.
"""
import json
import re
from pathlib import Path


def converter_quantidade(valor):
    """
    Converte strings de quantidade para número.
    Aceita: "28", "1.00000", "1,055.00000" (vírgula = milhar, ponto = decimal).
    """
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip()
    if s == "":
        return 0.0
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def converter_valor_monetario(valor):
    """
    Converte strings de valor monetário para float.
    Aceita: "4,50", "1.234,56", 11.5 (já numérico).
    """
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip()
    if s == "":
        return 0.0
    # Formato BR: 1.234,56 → milhar com ponto, decimal com vírgula
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_nome_arquivo(json_path: Path) -> tuple[str, str]:
    """
    Extrai UG e número do pregão a partir do nome do arquivo.
    Ex.: '160368 - 00001_2021.json' -> ('160368', '00001_2021')
    """
    nome = json_path.name
    padrao = r"(\d+)\s*-\s*(.+)\.json$"
    m = re.match(padrao, nome)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", json_path.stem.strip()


def carregar_itens_arquivo(json_path: Path) -> list[dict]:
    """
    Lê um arquivo JSON e retorna a lista de itens.
    Suporta: lista direta [ {...} ] ou dict com chave 'dados' ou 'itens'.
    """
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
