#!/usr/bin/env python3
"""
Script to extract DOIs and taxonomic information from Pensoft RIO collection.

This script:
1. Scrapes the collection page to get all publication DOIs and URLs
2. For each publication, fetches the XML and extracts genus and species names
"""

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Set, Tuple
import time


class RIOCollectionScraper:
    """Scraper for Pensoft RIO collection articles."""
    
    def __init__(self, collection_url: str):
        self.collection_url = collection_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'
        })
    
    def get_all_publication_metadata(self) -> List[Dict[str, str]]:
        """
        Fetch all publication DOIs and URLs from the collection.
        
        Returns:
            List of dicts containing 'doi', 'url', 'title' for each publication
        """
        publications = []
        page = 0
        
        # Extract collection_id from URL for pagination
        collection_id = "280"  # Default
        match = re.search(r'collection[_/](\d+)', self.collection_url)
        if match:
            collection_id = match.group(1)
        
        while True:
            # Construct URL for current page
            # Format: /browse_topical_collection_documents.php?journal_name=rio&collection_id=280&lang=&journal_id=17&p=1
            if page == 0:
                url = self.collection_url
            else:
                # Use the browse endpoint for pagination
                base_url = "https://riojournal.com/browse_topical_collection_documents.php"
                url = f"{base_url}?journal_name=rio&collection_id={collection_id}&lang=&journal_id=17&p={page}"
            
            print(f"Fetching page {page + 1}: {url}")
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links on the page
            page_pubs = []
            articles_on_page = 0
            
            # Method 1: Find DOI links in the format doi.org/10.3897/...
            doi_pattern = re.compile(r'(https?://)?doi\.org/(10\.3897/[^\s"\'>]+)')
            for link in soup.find_all('a', href=doi_pattern):
                href = link.get('href', '')
                match = re.search(r'10\.3897/([^\s"\'>]+)', href)
                if match:
                    doi = f"10.3897/{match.group(1)}"
                    # Clean up DOI (remove trailing punctuation)
                    doi = re.sub(r'[,;:)\]}]+$', '', doi)
                    
                    # Try to find the title
                    title = link.get_text(strip=True)
                    if not title or len(title) < 10:
                        # Look for title in parent or sibling elements
                        parent = link.find_parent(['h3', 'h4', 'div'])
                        if parent:
                            title = parent.get_text(strip=True)
                    
                    page_pubs.append({
                        'doi': doi,
                        'url': f"https://doi.org/{doi}",
                        'title': title or f"Publication {doi}"
                    })
                    articles_on_page += 1
            
            # Method 2: Find article page links /article/\d+
            for link in soup.find_all('a', href=re.compile(r'/article/\d+')):
                article_url = link['href']
                if not article_url.startswith('http'):
                    article_url = f"https://riojournal.com{article_url}"
                
                # Extract article ID
                article_id = re.search(r'/article/(\d+)', link['href']).group(1)
                
                # Try to find the title
                title = link.get_text(strip=True)
                if not title or len(title) < 10:
                    parent = link.find_parent(['h3', 'h4', 'div'])
                    if parent:
                        title = parent.get_text(strip=True)
                
                # Check if we already have this via DOI
                if not any(p['url'] == article_url for p in page_pubs):
                    page_pubs.append({
                        'doi': None,  # Will try to extract from article page
                        'url': article_url,
                        'title': title or f"Article {article_id}",
                        'article_id': article_id
                    })
                    articles_on_page += 1
            
            # Method 3: Look for external DOIs (like pcjournal)
            external_doi_pattern = re.compile(r'doi\.org/(10\.\d+/[^\s"\'>]+)')
            for link in soup.find_all('a', href=external_doi_pattern):
                href = link.get('href', '')
                match = re.search(r'doi\.org/(10\.\d+/[^\s"\'>]+)', href)
                if match:
                    doi = match.group(1)
                    doi = re.sub(r'[,;:)\]}]+$', '', doi)
                    
                    # Skip if already added
                    if any(p['doi'] == doi for p in page_pubs):
                        continue
                    
                    title = link.get_text(strip=True)
                    if not title or len(title) < 10:
                        parent = link.find_parent(['h3', 'h4', 'div'])
                        if parent:
                            title = parent.get_text(strip=True)
                    
                    page_pubs.append({
                        'doi': doi,
                        'url': f"https://doi.org/{doi}",
                        'title': title or f"Publication {doi}"
                    })
                    articles_on_page += 1
            
            print(f"  Found {articles_on_page} articles on this page")
            
            if not page_pubs:
                print(f"  No articles found on page {page + 1}, stopping pagination")
                break
            
            publications.extend(page_pubs)
            
            # Check if there's a next page by looking for pagination links
            # Look for links with p= parameter
            next_page_links = soup.find_all('a', href=re.compile(rf'p={page + 1}'))
            
            if not next_page_links:
                print(f"  No next page link found, stopping pagination")
                break
            
            if page >= 10:  # Safety limit
                print(f"  Reached safety limit of 10 pages")
                break
            
            page += 1
            time.sleep(1)  # Be polite to the server
        
        # Deduplicate based on DOI or URL
        seen = set()
        unique_pubs = []
        for pub in publications:
            key = pub['doi'] or pub['url']
            if key not in seen:
                seen.add(key)
                unique_pubs.append(pub)
        
        return unique_pubs
    
    def get_xml_from_doi(self, doi: str) -> str:
        """
        Fetch the XML content for a given DOI.
        
        Args:
            doi: The DOI of the publication
            
        Returns:
            XML content as string
        """
        # Pensoft articles can be accessed as XML by adding /download/xml/
        if 'arphapreprints' in doi:
            # Arpha preprints XML URL format
            xml_url = f"https://doi.org/{doi}"
            # Try to get the actual article page first
            response = self.session.get(xml_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            xml_link = soup.find('a', href=re.compile(r'\.xml'))
            if xml_link:
                xml_url = xml_link['href']
                if not xml_url.startswith('http'):
                    xml_url = f"https://arphapreprints.com{xml_url}"
        else:
            # Regular RIO journal XML format
            article_id = doi.split('.')[-1].replace('e', '')
            xml_url = f"https://riojournal.com/article/{article_id}/download/xml/"
        
        print(f"  Fetching XML from: {xml_url}")
        response = self.session.get(xml_url)
        response.raise_for_status()
        
        return response.text
    
    def extract_taxa_from_xml(self, xml_content: str) -> List[Dict[str, str]]:
        """
        Extract genus and species names from XML content.
        
        Args:
            xml_content: XML string content
            
        Returns:
            List of dicts with 'genus' and 'species' keys
        """
        taxa = []
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Define namespaces commonly used in scientific articles
            namespaces = {
                'tp': 'http://www.plazi.org/taxpub',
                'xlink': 'http://www.w3.org/1999/xlink',
                'mml': 'http://www.w3.org/1998/Math/MathML'
            }
            
            # Method 1: Look for taxonomic names in specific tags
            # Check for <tp:taxon-name> elements
            for taxon in root.findall('.//tp:taxon-name', namespaces):
                genus_elem = taxon.find('.//tp:taxon-name-part[@taxon-name-part-type="genus"]', namespaces)
                species_elem = taxon.find('.//tp:taxon-name-part[@taxon-name-part-type="species"]', namespaces)
                
                if genus_elem is not None and species_elem is not None:
                    taxa.append({
                        'genus': genus_elem.text.strip() if genus_elem.text else '',
                        'species': species_elem.text.strip() if species_elem.text else ''
                    })
            
            # Method 2: Look for italic text that might be binomial names
            # This catches <italic>Genus species</italic> patterns
            for italic in root.findall('.//italic'):
                text = ''.join(italic.itertext()).strip()
                # Match binomial nomenclature pattern
                match = re.match(r'^([A-Z][a-z]+)\s+([a-z]+)$', text)
                if match:
                    taxa.append({
                        'genus': match.group(1),
                        'species': match.group(2)
                    })
            
            # Method 3: Look in article title for scientific names
            for title in root.findall('.//article-title'):
                text = ''.join(title.itertext())
                # Find all binomial names in the title
                matches = re.findall(r'([A-Z][a-z]+)\s+([a-z]+)', text)
                for match in matches:
                    taxa.append({
                        'genus': match[0],
                        'species': match[1]
                    })
            
            # Method 4: Check subject tags for taxonomic information
            for subject in root.findall('.//kwd'):
                text = ''.join(subject.itertext()).strip()
                match = re.match(r'^([A-Z][a-z]+)\s+([a-z]+)$', text)
                if match:
                    taxa.append({
                        'genus': match.group(1),
                        'species': match.group(2)
                    })
            
        except ET.ParseError as e:
            print(f"  Error parsing XML: {e}")
            return []
        
        # Deduplicate taxa
        unique_taxa = []
        seen = set()
        for taxon in taxa:
            key = (taxon['genus'], taxon['species'])
            if key not in seen and taxon['genus'] and taxon['species']:
                seen.add(key)
                unique_taxa.append(taxon)
        
        return unique_taxa


def main():
    """Main execution function."""
    collection_url = "https://riojournal.com/topical_collection/280/"
    
    print("=" * 80)
    print("RIO Collection Taxonomic Data Extractor")
    print("=" * 80)
    print()
    
    scraper = RIOCollectionScraper(collection_url)
    
    # Step 1: Get all publication metadata
    print("Step 1: Fetching all publication DOIs and URLs...")
    print("-" * 80)
    publications = scraper.get_all_publication_metadata()
    print(f"\nFound {len(publications)} publications")
    print()
    
    # Display the list
    print("Step 1 Results: Publication Metadata")
    print("-" * 80)
    for i, pub in enumerate(publications, 1):
        print(f"{i}. DOI: {pub['doi']}")
        print(f"   URL: {pub['url']}")
        print(f"   Title: {pub['title'][:80]}...")
        print()
    
    # Step 2: For each publication, extract taxonomic information
    print("\n" + "=" * 80)
    print("Step 2: Extracting taxonomic information from each publication")
    print("=" * 80)
    print()
    
    results = []
    
    for i, pub in enumerate(publications, 1):
        print(f"\n[{i}/{len(publications)}] Processing: {pub['title'][:60]}...")
        print(f"  DOI: {pub['doi']}")
        
        if not pub['doi']:
            print("  ⚠ No DOI available, skipping XML extraction")
            results.append({
                'publication': pub,
                'taxa': [],
                'error': 'No DOI available'
            })
            continue
        
        try:
            # Get XML
            xml_content = scraper.get_xml_from_doi(pub['doi'])
            
            # Extract taxa
            taxa = scraper.extract_taxa_from_xml(xml_content)
            
            print(f"  ✓ Found {len(taxa)} taxa")
            for taxon in taxa:
                print(f"    - {taxon['genus']} {taxon['species']}")
            
            results.append({
                'publication': pub,
                'taxa': taxa,
                'error': None
            })
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                'publication': pub,
                'taxa': [],
                'error': str(e)
            })
        
        time.sleep(1)  # Be polite to the server
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total publications: {len(publications)}")
    print(f"Successfully processed: {sum(1 for r in results if not r['error'])}")
    print(f"Errors: {sum(1 for r in results if r['error'])}")
    print(f"Total taxa found: {sum(len(r['taxa']) for r in results)}")
    
    return results


if __name__ == "__main__":
    results = main()
