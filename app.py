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
import os

app = Flask(__name__)

class ProxyManager:
    def __init__(self):
        self.proxy_list = []
        self.working_proxies = []
        self.load_proxies()
        
    def load_proxies(self):
        """Load proxies from file"""
        try:
            if os.path.exists('proxies.txt'):
                with open('proxies.txt', 'r') as f:
                    self.proxy_list = [line.strip() for line in f if line.strip()]
            else:
                self.proxy_list = []
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
            return []
            
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
        
    def setup_driver(self, proxy=None):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Random user agent
            ua = UserAgent()
            user_agent = ua.chrome
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            if proxy:
                chrome_options.add_argument(f'--proxy-server={proxy}')
                self.proxy = proxy
                self.current_step = f"Using proxy: {proxy}"
            
            # Setup Chrome driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except Exception as e:
            self.status = f"Error setting up driver: {str(e)}"
            return False
    
    def check_ip_leak(self):
        try:
            self.current_step = "Checking IP leak..."
            self.driver.get("https://api.ipify.org?format=json")
            time.sleep(3)
            page_source = self.driver.page_source
            return "ip" in page_source.lower()
        except:
            return False
    
    def accept_cookies(self):
        """Handle cookie consent dialogs"""
        try:
            cookie_selectors = [
                "button#L2AGLb",
                "button[aria-label*='Accept all']",
                "button[onclick*='cookie']",
                "//button[contains(., 'Accept all')]",
                "//button[contains(., 'I agree')]"
            ]
            
            for selector in cookie_selectors:
                try:
                    if selector.startswith("//"):
                        element = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    element.click()
                    self.current_step = "Cookie dialog accepted"
                    time.sleep(1)
                    return True
                except:
                    continue
            return False
        except:
            return False

    def perform_search_flow(self, keyword, website_url):
        try:
            self.website_opened = False
            
            # Step 1: Buka Google
            self.current_step = "Opening Google.com..."
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(3, 5))
            
            # Accept cookies
            self.accept_cookies()
            
            # Step 2: Cari search box
            self.current_step = f"Typing keyword: '{keyword}'..."
            
            search_box = None
            search_selectors = [
                "textarea[name='q']",
                "input[name='q']",
                "textarea[title='Search']",
                "input[title='Search']"
            ]
            
            for selector in search_selectors:
                try:
                    search_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not search_box:
                self.current_step = "Cannot find search box"
                return False
            
            # Type keyword
            search_box.clear()
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            time.sleep(1)
            
            # Step 3: Search
            self.current_step = "Performing search..."
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(4, 7))
            
            # Step 4: Find and click first result
            self.current_step = "Finding top search result..."
            
            # Wait for results
            result_selectors = [
                "div.g",
                "div.tF2Cxc",
                "div.rc"
            ]
            
            search_results = []
            for selector in result_selectors:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    search_results = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if search_results:
                        break
                except:
                    continue
            
            if not search_results:
                self.current_step = "No search results found"
                return False
            
            # Get first result
            first_result = search_results[0]
            link_element = None
            
            # Find link in first result
            link_strategies = [
                lambda: first_result.find_element(By.TAG_NAME, "a"),
                lambda: first_result.find_element(By.CSS_SELECTOR, "a"),
                lambda: self.driver.find_element(By.CSS_SELECTOR, "div.g a:first-child")
            ]
            
            for strategy in link_strategies:
                try:
                    link_element = strategy()
                    if link_element:
                        href = link_element.get_attribute("href")
                        if href and ("http" in href):
                            break
                        else:
                            link_element = None
                except:
                    continue
            
            if link_element:
                href = link_element.get_attribute("href")
                self.current_step = f"Clicking link: {href[:50]}..."
                
                # Click the link
                self.driver.execute_script("arguments[0].click();", link_element)
                time.sleep(random.uniform(6, 10))
                
                # Check if we left Google
                current_url = self.driver.current_url
                if "google.com" not in current_url:
                    self.website_opened = True
                    self.current_step = f"Success! Opened website: {current_url[:50]}..."
                    
                    # Scroll the page
                    self.perform_scrolling()
                    
                    return True
                else:
                    self.current_step = "Still on Google after click"
                    return False
            else:
                self.current_step = "Could not find clickable link"
                return False
                
        except Exception as e:
            self.current_step = f"Error in search flow: {str(e)}"
            return False
    
    def perform_scrolling(self):
        """Natural scrolling behavior"""
        try:
            self.current_step = "Scrolling page..."
            
            # Scroll down
            scroll_points = [300, 600, 900, 1200, 1500]
            for point in scroll_points:
                self.driver.execute_script(f"window.scrollTo(0, {point});")
                time.sleep(random.uniform(1, 2))
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
        except Exception as e:
            self.current_step = f"Scrolling issue: {str(e)}"
    
    def run_traffic_session(self, keyword, website_url, iterations):
        self.total_iterations = iterations
        session_success = 0
        
        for i in range(iterations):
            self.current_iteration = i + 1
            self.status = f"Running iteration {i+1}/{iterations}"
            
            # Setup driver
            current_proxy = None
            if self.proxy_manager.working_proxies:
                current_proxy = self.proxy_manager.get_random_working_proxy()
            
            self.close_driver()
            
            if current_proxy:
                self.current_step = f"Using proxy: {current_proxy}"
                if not self.setup_driver(current_proxy):
                    self.current_step = "Proxy failed, trying direct connection..."
                    if not self.setup_driver():
                        continue
            else:
                self.current_step = "Using direct connection"
                if not self.setup_driver():
                    continue
            
            # Verify connection
            try:
                self.current_step = "Verifying connection..."
                self.driver.get("https://www.google.com")
                time.sleep(2)
            except:
                self.current_step = "Connection failed"
                continue
            
            # Run search flow
            success = self.perform_search_flow(keyword, website_url)
            
            if success and self.website_opened:
                session_success += 1
                self.current_step = f"Iteration {i+1} successful"
            else:
                self.current_step = f"Iteration {i+1} failed"
            
            # Delay between iterations
            if i < iterations - 1:
                delay = random.uniform(15, 30)
                self.current_step = f"Waiting {int(delay)}s before next iteration..."
                time.sleep(delay)
        
        self.status = f"Completed: {session_success}/{iterations} successful"
        self.current_step = "Traffic generation finished"
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
            return jsonify({"status": "success", "message": f"Saved {len(proxies_list)} proxies"})
        else:
            return jsonify({"status": "error", "message": "Failed to save proxies"})
    
    return jsonify({"status": "error", "message": "No proxies provided"})

@app.route('/start_traffic', methods=['POST'])
def start_traffic():
    data = request.json
    keyword = data.get('keyword', '').strip()
    website_url = data.get('website_url', '').strip()
    iterations = data.get('iterations', 1)
    
    if not keyword:
        return jsonify({"status": "error", "message": "Keyword is required"})
    
    if not website_url:
        return jsonify({"status": "error", "message": "Website URL is required"})
    
    # Reset status
    bot_instance.status = "Starting..."
    bot_instance.current_step = "Initializing session..."
    bot_instance.website_opened = False
    
    def run_traffic():
        try:
            success_count = bot_instance.run_traffic_session(keyword, website_url, iterations)
            bot_instance.status = f"Finished: {success_count}/{iterations} successful"
            bot_instance.current_step = "Process completed"
        except Exception as e:
            bot_instance.status = f"Error: {str(e)}"
            bot_instance.current_step = f"Process failed: {str(e)}"
        finally:
            bot_instance.close_driver()
    
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
        "website_opened": bot_instance.website_opened
    })

@app.route('/stop_traffic', methods=['POST'])
def stop_traffic():
    bot_instance.close_driver()
    bot_instance.status = "Stopped by user"
    bot_instance.current_step = "Process stopped"
    return jsonify({"status": "stopped", "message": "Traffic generation stopped"})

if __name__ == '__main__':
    print("Starting Google Traffic Generator...")
    proxy_manager.get_working_proxies()
    app.run(host='0.0.0.0', port=5000, debug=False)
