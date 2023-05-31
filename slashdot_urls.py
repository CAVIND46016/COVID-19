import time
import json
import re
from http.client import RemoteDisconnected
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


def get_browser(
    headless=False,
    incognito=False,
    sandbox=False,
    extensions=False,
    notifications=False,
    dev_shm_usage=False,
):
    """
    Creates and returns a Selenium WebDriver instance for Chrome.

    :param headless: Whether to run Chrome in headless mode (without GUI).
    :param incognito: Whether to launch Chrome in incognito mode.
    :param sandbox: Whether to disable the sandbox for Chrome.
    :param extensions: Whether to disable Chrome extensions.
    :param notifications: Whether to disable Chrome notifications.
    :param dev_shm_usage: Whether to disable the use of /dev/shm for shared memory in Chrome.
    :return: Selenium WebDriver instance for Chrome.
    """

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")

    if incognito:
        chrome_options.add_argument("--incognito")

    if not sandbox:
        chrome_options.add_argument("--no-sandbox")

    if not extensions:
        chrome_options.add_argument("--disable-extensions")

    if not notifications:
        chrome_options.add_argument("--disable-notifications")

    if not dev_shm_usage:
        chrome_options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(
        executable_path="/path/to/chromedriver",
        options=chrome_options
    )


def main():
    driver = get_browser(headless=False, incognito=True)

    page_num = 0

    kwd_match = lambda kwd: re.compile(f"{'|'.join(kwd)}", flags=re.IGNORECASE).search
    keywords = ['covid', 'coronavirus', 'wuhan', 'ncov']

    url_dict = {}
    while True:
        stop_loop = False
        page_url = f"https://slashdot.org/?page={page_num}"
        print(f"Processing page no. {page_num}...")

        try:
            driver.set_page_load_timeout(40)
            driver.get(page_url)
        except TimeoutException:
            print(f"\t{page_url} - Timed out receiving message from renderer")
            continue
        except RemoteDisconnected:
            print(f"\tError 404: {page_url} not found.")
            continue

        WebDriverWait(driver, timeout=40).until(
            expected_conditions.presence_of_element_located(
                (
                    By.CLASS_NAME, "paginate")
            )
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        story_list = soup.find(
            "div",
            attrs={
                "id": "firehoselist"
            }
        ).find_all(
            "article",
            attrs={
                "id": re.compile("firehose-")
            }
        )

        for story in story_list:
            title_tag = story.find("span", attrs={"class": "story-title"})
            if not title_tag:
                continue

            title_id = title_tag['id'].replace("title-", "")
            time_tag = story.find("time", attrs={"id": f"fhtime-{title_id}"})
            date_obj = datetime.strptime(
                time_tag['datetime'], "on %A %B %d, %Y @%I:%M%p"
            ).strftime("%Y-%m-%d")

            if date_obj < '2020-01-19':
                stop_loop = True
                break

            story_url = title_tag.find("a")['href']
            if not kwd_match(keywords)(story_url):
                continue

            print(f"\t{date_obj}")
            url_dict[title_id] = f"https:{story_url}"

        if stop_loop:
            break

        page_num += 1
        time.sleep(4)

    driver.quit()

    print("Writing dict to json file...")
    with open("slashdot_urls.json", 'w') as outfile:
        json.dump(url_dict, outfile, indent=4)

    print("DONE!!!")


if __name__ == "__main__":
    main()
