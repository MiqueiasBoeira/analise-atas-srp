"""
CLI do projeto: coleta, resumo e análise de dados de contratos públicos.
Uso:
  python main.py analyze [--input-dir PASTA]   # análise a partir dos JSONs (não precisa do site)
  python main.py resumo [--input-dir PASTA]    # resumo por pregão
  python main.py collect --url URL [--output-dir PASTA]  # coleta no site (Chrome + login)
"""
import argparse
import sys
from pathlib import Path

import config
from pipeline.analise import run as run_analise
from pipeline.resumo import run as run_resumo
from pipeline.collect import run as run_collect


def cmd_analyze(args):
    input_dir = Path(args.input_dir) if args.input_dir else config.DATA_DIR
    df = run_analise(input_dir=input_dir)
    print(f"Análise concluída: {len(df)} itens. Saídas em {config.OUTPUT_ANALISE_EXCEL} e {config.OUTPUT_ANALISE_CSV}")


def cmd_resumo(args):
    input_dir = Path(args.input_dir) if args.input_dir else config.DATA_DIR
    df = run_resumo(input_dir=input_dir)
    print(f"Resumo concluído: {len(df)} pregões. Saídas em {config.OUTPUT_RESUMO_EXCEL} e {config.OUTPUT_RESUMO_CSV}")


def cmd_collect(args):
    if not args.url:
        print("Erro: --url é obrigatório para o comando collect.")
        sys.exit(1)
    output_dir = Path(args.output_dir) if args.output_dir else config.DATA_DIR
    itens, path = run_collect(args.url, output_dir=output_dir, salvar_intermediarios=args.intermediarios)
    print(f"Coleta concluída: {len(itens)} itens salvos em {path}")


def main():
    parser = argparse.ArgumentParser(description="Análise de contratos públicos (pregões)")
    sub = parser.add_subparsers(dest="comando", required=True)

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analisar JSONs (todos os itens, percentual empenhado)")
    p_analyze.add_argument("--input-dir", help="Pasta com os JSONs (default: config.DATA_DIR)")
    p_analyze.set_defaults(func=cmd_analyze)

    # resumo
    p_resumo = sub.add_parser("resumo", help="Gerar resumo por pregão (totais empenhado/homologado)")
    p_resumo.add_argument("--input-dir", help="Pasta com os JSONs")
    p_resumo.set_defaults(func=cmd_resumo)

    # collect
    p_collect = sub.add_parser("collect", help="Coletar dados do portal (Chrome aberto + login)")
    p_collect.add_argument("--url", help="URL da página de itens da contratação (ex: .../compras/486754/itens)")
    p_collect.add_argument("--output-dir", help="Pasta para salvar o JSON")
    p_collect.add_argument("--intermediarios", action="store_true", help="Salvar JSONs intermediários")
    p_collect.set_defaults(func=cmd_collect)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
