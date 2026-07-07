import time
import random
import re
import os
import urllib.parse
from bs4 import BeautifulSoup
import pandas as pd
from seleniumbase import SB

# Input and Output Settings
input_csv = "agents_data_cleaned.csv"
output_csv = "agents_detailed_info.csv"

if not os.path.exists(input_csv):
    print(f"Error: Couldn't find '{input_csv}'.")
    exit()

df_input = pd.read_csv(input_csv)
df_targets = df_input[df_input["Agent Link"].notna() & df_input["Agent Link"].str.startswith("http")]
print(f"Loaded Cleaned CSV. Found {len(df_targets)} agent links to process.")

scraped_records = []
completed_links = set()
if os.path.exists(output_csv):
    try:
        df_existing = pd.read_csv(output_csv)
        scraped_records = df_existing.to_dict(orient="records")
        completed_links = set(df_existing["Agent Link"].tolist())
        print(f"Resuming script. Skipping {len(completed_links)} records.")
    except Exception:
        pass

with SB(uc=True, rtf=True) as sb:
    for idx, row in enumerate(df_targets.to_dict(orient="records"), start=1):
        agent_url = row["Agent Link"]
        agent_name = row.get("Name", "Unknown Agent")
        
        if agent_url in completed_links:
            continue
            
        print(f"\n⚡ [{idx}/{len(df_targets)}] Processing: {agent_name}")
        
        try:
            sb.open(agent_url)
            # Give the network socket just a brief moment to settle down raw DOM
            time.sleep(2) 
            
            # Extract raw DOM page source code instantly for blazing fast parsing
            html = sb.get_page_source()
            soup = BeautifulSoup(html, "html.parser")
            
            # --- 1. OFFICE ADDRESS (Extracted directly from Google Maps URLs) ---
            address_clean = "N/A"
            map_link = soup.find("a", href=re.compile(r"maps\.google\.com\/\?q="))
            if map_link:
                try:
                    raw_q = re.search(r"q=([^&]+)", map_link["href"])
                    if raw_q:
                        address_clean = urllib.parse.unquote(raw_q.group(1)).replace("+", " ")
                except Exception:
                    pass
            
            # Fallback Address Parsing if map link anchor wrapper parsing fails
            if address_clean == "N/A":
                loc_svg = soup.find("svg", {"data-testid": "icon-location"})
                if loc_svg:
                    parent_div = loc_svg.find_parent("div")
                    if parent_div:
                        # Grab text and strip out the "View map" link action text
                        address_clean = parent_div.get_text(", ").replace(", View map", "").strip()

            # --- 2. AGENT LICENSE # ---
            license_no = "N/A"
            lic_text = soup.find(text=re.compile(r"Agent license\s*#"))
            if lic_text:
                license_no = lic_text.split("#")[-1].strip()
            else:
                match = re.search(r"Agent license\s*#\s*(\d+)", html)
                if match:
                    license_no = match.group(1)

            # --- 3. YEARS OF EXPERIENCE ---
            experience = "N/A"
            exp_el = soup.find(attrs={"data-testid": "avatar-exp"})
            if exp_el:
                txt = exp_el.get_text().strip()
                if "undefined" not in txt.lower():
                    experience = txt

            # --- 4. TELEPHONE NUMBERS ---
            phone_list = []
            for a in soup.find_all("a", href=re.compile(r"^tel:")):
                p_text = a.get_text().strip()
                if p_text and p_text not in phone_list:
                    phone_list.append(p_text)
            phone_numbers = " | ".join(phone_list) if phone_list else "N/A"

            # --- 5. EXTERNAL CORPORATE WEBSITES ---
            site_urls = []
            for a in soup.find_all("a", href=True, target="_blank"):
                href = a["href"]
                # Instant block check constraints matching strings to avoid looping through junk URLs
                if any(x in href for x in ["google.com", "facebook.com", "twitter.com", "linkedin.com", "instagram.com", "youtube.com", "tiktok.com", "sell.realtor.com", "realestateandhomes-detail"]):
                    continue
                if href not in site_urls:
                    site_urls.append(href)
            websites = " | ".join(site_urls) if site_urls else "N/A"

            # --- 6. SPECIALTIES ---
            specialties = "N/A"
            spec_div = soup.find(attrs={"data-testid": "specialties"})
            if spec_div:
                p_tags = spec_div.find_all("p")
                if len(p_tags) >= 2:
                    specialties = ", ".join([s.strip() for s in p_tags[1].get_text().split("•") if s.strip()])

            # --- 7. OVERVIEW/BIO DESCRIPTION ---
            bio_clean = "N/A"
            bio_el = soup.find(attrs={"data-testid": "bio"})
            if bio_el:
                bio_clean = bio_el.get_text().replace("See less", "").replace("See more", "").replace("Read more", "").strip()

            # --- 8. AREAS SERVED ---
            areas_served = "N/A"
            areas_el = soup.find(attrs={"data-testid": "areas-served-component"})
            if areas_el:
                p_tag = areas_el.find("p")
                if p_tag:
                    areas_served = ", ".join([a.strip() for a in p_tag.get_text().split("•") if a.strip()])

            # --- 9. SELLER & BUYER SERVICES ---
            seller_services = "N/A"
            seller_el = soup.find(attrs={"data-testid": "seller-services"})
            if seller_el:
                p_tag = seller_el.find("p")
                if p_tag:
                    seller_services = ", ".join([s.strip() for s in p_tag.get_text().split("•") if s.strip()])

            buyer_services = "N/A"
            buyer_el = soup.find(attrs={"data-testid": "buyer-services"})
            if buyer_el:
                p_tag = buyer_el.find("p")
                if p_tag:
                    buyer_services = ", ".join([b.strip() for b in p_tag.get_text().split("•") if b.strip()])

            # Compile into full final records layout
            full_record = row.copy()
            full_record.update({
                "License Number": license_no,
                "Years of Experience": experience,
                "Phone Numbers": phone_numbers,
                "Office Address": address_clean,
                "Websites": websites,
                "Specialties": specialties,
                "Areas Served": areas_served,
                "Seller Services": seller_services,
                "Buyer Services": buyer_services,
                "Overview Description": bio_clean
            })
            
            scraped_records.append(full_record)
            print(f"   📍 Address Found: {address_clean}")
            print(f"   📞 Phones Found: {phone_numbers}")
            
        except Exception as e:
            print(f"❌ Critical Failure parsing rows for {agent_name}: {e}")
            full_record = row.copy()
            scraped_records.append(full_record)

        # File Auto-Save Routine Checks every single loop iteration
        df_output = pd.DataFrame(scraped_records)
        df_output.to_csv(output_csv, index=False, encoding="utf-8")
        
        # Keep variable safety cushion delays minimal
        time.sleep(random.uniform(0.5, 1.5))


print(f"\nExecution Complete! Full outputs stored cleanly inside: '{output_csv}'")