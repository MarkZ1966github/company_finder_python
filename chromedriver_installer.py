import os
import platform
import logging
import subprocess
from shutil import which
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger('ChromeDriverInstaller')

def is_chrome_installed():
    """Check if Chrome is installed on the system"""
    if platform.system() == "Darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                logger.info(f"Chrome found at: {path}")
                return True
    elif platform.system() == "Windows":
        chrome_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Google\\Chrome\\Application\\chrome.exe')
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                logger.info(f"Chrome found at: {path}")
                return True
    else:  # Linux and others
        if which('google-chrome') is not None or which('chromium-browser') is not None:
            logger.info("Chrome found in PATH")
            return True
    
    logger.warning("Google Chrome not found on system")
    return False

def get_chrome_version():
    """Get the Chrome version if installed"""
    if not is_chrome_installed():
        return None
    
    try:
        if platform.system() == "Darwin":  # macOS
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if not os.path.exists(chrome_path):
                chrome_path = os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            
            output = subprocess.check_output([chrome_path, "--version"], stderr=subprocess.STDOUT)
            version = output.decode('utf-8').strip().split(' ')[-1]
            logger.info(f"Chrome version: {version}")
            return version
        elif platform.system() == "Windows":
            # Windows version detection requires registry query or more complex handling
            return None
        else:  # Linux
            output = subprocess.check_output(["google-chrome", "--version"], stderr=subprocess.STDOUT)
            version = output.decode('utf-8').strip().split(' ')[-1]
            logger.info(f"Chrome version: {version}")
            return version
    except Exception as e:
        logger.warning(f"Error detecting Chrome version: {e}")
        return None

def setup_chrome_driver():
    """Set up Chrome driver using multiple fallback methods"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    if not is_chrome_installed():
        logger.warning("Chrome not installed. Cannot set up ChromeDriver.")
        return None
    
    # Try multiple methods to set up ChromeDriver
    methods = [
        setup_with_webdriver_manager,
        setup_with_cached_driver,
        setup_with_direct_chrome
    ]
    
    for method in methods:
        try:
            logger.info(f"Trying Chrome setup method: {method.__name__}")
            driver = method(chrome_options)
            if driver:
                logger.info(f"Chrome driver setup successfully using {method.__name__}")
                return driver
        except Exception as e:
            logger.warning(f"{method.__name__} failed: {e}")
    
    logger.error("All ChromeDriver setup methods failed")
    return None

def setup_with_webdriver_manager(chrome_options):
    """Setup Chrome using webdriver-manager"""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        return driver
    except Exception as e:
        logger.warning(f"ChromeDriverManager setup failed: {e}")
        return None

def setup_with_cached_driver(chrome_options):
    """Setup Chrome using cached driver path"""
    try:
        home_dir = os.path.expanduser("~")
        # Check multiple possible paths for cached ChromeDriver
        possible_paths = [
            os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "mac64", "latest", "chromedriver"),
            os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "mac_arm64", "latest", "chromedriver"),
            os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "mac64_m1", "latest", "chromedriver"),
            os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "win32", "latest", "chromedriver.exe"),
            os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "linux64", "latest", "chromedriver")
        ]
        
        for driver_path in possible_paths:
            if os.path.exists(driver_path):
                logger.info(f"Found cached ChromeDriver at: {driver_path}")
                driver = webdriver.Chrome(
                    service=Service(driver_path),
                    options=chrome_options
                )
                return driver
        
        return None
    except Exception as e:
        logger.warning(f"Cached driver setup failed: {e}")
        return None

def setup_with_direct_chrome(chrome_options):
    """Try direct Chrome setup as last resort"""
    try:
        logger.info("Attempting direct Chrome setup")
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.warning(f"Direct Chrome setup failed: {e}")
        return None