# Durian Inventory & Sales App

A simple Flask application to manage durian species, variations, inventory and sales. The app tracks when a durian variation is sold as another variation and calculates profit. Sales can be optionally synced to Google Sheets and a receipt is generated for each sale.

## Features
- Manage durian species and variations with flexible price per kg
- Record inventory purchases
- Record sales where purchased variation differs from sold variation
- Dashboard summarising profits per variation mapping
- Generate text receipt for every sale
- Optional Google Sheets sync (requires `credentials.json`)

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The application uses SQLite database `durian.db` in the project directory.

To enable Google Sheets sync, place a Google service account `credentials.json` file in the project root and create a spreadsheet named `DurianSales`.

Receipts are stored in the `receipts/` directory.
