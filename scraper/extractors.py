"""
Extração de dados do portal de contratos: tabela de itens, links internos e detalhes.
XPaths referem-se ao layout atual do site contratos.sistema.gov.br.
"""
import json
import re
import time
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scraper.driver import esperar


# XPaths do portal (podem quebrar se o site mudar o layout)
XPATH_SELECT_TODOS = "/html/body/div[2]/main/div/div/div/div/div[2]/div/div/div[2]/div/div[3]/div[1]/div/label/select"
XPATH_OPTION_TODOS = "//option[@value='-1']"
XPATH_TABLE_ITENS = "/html/body/div[2]/main/div/div/div/div/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr"
XPATH_CRUD_TABLE_ROW = '//*[@id="crudTable"]/tbody/tr'
XPATH_ITEM_NUMERO = '//*[@id="crudTable"]/tbody/tr[{i}]/td[1]/span'
XPATH_ITEM_LINK = "/html/body/div[2]/main/div/div/div/div/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr[{i}]/td[5]/a"
XPATH_PAGINA_ITEM_TABLE = "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table"
XPATH_NOVO_LINK = "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[9]/td[2]/span/table/tbody/tr/td[6]/a"
XPATH_QNT_HOMOLOGADA = "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[3]/td[2]/span"
XPATH_QNT_EMPENHADA = "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[8]/td[2]/span"
XPATH_VALOR_UNITARIO = "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[6]/td[2]/span"
XPATH_HEADER_TITULO = "/html/body/header/div/div[2]/div/div[2]/div[1]"


def selecionar_todos(driver) -> None:
    """Seleciona a opção 'Todos' no seletor de itens e aguarda a tabela recarregar."""
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, XPATH_SELECT_TODOS))
    )
    select_element.click()
    time.sleep(0.5)
    option_todos = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, XPATH_OPTION_TODOS))
    )
    option_todos.click()
    esperar(driver, XPATH_CRUD_TABLE_ROW)


def extrair_links_itens(driver, salvar_arquivo: bool = False, output_path: Path | str | None = None) -> list[dict]:
    """Extrai da tabela da contratação a lista de itens: numero e link. Retorna [{"numero": "...", "link": "..."}]."""
    selecionar_todos(driver)
    esperar(driver, XPATH_CRUD_TABLE_ROW)
    rows = driver.find_elements(By.XPATH, XPATH_TABLE_ITENS)
    itens = []
    for i in range(1, len(rows) + 1):
        numero = None
        try:
            elem = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, XPATH_ITEM_NUMERO.format(i=i)))
            )
            numero = elem.text.strip()
            tentativas = 0
            while numero == "" and tentativas < 10:
                time.sleep(0.5)
                numero = elem.text.strip()
                tentativas += 1
        except Exception:
            pass
        link = None
        try:
            link_elem = driver.find_element(By.XPATH, XPATH_ITEM_LINK.format(i=i))
            link = link_elem.get_attribute("href")
        except Exception:
            pass
        if numero and link:
            itens.append({"numero": numero, "link": link})
    if salvar_arquivo and output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(itens, f, ensure_ascii=False, indent=2)
    return itens


def extrair_links_internos(driver, itens: list[dict]) -> list[dict]:
    """Para cada item, acessa a página do item e extrai novo_link (link compra-item-fornecedor)."""
    resultado = [dict(item) for item in itens]
    for item in resultado:
        driver.get(item["link"])
        esperar(driver, XPATH_PAGINA_ITEM_TABLE)
        try:
            el = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, XPATH_NOVO_LINK))
            )
            item["novo_link"] = el.get_attribute("href")
        except Exception:
            item["novo_link"] = None
    return resultado


def enriquecer_com_quantidades(driver, itens: list[dict]) -> list[dict]:
    """Para cada item com novo_link, acessa a página e extrai qnt_homologada, qnt_empenhada, valor_unitario."""
    resultado = [dict(item) for item in itens]
    for item in resultado:
        if not item.get("novo_link"):
            continue
        driver.get(item["novo_link"])
        esperar(driver, XPATH_PAGINA_ITEM_TABLE)
        for key, xpath in [
            ("qnt_homologada", XPATH_QNT_HOMOLOGADA),
            ("qnt_empenhada", XPATH_QNT_EMPENHADA),
        ]:
            try:
                el = esperar(driver, xpath)
                text = el.text.strip()
                while text == "":
                    time.sleep(0.5)
                    text = el.text.strip()
                item[key] = text
            except Exception:
                item[key] = None
        try:
            el = esperar(driver, XPATH_VALOR_UNITARIO)
            raw = el.text.strip()
            item["valor_unitario"] = float(raw.replace(".", "").replace(",", "."))
        except Exception:
            item["valor_unitario"] = None
    return resultado


def gerar_nome_arquivo_final(driver) -> str:
    """Lê o header da página e gera nome no formato 'UG - NUMERO_PREGAO.json'."""
    header = esperar(driver, XPATH_HEADER_TITULO)
    texto = header.text.strip()
    if ":" in texto:
        _, resto = texto.split(":", 1)
    else:
        resto = texto
    resto = resto.strip()
    partes = resto.split("-", 1)
    ug = partes[0].strip() if partes else ""
    if "|" in resto:
        num_parte = resto.split("|")[-1].strip()
    else:
        num_parte = resto.split()[-1].strip() if resto else ""
    numero_pregao = num_parte.replace("/", "_")
    nome_base = f"{ug} - {numero_pregao}"
    nome_limpo = re.sub(r'[\\/:*?"<>|]', "_", nome_base)
    return nome_limpo + ".json"
