from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
from datetime import datetime
import logging
from urllib.parse import quote_plus

# Configurar logging para reduzir mensagens desnecessárias
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

class MagaluScraperSimple:
    def __init__(self, headless=False):
        """Inicializa o scraper do Magazine Luiza - versão simples e funcional"""
        try:
            self.options = Options()
            
            # Configurações básicas para performance
            self.options.add_argument("--no-sandbox")
            self.options.add_argument("--disable-dev-shm-usage")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--disable-extensions")
            self.options.add_argument("--disable-plugins")
            self.options.add_argument("--disable-images")  # Acelera muito
            self.options.add_argument("--disable-notifications")
            
            # Anti-detecção
            self.options.add_argument("--disable-blink-features=AutomationControlled")
            self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self.options.add_experimental_option('useAutomationExtension', False)
            self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Reduz logs
            self.options.add_argument("--log-level=3")
            self.options.add_argument("--silent")
            
            if headless:
                self.options.add_argument("--headless")
            
            # WebDriver
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=self.options)
                print("✅ ChromeDriver instalado automaticamente")
            except Exception as e:
                print(f"⚠️ Erro com webdriver-manager, tentando ChromeDriver padrão: {e}")
                self.driver = webdriver.Chrome(options=self.options)
            
            # Configurações do navegador
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 10)
            self.all_results = []
            
            print("✅ Navegador inicializado com sucesso")
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            raise
        
    def setup_driver(self):
        """Configura o driver"""
        self.driver.maximize_window()
        
    def read_products_list(self, file_path):
        """Lê lista de produtos do arquivo Excel ou CSV"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                print(f"📋 Arquivo Excel lido: {file_path}")
            elif file_extension == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                print(f"📋 Arquivo CSV lido: {file_path}")
            else:
                raise ValueError("Formato não suportado. Use .xlsx, .xls ou .csv")
            
            # Identifica coluna de produtos
            possible_columns = ['produto', 'produtos', 'item', 'itens', 'modelo', 'nome', 'busca', 'search']
            product_column = None
            
            for col in df.columns:
                if col.lower().strip() in possible_columns:
                    product_column = col
                    break
            
            if product_column is None:
                product_column = df.columns[0]
                print(f"⚠️ Usando primeira coluna: '{product_column}'")
            else:
                print(f"✅ Coluna encontrada: '{product_column}'")
            
            products_list = df[product_column].dropna().tolist()
            products_list = [str(product).strip() for product in products_list if str(product).strip()]
            
            print(f"📊 Total: {len(products_list)} produtos")
            return products_list
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {e}")
            return []
    
    def search_product(self, product_name):
        """Busca produto usando URL direta (mais rápido que caixa de busca)"""
        try:
            print(f"🔍 Buscando: {product_name}")
            
            # Vai direto para URL de busca (mais rápido)
            search_url = f"https://www.magazineluiza.com.br/busca/{quote_plus(product_name)}/"
            self.driver.get(search_url)
            time.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return False
    
    def get_first_product_link(self):
        """Pega o link do primeiro produto (sem validações complexas)"""
        try:
            time.sleep(2)
            
            # Seletores do Magazine Luiza (do mais específico ao mais genérico)
            product_selectors = [
                "a[data-testid='product-card-container']",
                "a[href*='/p/']",
                "[data-testid='product-card'] a",
                ".product-card a"
            ]
            
            for selector in product_selectors:
                try:
                    products = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if products:
                        # Pega o primeiro produto válido
                        for product in products[:3]:  # Tenta os primeiros 3
                            href = product.get_attribute('href')
                            if href and '/p/' in href and 'magazineluiza.com.br' in href:
                                print(f"✅ Produto encontrado")
                                return href
                except Exception:
                    continue
            
            print("❌ Nenhum produto encontrado")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao procurar produtos: {e}")
            return None
    
    def extract_product_info(self, product_url, search_term):
        """Extração simples e direta das informações do produto"""
        try:
            self.driver.get(product_url)
            time.sleep(4)  # Aguarda carregamento completo
            
            product_data = {
                'produto_buscado': search_term,
                'url': product_url,
                'modelo': 'N/A',
                'vendido_por': 'N/A',
                'preco_vista': 'N/A',
                'preco_credito': 'N/A',
                'disponivel': 'Sim',
                'e_magalu': 'N/A',
                'data_consulta': datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            # 1. TÍTULO/MODELO (igual ao script original)
            title_selectors = [
                "h1[data-testid='heading-product-title']",
                "h1.sc-fcdeBU",
                ".product-title h1",
                "h1"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    product_data['modelo'] = title_element.text.strip()
                    break
                except:
                    continue
            
            # 2. DISPONIBILIDADE (igual ao script original)
            try:
                unavailable_indicators = [
                    "//*[contains(text(), 'Produto indisponível')]",
                    "//*[contains(text(), 'Fora de estoque')]",
                    "//*[contains(text(), 'Esgotado')]"
                ]
                
                is_available = True
                for indicator in unavailable_indicators:
                    if self.driver.find_elements(By.XPATH, indicator):
                        is_available = False
                        break
                
                product_data['disponivel'] = 'Sim' if is_available else 'Não'
            except:
                pass
            
            # 3. VENDEDOR (igual ao script original)
            vendor_selectors = [
                "[data-testid='seller-info']",
                ".seller-info",
                "[data-testid='merchant-name']",
                "[data-testid='marketplaceSellerName']"  # Adicionado
            ]
            
            is_magalu_seller = True  # Assume Magalu por padrão
            for selector in vendor_selectors:
                try:
                    vendor_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    vendor_text = vendor_element.text.lower()
                    product_data['vendido_por'] = vendor_element.text.strip()
                    
                    if 'magazine luiza' not in vendor_text and 'magalu' not in vendor_text:
                        is_magalu_seller = False
                    break
                except:
                    continue
            
            if product_data['vendido_por'] == 'N/A':
                product_data['vendido_por'] = 'Magazine Luiza'
            
            product_data['e_magalu'] = 'Sim' if is_magalu_seller else 'Não'
            
            # 4. PREÇO À VISTA (melhorado mas simples)
            pix_selectors = [
                "[data-testid='price-value']",
                ".price-pix",
                "[data-testid='price-original']"
            ]
            
            for selector in pix_selectors:
                try:
                    price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text
                    if 'R$' in price_text:
                        product_data['preco_vista'] = price_text.strip()
                        break
                except:
                    continue
            
            # Se não encontrou, procura por qualquer elemento com preço PIX
            if product_data['preco_vista'] == 'N/A':
                try:
                    pix_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Pix') or contains(text(), 'PIX')]")
                    for elem in pix_elements:
                        text = elem.text
                        if 'R$' in text and any(c.isdigit() for c in text):
                            # Extrai apenas o preço
                            import re
                            price_match = re.search(r'R\$\s*[\d.,]+', text)
                            if price_match:
                                product_data['preco_vista'] = price_match.group(0)
                                break
                except:
                    pass
            
            # 5. PREÇO NO CARTÃO (igual ao original + melhorias)
            credit_selectors = [
                "[data-testid='price-installments']",
                ".price-installment"
            ]
            
            for selector in credit_selectors:
                try:
                    credit_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    credit_text = credit_element.text
                    if 'R$' in credit_text:
                        product_data['preco_credito'] = credit_text.strip()
                        break
                except:
                    continue
            
            # Se não encontrou, busca parcelamento (igual ao original)
            if product_data['preco_credito'] == 'N/A':
                try:
                    installment_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'x de R$') or contains(text(), 'parcela')]")
                    if installment_elements:
                        product_data['preco_credito'] = installment_elements[0].text.strip()
                except:
                    pass
            
            # Se ainda não encontrou, procura por "sem juros" ou "cartão"
            if product_data['preco_credito'] == 'N/A':
                try:
                    card_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'sem juros') or contains(text(), 'cartão') or contains(text(), 'Cartão')]")
                    for elem in card_elements:
                        text = elem.text
                        if 'R$' in text and ('x' in text or 'parcela' in text.lower()):
                            product_data['preco_credito'] = text.strip()
                            break
                except:
                    pass
            
            print(f"✅ {product_data['modelo'][:50]}...")
            print(f"   💰 À vista: {product_data['preco_vista']}")
            print(f"   💳 Cartão: {product_data['preco_credito']}")
            print(f"   🏪 Magalu: {product_data['e_magalu']}")
            
            return product_data
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados: {e}")
            return {
                'produto_buscado': search_term,
                'url': product_url,
                'modelo': 'ERRO NA EXTRAÇÃO',
                'vendido_por': 'N/A',
                'preco_vista': 'N/A',
                'preco_credito': 'N/A',
                'disponivel': 'N/A',
                'e_magalu': 'N/A',
                'data_consulta': datetime.now().strftime("%d/%m/%Y %H:%M")
            }
    
    def save_results(self, filename=None):
        """Salva resultados (igual ao original)"""
        try:
            if not self.all_results:
                print("❌ Nenhum resultado para salvar")
                return
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"levantamento_magalu_{timestamp}.csv"
            
            df = pd.DataFrame(self.all_results)
            
            column_order = [
                'produto_buscado', 'modelo', 'preco_vista', 'preco_credito', 
                'disponivel', 'e_magalu', 'vendido_por', 'data_consulta', 'url'
            ]
            df = df.reindex(columns=column_order)
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"\n📊 RESUMO DOS RESULTADOS:")
            print(f"✅ Total de produtos processados: {len(self.all_results)}")
            print(f"🏪 Vendidos pela Magalu: {len([r for r in self.all_results if r.get('e_magalu') == 'Sim'])}")
            print(f"🛒 Disponíveis: {len([r for r in self.all_results if r.get('disponivel') == 'Sim'])}")
            print(f"💾 Arquivo salvo: {filename}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar resultados: {e}")
    
    def process_products_list(self, file_path, only_magalu=False, max_products=None):
        """Processamento simples e direto (baseado no script original)"""
        try:
            self.setup_driver()
            
            products_list = self.read_products_list(file_path)
            
            if not products_list:
                print("❌ Nenhum produto para processar")
                return
            
            # Limita produtos se especificado
            if max_products:
                products_list = products_list[:max_products]
                print(f"⚠️ Limitando a {max_products} produtos")
            
            print(f"\n🚀 Processando {len(products_list)} produtos...")
            print(f"🏪 Apenas Magalu: {'Sim' if only_magalu else 'Não'}")
            print("-" * 60)
            
            for i, product in enumerate(products_list, 1):
                try:
                    print(f"\n📦 [{i}/{len(products_list)}] {product}")
                    
                    # Busca o produto
                    if not self.search_product(product):
                        # Adiciona como não encontrado
                        self.all_results.append({
                            'produto_buscado': product,
                            'modelo': 'FALHA NA BUSCA',
                            'preco_vista': 'N/A',
                            'preco_credito': 'N/A',
                            'disponivel': 'N/A',
                            'e_magalu': 'N/A',
                            'vendido_por': 'N/A',
                            'data_consulta': datetime.now().strftime("%d/%m/%Y %H:%M"),
                            'url': 'N/A'
                        })
                        continue
                    
                    # Pega o primeiro resultado (SEM validações de similaridade)
                    product_link = self.get_first_product_link()
                    
                    if not product_link:
                        # Adiciona como não encontrado
                        self.all_results.append({
                            'produto_buscado': product,
                            'modelo': 'NÃO ENCONTRADO',
                            'preco_vista': 'N/A',
                            'preco_credito': 'N/A',
                            'disponivel': 'N/A',
                            'e_magalu': 'N/A',
                            'vendido_por': 'N/A',
                            'data_consulta': datetime.now().strftime("%d/%m/%Y %H:%M"),
                            'url': 'N/A'
                        })
                        continue
                    
                    # Extrai informações
                    product_data = self.extract_product_info(product_link, product)
                    
                    # Filtro Magalu (opcional)
                    if only_magalu and product_data.get('e_magalu') != 'Sim':
                        print(f"⚠️ Não é Magalu, pulando...")
                        continue
                    
                    self.all_results.append(product_data)
                    
                    # Pausa entre produtos
                    time.sleep(2)
                    
                except KeyboardInterrupt:
                    print("\n⚠️ Interrompido pelo usuário")
                    break
                except Exception as e:
                    print(f"❌ Erro: {e}")
                    continue
            
            # Salva resultados
            self.save_results()
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")
        finally:
            self.close()
    
    def close(self):
        """Fecha navegador"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("🔚 Navegador fechado")


def criar_lista_exemplo():
    """Cria arquivo de exemplo"""
    filename = "lista_produtos.xlsx"
    
    if os.path.exists(filename):
        return filename
    
    print("📝 Criando arquivo de exemplo...")
    produtos_exemplo = [
        "smartphone samsung galaxy",
        "notebook dell inspiron", 
        "tablet apple ipad",
        "fone bluetooth jbl",
        "mouse gamer logitech"
    ]
    
    df = pd.DataFrame({'produto': produtos_exemplo})
    df.to_excel(filename, index=False)
    print(f"✅ Arquivo criado: {filename}")
    return filename


# EXECUÇÃO PRINCIPAL
if __name__ == "__main__":
    print("🏢 LEVANTAMENTO SIMPLIFICADO - MAGAZINE LUIZA")
    print("=" * 50)
    
    # CONFIGURAÇÕES
    ARQUIVO_LISTA = "lista_produtos.xlsx"
    APENAS_MAGALU = False  # False = pega todos os produtos
    MAX_PRODUTOS = None    # None = todos, ou número para testar
    HEADLESS = False       # True = sem janela do navegador
    
    # Verifica arquivo
    if not os.path.exists(ARQUIVO_LISTA):
        print(f"📁 Arquivo '{ARQUIVO_LISTA}' não encontrado.")
        resposta = input("Criar arquivo de exemplo? (s/n): ").lower().strip()
        
        if resposta == 's':
            ARQUIVO_LISTA = criar_lista_exemplo()
        else:
            print("\n📝 COMO CRIAR O ARQUIVO:")
            print("1. Excel/CSV com coluna 'produto'")
            print("2. Um produto por linha")
            exit(1)
    
    # Executa
    try:
        scraper = MagaluScraperSimple(headless=HEADLESS)
        
        scraper.process_products_list(
            file_path=ARQUIVO_LISTA,
            only_magalu=APENAS_MAGALU,
            max_products=MAX_PRODUTOS
        )
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")