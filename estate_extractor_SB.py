import time
import random
from seleniumbase import SB

url = "https://www.realtor.com/realestateagents/90001/intent-buy/sort-relevantagents/agenttype-all/pg-1"

with SB(uc=True, rtf=True) as sb:
    print("Navigating to Realtor.com...")
    sb.uc_open_with_reconnect(url, reconnect_time=6)
    
    # Human-like thinking delay to let JavaScript populate the cards
    time.sleep(random.uniform(5.0, 7.5))
    
    print("Extracting updated agent layout elements...")
    
    # 1. Target the cards using the explicit data-testid found in your HTML snippet
    agent_cards = sb.find_elements('[data-testid="agent-card-item-component"]')
    
    print(f"--- Successfully identified {len(agent_cards)} agent slots ---\n")
    
    for index, card in enumerate(agent_cards, start=1):
        try:
            # 2. Look inside the card for the class containing the name text (e.g. "AL Galvis")
            # In your HTML, it is styled with the class '.dTjoPB' or nested inside the title section
            name_element = card.find_element("css selector", '[data-testid="agent-title-section-component"] .dTjoPB')
            
            full_name = name_element.text.strip()
            print(f"{index}. {full_name}")
            
        except Exception:
            # Fallback approach: If they randomize the minor class name, pull it from the title-section button text directly
            try:
                fallback_element = card.find_element("css selector", '[data-testid="agent-title-section-component"] button')
                # Split lines or clean text if it contains the brokerage name too
                raw_text = fallback_element.text.split('\n')[0]
                print(f"{index}. {raw_text.strip()}")
            except Exception:
                print(f"{index}. [Could not parse name layout structure]")