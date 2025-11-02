from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import threading
import requests
from fake_useragent import UserAgent
import concurrent.futures
import json
import os

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
                # Default free proxy list (you should replace with your own)
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
    
    def get_working_proxies(self, max_workers=10):
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
        self.proxy = None
        self.proxy_manager = proxy_manager
        self.current_iteration = 0
        self.total_iterations = 0
        
    def setup_driver(self, proxy=None):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--headless')  # Run in background on server
            
            # Random user agent
            ua = UserAgent()
            user_agent = ua.random
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            if proxy:
                chrome_options.add_argument(f'--proxy-server={proxy}')
                self.proxy = proxy
            
            # Setup Chrome driver
            chrome_options.binary_location = '/usr/bin/google-chrome'
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except Exception as e:
            self.status = f"Error setting up driver: {str(e)}"
            return False
    
    def check_ip_leak(self):
        try:
            self.driver.get("https://api.ipify.org?format=json")
            time.sleep(3)
            page_source = self.driver.page_source
            if "ip" in page_source.lower():
                return True
            return False
        except:
            return False
    
    def check_proxy_working(self):
        """Check if current proxy is still working"""
        try:
            self.driver.get("https://httpbin.org/ip")
            time.sleep(2)
            return True
        except:
            return False
    
    def perform_search_flow(self, keyword, website_url):
        try:
            self.status = "Membuka Google.com"
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(3, 5))
            
            # Terima cookies jika ada
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Terima semua') or contains(., 'Setuju') or contains(., 'Accept all')]"))
                )
                cookie_button.click()
                time.sleep(2)
            except:
                pass
            
            self.status = "Mengetik kata kunci pencarian"
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Clear existing text and type with natural delay
            search_box.clear()
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(2)
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(3, 5))
            
            self.status = "Mencari URL target"
            # Cari link yang sesuai
            search_results = self.driver.find_elements(By.CSS_SELECTOR, "div.g h3")
            target_link = None
            
            for result in search_results[:5]:
                try:
                    link_element = result.find_element(By.XPATH, "./..")
                    href = link_element.get_attribute("href")
                    if website_url.lower() in href.lower() or any(kw.lower() in result.text.lower() for kw in website_url.split()):
                        target_link = link_element
                        break
                except:
                    continue
            
            if not target_link and search_results:
                target_link = search_results[0].find_element(By.XPATH, "./..")
            
            if target_link:
                self.status = "Membuka link hasil pencarian"
                target_link.click()
                time.sleep(random.uniform(5, 8))
                
                # Scroll behavior - natural scrolling
                self.status = "Scrolling halaman secara natural"
                scroll_actions = [
                    (300, 2), (600, 2), (900, 2), (1200, 2),
                    (1500, 2), (1800, 2), (2100, 2)
                ]
                
                for scroll_pos, pause in scroll_actions:
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
                    time.sleep(pause)
                
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Scroll back to top
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                
                # Klik postingan acak jika ada
                try:
                    post_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/'], a[href*='/post/'], a[href*='/article/'], a[href*='/blog/']")
                    if post_links:
                        random_post = random.choice(post_links[:5])
                        self.status = "Membuka postingan artikel"
                        random_post.click()
                        time.sleep(random.uniform(5, 8))
                        
                        # Scroll artikel
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(4)
                        self.driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(2)
                        
                        # Kembali ke halaman sebelumnya
                        self.driver.execute_script("window.history.go(-1)")
                        time.sleep(3)
                
                except Exception as e:
                    self.status = f"Error browsing posts: {str(e)}"
                
                return True
            
            return False
            
        except Exception as e:
            self.status = f"Error in search flow: {str(e)}"
            return False
    
    def run_traffic_session(self, keyword, website_url, iterations):
        self.total_iterations = iterations
        session_success = 0
        
        for i in range(iterations):
            self.current_iteration = i + 1
            
            # Get new proxy for each iteration or reuse if still working
            if i == 0 or not self.check_proxy_working():
                new_proxy = self.proxy_manager.get_random_working_proxy()
                if new_proxy:
                    self.close_driver()
                    if not self.setup_driver(new_proxy):
                        self.status = "Gagal setup driver dengan proxy baru"
                        continue
                else:
                    self.status = "Tidak ada proxy yang bekerja, menggunakan koneksi langsung"
                    self.close_driver()
                    if not self.setup_driver():
                        continue
            
            # Cek kebocoran data
            self.status = "Memeriksa kebocoran data"
            if not self.check_ip_leak():
                self.status = "Peringatan: Kemungkinan kebocoran data terdeteksi"
            else:
                self.status = "Status: Aman, melanjutkan..."
            
            time.sleep(2)
            
            # Jalankan search flow
            self.status = f"Menjalankan iterasi {i+1}/{iterations}"
            success = self.perform_search_flow(keyword, website_url)
            
            if success:
                session_success += 1
                self.status = f"Berhasil iterasi {i+1}"
            else:
                self.status = f"Gagal pada iterasi {i+1}"
            
            # Delay antara iterasi
            if i < iterations - 1:
                delay = random.uniform(15, 30)
                self.status = f"Menunggu {int(delay)} detik sebelum iterasi berikutnya..."
                time.sleep(delay)
        
        self.status = f"Selesai: {session_success}/{iterations} iterasi berhasil"
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
    
    def run_traffic():
        try:
            success_count = bot_instance.run_traffic_session(keyword, website_url, iterations)
            bot_instance.status = f"Traffic generation selesai. Berhasil: {success_count}/{iterations}"
        except Exception as e:
            bot_instance.status = f"Error: {str(e)}"
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
        "current_iteration": bot_instance.current_iteration,
        "total_iterations": bot_instance.total_iterations,
        "proxy": bot_instance.proxy
    })

@app.route('/stop_traffic', methods=['POST'])
def stop_traffic():
    bot_instance.close_driver()
    bot_instance.status = "Dihentikan oleh pengguna"
    return jsonify({"status": "stopped", "message": "Traffic generation stopped"})

if __name__ == '__main__':
    # Pre-check working proxies on startup
    print("Checking working proxies...")
    proxy_manager.get_working_proxies()
    app.run(host='0.0.0.0', port=5000, debug=False)
