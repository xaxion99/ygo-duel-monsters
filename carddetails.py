import requests
import json
import csv
import time
from bs4 import BeautifulSoup


class CardDetails:
    BASE_URL = "https://yugipedia.com"
    LIST_PAGE_URL = "https://yugipedia.com/wiki/List_of_Yu-Gi-Oh!_Duel_Monsters_cards"

    def __init__(self):
        self.all_cards = []  # Will hold all parsed card data

    def fetch_html(self, url):
        """Fetch HTML content from the URL."""
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; Bot/0.1)'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def get_card_links(self):
        """
        From the Duel Monsters cards list page, extract and return a list of full URLs
        to the individual card pages.
        """
        html = self.fetch_html(self.LIST_PAGE_URL)
        soup = BeautifulSoup(html, "html.parser")
        card_links = []
        # Find all tables with class "wikitable"
        tables = soup.find_all("table", class_="wikitable")
        for table in tables:
            header_row = table.find("tr")
            if not header_row:
                continue
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all("th")]
            if "card" not in headers:
                continue  # Skip tables without a "Card" header
            card_index = headers.index("card")
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if not cells or len(cells) <= card_index:
                    continue
                card_cell = cells[card_index]
                a_tag = card_cell.find("a")
                if a_tag and a_tag.has_attr("href"):
                    full_url = self.BASE_URL + a_tag["href"]
                    card_links.append(full_url)
        return card_links

    def parse_card_page(self, html):
        """
        Parse an individual card page HTML and extract:
          - card_name: from <div class="heading">
          - languages: from the <dl> in <div class="above"><div class="hlist">
          - image: the <img> tag inside <div class="imagecolumn"> (all its attributes)
          - info: all key/value pairs from the infocolumn table plus any lore text.
        Returns a dictionary with these fields.
        """
        soup = BeautifulSoup(html, "html.parser")
        data = {}

        # --- Card name (heading) ---
        heading_div = soup.find("div", class_="heading")
        if heading_div:
            inner_div = heading_div.find("div")
            data["card_name"] = inner_div.get_text(strip=True) if inner_div else heading_div.get_text(strip=True)
        else:
            data["card_name"] = ""

        # --- Language information (above section) ---
        data["languages"] = {}
        above_div = soup.find("div", class_="above")
        if above_div:
            hlist_div = above_div.find("div", class_="hlist")
            if hlist_div:
                dl = hlist_div.find("dl")
                if dl:
                    dts = dl.find_all("dt")
                    dds = dl.find_all("dd")
                    for dt, dd in zip(dts, dds):
                        key = dt.get_text(strip=True)
                        value = dd.get_text(strip=True)
                        data["languages"][key] = value

        # --- Card image information (imagecolumn) ---
        data["image"] = {}
        imagecolumn_div = soup.find("div", class_="imagecolumn")
        if imagecolumn_div:
            img_tag = imagecolumn_div.find("img")
            if img_tag:
                data["image"]["src"] = img_tag.get("src", "")
                data["image"]["alt"] = img_tag.get("alt", "")
                data["image"]["width"] = img_tag.get("width", "")
                data["image"]["height"] = img_tag.get("height", "")
                data["image"]["data_file_width"] = img_tag.get("data-file-width", "")
                data["image"]["data_file_height"] = img_tag.get("data-file-height", "")

        # --- Infocolumn data ---
        data["info"] = {}
        infocolumn_div = soup.find("div", class_="infocolumn")
        if infocolumn_div:
            innertable = infocolumn_div.find("table", class_="innertable")
            if innertable:
                rows = innertable.find_all("tr")
                lore_texts = []
                for row in rows:
                    th = row.find("th")
                    tds = row.find_all("td")
                    if th:
                        key = th.get_text(strip=True)
                        # Combine text from all <td> cells (if more than one exists)
                        value = " / ".join(td.get_text(strip=True) for td in tds)
                        data["info"][key] = value
                    else:
                        # Some rows may not have a <th> and instead contain lore (colspan=2)
                        p_tags = row.find_all("p")
                        for p in p_tags:
                            lore_texts.append(p.get_text(strip=True))
                if lore_texts:
                    data["info"]["lore"] = " ".join(lore_texts)
        return data

    def flatten_card_data(self, card):
        """
        For CSV export we need a flat dictionary.
        This method takes the nested card dictionary and flattens:
          - languages → keys like "language_Japanese", etc.
          - image → keys like "image_src", "image_alt", etc.
          - info → keys like "info_number", "info_atk_/__def", etc.
        """
        flat = {}
        flat["card_name"] = card.get("card_name", "")
        for lang_key, lang_val in card.get("languages", {}).items():
            flat[f"language_{lang_key}"] = lang_val
        for img_key, img_val in card.get("image", {}).items():
            flat[f"image_{img_key}"] = img_val
        for info_key, info_val in card.get("info", {}).items():
            key_clean = info_key.replace(" ", "_").replace("/", "_").lower()
            flat[f"info_{key_clean}"] = info_val
        return flat

    def export_to_json(self, data, filename):
        """Export the list of card data dictionaries to a JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Exported JSON to {filename}")

    def export_to_csv(self, data, filename):
        """Export the list of card data dictionaries (flattened) to a CSV file."""
        if not data:
            print("No data to export to CSV.")
            return
        flat_data = [self.flatten_card_data(card) for card in data]
        # Create a union of all keys for CSV header
        fieldnames = set()
        for d in flat_data:
            fieldnames.update(d.keys())
        fieldnames = list(fieldnames)
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_data)
        print(f"Exported CSV to {filename}")

    def format_json(self, input_filename, output_filename, model_name):
        # Read the input JSON file.
        with open(input_filename, "r", encoding="utf-8") as infile:
            cards = json.load(infile)

        formatted_cards = []
        for i, card in enumerate(cards, start=1):
            fixture_entry = {
                "model": model_name,
                "pk": i,
                "fields": card
            }
            formatted_cards.append(fixture_entry)

        # Write the new fixture file.
        with open(output_filename, "w", encoding="utf-8") as outfile:
            json.dump(formatted_cards, outfile, indent=4, ensure_ascii=False)

        print(f"Fixture saved to {output_filename}")

    def run(self):
        """
        Main process:
         1. Get individual card page links from the list page.
         2. Parse each card page.
         3. Export all card data to JSON and CSV.
        """
        card_links = self.get_card_links()
        print(f"Found {len(card_links)} card links.")

        for i, link in enumerate(card_links):
            print(f"Processing card {i + 1}/{len(card_links)}: {link}")
            try:
                card_html = self.fetch_html(link)
                card_data = self.parse_card_page(card_html)
                self.all_cards.append(card_data)
            except Exception as e:
                print(f"Error processing {link}: {e}")
            time.sleep(1)  # Be polite to the server

        self.export_to_json(self.all_cards, "json/card_details.json")
        self.export_to_csv(self.all_cards, "csv/card_details.csv")
