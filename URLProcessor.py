import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse

class URLProcessor:
    def normalize_url(self, url):
        parsed_url = urlparse(url)
        scheme = 'https' if not parsed_url.scheme else parsed_url.scheme
        netloc = parsed_url.netloc.replace('www.', '')
        normalized = urlunparse((scheme, netloc, parsed_url.path, '', parsed_url.query, ''))
        return normalized

    def get_all_links(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = set()

            for a_tag in soup.find_all('a', href=True):
                absolute_url = urljoin(url, a_tag['href'])
                normalized_url = self.normalize_url(absolute_url)
                links.add(normalized_url)

            return links
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return set()

    def find_components(self, url, all_unique):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            all_divs = soup.find_all('div')
            unique_contents = set()

            def find_most_inner_content(element):
                inner_divs = element.find_all('div')
                if not inner_divs:
                    return element.get_text(strip=True)
                else:
                    return find_most_inner_content(inner_divs[-1])

            for div in all_divs:
                most_inner_content = find_most_inner_content(div).lower()
                unique_contents.add(most_inner_content)

            all_unique.update(unique_contents)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")

