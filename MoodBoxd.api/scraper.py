from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
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
    page_num = 1

    try:
        driver = webdriver.Chrome(service=service, options=options)

        while True:
            url = f"https://letterboxd.com/{username}/films/page/{page_num}/"
            print(f"Loading page {page_num}: {url}")
            driver.get(url)

            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.poster-grid")))

            # Scroll to load all movie posters on current page
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(3):  # scroll down a few times to ensure loading
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Grab all movies on this page
            movie_entries = driver.find_elements(By.CSS_SELECTOR, "div.poster-grid li.griditem")

            for entry in movie_entries:
                img = entry.find_element(By.CSS_SELECTOR, "img.image")
                title = img.get_attribute("alt")
                poster_url = img.get_attribute("src")

                try:
                    rating_span = entry.find_element(By.CSS_SELECTOR, "span.rating")
                    numeric_rating = None
                    for c in rating_span.get_attribute("class").split():
                        if c.startswith("rated-"):
                            numeric_rating = int(c.replace("rated-", "")) / 2.0
                            break
                except:
                    numeric_rating = None

                movies.append({
                    "title": title,
                    "poster_url": poster_url,
                    "user_rating": numeric_rating
                })



            # Check if "next" page exists; if not, break loop
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a.next")
                if not next_button.is_displayed():
                    break
            except NoSuchElementException:
                break

            page_num += 1

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
