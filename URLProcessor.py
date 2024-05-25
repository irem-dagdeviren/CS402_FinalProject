import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse

from langdetect import detect, LangDetectException

class URLProcessor:
    def __init__(self):
        self.languages = set()

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
            hasInstagram = False
            hasFacebook = False
            hasTwitter = False
            hasTripAdvisor = False
            hasMap = False

            for a_tag in soup.find_all('a', href=True):
                absolute_url = urljoin(url, a_tag['href'])
                normalized_url = self.normalize_url(absolute_url)
                print(normalized_url)
                if 'instagram' in normalized_url.lower():
                    hasInstagram = True
                if 'facebook' in normalized_url.lower():
                    hasFacebook = True
                if 'twitter' in normalized_url.lower():
                    hasTwitter = True
                if 'tripadvisor' in normalized_url.lower():
                    hasTripAdvisor = True
                if ('maps' in normalized_url.lower()):
                    hasMap = True
                links.add(normalized_url)

            return links, hasInstagram, hasFacebook, hasTwitter, hasTripAdvisor, hasMap
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return set(), False, False, False, False, False

    def find_components(self, url, all_unique):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            language = self.detect_language(soup)
            self.languages.add(language)
            all_divs = soup.find_all('div')
            unique_contents = set()
            print(language)

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

    def detect_language(self, soup):
        # Check for <html lang="..."> attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            lang_code = html_tag.get('lang').split('-')[0]
            return lang_code

        # Check for <meta> tags
        meta_tag = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if meta_tag and meta_tag.get('content'):
            lang_code = meta_tag['content'].split('-')[0]
            return lang_code

        # Fallback to language detection library
        try:
            text_content = ' '.join([p.get_text() for p in soup.find_all('p')])
            if text_content:
                lang_code = detect(text_content).split('-')[0]
                return lang_code
        except LangDetectException:
            pass

        return 'Unknown'

# Usage example
processor = URLProcessor()
links, hasInstagram, hasFacebook, hasTwitter, hasTripAdvisor, hasMap = processor.get_all_links('https://example.com')
print(f"Links: {links}")
print(f"Has Instagram: {hasInstagram}")
print(f"Has Facebook: {hasFacebook}")
print(f"Has Twitter: {hasTwitter}")
print(f"Has TripAdvisor: {hasTripAdvisor}")
print(f"Has Maps: {hasMap}")
print(f"Languages: {processor.languages}")
