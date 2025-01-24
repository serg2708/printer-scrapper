import csv
import time
from datetime import datetime
import logging

import requests
from bs4 import BeautifulSoup
from fontTools.misc.timeTools import timestampNow

# Set up logging
timestamp = datetime.now().strftime('%Y%m%d%H%M')
logging.basicConfig(filename=f'printer_scraper_{timestamp}.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# List of printer URLs
printer_urls = [
    'http://printer_link',
    "http://printer_link",

]

# Login URL and data
login_url = "http://{}/checkLogin.cgi"
login_data = {
    'i0012': '1',
    'i0017': '2',
    'i0019': '',
    'i2101': '7654321'
}

# Counter URL and Info URL
counter_url = "http://{}/d_counter.html"
info_url = "http://{}/d_info.html"
portal_top_url = "http://{}/portal_top.html"


def extract_toner_info(soup):
    toner_info = {}
    # Try several possible HTML structures
    toner_elements = soup.select('#tonerInfomationModule table tr') or \
                     soup.select('.tonerInfomation table tr') or \
                     soup.select('table.consumables tr')

    if not toner_elements:
        # If no specific toner elements found, look for any percentage in the soup
        percentages = soup.find_all(string=lambda text: '%' in text)
        if percentages:
            toner_info[''] = percentages[0].strip()
        else:
            toner_info[''] = '-%'
    else:
        for row in toner_elements[1:]:  # Skip the header
            cells = row.select('td')
            if len(cells) >= 2:
                color = cells[0].text.strip()
                # Look for toner level in percentages or other formats
                level = None
                for cell in cells[1:]:
                    if '%' in cell.text:
                        level = cell.text.strip()
                        break
                if level:
                    toner_info[color] = level
                else:
                    toner_info[color] = '-%'

    logging.info(f"Extracted toner info: {toner_info}")
    return toner_info


def fetch_and_save_counters(printer_url):
    session = requests.Session()

    try:
        # Login
        response = session.post(login_url.format(printer_url.replace("http://", "")), data=login_data)
        if response.status_code != 200 or 'Remote UI: Portal' not in response.text:
            logging.error(f"Failed to log in to {printer_url}. Status code: {response.status_code}")
            return  # Skip this printer and move to the next one

        logging.info(f"Login successful for {printer_url}")

        # Navigate to the device information page
        response = session.get(info_url.format(printer_url.replace("http://", "")))
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            device_name_elem = soup.find(string='Device Name:')
            device_name = device_name_elem.find_next('td').text.strip() if device_name_elem else "Unknown"

            serial_number_elem = soup.find(string='Serial Number:')
            serial_number = serial_number_elem.find_next('td').text.strip() if serial_number_elem else "Unknown"

        # Navigate to the counter page
        response = session.get(counter_url.format(printer_url.replace("http://", "")))
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            total_pages_elem = soup.find(string='113: Total (Black & White/Small)')
            total_pages = int(total_pages_elem.find_next('td').text.strip()) if total_pages_elem else 0

            scanned_pages_elem = soup.find(string='501: Scan (Total 1)')
            scanned_pages = int(scanned_pages_elem.find_next('td').text.strip()) if scanned_pages_elem else 0

            printed_pages_elem = soup.find(string='301: Print (Total 1)')
            printed_pages = int(printed_pages_elem.find_next('td').text.strip()) if printed_pages_elem else 0

        # Navigate to the portal top page for toner levels
        response = session.get(portal_top_url.format(printer_url.replace("http://", "")))
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            toner_info = extract_toner_info(soup)

            # Get toner levels, defaulting to '-% if not found
            black_toner = toner_info.get('Black', toner_info.get('', '-%'))
            cyan_toner = toner_info.get('Cyan', toner_info.get('', '-%'))
            magenta_toner = toner_info.get('Magenta', toner_info.get('', '-%'))
            yellow_toner = toner_info.get('Yellow', toner_info.get('', '-%'))
        else:
            logging.error(f"Failed to fetch portal top data for {printer_url}, status code: {response.status_code}")
            black_toner = cyan_toner = magenta_toner = yellow_toner = '-%'

        # ... (rest of the function remains the same)

        # Save the data to CSV
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f'printer_counters_{timestamp}.csv'

        with open(filename, 'a', newline='') as csvfile:
            fieldnames = [
                'Timestamp',
                'Printer',
                'Device Name',
                'Serial Number',
                'Total Pages (B&W)',
                'Total Scanned Pages',
                'Total Printed Pages',
                'Black Toner Level',
                'Cyan Toner Level',
                'Magenta Toner Level',
                'Yellow Toner Level'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if csvfile.tell() == 0:
                writer.writeheader()

            writer.writerow({
                'Timestamp': timestamp,
                'Printer': printer_url,
                'Device Name': device_name,
                'Serial Number': serial_number,
                'Total Pages (B&W)': total_pages,
                'Total Scanned Pages': scanned_pages,
                'Total Printed Pages': printed_pages,
                'Black Toner Level': black_toner,
                'Cyan Toner Level': cyan_toner,
                'Magenta Toner Level': magenta_toner,
                'Yellow Toner Level': yellow_toner
            })

        logging.info(f"Report saved to {filename}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Connection error for {printer_url}: {e}")
    except Exception as e:
        logging.error(f"Error processing {printer_url}: {e}")


# Fetch and save counters for all printers
for printer_url in printer_urls:
    fetch_and_save_counters(printer_url)
    time.sleep(2)  # Add a small delay to avoid overwhelming the servers