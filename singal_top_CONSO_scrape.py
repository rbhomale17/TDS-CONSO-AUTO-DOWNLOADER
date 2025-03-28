from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
import time
import os
import tempfile
import pytesseract
from PIL import Image
import io
import requests

def solve_captcha(driver):
    # Get captcha image
    captcha_img = driver.find_element(By.ID, "captchaImg")
    
    # Take screenshot of captcha
    captcha_img.screenshot("captcha.png")
    
    print("Captcha saved. Please check captcha.png and enter the captcha text:")
    captcha_text = input("Enter captcha: ")
    
    try:
        return captcha_text.strip()
    finally:
        # Clean up the temporary file
        if os.path.exists("captcha.png"):
            os.remove("captcha.png")

def login(driver, username, password, tan):
    try:
        # Select Deductor radio button
        deductor_radio = driver.find_element(By.ID, "ded")
        deductor_radio.click()
        time.sleep(1)
        
        # Fill in username
        username_field = driver.find_element(By.ID, "userId")
        username_field.clear()
        username_field.send_keys(username)
        time.sleep(1)
        
        # Fill in password
        password_field = driver.find_element(By.ID, "psw")
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)
        
        # Fill in TAN
        tan_field = driver.find_element(By.ID, "tanpan")
        tan_field.clear()
        tan_field.send_keys(tan)
        time.sleep(1)
        
        # Wait for captcha to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "captchaImg"))
        )
        
        # Get manual captcha input
        captcha_text = solve_captcha(driver)
        if captcha_text:
            captcha_field = driver.find_element(By.ID, "captcha")
            captcha_field.clear()
            captcha_field.send_keys(captcha_text)
            time.sleep(1)
            
            # Click login button
            login_button = driver.find_element(By.ID, "clickLogin")
            login_button.click()
            
            # Wait for redirect after login
            time.sleep(5)
            
            # Check if we're logged in by looking for a unique element
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "welcomeMenu"))
                )
                print("Login successful!")
                return True
            except TimeoutException:
                print("Login unsuccessful - welcome menu not found")
                return False
                
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

def download_tds_file():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Create a temporary directory for user data
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
    
    # Set up download directory
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    
    try:
        # Initialize Chrome driver with options
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to login page
        driver.get("https://www.tdscpc.gov.in/app/login.xhtml?usr=Ded")
        time.sleep(2)
        
        # Attempt login with provided credentials
        username = "YOUR_USERNAME"
        password = "YOUR_PASSWORD"
        tan = "YOUR_TAN_NUMBER"
        
        if login(driver, username, password, tan):
            print("Navigating to downloads page...")
            
            # Handle any popups after login
            try:
                paperless_no = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.NAME, "j_id1610532955_33b1d17f:nobtn"))
                )
                paperless_no.click()
                time.sleep(2)
            except:
                print("No popup found or popup already handled")
            
            # Navigate to downloads through menu
            try:
                # Click Downloads menu
                downloads_menu = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Downloads')]"))
                )
                downloads_menu.click()
                time.sleep(1)
                
                # Click Requested Downloads
                requested_downloads = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Requested Downloads')]"))
                )
                requested_downloads.click()
                time.sleep(3)
                
                # Click the View All radio button
                print("Selecting View All option...")
                view_all_radio = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "search3"))
                )
                view_all_radio.click()
                time.sleep(2)  # Short wait for the grid to update
                
                # Wait for the downloads grid
                print("Waiting for downloads grid...")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "reqList"))
                )
                
                # Click on first row of the grid
                first_row = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//table[@id='reqList']//tr[2]"))
                )
                first_row.click()
                
                # Click HTTP Download button
                download_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "downloadhttp"))
                )
                download_btn.click()
                
                # Wait for download to complete
                time.sleep(5)
                
                print(f"Download initiated successfully! Files will be saved to: {download_dir}")
                
            except Exception as e:
                print(f"Error during download navigation: {str(e)}")
                
        else:
            print("Login failed!")
            
    except TimeoutException:
        print("Timeout waiting for element. Please check your internet connection or site availability.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        input("Press Enter to close the browser...")
        driver.quit()
        # Clean up the temporary directory
        try:
            import shutil
            shutil.rmtree(user_data_dir)
        except:
            pass

if __name__ == "__main__":
    download_tds_file() 