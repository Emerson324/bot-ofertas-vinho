import time
import requests
import pyperclip
import unicodedata
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------- FUNÇÕES AUXILIARES ----------
def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def eh_vinho_valido(titulo):
    titulo_lower = normalizar(titulo)
    permitidos = [
        "vinho", "malbec", "cabernet", "tinto", "branco", "rose", "espumante",
        "dv catena", "angelica zapata", "alma negra", "el enemigo", "luigi bosca"
    ]
    proibidos = ["whisky", "cerveja", "vodka", "gin", "licor", "cachaça", "rum"]

    if any(p in titulo_lower for p in proibidos):
        return False
    if any(p in titulo_lower for p in permitidos):
        return True
    return False

def preco_para_float(preco_str):
    try:
        return float(preco_str.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except:
        return float("inf")

# ---------- COLETA DE VINHOS ESPECÍFICOS ----------
def coletar_vinho_especifico(nome_vinho, exigir_malbec=False):
    url = f'https://www.amazon.com.br/s?k={nome_vinho.replace(" ", "+")}'
    driver = webdriver.Chrome()
    try:
        driver.get(url)
        time.sleep(5)
        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".s-result-item")

    ofertas = []
    nome_norm = normalizar(nome_vinho)
    vistos = set()  # evitar duplicados

    for item in items:
        titulo = item.select_one("h2 span")
        preco_tag = item.select_one("span.a-offscreen") or item.select_one(".a-price-whole")
        link_tag = item.select_one("a.a-link-normal")

        if titulo and preco_tag and link_tag:
            titulo_clean = titulo.text.strip()
            titulo_norm = normalizar(titulo_clean)

            if not eh_vinho_valido(titulo_clean):
                continue

            if exigir_malbec and "malbec" not in titulo_norm:
                continue

            if nome_norm not in titulo_norm:
                continue

            # evitar duplicados pelo título normalizado
            if titulo_norm in vistos:
                continue
            vistos.add(titulo_norm)

            href = link_tag.get('href')
            link = href if href.startswith('http') else ("https://www.amazon.com.br" + href)

            preco_text = preco_tag.get_text(strip=True) if preco_tag else ''
            preco_clean = preco_text.replace('\xa0', ' ').encode('ascii', 'ignore').decode('ascii')

            ofertas.append({
                'title': titulo_clean,
                'price': preco_clean,
                'link': link,
            })

    # ordenar: primeiro individuais, depois kits/caixas, e dentro disso pelo preço
    def prioridade(oferta):
        titulo_norm = normalizar(oferta['title'])
        if any(p in titulo_norm for p in ["kit", "caixa", "unidades", "garrafas", "combo"]):
            return (1, preco_para_float(oferta['price']))
        return (0, preco_para_float(oferta['price']))

    return sorted(ofertas, key=prioridade)[:2]

# ---------- ENCURTAR LINK ----------
def encurtar_link_tinyurl(long_url):
    try:
        resp = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}")
        if resp.status_code == 200:
            short = resp.text
            return short.replace("https://", "").replace("http://", "")
    except Exception as e:
        print(f"Erro ao encurtar link: {e}")
    return long_url

# ---------- LOCALIZAR CAIXA DE MENSAGEM ----------
def find_message_box(driver, timeout=10):
    xpaths = [
        '//div[@contenteditable="true" and contains(@aria-label, "Digitar na conversa")]',
        '//div[@contenteditable="true" and contains(@aria-label, "Digitar no grupo")]',
        '//div[@contenteditable="true" and contains(@aria-placeholder, "Digite uma mensagem")]',
        '//div[@contenteditable="true" and @data-tab]',
        '//div[@contenteditable="true"]',
    ]
    for xp in xpaths:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xp))
            )
            try:
                el.click()
            except Exception:
                pass
            return el
        except Exception:
            continue
    raise Exception('Caixa de mensagem não encontrada')

# ---------- ENVIO NO WHATSAPP ----------
def enviar_whatsapp(vinhos_por_rotulo, grupo_nome):
    driver = webdriver.Chrome()
    driver.get("https://web.whatsapp.com")
    input("📲 Escaneie o QR Code e pressione Enter...")

    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Caixa de texto de pesquisa"]'))
    )
    search_box.click()
    search_box.send_keys(grupo_nome)
    time.sleep(2)
    search_box.send_keys(Keys.ENTER)
    time.sleep(3)

    lines = ["*Vinhos selecionados*"]
    lines.append("")

    for rotulo, ofertas in vinhos_por_rotulo.items():
        lines.append(f"➡️ {rotulo}")
        if not ofertas:
            lines.append("⚠️ Nenhuma oferta encontrada")
            lines.append("")
            continue
        for oferta in ofertas:
            title = oferta.get('title')
            price = oferta.get('price')
            link = oferta.get('link')
            try:
                if '?tag=' not in link:
                    sep = '&' if '?' in link else '?'
                    link = link + sep + 'tag=teste0df-20'
            except Exception:
                pass
            short_link = encurtar_link_tinyurl(link)

            lines.append(f"{title}")
            lines.append(f"Preço: {price}")
            lines.append(f"Link: {short_link}")
            lines.append("")
        lines.append("")  # espaço entre rótulos

    mensagem_unica = "\n".join(lines).strip()

    try:
        msg_box = find_message_box(driver)
        msg_box.click()
        pyperclip.copy(mensagem_unica)
        msg_box.send_keys(Keys.CONTROL, 'v')
        time.sleep(0.5)
        msg_box.send_keys(Keys.ENTER)
        time.sleep(20)
        print("✓ Mensagem enviada")
    except Exception as e:
        print(f"✗ Erro ao enviar mensagem: {e}")

    driver.quit()

# ---------- EXECUÇÃO ----------
if __name__ == "__main__":
    vinhos_fixos = {
        "DV Catena": True,       # exigir malbec
        "Angélica Zapata": False,
        "Alma negra": True,      # exigir malbec
        "El enemigo": False,
        "Luigi Bosca": False
    }

    vinhos_por_rotulo = {}
    for vinho, exigir_malbec in vinhos_fixos.items():
        vinhos_por_rotulo[vinho] = coletar_vinho_especifico(vinho, exigir_malbec)

    enviar_whatsapp(vinhos_por_rotulo, "Ofertas")  # troque pelo nome do seu grupo