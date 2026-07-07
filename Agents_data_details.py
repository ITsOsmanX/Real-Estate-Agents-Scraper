import time
import random
import re
import os
import pandas as pd
from seleniumbase import SB

# Input and Output Settings
input_csv = "agents_data_cleaned.csv"
output_csv = "agents_detailed_info.csv"

# Check if the input file exists before continuing
if not os.path.exists(input_csv):
    print(f"Error: Couldn't find '{input_csv}'. Please ensure your cleaned file exists.")
    exit()

# Load the cleaned dataframe
df_input = pd.read_csv(input_csv)

if "Agent Link" not in df_input.columns:
    print("Error: The input CSV does not contain an 'Agent Link' column.")
    exit()

# Filter out rows that do not possess a valid agent profile URL string
df_targets = df_input[df_input["Agent Link"].notna() & df_input["Agent Link"].str.startswith("http")]
print(f"Loaded Cleaned CSV. Found {len(df_targets)} agent links to process.")

# Load existing progress snapshot tracking to avoid scraping duplicates if restarted
scraped_records = []
completed_links = set()
if os.path.exists(output_csv):
    try:
        df_existing = pd.read_csv(output_csv)
        scraped_records = df_existing.to_dict(orient="records")
        completed_links = set(df_existing["Agent Link"].tolist())
        print(f"Found existing progress output file. Skimming past {len(completed_links)} records.")
    except Exception:
        pass

# Initialize SeleniumBase UC Engine
with SB(uc=True, rtf=True) as sb:
    
    for idx, row in enumerate(df_targets.to_dict(orient="records"), start=1):
        agent_url = row["Agent Link"]
        agent_name = row.get("Name", "Unknown Agent")
        
        if agent_url in completed_links:
            continue
            
        print(f"\n=========================================")
        print(f" CRAWLING AGENT [{idx}/{len(df_targets)}]: {agent_name}")
        print(f" URL: {agent_url}")
        print(f"=========================================")
        
        try:
            sb.open(agent_url)
            # Give individual fields ample layout engine loading buffer windows
            time.sleep(random.uniform(5.0, 7.5))
            
            # Simulated scroll lookup patterns
            sb.execute_script("window.scrollTo({top: 500, behavior: 'smooth'});")
            time.sleep(random.uniform(1.0, 2.0))
            
            # --- 1. YEARS OF EXPERIENCE ---
            try:
                exp_text = sb.get_text('[data-testid="avatar-exp"]')
                experience = exp_text.strip()
            except Exception:
                experience = "N/A"
                
            # --- 2. AGENT LICENSE # ---
            try:
                lic_element = sb.find_element('p:contains("Agent license #")')
                license_no = lic_element.text.replace("Agent license #", "").strip()
            except Exception:
                try:
                    # Alternative regex check out of raw page layouts source if structural class changes
                    page_source = sb.get_page_source()
                    match = re.search(r'Agent license\s*#\s*(\d+)', page_source)
                    license_no = match.group(1) if match else "N/A"
                except Exception:
                    license_no = "N/A"

            # --- 3. SPECIALTIES ---
            try:
                spec_text = sb.get_text('[data-testid="specialties"] p:nth-of-type(2)')
                specialties = ", ".join([s.strip() for s in spec_text.split("•") if s.strip()])
            except Exception:
                specialties = "N/A"

            # --- 4. OVERVIEW/BIO DESCRIPTION ---
            try:
                bio_text = sb.get_text('[data-testid="bio"]')
                bio_clean = bio_text.replace("See less", "").replace("See more", "").strip().strip('"')
            except Exception:
                bio_clean = "N/A"

            # --- 5. AREAS SERVED ---
            try:
                areas_text = sb.get_text('[data-testid="areas-served-component"] [data-testid="bullet-list"] p')
                areas_served = ", ".join([a.strip() for a in areas_text.split("•") if a.strip()])
            except Exception:
                areas_served = "N/A"

            # --- 6. SELLER SERVICES ---
            try:
                seller_text = sb.get_text('[data-testid="seller-services"] [data-testid="bullet-list"] p')
                seller_services = ", ".join([s.strip() for s in seller_text.split("•") if s.strip()])
            except Exception:
                seller_services = "N/A"

            # --- 7. BUYER SERVICES ---
            try:
                buyer_text = sb.get_text('[data-testid="buyer-services"] [data-testid="bullet-list"] p')
                buyer_services = ", ".join([b.strip() for b in buyer_text.split("•") if b.strip()])
            except Exception:
                buyer_services = "N/A"

            # --- 8. TELEPHONE NUMBERS ---
            try:
                phone_els = sb.find_elements('a[href^="tel:"]')
                phone_list = []
                for p in phone_els:
                    txt = p.text.strip()
                    if not txt:
                        parent_text = sb.execute_script("return arguments[0].parentNode.innerText;", p)
                        txt = parent_text.strip()
                    if txt and txt not in phone_list:
                        phone_list.append(txt)
                phone_numbers = " | ".join(phone_list) if phone_list else "N/A"
            except Exception:
                phone_numbers = "N/A"

            # --- 9. OFFICE ADDRESS ---
            try:
                addr_container = sb.find_element('svg[data-testid="icon-location"] + div')
                addr_lines = addr_container.text.split("\n")
                addr_clean = ", ".join([line.strip() for line in addr_lines if "map" not in line.lower() and line.strip()])
            except Exception:
                addr_clean = "N/A"

            # --- 10. EXTERNAL CORPORATE WEBSITES ---
            try:
                web_els = sb.find_elements('a[target="_blank"]')
                site_urls = []
                for w in web_els:
                    href_str = w.get_attribute("href")
                    if href_str and "google.com" not in href_str and "twitter.com" not in href_str and "facebook.com" not in href_str:
                        if href_str not in site_urls:
                            site_urls.append(href_str)
                websites = " | ".join(site_urls) if site_urls else "N/A"
            except Exception:
                websites = "N/A"

            # Merge the original data with the newly parsed elements
            full_record = row.copy()
            full_record.update({
                "License Number": license_no,
                "Years of Experience": experience,
                "Phone Numbers": phone_numbers,
                "Office Address": addr_clean,
                "Websites": websites,
                "Specialties": specialties,
                "Areas Served": areas_served,
                "Seller Services": seller_services,
                "Buyer Services": buyer_services,
                "Overview Description": bio_clean
            })
            
            scraped_records.append(full_record)
            print(f"Logged details for {agent_name} safely.")
            
        except Exception as e:
            print(f"Failed to cleanly extract profile metric details for {agent_name}: {e}")
            # Log placeholder minimal tracking entry row to avoid breaking dataset sequence
            full_record = row.copy()
            full_record.update({
                "License Number": "N/A", "Years of Experience": "N/A", "Phone Numbers": "N/A", 
                "Office Address": "N/A", "Websites": "N/A", "Specialties": "N/A", 
                "Areas Served": "N/A", "Seller Services": "N/A", "Buyer Services": "N/A", 
                "Overview Description": "N/A"
            })
            scraped_records.append(full_record)

        # --- PROGRESS AUTO-SAVE CHECKPOINT SNAPSHOT ---
        df_output = pd.DataFrame(scraped_records)
        df_output.to_csv(output_csv, index=False, encoding="utf-8")
        print(f"--> [File Saved Backup Status]: {len(scraped_records)} records stored.")
        
        # Human behavior break buffer adjustments between loops
        time.sleep(random.uniform(2.0, 4.5))

print(f"\nExecution success! Deep profile details dataset saved directly into: '{output_csv}'")