from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

# --- Paths ---
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
CHROMEDRIVER_PATH = "../docs/chromedriver.exe"  # relative to MoodBoxd.api directory

# --- Scraper Function ---
def scrape_letterboxd_movies(username):
    options = webdriver.ChromeOptions()
    options.binary_location = BRAVE_PATH
    options.add_argument("--window-size=1920,1080")
    # Keep visual for now (helps debug). Switch to headless later.
    # options.add_argument("--headless")

    # Make automation less detectable
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(CHROMEDRIVER_PATH)
    driver = None
    movies = []

    try:
        driver = webdriver.Chrome(service=service, options=options)
        url = f"https://letterboxd.com/{username}/films/"
        print(f"Loading {url}...")
        driver.get(url)

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.poster-grid")))

        # Scroll to load more movies (useful for long lists)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Grab all movies
        movie_elements = driver.find_elements(By.CSS_SELECTOR, "div.poster-grid li.griditem img.image")
        print(f"Found {len(movie_elements)} movies")

        for elem in movie_elements:
            title = elem.get_attribute("alt")
            poster_url = elem.get_attribute("src")
            if title:
                movies.append({"title": title, "poster_url": poster_url})

    except TimeoutException:
        print("Error: Page took too long to load or movies not found.")
        with open("debug_output.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except WebDriverException as e:
        print(f"Selenium error: {e}")
    finally:
        if driver:
            driver.quit()
    return movies

# --- Run/Test Script ---
if __name__ == "__main__":
    username = "aaawhan"  # Replace this
    movie_list = scrape_letterboxd_movies(username)
    if movie_list:
        print("\nMovies scraped successfully:")
        for m in movie_list:
            print(f"• {m['title']} ({m['poster_url']})")
    else:
        print("No movies found.")
