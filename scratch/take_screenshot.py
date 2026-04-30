import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def take_screenshot():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    
    try:
        # Go to login page
        driver.get('http://127.0.0.1:5006/login')
        time.sleep(2)
        
        # Login
        driver.find_element(By.NAME, 'email').send_keys('admin@oriflame.com')
        driver.find_element(By.NAME, 'password').send_keys('admin123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(2)
        
        # Go to products page
        driver.get('http://127.0.0.1:5006/oriflame-admin-panel-x9k2/products')
        time.sleep(2)
        
        # Click "Add New Product"
        add_btn = driver.find_element(By.CSS_SELECTOR, '.admin-btn-primary')
        add_btn.click()
        time.sleep(1)
        
        # Take screenshot of the modal
        driver.save_screenshot('c:\\Users\\nilad\\.gemini\\antigravity\\brain\\3b787514-a795-41bd-a1c9-a09646db2ce6\\artifacts\\modal_screenshot.png')
        print("Screenshot saved to artifacts/modal_screenshot.png")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == '__main__':
    take_screenshot()
