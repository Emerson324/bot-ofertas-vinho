import time
import requests
import subprocess
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------- PARTE 1: Scraping Amazon ----------
def coletar_ofertas_amazon():
    url = "https://www.amazon.com.br/s?k=vinho"
    driver = webdriver.Chrome()
    try:
        driver.get(url)
        time.sleep(5)
        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    ofertas = []
    items = soup.select(".s-result-item")

    for item in items[6:]:
        titulo = item.select_one("h2 span")
        preco_tag = item.select_one("span.a-offscreen") or item.select_one(".a-price-whole")
        link_tag = item.select_one("a.a-link-normal")

        if titulo and preco_tag and link_tag:
            href = link_tag.get('href')
            link = href if href.startswith('http') else ("https://www.amazon.com.br" + href)

            titulo_clean = titulo.text.strip().encode('ascii', 'ignore').decode('ascii')
            preco_text = preco_tag.get_text(strip=True) if preco_tag else ''
            preco_clean = preco_text.replace('\xa0', ' ').encode('ascii', 'ignore').decode('ascii')

            ofertas.append({
                'title': titulo_clean,
                'price': preco_clean,
                'link': link,
            })
    return ofertas

# ---------- PARTE 2: Encurtar link com TinyURL ----------
def encurtar_link_tinyurl(long_url):
    try:
        resp = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}")
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"Erro ao encurtar link: {e}")
    return long_url


# Helper: localizar caixa de mensagem do WhatsApp Web (várias variações de DOM)
def find_message_box(driver, timeout=10):
    xpaths = [
        # WhatsApp Web: 'Digitar na conversa com ...'
        '//div[@contenteditable="true" and contains(@aria-label, "Digitar na conversa")]',
        # 'Digitar no grupo' variante
        '//div[@contenteditable="true" and contains(@aria-label, "Digitar no grupo")]',
        # placeholder-based
        '//div[@contenteditable="true" and contains(@aria-placeholder, "Digite uma mensagem")]',
        # data-tab presence (some versions use data-tab numbers)
        '//div[@contenteditable="true" and @data-tab]',
        # generic fallback
        '//div[@contenteditable="true"]',
    ]
    for xp in xpaths:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xp))
            )
            # ensure it's interactable
            try:
                el.click()
            except Exception:
                pass
            return el
        except Exception:
            continue
    raise Exception('Caixa de mensagem não encontrada')

# ---------- PARTE 3: Envio no WhatsApp ----------
def enviar_whatsapp(ofertas, grupo_nome):
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

    # Construir uma única mensagem com todas as ofertas
    lines = ["Ofertas de hoje:"]
    for oferta in ofertas[:5]:
        title = oferta.get('title')
        price = oferta.get('price')
        link = oferta.get('link')
        # garantir que o link contenha a tag de associado
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
        lines.append("")  # linha em branco entre ofertas

    mensagem_unica = "\n".join(lines).strip()

    try:
        msg_box = find_message_box(driver)
        msg_box.click()
        # usar clipboard para preservar quebras de linha, com fallback para send_keys
        try:
            p = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            p.communicate(mensagem_unica.encode('utf-8'))
            msg_box.send_keys(Keys.CONTROL + 'v')
            time.sleep(0.3)
        except Exception:
            msg_box.send_keys(mensagem_unica)

        msg_box.send_keys(Keys.ENTER)
        time.sleep(1)
        print(f"✓ Mensagem única enviada com {min(5, len(ofertas))} oferta(s)")
    except Exception as e:
        print(f"✗ Erro ao enviar mensagem única: {e}")

    # mensagem enviada (ou erro já impresso acima)

    driver.quit()

# ---------- EXECUÇÃO ----------
if __name__ == "__main__":
    ofertas = coletar_ofertas_amazon()
    if ofertas:
        enviar_whatsapp(ofertas, "Anotações")  # troque pelo nome do seu grupo
    else:
        print("Nenhuma oferta encontrada.")