import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote_plus
import time

# ===============================
# SELENIUM HELPERS
# ===============================
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def search_retailer(driver, template_url, query, limit=5):
    url = template_url.replace("{query}", quote_plus(query))
    driver.get(url)
    time.sleep(3)  # wait for products to load
    results = []

    # Simple example: find all product links
    # Adjust selectors based on retailer site structure
    product_elements = driver.find_elements(By.XPATH, "//a[contains(@href,'/product') or contains(@href,'/prd')]")
    for p in product_elements[:limit]:
        name = p.text
        link = p.get_attribute("href")
        results.append({"name": name, "url": link})
    return results

# ===============================
# STREAMLIT APP
# ===============================
def main():
    st.set_page_config(page_title="Fashion Skyscanner", layout="wide")
    st.title("🛍️ Fashion Skyscanner (Selenium MVP)")

    # Initialize retailers
    if "retailers" not in st.session_state:
        st.session_state.retailers = [
            {"name": "ASOS", "search_url": "https://www.asos.com/search/?q={query}"},
            {"name": "Terraces Menswear", "search_url": "https://www.terracesmenswear.co.uk/index.php?route=product/search&search={query}"}
        ]

    # Sidebar - add retailer
    st.sidebar.header("Add a retailer")
    with st.sidebar.form("add_retailer"):
        name = st.text_input("Retailer Name")
        search_url = st.text_input("Search URL template", placeholder="https://site.com/search?q={query}")
        submitted = st.form_submit_button("Add Retailer")
        if submitted:
            if "{query}" in search_url:
                st.session_state.retailers.append({"name": name, "search_url": search_url})
                st.sidebar.success(f"{name} added!")
            else:
                st.sidebar.error("Search URL must contain {query} placeholder!")

    # Sidebar - list retailers
    st.sidebar.markdown("### Favourite Retailers")
    for r in st.session_state.retailers:
        st.sidebar.write("•", r["name"])

    # Main search
    query = st.text_input("Search for a clothing item (e.g., white t-shirt)")
    if st.button("Search") and query:
        driver = init_driver()
        results = []
        for r in st.session_state.retailers:
            res = search_retailer(driver, r["search_url"], query)
            for item in res:
                item["retailer"] = r["name"]
                results.append(item)
        driver.quit()

        # Display results
        if results:
            cols = st.columns(3)
            for i, item in enumerate(results):
                with cols[i % 3]:
                    st.markdown(f"**{item['name']}**")
                    st.markdown(f"[View Product]({item['url']})")
        else:
            st.warning("No results found.")

if __name__ == "__main__":
    main()

