import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import quote_plus

# ===============================
# HELPER FUNCTIONS
# ===============================
HEADERS = {"User-Agent": "Mozilla/5.0"}

def build_search_url(template, query):
    return template.replace("{query}", quote_plus(query))

def get_product_links(search_url, limit=5):
    try:
        html = requests.get(search_url, headers=HEADERS, timeout=10).text
    except:
        return []
    soup = BeautifulSoup(html, "html.parser")
    base = search_url.split("/")[0] + "//" + search_url.split("/")[2]
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(x in href for x in ["/product/", "/prd/", "/p/"]):
            if href.startswith("/"):
                href = base + href
            links.add(href)
        if len(links) >= limit:
            break
    return list(links)

def extract_product_data(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
            except:
                continue
            if isinstance(data, dict) and data.get("@type") == "Product":
                offers = data.get("offers", {})
                return {
                    "name": data.get("name"),
                    "price": offers.get("price"),
                    "currency": offers.get("priceCurrency", ""),
                    "image": data.get("image"),
                    "url": url
                }
    except:
        pass
    return None

# ===============================
# STREAMLIT APP
# ===============================
def main():
    st.set_page_config(page_title="Fashion Skyscanner", layout="wide")
    st.title("🛍️ Fashion Skyscanner MVP")

    # Initialize default retailers
    if "retailers" not in st.session_state:
        st.session_state.retailers = [
            {"name": "ASOS", "search_url": "https://www.asos.com/search/?q={query}"},
            {"name": "Uniqlo", "search_url": "https://www.uniqlo.com/uk/en/search/?q={query}"}
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
        results = []
        with st.spinner("Searching retailers..."):
            for r in st.session_state.retailers:
                search_url = build_search_url(r["search_url"], query)
                links = get_product_links(search_url)
                for link in links:
                    product = extract_product_data(link)
                    if product and product["price"]:
                        product["retailer"] = r["name"]
                        results.append(product)

        # Display results
        if results:
            cols = st.columns(4)
            for i, item in enumerate(results):
                with cols[i % 4]:
                    st.image(item["image"], use_container_width=True)
                    st.markdown(f"**{item['name']}**")
                    st.markdown(f"💷 {item['price']} {item['currency']}")
                    st.caption(item["retailer"])
                    st.markdown(f"[View Product]({item['url']})")
        else:
            st.warning("No results found.")

if __name__ == "__main__":
    main()
