# humble-retrieve

A Python 3.14 script that retrieves your Humble Bundle library via the Humble API and exports a flattened CSV with order, product, subproduct, and download-level details.

## Features

- Fetches all order game keys from your account
- Fetches details for each order concurrently
- Exports results to library.csv
- Includes expanded CSV columns for:
  - order keys
  - amount and currency
  - bundle metadata
  - subproduct/download metadata
  - download links
- Prints final spend totals in terminal:
  - total USD
  - total EUR

## Requirements

- Python 3.14
- uv
- A valid Humble session cookie value for _simpleauth_sess

## Setup with uv

1. Clone the repo and enter it

   git clone <your-repo-url>
   cd humble_retrieve

2. Install dependencies

   uv sync

3. Create your environment file

   Create a file named .env in the project root with:

   humble_session_key=YOUR_HUMBLE_SIMPLEAUTH_SESS_VALUE
   request_timeout_seconds=30
   user_agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

Notes:
- humble_session_key is required.
- request_timeout_seconds is optional (defaults to 30).
- user_agent is optional (defaults to the value in config).

## How to get humble_session_key

1. Log into Humble Bundle in your browser
2. Open browser developer tools
3. Find cookies for humblebundle.com
4. Copy the value of _simpleauth_sess
5. Put it into .env as humble_session_key

Keep this value secret. It grants account access for API requests.

## Run

From the project root:

uv run main.py

## Output

- CSV is written to:
  - library.csv
- Terminal logs include:
  - progress per order
  - final CSV save path
  - spend summary line like:
    Total spent summary | USD: X.XX | EUR: Y.YY

## Project structure

- main.py: orchestration, CSV generation, total currency summary
- client.py: API calls for index and per-order details
- models.py: Pydantic data models for API responses
- config.py: environment-based configuration loading
- output/: generated CSV output (gitignored)

## Troubleshooting

- Missing .env or missing humble_session_key:
  - Startup will fail due strict settings validation.
- 401/403 or empty library:
  - Session key may be expired or invalid.
- Request/network errors:
  - Retry later or increase request_timeout_seconds.