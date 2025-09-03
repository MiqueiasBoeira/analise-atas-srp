"""
Configuração central do projeto.
Valores podem ser sobrescritos por variáveis de ambiente (.env).
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Diretório raiz do projeto (onde está config.py)
PROJECT_ROOT = Path(__file__).resolve().parent

# Chrome / Selenium
CHROME_DEBUG_ADDRESS = os.getenv("CHROME_DEBUG_ADDRESS", "127.0.0.1:9223")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "")

# Dados (default: samples para rodar analyze/resumo sem configurar)
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data" / "samples")))
DATA_JSON_DIR = PROJECT_ROOT / "data" / "json"
DATA_SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"

# Saídas da análise (podem ser sobrescritas por argumentos CLI)
OUTPUT_RESUMO_EXCEL = PROJECT_ROOT / "output" / "resumo_total_empenhado.xlsx"
OUTPUT_RESUMO_CSV = PROJECT_ROOT / "output" / "resumo_total_empenhado.csv"
OUTPUT_ANALISE_EXCEL = PROJECT_ROOT / "output" / "analise_pregoes_itens.xlsx"
OUTPUT_ANALISE_CSV = PROJECT_ROOT / "output" / "analise_pregoes_itens.csv"

# URL base do portal
BASE_URL = os.getenv("BASE_URL", "https://contratos.sistema.gov.br")
