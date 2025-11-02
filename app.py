from flask import Flask, render_template, request, jsonify, Response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random
import threading
import requests
from fake_useragent import UserAgent
import concurrent.futures
import json
import os
import base64
import io
from PIL import Image

app = Flask(__name__)

class ProxyManager:
    def __init__(self):
        self.proxy_list = []
        self.working_proxies = []
        self.load_proxies()
        
    def load_proxies(self):
        """Load proxies from file or use default ones"""
        try:
            if os.path.exists('proxies.txt'):
                with open('proxies.txt', 'r') as f:
                    self.proxy_list = [line.strip() for line in f if line.strip()]
            else:
                # Default free proxy list
                self.proxy_list = [
                    'http://45.77.56.101:3128',
                    'http://51.158.68.68:8811', 
                    'http://163.172.157.7:8080',
                    'http://51.158.68.133:8811',
                    'http://51.158.68.26:8811'
                ]
        except Exception as e:
            print(f"Error loading proxies: {e}")
            self.proxy_list = []
    
    def save_proxies(self, proxies):
        """Save new proxies to file"""
        try:
            with open('proxies.txt', 'w') as f:
                for proxy in proxies:
                    f.write(proxy + '\n')
            self.proxy_list = proxies
            return True
        except Exception as e:
            print(f"Error saving proxies: {e}")
            return False
    
    def test_proxy(self, proxy):
        """Test if a proxy is working"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': proxy,
                'https': proxy
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                print(f"Proxy {proxy} is working")
                return proxy
        except Exception as e:
            print(f"Proxy {proxy} failed: {e}")
        return None
    
    def get_working_proxies(self, max_workers=5):
        """Get list of working proxies using multithreading"""
        if not self.proxy_list:
            self.load_proxies()
            
        self.working_proxies = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(self.test_proxy, proxy): proxy for proxy in self.proxy_list}
            
            for future in concurrent.futures.as_completed(future_to_proxy):
                result = future.result()
                if result:
                    self.working_proxies.append(result)
        
        print(f"Found {len(self.working_proxies)} working proxies")
        return self.working_proxies
    
    def get_random_working_proxy(self):
        """Get a random working proxy"""
        if not self.working_proxies:
            self.get_working_proxies()
        
        if self.working_proxies:
            return random.choice(self.working_proxies)
        return None

class GoogleTrafficBot:
    def __init__(self, proxy_manager):
        self.driver = None
        self.status = "Ready"
        self.current_step = ""
        self.proxy = None
        self.proxy_manager = proxy_manager
        self.current_iteration = 0
        self.total_iterations = 0
        self.website_opened = False
        self.last_screenshot = None
        
    def setup_driver(self, proxy=None):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Random user agent
            ua = UserAgent()
            user_agent = ua.random
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            if proxy:
                chrome_options.add_argument(f'--proxy-server={proxy}')
                self.proxy = proxy
                self.current_step = f"Menggunakan proxy: {proxy}"
            
            # Setup Chrome driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except Exception as e:
            self.status = f"Error setting up driver: {str(e)}"
            return False
    
    def take_screenshot(self):
        """Take screenshot and convert to base64"""
        try:
            if self.driver:
                screenshot = self.driver.get_screenshot_as_png()
                img = Image.open(io.BytesIO(screenshot))
                
                # Resize image to reduce size
                img.thumbnail((800, 600))
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=70)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                self.last_screenshot = f"data:image/jpeg;base64,{img_str}"
                return self.last_screenshot
        except Exception as e:
            print(f"Screenshot error: {e}")
        return None
    
    def check_ip_leak(self):
        try:
            self.current_step = "Memeriksa kebocoran IP..."
            self.driver.get("https://api.ipify.org?format=json")
            time.sleep(3)
            page_source = self.driver.page_source
            self.take_screenshot()
            return "ip" in page_source.lower()
        except:
            return False
    
    def perform_search_flow(self, keyword, website_url):
        try:
            self.website_opened = False
            
            # Step 1: Buka Google
            self.current_step = "Membuka Google.com..."
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(3, 5))
            self.take_screenshot()
            
            # Terima cookies jika ada
            try:
                cookie_buttons = [
                    "//button[contains(., 'Terima semua')]",
                    "//button[contains(., 'Setuju')]", 
                    "//button[contains(., 'Accept all')]",
                    "//button[contains(., 'I agree')]",
                    "//div[contains(., 'cookie')]//button"
                ]
                
                for xpath in cookie_buttons:
                    try:
                        cookie_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        cookie_button.click()
                        self.current_step = "Menutup dialog cookies..."
                        time.sleep(2)
                        self.take_screenshot()
                        break
                    except:
                        continue
            except:
                pass
            
            # Step 2: Ketik kata kunci
            self.current_step = f"Mengetik kata kunci: '{keyword}'..."
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Clear dan ketik dengan natural delay
            search_box.clear()
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(1)
            self.take_screenshot()
            
            # Step 3: Tekan Enter untuk search
            self.current_step = "Melakukan pencarian..."
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(4, 6))
            self.take_screenshot()
            
            # Step 4: Cari dan klik link paling atas
            self.current_step = "Mencari hasil pencarian teratas..."
            
            # Tunggu hasil pencarian muncul
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
            )
            
            # Dapatkan semua hasil pencarian
            search_results = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
            
            if not search_results:
                self.current_step = "Tidak menemukan hasil pencarian, mencoba selector alternatif..."
                search_results = self.driver.find_elements(By.CSS_SELECTOR, ".tF2Cxc, .g, .rc")
            
            if search_results:
                # Cari link di hasil pertama
                first_result = search_results[0]
                try:
                    # Coba berbagai selector untuk link
                    link_selectors = [
                        "a",
                        "h3 a", 
                        ".yuRUbf a",
                        ".rc a",
                        "a[ping]"
                    ]
                    
                    link_element = None
                    for selector in link_selectors:
                        try:
                            link_element = first_result.find_element(By.CSS_SELECTOR, selector)
                            if link_element:
                                break
                        except:
                            continue
                    
                    if link_element:
                        link_url = link_element.get_attribute("href")
                        self.current_step = f"Membuka link: {link_url[:50]}..."
                        
                        # Klik link
                        self.driver.execute_script("arguments[0].click();", link_element)
                        time.sleep(random.uniform(5, 8))
                        self.take_screenshot()
                        
                        self.website_opened = True
                        self.current_step = "Berhasil membuka website target!"
                        
                        # Step 5: Scroll halaman
                        self.perform_scrolling()
                        
                        # Step 6: Coba cari dan klik postingan
                        self.click_random_post()
                        
                        return True
                    else:
                        self.current_step = "Tidak bisa menemukan link di hasil pertama"
                except Exception as e:
                    self.current_step = f"Error klik link: {str(e)}"
            else:
                self.current_step = "Tidak ada hasil pencarian yang ditemukan"
                
            return False
            
        except Exception as e:
            self.current_step = f"Error dalam proses pencarian: {str(e)}"
            self.take_screenshot()
            return False
    
    def perform_scrolling(self):
        """Lakukan scrolling natural"""
        try:
            self.current_step = "Melakukan scrolling halaman..."
            
            # Scroll bertahap dengan pola natural
            scroll_points = [300, 600, 400, 800, 1200, 900, 1500]
            for point in scroll_points:
                self.driver.execute_script(f"window.scrollTo(0, {point});")
                time.sleep(random.uniform(1, 3))
                self.take_screenshot()
            
            # Scroll ke paling bawah
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            self.take_screenshot()
            
            # Scroll kembali ke atas
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            self.take_screenshot()
            
        except Exception as e:
            self.current_step = f"Error saat scrolling: {str(e)}"
    
    def click_random_post(self):
        """Coba klik postingan acak"""
        try:
            self.current_step = "Mencari postingan artikel..."
            
            # Cari link yang kemungkinan adalah postingan
            post_selectors = [
                "a[href*='/p/']",
                "a[href*='/post/']", 
                "a[href*='/article/']",
                "a[href*='/blog/']",
                "a[href*='/read/']",
                "a:not([href*='google'])"
            ]
            
            all_links = []
            for selector in post_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute('href')
                        if href and len(href) > 10:
                            all_links.append(link)
                except:
                    continue
            
            # Filter link yang unik
            unique_links = []
            seen_urls = set()
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                        unique_links.append(link)
                except:
                    continue
            
            if unique_links:
                # Pilih link acak (bukan yang pertama)
                if len(unique_links) > 1:
                    random_post = random.choice(unique_links[1:min(6, len(unique_links))])
                else:
                    random_post = unique_links[0]
                
                self.current_step = "Membuka postingan acak..."
                self.driver.execute_script("arguments[0].click();", random_post)
                time.sleep(random.uniform(5, 8))
                self.take_screenshot()
                
                # Scroll postingan
                self.perform_scrolling()
                
                # Kembali ke halaman sebelumnya
                self.current_step = "Kembali ke halaman sebelumnya..."
                self.driver.execute_script("window.history.go(-1)")
                time.sleep(3)
                self.take_screenshot()
                
        except Exception as e:
            self.current_step = f"Tidak bisa membuka postingan: {str(e)}"
    
    def run_traffic_session(self, keyword, website_url, iterations):
        self.total_iterations = iterations
        session_success = 0
        
        for i in range(iterations):
            self.current_iteration = i + 1
            self.status = f"Menjalankan iterasi {i+1}/{iterations}"
            
            # Setup proxy untuk iterasi ini
            current_proxy = self.proxy_manager.get_random_working_proxy()
            if current_proxy:
                self.current_step = f"Menggunakan proxy: {current_proxy}"
                self.close_driver()
                if not self.setup_driver(current_proxy):
                    self.current_step = "Gagal setup driver dengan proxy, mencoba tanpa proxy..."
                    if not self.setup_driver():
                        continue
            else:
                self.current_step = "Tidak ada proxy aktif, menggunakan koneksi langsung"
                self.close_driver()
                if not self.setup_driver():
                    continue
            
            # Jalankan search flow
            success = self.perform_search_flow(keyword, website_url)
            
            if success and self.website_opened:
                session_success += 1
                self.current_step = f"✅ Iterasi {i+1} berhasil - Website dibuka"
            else:
                self.current_step = f"❌ Iterasi {i+1} gagal - Website tidak terbuka"
            
            # Delay antara iterasi
            if i < iterations - 1:
                delay = random.uniform(10, 20)
                self.current_step = f"Menunggu {int(delay)} detik sebelum iterasi berikutnya..."
                time.sleep(delay)
        
        self.status = f"Selesai: {session_success}/{iterations} iterasi berhasil"
        self.current_step = "Traffic generation completed"
        return session_success
    
    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None

# Initialize proxy manager and bot
proxy_manager = ProxyManager()
bot_instance = GoogleTrafficBot(proxy_manager)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_proxies')
def get_proxies():
    working_proxies = proxy_manager.get_working_proxies()
    return jsonify({
        "total_proxies": len(proxy_manager.proxy_list),
        "working_proxies": len(working_proxies),
        "proxy_list": proxy_manager.proxy_list,
        "working_list": working_proxies
    })

@app.route('/update_proxies', methods=['POST'])
def update_proxies():
    data = request.json
    proxies_text = data.get('proxies', '')
    
    if proxies_text:
        proxies_list = [p.strip() for p in proxies_text.split('\n') if p.strip()]
        if proxy_manager.save_proxies(proxies_list):
            return jsonify({"status": "success", "message": f"Berhasil menyimpan {len(proxies_list)} proxy"})
        else:
            return jsonify({"status": "error", "message": "Gagal menyimpan proxy"})
    
    return jsonify({"status": "error", "message": "Tidak ada proxy yang diberikan"})

@app.route('/start_traffic', methods=['POST'])
def start_traffic():
    data = request.json
    keyword = data.get('keyword', 'technology news')
    website_url = data.get('website_url', '')
    iterations = data.get('iterations', 1)
    
    # Reset status
    bot_instance.status = "Memulai..."
    bot_instance.current_step = "Mempersiapkan session..."
    
    def run_traffic():
        try:
            success_count = bot_instance.run_traffic_session(keyword, website_url, iterations)
            bot_instance.status = f"Traffic generation selesai. Berhasil: {success_count}/{iterations}"
            bot_instance.current_step = "✅ Process completed"
        except Exception as e:
            bot_instance.status = f"Error: {str(e)}"
            bot_instance.current_step = f"❌ Process failed: {str(e)}"
        finally:
            bot_instance.close_driver()
    
    # Jalankan di thread terpisah
    thread = threading.Thread(target=run_traffic)
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "message": "Traffic generation started"})

@app.route('/status')
def get_status():
    return jsonify({
        "status": bot_instance.status,
        "current_step": bot_instance.current_step,
        "current_iteration": bot_instance.current_iteration,
        "total_iterations": bot_instance.total_iterations,
        "proxy": bot_instance.proxy,
        "screenshot": bot_instance.last_screenshot,
        "website_opened": bot_instance.website_opened
    })

@app.route('/stop_traffic', methods=['POST'])
def stop_traffic():
    bot_instance.close_driver()
    bot_instance.status = "Dihentikan oleh pengguna"
    bot_instance.current_step = "Process stopped by user"
    return jsonify({"status": "stopped", "message": "Traffic generation stopped"})

if __name__ == '__main__':
    # Pre-check working proxies on startup
    print("Checking working proxi
