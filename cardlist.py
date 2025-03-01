import requests
import json
import csv
from bs4 import BeautifulSoup


class CardList:
    BASE_URL = "https://yugipedia.com"
    PAGE_URL = "https://yugipedia.com/wiki/List_of_Yu-Gi-Oh!_Duel_Monsters_cards"

    def __init__(self):
        self.table_data = []

    def fetch_html(self, url):
        """Fetch HTML content from a given URL."""
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; Bot/0.1)'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def extract_table_data(self, html_content):
        """
        Extracts data from all tables with class "wikitable" as a list of dictionaries.
        For each row, if the header is "Card", the method looks for an <a> tag in the cell,
        extracts its href attribute, and stores it as a new key "Card_href" with the full URL.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        data = []
        tables = soup.find_all("table", class_="wikitable")

        for table in tables:
            # Find header row: assume the first row with <th> elements is the header.
            header_row = table.find("tr")
            if not header_row:
                continue
            headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
            if not headers:
                continue  # Skip table if no headers found

            # Process the rest of the rows
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                # Skip if this row does not have enough data cells.
                if not cells or len(cells) < len(headers):
                    continue

                row_dict = {}
                for i, cell in enumerate(cells):
                    # Use the header as key (if available)
                    key = headers[i] if i < len(headers) else f"column_{i}"
                    # Extract the text from the cell
                    cell_text = cell.get_text(strip=True)
                    row_dict[key] = cell_text

                    # If this cell belongs to the "Card" column, attempt to extract the href.
                    if key.lower() == "card":
                        a_tag = cell.find("a")
                        if a_tag and a_tag.has_attr("href"):
                            # Build the full URL
                            row_dict["Card_href"] = self.BASE_URL + a_tag["href"]
                        else:
                            row_dict["Card_href"] = ""
                data.append(row_dict)
        self.table_data = data
        return data

    def export_to_json(self, filename):
        """Export the table data (a list of dictionaries) to a JSON file."""
        if not self.table_data:
            print("No data to export.")
            return
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(self.table_data, json_file, indent=4, ensure_ascii=False)
        print(f"Data exported to JSON file: {filename}")

    def export_to_csv(self, filename):
        """Export the table data (a list of dictionaries) to a CSV file."""
        if not self.table_data:
            print("No data to export to CSV.")
            return

        # Determine fieldnames by taking keys from the first item (assumes all rows share the same keys)
        fieldnames = list(self.table_data[0].keys())
        with open(filename, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.table_data)
        print(f"Data exported to CSV file: {filename}")

    def run(self):
        """Main method to fetch HTML, extract table data, and export it to JSON and CSV."""
        html_content = self.fetch_html(self.PAGE_URL)

        table_data = self.extract_table_data(html_content)
        print(f"Extracted {len(table_data)} rows from the tables.")

        self.export_to_json("json/card_list.json")
        self.export_to_csv("csv/card_list.csv")
