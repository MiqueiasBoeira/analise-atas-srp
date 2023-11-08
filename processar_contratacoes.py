# ============================
# IMPORTAÇÕES
# ============================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import json
import re

# ============================
# CONECTAR AO CHROME EXISTENTE (PORTA 9223)
# ============================

def conectar_driver():
    """
    Conecta ao Chrome já aberto com --remote-debugging-port=9223.
    Você deve abrir manualmente o Chrome com essa porta E fazer login no sistema
    antes de rodar o script.
    """
    chrome_options = Options()
    chrome_options.debugger_address = "127.0.0.1:9223"
    service = Service(r"C:\Users\PC\Documents\chromedriver-win64\chromedriver.exe")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("Conectado ao Chrome na porta 9223!")
    return driver


# ============================
# GARANTIR QUE O SELENIUM USE UMA ABA NOVA (ISOLADA)
# ============================

def abrir_nova_aba(driver, url):
    """
    Abre uma nova aba EXCLUSIVA para o Selenium.
    Não interfere na aba que você está usando para navegar manualmente.
    """
    driver.execute_script("window.open('');")  # cria nova aba
    driver.switch_to.window(driver.window_handles[-1])  # foca na aba nova
    driver.get(url)  # navega na aba nova
    print(f"Aba criada e carregada → {url}")

# ============================
# SELECIONAR "TODOS" NO SELECT
# ============================

def esperar(driver, xpath, timeout=20):
    """
    Aguarda até que o elemento desejado exista no DOM.
    Não exige visibilidade.
    Substitui completamente time.sleep().
    """
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )


def selecionar_todos(driver):
    """
    Seleciona a opção 'Todos' (value = -1) no seletor de quantidade de itens
    e aguarda a tabela recarregar.
    """
    try:
        # Aguarda o <select> aparecer
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                "/html/body/div[2]/main/div/div/div/div/div[2]/div/div/div[2]/div/div[3]/div[1]/div/label/select"
            ))
        )

        # Clica no select para abrir as opções
        select_element.click()
        time.sleep(0.5)  # esse pequeno sleep é para estabilidade do clique, não de carregamento

        # Localiza a opção "Todos" pelo value = -1
        option_todos = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((
                By.XPATH,
                "/html/body/div[2]/main/div/div/div/div/div[2]/div/div/div[2]/div/div[3]/div[1]/div/label/select/option[@value='-1']"
            ))
        )
        option_todos.click()

        print("✔ Opção 'Todos' selecionada com sucesso.")

        # ANTES:
        # time.sleep(3)  # esperar a tabela recarregar com todos os itens

        # DEPOIS: espera até existir pelo menos uma linha na tabela (crudTable)
        esperar(driver, '//*[@id="crudTable"]/tbody/tr')

    except Exception as e:
        print(f"❌ Erro ao selecionar 'Todos': {e}")


# ============================
# EXTRAÇÃO DE ITENS DA TABELA
# ============================

def extrair_links_itens(
    driver,
    salvar_arquivo: bool = True,
    nome_arquivo: str = "itens_contratacao_raw.json"
):
    """
    Parte 1:
    Extrai os itens da tabela da contratação atual e retorna:
        [{"numero": "...", "link": "..."}]

    Também salva o JSON se salvar_arquivo=True.
    """

    # Sempre selecionar "Todos" antes de extrair
    selecionar_todos(driver)

    # ANTES:
    # time.sleep(5)  # tempo extra para garantir que a tabela esteja estável

    # DEPOIS: aguarda a presença das linhas na tabela principal
    esperar(driver, '//*[@id="crudTable"]/tbody/tr')

    itens = []

    # Localiza as linhas da tabela
    rows = driver.find_elements(
        By.XPATH,
        "/html/body/div[2]/main/div/div/div/div/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr"
    )

    print(f"✅ Número de linhas na página atual: {len(rows)}")

    # Itera nas linhas por índice
    for i in range(1, len(rows) + 1):

        # ---------------------------
        # CAPTURAR NÚMERO DO ITEM
        # ---------------------------
        try:
            numero_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="crudTable"]/tbody/tr[{i}]/td[1]/span')
                )
            )

            numero = numero_element.text.strip()

            tentativas = 0
            while numero == "" and tentativas < 10:
                time.sleep(0.5)  # aqui faz sentido: esperando o texto daquele span em específico
                numero = numero_element.text.strip()
                tentativas += 1

            print(f"   ✔ Número linha {i}: {numero}")

        except Exception as e:
            print(f"   ❌ Falha capturando número na linha {i}: {e}")
            numero = None

        # ---------------------------
        # CAPTURAR LINK DO BOTÃO
        # ---------------------------
        try:
            link_element = driver.find_element(
                By.XPATH,
                f"/html/body/div[2]/main/div/div/div/div/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr[{i}]/td[5]/a"
            )
            link = link_element.get_attribute("href")

        except Exception as e:
            print(f"   ❌ Falha capturando link linha {i}: {e}")
            link = None

        # ---------------------------
        # ADICIONAR À LISTA
        # ---------------------------
        if numero and link:
            itens.append({"numero": numero, "link": link})
            print(f"   → Linha {i}: Número {numero} → {link}")

    # ---------------------------
    # SALVAR JSON (PARTE 1)
    # ---------------------------
    if salvar_arquivo:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(itens, f, ensure_ascii=False, indent=4)

        print(f"\n📂 JSON (Parte 1) salvo como '{nome_arquivo}'")
        print(f"   Total: {len(itens)} itens extraídos.")

    return itens

# ============================
# PARTE 2A: EXTRAIR novo_link DE CADA ITEM
# ============================

def extrair_links_internos(
    driver,
    itens,
    salvar_arquivo: bool = True,
    nome_arquivo: str = "itens_contratacao_stage2.json"
):
    """
    Parte 2A:
    Para cada item encontrado na tabela da contratação,
    acessa a página do item e extrai o segundo link (novo_link).

    Estrutura retornada:
    [
        {
            "numero": "...",
            "link": "...",
            "novo_link": "..."
        },
        ...
    ]
    """

    itens_atualizados = itens.copy()

    for item in itens_atualizados:
        item_link = item["link"]
        print(f"\n🔎 Acessando {item_link}...")

        driver.get(item_link)

        # ANTES:
        # time.sleep(3)  # delay para carregamento da página interna

        # DEPOIS: aguarda a tabela interna onde está o novo_link
        esperar(driver, "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table")

        # Tenta capturar o novo link do item
        try:
            novo_link_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[9]/td[2]/span/table/tbody/tr/td[6]/a"
                ))
            )

            novo_link = novo_link_element.get_attribute("href")
            item["novo_link"] = novo_link
            print(f"   ✔ novo_link capturado: {novo_link}")

        except Exception as e:
            item["novo_link"] = None
            print(f"   ❌ Não foi possível capturar novo_link ({e})")

    # ---------------------------
    # SALVAR JSON (PARTE 2A)
    # ---------------------------
    if salvar_arquivo:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(itens_atualizados, f, ensure_ascii=False, indent=4)

        print(f"\n📂 JSON (Parte 2A) salvo como '{nome_arquivo}'")

    return itens_atualizados

def enriquecer_com_quantidades(
    driver,
    itens,
    salvar_arquivo: bool = True,
    nome_arquivo: str | None = None,
):
    """
    Parte 2B:
    Para cada item que já tem 'novo_link', acessa a página correspondente
    e captura:
        - qnt_homologada   (tr[3]/td[2]/span)
        - qnt_empenhada    (tr[8]/td[2]/span)
        - valor_unitario   (tr[6]/td[2]/span)  <-- NOVO
    """

    itens_atualizados = itens.copy()

    for item in itens_atualizados:
        if "novo_link" not in item or not item["novo_link"]:
            print(f"⚠️ Pulando item {item.get('numero', '?')} - novo_link ausente.")
            continue

        item_link = item["novo_link"]
        print(f"\n🔎 Acessando {item_link}...")

        driver.get(item_link)

        # ANTES:
        # time.sleep(2)

        # DEPOIS: aguarda a presença da tabela
        esperar(driver, "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table")

        # ---------------------------
        # Capturar quantidade homologada
        # ---------------------------
        try:
            qnt_homologada_element = esperar(
                driver,
                "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[3]/td[2]/span"
            )

            qnt_homologada = qnt_homologada_element.text.strip()
            while qnt_homologada == "":
                time.sleep(0.5)
                qnt_homologada = qnt_homologada_element.text.strip()

            item["qnt_homologada"] = qnt_homologada

            print(f"   ✔ Quantidade homologada: {qnt_homologada}")

        except Exception as e:
            item["qnt_homologada"] = None
            print(f"   ❌ Erro ao capturar qnt_homologada ({e})")

        # ---------------------------
        # Capturar quantidade empenhada
        # ---------------------------
        try:
            qnt_empenhada_element = esperar(
                driver,
                "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[8]/td[2]/span"
            )

            qnt_empenhada = qnt_empenhada_element.text.strip()
            while qnt_empenhada == "":
                time.sleep(0.5)
                qnt_empenhada = qnt_empenhada_element.text.strip()

            item["qnt_empenhada"] = qnt_empenhada

            print(f"   ✔ Quantidade empenhada: {qnt_empenhada}")

        except Exception as e:
            item["qnt_empenhada"] = None
            print(f"   ❌ Erro ao capturar qnt_empenhada ({e})")

        # ---------------------------
        # NOVO: Capturar valor unitário
        # ---------------------------
        try:
            valor_unitario_element = esperar(
                driver,
                "/html/body/div[1]/main/div/div/div/div/div[2]/div/div/div/div/table/tbody/tr[6]/td[2]/span"
            )

            valor_unitario_raw = valor_unitario_element.text.strip()

            # texto vem como "4,50" ou "1.234,99"
            # converter para número float em padrão Python
            valor_unitario_num = float(
                valor_unitario_raw.replace(".", "").replace(",", ".")
            )

            item["valor_unitario"] = valor_unitario_num

            print(f"   ✔ Valor unitário capturado: R$ {valor_unitario_raw} → {valor_unitario_num}")

        except Exception as e:
            item["valor_unitario"] = None
            print(f"   ❌ Erro ao capturar valor_unitario ({e})")

    # ---------------------------
    # Salvar JSON final
    # ---------------------------
    if salvar_arquivo:
        # Se nenhum nome foi passado, gera automaticamente a partir do header
        if nome_arquivo is None:
            nome_arquivo = gerar_nome_arquivo_final(driver)

        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(itens_atualizados, f, ensure_ascii=False, indent=4)

    return itens_atualizados

def gerar_nome_arquivo_final(driver):
    """
    Lê o header da página e gera um nome de arquivo no formato:
        'UG - NUMERO_PREGAO.json'

    Exemplo de texto no header:
        'Itens da compra: 160377 - Pregão | 00005/2022'
    -> '160377 - 00005_2022.json'
    """

    # Espera o elemento do título no header
    header_elem = esperar(
        driver,
        "/html/body/header/div/div[2]/div/div[2]/div[1]"
    )
    texto = header_elem.text.strip()

    # Remove prefixo 'Itens da compra:' se existir
    if ":" in texto:
        _, resto = texto.split(":", 1)
    else:
        resto = texto
    resto = resto.strip()  # "160377 - Pregão | 00005/2022"

    # UG = parte antes do primeiro '-'
    partes_hifen = resto.split("-", 1)
    ug = partes_hifen[0].strip()  # "160377"

    # Número do pregão = parte depois do '|', ex. "00005/2022"
    if "|" in resto:
        num_parte = resto.split("|")[-1].strip()
    else:
        num_parte = resto.split()[-1].strip()

    numero_pregao = num_parte.replace("/", "_")  # "00005_2022"

    nome_base = f"{ug} - {numero_pregao}"

    # Sanitizar caracteres inválidos para nomes de arquivo em Windows
    # ( \ / : * ? " < > | )
    nome_base_limpo = re.sub(r'[\\/:*?"<>|]', "_", nome_base)

    return nome_base_limpo + ".json"


# ============================
# MAIN DE TESTE DA PARTE 1
# ============================

def main():
    driver = conectar_driver()

    # URL da contratação que você quer testar
    url = "https://contratos.sistema.gov.br/compras/486754/itens"

     # Abrir em nova aba para não interferir na aba manual
    abrir_nova_aba(driver, url)

    nome_arquivo_final = gerar_nome_arquivo_final(driver)
    print(f"Nome do arquivo final: {nome_arquivo_final}")

    # Parte 1: extrair itens da tabela principal
    itens_raw = extrair_links_itens(driver)

    # Parte 2A: para cada item, extrair o novo_link na página interna
    itens_stage2 = extrair_links_internos(driver, itens_raw)

    # Parte 2B: para cada item com novo_link, extrair quantidades + valor unitário
    itens_completos = enriquecer_com_quantidades(
        driver,
        itens_stage2,
        nome_arquivo=nome_arquivo_final,   # 🔹 usa o nome capturado no início
    )

    print("\n=== RESUMO FINAL (PIPELINE COMPLETA) ===")
    print(f"Total de itens: {len(itens_completos)}")
    for item in itens_completos[:3]:
        print(item)

    # Opcional: encerrar o driver
    # driver.quit()


if __name__ == "__main__":
    main()