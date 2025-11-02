from flask import Flask, render_template, request, jsonify
import threading
import time
import random
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-123')

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
                logger.info(f"Active proxy: {proxy}")
        
        return len(self.active_proxies) > 0
    
    def setup_driver(self, proxy=None):
        """Menyiapkan Chrome driver dengan konfigurasi untuk Render"""
        chrome_options = Options()
        
        # Konfigurasi untuk environment Render
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        
        # User agent acak
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
        
        try:
            # Untuk Render, kita perlu menggunakan ChromeDriver yang sudah tersedia
            chrome_options.binary_location = '/usr/bin/google-chrome'
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def simulate_traffic(self):
        """Simulasi traffic yang disederhanakan untuk demo"""
        try:
            self.status = "Starting traffic simulation"
            active_sessions[self.session_id] = self.status
            
            # Simulasi proses step-by-step
            steps = [
                "Checking data leak protection",
                "Opening target website",
                "Performing Google search",
                "Clicking top result",
                "Scrolling page content",
                "Simulating user behavior",
                "Closing ads if any",
                "Returning to homepage"
            ]
            
            for step in steps:
                self.status = step
                active_sessions[self.session_id] = self.status
                time.sleep(2)  # Simulasi delay
                
            self.status = "Traffic simulation completed successfully"
            active_sessions[self.session_id] = self.status
            
            return True
            
        except Exception as e:
            self.status = f"Error during simulation: {str(e)}"
            active_sessions[self.session_id] = self.status
            logger.error(f"Simulation error: {e}")
            return False
    
    def run_session(self):
        """Menjalankan sesi traffic"""
        try:
            # Cek proxy yang aktif
            if not self.check_proxies():
                self.status = "No active proxies found"
                active_sessions[self.session_id] = self.status
                return
            
            # Setup browser dengan proxy acak
            proxy = random.choice(self.active_proxies)
            if not self.setup_driver(proxy):
                self.status = "Failed to setup browser"
                active_sessions[self.session_id] = self.status
                return
            
            # Jalankan simulasi traffic
            self.simulate_traffic()
            
        except Exception as e:
            self.status = f"Session error: {str(e)}"
            active_sessions[self.session_id] = self.status
            logger.error(f"Session error: {e}")
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

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
        return jsonify({'error': 'Proxies and target URL are required'}), 400
    
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
