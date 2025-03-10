from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ChromeTest')

print('Setting up Chrome driver...')
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

try:
    # Try with version="latest"
    print("Trying ChromeDriverManager with version='latest'")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager(version="latest").install()),
        options=options
    )
    print('Chrome driver setup successful with version="latest"!')
    driver.quit()
except Exception as e:
    print(f'Chrome driver setup failed with version="latest": {e}')
    
    try:
        # Try without specifying version
        print("Trying ChromeDriverManager without version parameter")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        print('Chrome driver setup successful without version parameter!')
        driver.quit()
    except Exception as e:
        print(f'Chrome driver setup failed without version parameter: {e}')
        
        try:
            # Try with a specific version
            print("Trying ChromeDriverManager with specific version='114.0.5735.90'")
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager(version="114.0.5735.90").install()),
                options=options
            )
            print('Chrome driver setup successful with specific version!')
            driver.quit()
        except Exception as e:
            print(f'Chrome driver setup failed with specific version: {e}')