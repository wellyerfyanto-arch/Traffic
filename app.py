from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import requests
import time
import random
import threading
import json
import os
import re

app = Flask(__name__)

# Inisialisasi User Agent
ua = UserAgent()

def validate_proxy(proxy):
    """Validasi format proxy"""
    patterns = [
        r'^\d+\.\d+\.\d+\.\d+:\d+$',  # IP:PORT
        r'^https?://\d+\.\d+\.\d+\.\d+:\d+$',  # http://IP:PORT
        r'^https?://[a-zA-Z0-9.-]+:\d+$',  # http://domain.com:PORT
    ]
    
    for pattern in patterns:
        if re.match(pattern, proxy.strip()):
            return True
    return False

def format_proxy(proxy):
    """Format proxy ke bentuk yang benar"""
    proxy = proxy.strip()
    if not proxy.startswith(('http://', 'https://')):
        proxy = 'http://' + proxy
    return proxy

def check_ip_leak(driver):
    """Cek kebocoran IP address"""
    try:
        driver.get("https://api.ipify.org?format=json")
        time.sleep(2)
        ip_element = driver.find_element(By.TAG_NAME, "pre")
        ip_data = json.loads(ip_element.text)
        return ip_data["ip"]
    except:
        return None

def setup_driver_with_proxy(proxy_list):
    """Setup Chrome driver dengan proxy dan user agent acak"""
    chrome_options = Options()
    
    # Setup headless
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Random user agent
    user_agent = ua.random
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    # Random proxy jika tersedia
    if proxy_list and len(proxy_list) > 0:
        proxy = random.choice(proxy_list)
        chrome_options.add_argument(f"--proxy-server={proxy}")
    else:
        proxy = "No Proxy"
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver, proxy, user_agent

def simulate_traffic(url, proxy_list, session_data):
    """Simulasi traffic otomatis"""
    try:
        # Setup driver
        driver, proxy, user_agent = setup_driver_with_proxy(proxy_list)
        session_data['status'] = 'Setting up browser...'
        session_data['proxy'] = proxy
        session_data['user_agent'] = user_agent
        
        # Cek kebocoran data
        session_data['status'] = 'Checking IP leak...'
        current_ip = check_ip_leak(driver)
        
        if current_ip:
            session_data['ip_address'] = current_ip
            session_data['status'] = f'IP Check: {current_ip} - Proceeding...'
            
            # Simpan detail session
            session_data['details'] = {
                'proxy': proxy,
                'user_agent': user_agent,
                'ip_address': current_ip
            }
        else:
            session_data['status'] = 'IP check failed, trying without proxy...'
            # Coba tanpa proxy
            driver.quit()
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={user_agent}")
            driver = webdriver.Chrome(options=chrome_options)
            session_data['status'] = 'Retrying without proxy...'
        
        # Buka URL target
        session_data['status'] = f'Opening URL: {url}'
        driver.get(url)
        time.sleep(random.uniform(3, 7))
        
        # Cari dan klik postingan acak
        session_data['status'] = 'Looking for posts...'
        posts = driver.find_elements(By.CSS_SELECTOR, 
            "a[href*='/p/'], a[href*='/post/'], article a, .post-title a, h2 a, h3 a, .entry-title a")
        
        if posts:
            random_post = random.choice(posts[:10])  # Batasi 10 post pertama
            try:
                post_url = random_post.get_attribute("href")
                session_data['status'] = f'Clicking post: {post_url[:50]}...'
                driver.get(post_url)
                time.sleep(random.uniform(4, 8))
            except:
                session_data['status'] = 'Failed to click post, continuing...'
        else:
            session_data['status'] = 'No posts found, performing alternative actions...'
        
        # Coba tutup iklan Google jika ada
        try:
            close_selectors = [
                "[aria-label*='close']", "[aria-label*='tutup']",
                "[class*='close']", "[class*='dismiss']",
                ".close-btn", ".ads-close", ".ad-close",
                "button[class*='close']", "div[class*='close']"
            ]
            
            for selector in close_selectors:
                try:
                    close_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in close_buttons[:2]:
                        if btn.is_displayed():
                            btn.click()
                            session_data['status'] = 'Ad closed successfully'
                            time.sleep(2)
                            break
                except:
                    continue
        except:
            session_data['status'] = 'No ads found or unable to close'
        
        # Simulasi scrolling yang lebih realistis
        scroll_patterns = [
            ("Scrolling down slowly...", random.randint(200, 500), random.uniform(2, 4)),
            ("Scrolling up a bit...", -random.randint(100, 300), random.uniform(1, 3)),
            ("Scrolling to bottom...", "bottom", random.uniform(3, 6)),
            ("Random scrolling...", random.randint(-200, 400), random.uniform(1, 2)),
            ("Final scroll...", "bottom", random.uniform(2, 4))
        ]
        
        for action_name, scroll_amount, delay in scroll_patterns:
            session_data['status'] = action_name
            
            if scroll_amount == "bottom":
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            else:
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            time.sleep(delay)
        
        # Kembali ke home
        session_data['status'] = 'Returning to homepage...'
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        
        session_data['status'] = 'Session completed successfully 🎉'
        session_data['completed'] = True
        
    except Exception as e:
        session_data['status'] = f'Error: {str(e)}'
        session_data['error'] = True
        session_data['error_message'] = str(e)
    
    finally:
        try:
            driver.quit()
        except:
            pass

# Store active sessions
active_sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_traffic', methods=['POST'])
def start_traffic():
    data = request.json
    url = data.get('url')
    session_count = data.get('session_count', 1)
    custom_proxies = data.get('proxies', '')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Process proxy list
    proxy_list = []
    if custom_proxies:
        proxy_lines = [p.strip() for p in custom_proxies.split('\n') if p.strip()]
        for proxy in proxy_lines:
            if validate_proxy(proxy):
                proxy_list.append(format_proxy(proxy))
    
    session_ids = []
    for i in range(session_count):
        session_id = f"session_{int(time.time())}_{i}"
        session_data = {
            'id': session_id,
            'url': url,
            'status': 'Initializing...',
            'started_at': time.time(),
            'completed': False,
            'error': False,
            'proxy': None,
            'user_agent': None,
            'ip_address': None,
            'details': {}
        }
        
        active_sessions[session_id] = session_data
        session_ids.append(session_id)
        
        # Jalankan di thread terpisah
        thread = threading.Thread(
            target=simulate_traffic, 
            args=(url, proxy_list, session_data)
        )
        thread.daemon = True
        thread.start()
    
    return jsonify({
        'message': f'Started {session_count} session(s)',
        'session_ids': session_ids,
        'proxies_used': len(proxy_list)
    })

@app.route('/session_status/<session_id>')
def session_status(session_id):
    session_data = active_sessions.get(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify(session_data)

@app.route('/active_sessions')
def get_active_sessions():
    active_count = len([s for s in active_sessions.values() if not s.get('completed') and not s.get('error')])
    completed_count = len([s for s in active_sessions.values() if s.get('completed')])
    error_count = len([s for s in active_sessions.values() if s.get('error')])
    
    return jsonify({
        'sessions': list(active_sessions.keys()),
        'counts': {
            'active': active_count,
            'completed': completed_count,
            'error': error_count,
            'total': len(active_sessions)
        }
    })

@app.route('/clear_sessions')
def clear_sessions():
    completed_sessions = [k for k, v in active_sessions.items() if v.get('completed') or v.get('error')]
    for session_id in completed_sessions:
        del active_sessions[session_id]
    
    return jsonify({
        'message': f'Cleared {len(completed_sessions)} sessions',
        'remaining': len(active_sessions)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
