import time
import random
import pandas as pd
from seleniumbase import SB

# Target URL and Output Settings
url = "https://www.realtor.com/realestateagents/90001/intent-buy/sort-relevantagents/agenttype-all/pg-1"
csv_filename = "agents_data.csv"

# Master list to hold all scraped dictionaries
all_agents = []

# Launch SeleniumBase with UC (Undetected ChromeDriver) Mode
with SB(uc=True, rtf=True) as sb:
    print("Navigating to Realtor.com...")
    sb.uc_open_with_reconnect(url, reconnect_time=6)
    
    page_number = 1
    
    while True:
        print(f"\n=========================================")
        print(f" PROCESSING PAGE {page_number}")
        print(f"=========================================")
        
        # Human-like delay to let components settle
        time.sleep(random.uniform(5.5, 8.0))
        
        # Smooth scrolling down to trigger asset loading metrics on the firewall
        print("Emulating human reading view scroll patterns...")
        sb.execute_script("window.scrollTo({top: document.body.scrollHeight / 2, behavior: 'smooth'});")
        time.sleep(random.uniform(1.5, 2.5))
        sb.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
        time.sleep(random.uniform(1.5, 2.5))
        
        # Extract the parent agent cards present on the page
        agent_cards = sb.find_elements('[data-testid="agent-card-item-component"]')
        print(f"Found {len(agent_cards)} agents on page {page_number}.\n")
        
        if len(agent_cards) == 0:
            print("No agents found. Exiting to protect session.")
            break
            
        for index, card in enumerate(agent_cards, start=1):
            # --- 1. FULL NAME ---
            try:
                name_element = card.find_element("css selector", '[data-testid="agent-title-section-component"] .dTjoPB')
                full_name = name_element.text.strip()
            except Exception:
                try:
                    fallback_element = card.find_element("css selector", '[data-testid="agent-title-section-component"] button')
                    full_name = fallback_element.text.split('\n')[0].strip()
                except Exception:
                    full_name = "N/A"

            # --- 2. AFFILIATED COMPANY ---
            try:
                company_element = card.find_element("css selector", '[data-testid="agent-title-section-component"] .iJPZCK p')
                affiliated_company = company_element.text.strip()
            except Exception:
                affiliated_company = "N/A"

            # --- 3. IMAGE URL ---
            try:
                image_url = card.find_element("css selector", '[data-testid="avatar-img"]').get_attribute("src")
            except Exception:
                image_url = "N/A"

            # --- 4. RATING ---
            try:
                rating_element = card.find_element("css selector", '[data-testid="agent-ratings-reviews-component"] p')
                rating = rating_element.text.strip()
            except Exception:
                rating = "N/A"

            # --- 5. REVIEWS & TESTIMONIALS ---
            try:
                metrics_element = card.find_element("css selector", '.dqgPGS')
                metrics = metrics_element.text.replace("\n", " ").strip()
            except Exception:
                metrics = "N/A"

            # --- 6. PRICE RANGE ---
            try:
                price_element = card.find_element("css selector", '[data-testid="agent-sales-and-price-component"] .breFRQ span')
                price_range = price_element.text.strip()
            except Exception:
                price_range = "N/A"

            # --- 7. RECENT SALES ---
            try:
                sales_element = card.find_element("css selector", '[data-testid="agent-sales-and-price-component"] > p')
                recent_sales = sales_element.text.strip()
            except Exception:
                recent_sales = "N/A"

            # Build data mapping dictionary
            agent_data = {
                "Page": page_number,
                "Index": index,
                "Name": full_name,
                "Affiliated Company": affiliated_company,
                "Image URL": image_url,
                "Rating": rating,
                "Metrics": metrics,
                "Price Range": price_range,
                "Recent Sales": recent_sales
            }
            
            all_agents.append(agent_data)
            print(f"Logged [{index}]: {full_name}")

        # --- AUTO-SAVE PROGRESS FALLBACK ---
        df_checkpoint = pd.DataFrame(all_agents)
        df_checkpoint.to_csv(csv_filename, index=False, encoding="utf-8")
        print(f"--> Saved checkpoint state for {len(all_agents)} total records.")

        # --- PAGINATION OPERATION ---
        print("\nChecking for Next Page navigation link...")
        try:
            next_button_selector = 'a.next-link[aria-label="Go to next page"]'
            
            # Corrected: standard check without the unsupported timeout keyword argument
            if sb.is_element_visible(next_button_selector):
                next_button = sb.find_element(next_button_selector)
                next_page_href = next_button.get_attribute("href")
                
                if next_page_href and "pg-" in next_page_href:
                    print(f"Moving to next page layout target link: {next_page_href}")
                    
                    sb.scroll_to(next_button_selector)
                    time.sleep(random.uniform(0.5, 1.2))
                    
                    sb.click(next_button_selector)
                    page_number += 1
                else:
                    print("Next button missing valid link structure. Final page reached.")
                    break
            else:
                print("No visible 'Next' navigation link layout found. Scraping complete.")
                break
                
        except Exception as e:
            print(f"Pagination processing completed or errored out: {e}")
            break

print(f"\nTask execution finished! File cleanly compiled at '{csv_filename}'")