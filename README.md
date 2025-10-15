Quick Setup Commands:
bash# Create project directory
mkdir ecourts-scraper
cd ecourts-scraper

# Copy all the files I created above into this folder

# Setup virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test CLI
python ecourts_scraper.py --cnr DLCT01-123456-2024 --state DL --today
python causelist_scraper.py --today

# Test Web Interface
python web_app.py
