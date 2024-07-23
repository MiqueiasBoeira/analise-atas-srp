import json
import time
import re
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# ============================
# CONFIGURAÇÕES DO USUÁRIO
# ============================

# Coloque aqui a pasta onde estão TODOS os JSON antigos
PASTA_JSON = Path(r"C:/Users/PC/PycharmProjects/Script análise gcalc/Análise 27NOV25/analises anteriores")

# Caminho do ChromeDriver
CHROMEDRIVER_PATH = r"C:/Users/PC/Documents/chromedriver-win64/chromedriver.exe"

# Porta do Chrome já aberto com depuração (você abre com --remote-debugging-port=9222)
CHROME_DEBUG_ADDRESS = "localhost:9223"

# XPaths na página de compra-item-fornecedor
XPATH_TABELA_BASE = "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table"
XPATH_VALOR_UNITARIO = "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[6]/td[2]/span"



# ============================
# FUNÇÕES AUXILIARES
# ============================

def esperar(driver, xpath, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )


def converter_numero(valor):
    """Converte strings '1.234,56' → 1234.56"""
    if valor is None:
        return 0
    if isinstance(valor, (int, float)):
        return valor
    if isinstance(valor, str):
        s = valor.strip()
        if s == "":
            return 0
        s = s.replace(".", "").replace(",", ".")
        try:
            num = float(s)
            if num.is_integer():
                return int(num)
            return num
        except:
            return 0
    return 0


def conectar_driver():
    """Conecta ao Chrome já aberto via porta de depuração."""
    chrome_options = Options()
    chrome_options.debugger_address = CHROME_DEBUG_ADDRESS

    driver = webdriver.Chrome(
        service=Service(CHROMEDRIVER_PATH),
        options=chrome_options
    )

    print("✔ Conectado ao Chrome já aberto.")
    return driver



# ============================
# PROCESSAMENTO DE UM JSON
# ============================

def atualizar_arquivo_json(json_path: Path, driver):
    """Atualiza um arquivo JSON adicionando valor_unitario e valor_empenhado."""

    with open(json_path, "r", encoding="utf-8") as f:
        itens = json.load(f)

    if not isinstance(itens, list):
        print(f"⚠ Arquivo ignorado (não é lista): {json_path.name}")
        return

    print(f"\n===============================")
    print(f"Processando arquivo: {json_path.name}")
    print(f"Itens encontrados: {len(itens)}")
    print("===============================\n")

    for idx, item in enumerate(itens, start=1):
        numero = item.get("numero")
        novo_link = item.get("novo_link") or item.get("link")

        if not novo_link:
            print(f"[{idx}] Item {numero}: ⚠ sem link, pulando.")
            item["valor_unitario"] = None
            item["valor_empenhado"] = None
            continue

        print(f"[{idx}] Item {numero}: acessando {novo_link}")

        try:
            driver.get(novo_link)

            # aguarda carregar a tabela principal
            esperar(driver, XPATH_TABELA_BASE, timeout=20)

            # captura valor unitário
            elem = esperar(driver, XPATH_VALOR_UNITARIO, timeout=10)
            valor_raw = elem.text.strip()
            valor_unitario = converter_numero(valor_raw)

            item["valor_unitario"] = valor_unitario

            # calcular valor empenhado
            qnt_empenhada = converter_numero(item.get("qnt_empenhada"))
            item["valor_empenhado"] = round(qnt_empenhada * valor_unitario, 2)

            print(f"    ✔ valor_unitario='{valor_raw}' → {valor_unitario} | valor_empenhado={item['valor_empenhado']}")

        except Exception as e:
            print(f"    ❌ Erro ao processar item {numero}: {e}")
            item["valor_unitario"] = None
            item["valor_empenhado"] = None

        time.sleep(0.2)

    # gerar arquivo novo com sufixo _atualizado.json
    output_path = json_path.with_name(json_path.stem + "_atualizado.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False, indent=4)

    print(f"📂 Arquivo atualizado salvo: {output_path.name}")


# ============================
# EXECUTAR EM LOTE
# ============================

def main():
    if not PASTA_JSON.exists():
        print(f"❌ A pasta '{PASTA_JSON}' não existe.")
        return

    arquivos = sorted([p for p in PASTA_JSON.iterdir() if p.suffix.lower() == ".json"])

    if not arquivos:
        print(f"❌ Nenhum arquivo .json encontrado em: {PASTA_JSON}")
        return

    driver = conectar_driver()

    for json_path in arquivos:
        try:
            atualizar_arquivo_json(json_path, driver)
        except Exception as e:
            print(f"❌ Erro inesperado ao processar {json_path.name}: {e}")

    print("\n✔ Finalizado. Todos os arquivos foram processados.")


if __name__ == "__main__":
    main()
