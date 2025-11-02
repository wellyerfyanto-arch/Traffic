from flask import Flask, render_template, request, jsonify, Response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
# PIL/Image tidak diperlukan jika Anda tidak benar-benar memproses gambar
# from PIL import Image 

app = Flask(__name__)

# --- UTILITIES (ProxyManager) ---

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
                # Default free proxy list (ganti dengan list proxy Anda yang valid)
                self.proxy_list = [
                    'http://45.77.56.101:3128',
                    'http://51.158.68.68:8811', 
                    'http://163.172.157.7:8080',
                ]
        except Exception as e:
            print(f"Error loading proxies: {e}")
            self.proxy_list = []

    def test_proxy(self, proxy):
        """Test if a single proxy works"""
        try:
            requests.get('http://google.com', proxies={'http': proxy, 'https': proxy}, timeout=5)
            return True
        except:
            return False

    def get_working_proxies(self):
        """Filter and return working proxies"""
        if self.working_proxies:
            return self.working_proxies
            
        print(f"Testing {len(self.proxy_list)} proxies...")
        workers = min(10, len(self.proxy_list))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_proxy = {executor.submit(self.test_proxy, proxy): proxy for proxy in self.proxy_list}
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                if future.result():
                    self.working_proxies.append(proxy)

        print(f"Found {len(self.working_proxies)} working proxies.")
        return self.working_proxies

# --- TRAFFIC BOT CLASS ---

class TrafficBot:
    def __init__(self):
        self.driver = None
        self.status = "Idle"
        self.current_step = "Initialized"
        self.proxy = "None"
        self.last_screenshot = None
        self.website_opened = False
        self.ua = UserAgent()
        # PERBAIKAN: Inisialisasi variabel untuk status iterasi
        self.total_iterations = 0
        self.current_iteration = 0

    def setup_driver(self, proxy_list):
        """Setup Chrome driver with options and proxy"""
        chrome_options = Options()
        
        # Human-like User Agent
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Proxy setup
        if proxy_list:
            proxy = random.choice(proxy_list)
            self.proxy = proxy
            chrome_options.add_argument(f'--proxy-server={proxy}')
            self.status = f"Setup dengan proxy: {proxy}"
        else:
            self.proxy = "None"
            self.status = "Setup tanpa proxy"
            
        # Standard settings to avoid detection
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.current_step = "Driver set up successfully"
            return True
        except WebDriverException as e:
            self.current_step = f"Driver setup failed: {e}"
            self.status = "Failed to launch driver"
            return False

    def capture_screenshot(self):
        """Capture screenshot and return as base64 string"""
        if self.driver:
            try:
                screenshot = self.driver.get_screenshot_as_base64()
                # Optional: resize or process image if needed, but keeping it raw base64 is simpler
                self.last_screenshot = screenshot
                return
            except:
                self.last_screenshot = None
        self.last_screenshot = None

    def run_traffic_session(self, keyword, target_website, iterations):
        """Main loop for generating traffic"""
        self.total_iterations = iterations
        success_count = 0
        
        pm = ProxyManager()
        working_proxies = pm.get_working_proxies()

        for i in range(1, iterations + 1):
            self.current_iteration = i
            if self.status == "Dihentikan oleh pengguna":
                break
                
            self.current_step = f"Cycle {i}/{iterations}: Setting up driver..."
            
            # Setup driver per cycle untuk rotasi IP
            if not self.setup_driver(working_proxies):
                self.status = "Gagal setup driver, skip cycle."
                self.close_driver()
                continue
            
            self.status = f"Cycle {i}/{iterations}: Searching for '{keyword}'"
            
            try:
                # 1. Go to Google
                self.driver.get("https://www.google.com")
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
                search_box.send_keys(keyword)
                search_box.submit()
                time.sleep(random.uniform(2, 4))
                
                # 2. Find and click target website
                self.current_step = f"Cycle {i}/{iterations}: Finding target link..."
                xpath = f"//a[contains(@href, '{target_website}')]"
                target_link = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                
                self.driver.execute_script("arguments[0].click();", target_link)
                self.website_opened = True
                
                # 3. Simulate human reading/scrolling
                read_time = random.randint(30, 60)
                self.current_step = f"Cycle {i}/{iterations}: Reading for {read_time}s"
                
                self.simulate_human_scroll(read_time)
                
                success_count += 1
                self.current_step = f"Cycle {i}/{iterations}: Success"
                
            except TimeoutException:
                self.current_step = f"Cycle {i}/{iterations}: Timeout or link not found"
            except Exception as e:
                self.current_step = f"Cycle {i}/{iterations}: General Error: {str(e)}"
            finally:
                self.capture_screenshot()
                self.close_driver()
                self.website_opened = False
                
            # Delay between cycles
            if i < iterations:
                delay = random.randint(10, 20)
                self.current_step = f"Waiting for {delay} seconds..."
                time.sleep(delay)

        self.status = "Completed"
        self.current_step = f"Process finished. Success: {success_count}/{iterations}"
        return success_count

    def simulate_human_scroll(self, duration):
        """Simulate human-like random scrolling for a given duration"""
        start_time = time.time()
        while time.time() - start_time < duration:
            # Scroll down
            scroll_amount = random.randint(200, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.8, 1.5))
            
            # Scroll up slightly sometimes
            if random.random() < 0.2:
                scroll_amount = random.randint(-100, -50)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 1))


    def close_driver(self):
        """Tutup driver Selenium"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

# --- FLASK ROUTES ---

# PERHATIAN: Instance global ini berbahaya untuk multi-user, 
# tetapi dipertahankan agar fungsi /status dan /stop bekerja sesuai desain asli
bot_instance = TrafficBot() 
proxy_manager = ProxyManager() # Gunakan instance proxy manager

@app.route('/')
def index():
    # Asumsi file index.html ada
    return render_template('index.html')

@app.route('/start_traffic', methods=['POST'])
def start_traffic():
    global bot_instance # Pastikan kita menggunakan instance global yang sama
    data = request.json
    
    website_url = data.get('website_url', '').strip()
    keywords = data.get('keywords', '').split(',')
    iterations = int(data.get('iterations', 1))
    
    if bot_instance.status not in ["Idle", "Completed", "Dihentikan oleh pengguna"]:
        return jsonify({"status": "error", "message": "Traffic generation is already running"}), 400
        
    if not website_url or not keywords:
        return jsonify({"status": "error", "message": "Missing website or keywords"}), 400

    # Reset bot instance untuk sesi baru
    bot_instance = TrafficBot() 
    bot_instance.status = "Starting..."

    def run_traffic():
        try:
            # Menggunakan bot_instance.run_traffic_session (tidak ada threading dalam loop ini)
            success_count = bot_instance.run_traffic_session(random.choice(keywords).strip(), website_url, iterations)
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
    global bot_instance
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
    global bot_instance
    bot_instance.status = "Dihentikan oleh pengguna" # Set status agar loop di run_traffic_session berhenti
    bot_instance.close_driver()
    bot_instance.current_step = "Process stopped by user"
    return jsonify({"status": "stopped", "message": "Traffic generation stopped"})

if __name__ == '__main__':
    # Gunakan server yang aman untuk production (Gunicorn, Waitress) 
    # atau tambahkan allow_unsafe_werkzeug=True jika hanya untuk testing
    # app.run(debug=True, host='0.0.0.0', port=5000) 
    # Pilihan umum untuk testing:
    print("Running Flask app in development server. Use gunicorn/waitress for production.")
    app.run(debug=True, host='0.0.0.0', port=5000)
