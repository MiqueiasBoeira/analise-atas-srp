"""
Coleta de dados do portal: uma URL de contratação → JSON com itens enriquecidos.
Requer Chrome aberto com --remote-debugging-port e login feito no portal.
"""
import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import config
from scraper.driver import conectar_driver, abrir_nova_aba
from scraper.extractors import (
    extrair_links_itens,
    extrair_links_internos,
    enriquecer_com_quantidades,
    gerar_nome_arquivo_final,
)


def coletar_contratacao(
    url: str,
    output_dir: Path | None = None,
    salvar_intermediarios: bool = False,
) -> tuple[list[dict], Path]:
    """
    Executa o pipeline de coleta para uma URL de itens da contratação.
    Retorna (lista de itens, path do JSON final salvo).
    """
    output_dir = output_dir or config.DATA_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    driver = conectar_driver()
    abrir_nova_aba(driver, url)
    nome_final = gerar_nome_arquivo_final(driver)
    output_path_final = output_dir / nome_final

    itens_raw = extrair_links_itens(
        driver,
        salvar_arquivo=salvar_intermediarios,
        output_path=(output_dir / "itens_contratacao_raw.json") if salvar_intermediarios else None,
    )
    itens_stage2 = extrair_links_internos(driver, itens_raw)
    itens_completos = enriquecer_com_quantidades(driver, itens_stage2, salvar_arquivo=False)

    with open(output_path_final, "w", encoding="utf-8") as f:
        json.dump(itens_completos, f, ensure_ascii=False, indent=2)

    return itens_completos, output_path_final


def run(url: str, output_dir: Path | None = None, salvar_intermediarios: bool = False) -> tuple[list[dict], Path]:
    """API de execução do pipeline de coleta."""
    return coletar_contratacao(url, output_dir=output_dir, salvar_intermediarios=salvar_intermediarios)
