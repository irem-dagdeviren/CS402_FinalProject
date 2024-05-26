from bs4 import BeautifulSoup
import requests
from langdetect import detect, LangDetectException
from urllib.parse import urljoin, urlparse, urlunparse

class URLProcessor:
    def __init__(self):
        self.languages = set()
        self.slider = False
        self.datepicker = False
        self.searchbar = False

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

                if 'instagram' in normalized_url.lower():
                    hasInstagram = True
                if 'facebook' in normalized_url.lower():
                    hasFacebook = True
                if 'twitter' in normalized_url.lower():
                    hasTwitter = True
                if 'tripadvisor' in normalized_url.lower():
                    hasTripAdvisor = True
                if 'maps' in normalized_url.lower():
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
            if not self.slider:
                    self.slider = self.detect_web_slider_elements(soup)
            if not self.datepicker:
                self.datepicker = self.detect_web_calendar_elements(soup)
            if not self.searchbar:
                self.searchbar = self.detect_web_searchbar_elements(soup)

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
            return False, False, False, False

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
            print(f"{LangDetectException}")
        return 'Unknown'
    
    def detect_web_calendar_elements(self, soup):
        if self.datepicker:
            return self.datepicker  # Already found
        try:
            datepicker_keywords = ['datepicker', 'date-picker', 'calendar']
            for keyword in datepicker_keywords:
                if soup.find(lambda tag: keyword in str(tag).lower()):
                    self.datepicker = True
                    break
        except Exception as e:
            print(f"Error detecting datepicker: {e}")
        return self.datepicker

    def detect_web_slider_elements(self, soup):
        if self.slider:
            return self.slider  # Already found
        try:
            if soup.find(lambda tag: 'slider' in str(tag).lower()):
                self.slider = True
        except Exception as e:
            print(f"Error detecting slider: {e}")
        return self.slider
    
    def detect_web_searchbar_elements(self, soup):
        if self.searchbar:
            return self.searchbar  # Already found
        try:
            searchbar_keywords = ['searchbar', 'search-bar']
            for keyword in searchbar_keywords:
                if soup.find(lambda tag: keyword in str(tag).lower()):
                    self.searchbar = True
                    break
        except Exception as e:
            print(f"Error detecting search bar: {e}")
        return self.searchbar
