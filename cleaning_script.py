import pandas as pd
import re

# 1. Load the compiled CSV data
input_filename = "agents_data.csv"
output_filename = "agents_data_cleaned.csv"

try:
    df = pd.read_csv(input_filename)
    print(f"Successfully loaded {len(df)} records for cleaning...")
    
    # 2. Remove 'Page' and 'Index' columns
    df = df.drop(columns=["Page", "Index"], errors="ignore")
    
    # 3. Separate 'Metrics' into 'Reviews' and 'Testimonials' columns
    def extract_metrics(text):
        if pd.isna(text) or not isinstance(text, str):
            return 0, 0
        
        # Extract total reviews count using regular expression
        reviews_match = re.search(r'(\d+)\s+reviews?', text, re.IGNORECASE)
        reviews = int(reviews_match.group(1)) if reviews_match else 0
        
        # Extract total testimonials count using regular expression
        testimonials_match = re.search(r'(\d+)\s+testimonials?', text, re.IGNORECASE)
        testimonials = int(testimonials_match.group(1)) if testimonials_match else 0
        
        return reviews, testimonials

    # Apply extractor and break out into two distinct layout structural columns
    metrics_data = df["Metrics"].apply(extract_metrics)
    df["Reviews"] = [m[0] for m in metrics_data]
    df["Testimonials"] = [m[1] for m in metrics_data]
    
    # Drop old combined Metrics column
    df = df.drop(columns=["Metrics"], errors="ignore")

    # 4. Clean 'Recent Sales' to isolate just the numeric value digits
    def extract_sales_number(text):
        if pd.isna(text) or not isinstance(text, str):
            return 0
        
        # Matches the first group of digits found in the text string
        sales_match = re.search(r'(\d+)', text)
        return int(sales_match.group(1)) if sales_match else 0

    df["Recent Sales"] = df["Recent Sales"].apply(extract_sales_number)

    # 5. Save the cleaned dataset structure out to a new file
    df.to_csv(output_filename, index=False, encoding="utf-8")
    print(f"Success! Cleaned output saved completely to '{output_filename}'")
    
    # Quick preview console log snapshot
    print("\nPreview of Cleaned Columns Layout:")
    print(df[["Name", "Reviews", "Testimonials", "Recent Sales"]].head())

except FileNotFoundError:
    print(f"Error: Could not find '{input_filename}'. Please ensure your scraper ran successfully.")
except Exception as e:
    print(f"An error occurred during parsing adjustments: {e}")