from flask import Flask, render_template, request, jsonify, session
import threading
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Status global untuk melacak proses yang sedang berjalan
active_sessions = {}

class TrafficBot:
    def __init__(self, proxy_list, target_url, session_id):
        self.proxy_list = proxy_list
        self.target_url = target_url
        self.session_id = session_id
        self.active_proxies = []
        self.driver = None
        self.status = "Initializing"
        
    def check_proxy(self, proxy):
        """Memeriksa apakah proxy aktif"""
        try:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'https://{proxy}'
            }
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def check_proxies(self):
        """Memeriksa semua proxy yang aktif"""
        self.status = "Checking proxies"
        active_sessions[self.session_id] = self.status
        
        self.active_proxies = []
        for proxy in self.proxy_list:
            if self.check_proxy(proxy):
                self.active_proxies.append(proxy)
                logger.info(f"Proxy aktif: {proxy}")
        
        return len(self.active_proxies) > 0
    
    def setup_driver(self, proxy=None):
        """Menyiapkan Chrome driver dengan konfigurasi"""
        chrome_options = Options()
        
        # Mode headless untuk server
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # User agent acak
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def check_data_leak(self):
        """Memeriksa kebocoran data"""
        try:
            # Contoh pemeriksaan sederhana
            self.driver.get("https://whatismyipaddress.com/")
            time.sleep(3)
            
            # Periksa apakah IP terdeteksi berbeda
            page_source = self.driver.page_source.lower()
            if "proxy" in page_source or "vpn" in page_source:
                return False
            return True
        except:
            return False
    
    def perform_search(self):
        """Melakukan pencarian Google"""
        try:
            self.status = "Performing Google search"
            active_sessions[self.session_id] = self.status
            
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Temukan kotak pencarian dan masukkan query
            search_box = self.driver.find_element(By.NAME, "q")
            domain = self.target_url.replace("https://", "").replace("http://", "").split("/")[0]
            search_box.send_keys(f"site:{domain}")
            search_box.submit()
            
            time.sleep(3)
            
            # Klik hasil pertama
            results = self.driver.find_elements(By.CSS_SELECTOR, "div.g h3")
            if results:
                results[0].click()
                time.sleep(5)
                return True
            return False
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return False
    
    def simulate_user_behavior(self):
        """Mensimulasikan perilaku pengguna"""
        try:
            # Scroll ke bawah dengan durasi acak
            self.status = "Scrolling down"
            active_sessions[self.session_id] = self.status
            
            scroll_duration = random.uniform(3, 8)
            start_time = time.time()
            
            while time.time() - start_time < scroll_duration:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
            
            # Scroll kembali ke atas
            self.status = "Scrolling up"
            active_sessions[self.session_id] = self.status
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Cari link postingan dan klik
            links = self.driver.find_elements(By.TAG_NAME, "a")
            article_links = [link for link in links if link.get_attribute("href") and any(keyword in link.text.lower() for keyword in ["blog", "article", "post", "read"])]
            
            if article_links:
                random.choice(article_links).click()
                time.sleep(5)
                
                # Scroll di halaman postingan
                self.status = "Scrolling in article"
                active_sessions[self.session_id] = self.status
                
                scroll_duration = random.uniform(2, 6)
                start_time = time.time()
                
                while time.time() - start_time < scroll_duration:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.5)
            
            # Kembali ke home
            self.driver.get(self.target_url)
            time.sleep(3)
            
            return True
        except Exception as e:
            logger.error(f"Error during user simulation: {e}")
            return False
    
    def close_ads(self):
        """Menutup iklan jika ada"""
        try:
            close_selectors = [
                "button[aria-label*='close']",
                "button[class*='close']",
                "div[class*='close']",
                "span[class*='close']"
            ]
            
            for selector in close_selectors:
                try:
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in close_buttons:
                        if button.is_displayed():
                            button.click()
                            time.sleep(1)
                except:
                    continue
        except:
            pass
    
    def run_session(self):
        """Menjalankan satu sesi traffic"""
        try:
            if not self.check_proxies():
                self.status = "No active proxies found"
                active_sessions[self.session_id] = self.status
                return
            
            proxy = random.choice(self.active_proxies)
            if not self.setup_driver(proxy):
                self.status = "Failed to setup browser"
                active_sessions[self.session_id] = self.status
                return
            
            self.status = "Checking data leak"
            active_sessions[self.session_id] = self.status
            
            if not self.check_data_leak():
                self.status = "Data leak detected - stopping"
                active_sessions[self.session_id] = self.status
                self.driver.quit()
                return
            
            self.status = "Starting traffic simulation"
            active_sessions[self.session_id] = self.status
            
            # Lakukan beberapa sesi
            for i in range(3):  # 3 sesi per proxy
                self.status = f"Session {i+1}/3"
                active_sessions[self.session_id] = self.status
                
                if not self.perform_search():
                    break
                
                self.close_ads()
                self.simulate_user_behavior()
                
                time.sleep(random.uniform(5, 15))
            
            self.status = "Completed successfully"
            active_sessions[self.session_id] = self.status
            
        except Exception as e:
            self.status = f"Error: {str(e)}"
            active_sessions[self.session_id] = self.status
            logger.error(f"Session error: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_traffic', methods=['POST'])
def start_traffic():
    data = request.json
    proxies = data.get('proxies', '').split('\n')
    target_url = data.get('target_url', '')
    session_id = str(int(time.time()))
    
    # Validasi input
    if not proxies or not target_url:
        return jsonify({'error': 'Proxies dan URL target harus diisi'}), 400
    
    # Bersihkan daftar proxy
    proxies = [p.strip() for p in proxies if p.strip()]
    
    # Buat dan jalankan bot di thread terpisah
    bot = TrafficBot(proxies, target_url, session_id)
    thread = threading.Thread(target=bot.run_session)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'session_id': session_id,
        'message': 'Traffic simulation started'
    })

@app.route('/status/<session_id>')
def get_status(session_id):
    status = active_sessions.get(session_id, 'Session not found')
    return jsonify({'status': status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
