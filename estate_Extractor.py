import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

# 1. Initialize Undetected ChromeDriver options
options = uc.ChromeOptions()

# 2. Add your optimization preferences
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--disable-notifications")
options.add_argument("--start-maximized")

# Optional: Add a real, modern User-Agent to match a real user browser
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Disable images to speed up page load (as requested in your original code)
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

url = "https://www.realtor.com/realestateagents/90001/intent-buy/sort-relevantagents/agenttype-all/pg-1"

# 3. Launch the protected browser instance
# Note: Undetected ChromeDriver downloads the matching driver version automatically
driver = uc.Chrome(options=options, page_load_strategy="eager")

try:
    print("Navigating to Realtor.com securely...")
    driver.get(url)

    # 4. Add human-like thinking delay so the anti-bot sees normal page interactive behavior
    time.sleep(5) 

    # 5. Extract and parse data
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    agents = soup.find_all("article", class_="agent-card")

    print(f"--- Successfully extracted {len(agents)} real estate agents ---\n")

    for index, agent in enumerate(agents, start=1):
        if agent.h2 and agent.h2.a:
            full_name = agent.h2.a.get("title", agent.h2.a.text.strip())
            print(f"{index}. {full_name}")
        else:
            print(f"{index}. [Could not parse name structural layout matches]")

finally:
    driver.quit()
