# 📦 Bot de Ofertas de Vinho para WhatsApp

Este projeto automatiza a coleta de ofertas de vinhos e envia as melhores opções diretamente para um grupo ou contato no **WhatsApp Web**.  
O envio é feito em um único bloco de texto, sem gerar preview dos links.

---

## 🚀 Funcionalidades

- **Scraping da Amazon**: coleta títulos, preços e links de vinhos.
- **Encurtamento de links**: utiliza a API do TinyURL para gerar links curtos e remove `https://` para evitar preview no WhatsApp.
- **Automação no WhatsApp Web**:
  - Abre o navegador com Selenium.
  - Localiza a caixa de mensagem do grupo/contato.
  - Cola a mensagem completa com todas as ofertas.
  - Envia automaticamente.

---

## 🛠️ Tecnologias utilizadas

- [Python 3](https://www.python.org/)
- [Selenium](https://www.selenium.dev/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [Requests](https://docs.python-requests.org/)
- [Pyperclip](https://pypi.org/project/pyperclip/)

---

## 📋 Pré-requisitos

1. **Python 3.8+** instalado.
2. Instalar dependências:
   ```bash
   pip install selenium beautifulsoup4 requests pyperclip