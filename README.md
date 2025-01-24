This script collects data from networked Canon printers and performs the following functions:

1. Connects to MF450 Series and iR2630 printers via URL list
2. Authenticates using preset credentials
3. Gathers data:
   - Device name and serial number
   - Total B&W page count
   - Scanned pages count
   - Printed pages count
   - Toner levels (black, cyan, magenta, yellow)

4. Saves data to CSV file (printer_counters_YYYYMMDD.csv)
5. Maintains operation log (printer_scraper.log) recording successful connections and errors

Additionally, two troubleshooting scripts are included:
- Credential combination testing script
- Model-specific handlers for different printer authentication methods

Logs show some printers are unreachable or have authentication issues, documented in troubleshooting.log.
