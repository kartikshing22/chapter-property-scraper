# chapter-property-scraper
Scraper for creating fake id and logging in and scrape the Property data

Steps to run the project


git clone https://github.com/kartikshing22/chapter-property-scraper.git
cd chapter-property-scraper/
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cd bookingScraper
scrapy crawl -s MONGODB_URI="your mongo string" -s MONGODB_DATABASE="your database" property
