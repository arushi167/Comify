import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlsplit
import re

class WebsiteCloner:
    def __init__(self, url):
        self.url = url
        self.base_folder = urlparse(url).netloc
        self.response = None

    def download_file(self, url, folder):
        parsed_url = urlsplit(url)
        path = parsed_url.path
        if not path or path.endswith('/'):
            filename = os.path.join(folder, 'index.html')
        else:
            folders = os.path.dirname(path)
            filename = os.path.join(folder, folders[1:], os.path.basename(path))
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'wb') as f:
            response = requests.get(url)
            f.write(response.content)
        return filename

    def clone_website(self):
        self.response = requests.get(self.url)
        if self.response.status_code == 200:
            if not os.path.exists(self.base_folder):
                os.makedirs(self.base_folder)

            soup = BeautifulSoup(self.response.content, 'html.parser')

            # Download linked CSS files
            css_files = soup.find_all('link', {'rel': 'stylesheet'})
            for css in css_files:
                css_url = urljoin(self.url, css['href'])
                self.download_file(css_url, self.base_folder)
                # Parse CSS files for asset URLs and download them
                self.parse_css(css_url, self.base_folder)

            # Download linked JS files
            js_files = soup.find_all('script', {'src': True})
            for js in js_files:
                js_url = urljoin(self.url, js['src'])
                self.download_file(js_url, self.base_folder)

            # Download images and other assets
            assets = soup.find_all(['img', 'link', 'script'], src=True)
            for asset in assets:
                asset_url = urljoin(self.url, asset.get('src'))
                self.download_file(asset_url, self.base_folder)

            # Save HTML with local CSS and JS links
            with open(os.path.join(self.base_folder, 'index.html'), 'wb') as f:
                f.write(self.response.content)

            print("Website cloned successfully.")
        else:
            print("Failed to clone website. Status code:", self.response.status_code)

    def parse_css(self, css_url, folder):
        response = requests.get(css_url)
        if response.status_code == 200:
            content = response.text
            # Find all URLs in CSS content
            urls = re.findall(r'url\([\'\"]?(.*?)[\'\"]?\)', content)
            for url in urls:
                asset_url = urljoin(css_url, url)
                self.download_file(asset_url, folder)
        else:
            print("Failed to parse CSS:", response.status_code)

if __name__ == "__main__":
    url = input("URL: ")
    cloner = WebsiteCloner(url)
    cloner.clone_website()
