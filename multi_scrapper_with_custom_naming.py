from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.options import Options
import time
import os
import tempfile
import pytesseract
from PIL import Image
import io
import requests
from urllib.parse import urljoin
import os
import zipfile
import shutil
from pathlib import Path


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


def download_tds_file(username: str, password: str, tan: str, downloads_dir: str):
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Create a temporary directory for user data
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    # Set up download directory - Fix path handling
    download_dir = os.path.abspath(os.path.join(os.getcwd(), downloads_dir))
    os.makedirs(download_dir, exist_ok=True)

    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )

    try:
        # Initialize Chrome driver with options
        driver = webdriver.Chrome(options=chrome_options)

        # Navigate to login page
        driver.get("https://www.tdscpc.gov.in/app/login.xhtml?usr=Ded")
        time.sleep(2)

        if login(driver, username, password, tan):
            print("Navigating to downloads page...")

            # Handle any popups after login
            try:
                paperless_no = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.NAME, "j_id1610532955_33b1d17f:nobtn")
                    )
                )
                paperless_no.click()
                time.sleep(2)
            except:
                print("No popup found or popup already handled")

            # Navigate to downloads through menu
            try:
                # Click Downloads menu
                downloads_menu = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//span[contains(text(),'Downloads')]")
                    )
                )
                downloads_menu.click()
                time.sleep(1)

                # Click Requested Downloads
                requested_downloads = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//a[contains(text(),'Requested Downloads')]")
                    )
                )
                requested_downloads.click()
                time.sleep(3)

                # Get the session cookies from Selenium
                selenium_cookies = driver.get_cookies()
                cookies = {
                    cookie["name"]: cookie["value"] for cookie in selenium_cookies
                }

                # Create a requests session with the same cookies
                session = requests.Session()
                session.cookies.update(cookies)

                # Base URL
                base_url = "https://www.tdscpc.gov.in"

                # Get downloads list
                print("Fetching downloads list...")
                downloads_url = urljoin(base_url, "/app/srv/GetReqListServlet")

                # Initialize page number and get first page
                page = 1
                while True:
                    params = {
                        "reqtype": 0,
                        "_search": "false",
                        "nd": int(time.time() * 1000),
                        "rows": 30,
                        "page": page,
                        "sidx": "reqNo",
                        "sord": "asc",
                    }

                    response = session.get(downloads_url, params=params)
                    downloads_data = response.json()

                    total_pages = int(downloads_data.get("totalpages", 0))
                    current_page = int(downloads_data.get("page", "1"))
                    total_rows = int(downloads_data.get("rowCount", 0))

                    print(
                        f"Processing page {current_page} of {total_pages} (Total records: {total_rows})"
                    )

                    # Process each available download on current page
                    for row in downloads_data["rows"]:
                        if (
                            row["status"] == "Available"
                            and row.get("dntype") == "NSDL Conso File"
                        ):
                            req_no = row["reqNo"]
                            fin_year = row.get("finYr", "")
                            quarter = row.get("qrtr", "")
                            form_type = row.get("frmType", "")

                            print(
                                f"Downloading NSDL Conso File request {req_no} ({form_type} {fin_year} {quarter})..."
                            )

                            try:
                                # First get the download URL
                                download_url = urljoin(
                                    base_url, "/app/srv/DownloadServlet"
                                )
                                form_data = {"reqNo": str(req_no)}

                                # Get the actual download URL
                                url_response = session.post(
                                    download_url, data=form_data
                                )
                                url_data = url_response.json()

                                print(
                                    f"Status code URL RESPONSE: {url_response.status_code}"
                                )
                                if "success" in url_data[0]:
                                    actual_download_url = url_data[0]["success"]
                                    filename = actual_download_url.split("/")[-1]
                                    custom_filename = f"{tan}_{str(req_no)}{os.path.splitext(filename)[1]}"
                                    print(f"Filename: {filename}")
                                    print(f"Filename Custom: {custom_filename}")

                                    # Download the file from the actual URL
                                    file_response = session.get(
                                        actual_download_url, stream=True
                                    )

                                    if file_response.status_code == 200:
                                        # Fix path handling for file saving
                                        file_path = os.path.abspath(os.path.join(
                                            download_dir, custom_filename
                                        ))
                                        # Ensure the directory exists
                                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                        
                                        with open(file_path, "wb") as f:
                                            for chunk in file_response.iter_content(
                                                chunk_size=8192
                                            ):
                                                if chunk:
                                                    f.write(chunk)
                                        print(
                                            f"Successfully downloaded: {custom_filename}"
                                        )
                                    else:
                                        print(
                                            f"Failed to download file for request {req_no}. Status code: {file_response.status_code}"
                                        )

                                time.sleep(2)  # Small delay between downloads

                            except Exception as e:
                                print(f"Error downloading request {req_no}: {str(e)}")
                                continue

                    # Check if we've processed all pages
                    if page >= total_pages:
                        break

                    # Move to next page
                    page += 1
                    time.sleep(10)  # Small delay between pages

                print(f"Download completed! Files saved to: {download_dir}")

            except Exception as e:
                print(f"Error during download navigation: {str(e)}")

        else:
            print("Login failed!")

    except TimeoutException:
        print(
            "Timeout waiting for element. Please check your internet connection or site availability."
        )
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        print("Closing browser...")
        driver.quit()

        # Clean up the temporary directory
        try:
            import shutil

            shutil.rmtree(user_data_dir)
        except:
            pass


def process_downloads(downloads_dir: str, tds_files_dir: str, extracted_dir: str):
    # Define directories
    downloads_dir = os.path.join(os.getcwd(), downloads_dir)
    extracted_dir = os.path.join(os.getcwd(), extracted_dir)
    tds_files_dir = os.path.join(os.getcwd(), tds_files_dir)

    # Create necessary directories
    os.makedirs(extracted_dir, exist_ok=True)
    os.makedirs(tds_files_dir, exist_ok=True)

    # Process each zip file in downloads directory
    for zip_file in Path(downloads_dir).glob("*.zip"):
        try:
            print(f"Processing {zip_file.name}")

            # Create a unique extraction directory for this zip
            zip_extract_dir = os.path.join(extracted_dir, zip_file.stem)
            os.makedirs(zip_extract_dir, exist_ok=True)

            # Get password from filename (remove .zip extension)
            password = zip_file.stem.encode("utf-8")  # Convert to bytes for zipfile
            print(f"Password: {password}")
            # Extract the zip file with password
            try:
                with zipfile.ZipFile(zip_file, "r") as zip_ref:
                    zip_ref.extractall(zip_extract_dir, pwd=password)
            except RuntimeError as e:
                if "Bad password" in str(e):
                    print(f"Failed to extract with password: {zip_file.stem}")
                    continue
                raise e

            # Find and move .tds files
            for tds_file in Path(zip_extract_dir).rglob("*.tds"):
                # Keep original filename but move to tds_files directory
                new_tds_path = os.path.join(tds_files_dir, tds_file.name)

                # If file already exists, add a number to the filename
                counter = 1
                while os.path.exists(new_tds_path):
                    base_name = tds_file.stem
                    new_tds_path = os.path.join(
                        tds_files_dir, f"{base_name}_{counter}.tds"
                    )
                    counter += 1

                # Move the .tds file
                shutil.move(str(tds_file), new_tds_path)
                print(f"Moved {tds_file.name} to {new_tds_path}")

            # Clean up extracted directory
            shutil.rmtree(zip_extract_dir)
            print(f"Cleaned up temporary directory: {zip_extract_dir}")

        except Exception as e:
            print(f"Error processing {zip_file.name}: {str(e)}")

    print(f"\nProcessing complete!")
    print(f"TDS files are stored in: {tds_files_dir}")


if __name__ == "__main__":
    # Attempt login with provided credentials
    username = "YOUR_USERNAME"
    password = "YOUR_PASSWORD"
    tan = "YOUR_TAN_NUMBER"

    downloads_dir = f"downloads/{tan}_CONSO"

    # Download TDS files
    download_tds_file(username, password, tan, downloads_dir)

    # Process downloaded zip files
    print("Starting to process downloaded zip files...")
    process_downloads(
        downloads_dir=downloads_dir,
        tds_files_dir=f"tds_files/{tan}_CONSO",
        extracted_dir=f"extracted/{tan}",
    )
    print("Finished processing downloaded zip files.")
