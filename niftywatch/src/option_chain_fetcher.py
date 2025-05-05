from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import time

def fetch_oi_with_selenium(symbol="BANKNIFTY"):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get("https://www.nseindia.com")
        time.sleep(3)
        driver.get(url)
        time.sleep(3)
        response = driver.find_element("tag name", "pre").text
        data = json.loads(response)

        ce_oi = 0
        pe_oi = 0
        for row in data["records"]["data"]:
            if "CE" in row:
                ce_oi += row["CE"]["openInterest"]
            if "PE" in row:
                pe_oi += row["PE"]["openInterest"]

        return {
            "call_oi_total": ce_oi,
            "put_oi_total": pe_oi,
            "trn_oi": pe_oi - ce_oi
        }
    except Exception as e:
        print("Error:", e)
        return None
    finally:
        driver.quit()

# Test
if __name__ == "__main__":
    result = fetch_oi_with_selenium("BANKNIFTY")
    print(result)
