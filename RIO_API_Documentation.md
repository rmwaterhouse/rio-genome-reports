# API Calls for RIO Collection Taxonomic Data Extraction

## Overview
This document describes the API calls needed to:
1. Get all publication DOIs and URLs from the ERGA Community Genome Reports collection
2. For each publication, fetch the XML and extract genus and species names

## Step 1: Get All Publication Metadata

### API Call Pattern

```python
import requests
from bs4 import BeautifulSoup
import re

def get_collection_publications(collection_url):
    """
    Fetch all publications from a RIO collection with pagination support.
    
    Args:
        collection_url: URL of the collection (e.g., https://riojournal.com/topical_collection/280/)
    
    Returns:
        List of dicts with 'doi', 'url', 'title' for each publication
    """
    publications = []
    page = 0
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'
    })
    
    # Extract collection_id from URL
    collection_id = re.search(r'collection[_/](\d+)', collection_url).group(1)
    
    while True:
        # Construct paginated URL
        # Page 0: Use the original collection URL
        # Page 1+: Use the browse_topical_collection_documents.php endpoint
        if page == 0:
            url = collection_url
        else:
            base_url = "https://riojournal.com/browse_topical_collection_documents.php"
            url = f"{base_url}?journal_name=rio&collection_id={collection_id}&lang=&journal_id=17&p={page}"
        
        print(f"Fetching page {page + 1}: {url}")
        response = session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles_on_page = 0
        
        # Extract DOIs and URLs from the page
        # Method 1: Direct DOI links (format: doi.org/10.3897/...)
        doi_pattern = re.compile(r'doi\.org/(10\.3897/[^\s"\'>]+)')
        for link in soup.find_all('a', href=doi_pattern):
            match = re.search(r'10\.3897/([^\s"\'>]+)', link['href'])
            if match:
                doi = f"10.3897/{match.group(1)}"
                doi = re.sub(r'[,;:)\]}]+$', '', doi)  # Clean trailing punctuation
                
                publications.append({
                    'doi': doi,
                    'url': f"https://doi.org/{doi}",
                    'title': link.get_text(strip=True)
                })
                articles_on_page += 1
        
        # Method 2: Article page links (/article/\d+)
        for link in soup.find_all('a', href=re.compile(r'/article/\d+')):
            article_url = link['href']
            if not article_url.startswith('http'):
                article_url = f"https://riojournal.com{article_url}"
            
            # Avoid duplicates
            if not any(p['url'] == article_url for p in publications):
                publications.append({
                    'url': article_url,
                    'title': link.get_text(strip=True)
                })
                articles_on_page += 1
        
        # Method 3: External DOIs (like pcjournal)
        external_doi_pattern = re.compile(r'doi\.org/(10\.\d+/[^\s"\'>]+)')
        for link in soup.find_all('a', href=external_doi_pattern):
            match = re.search(r'doi\.org/(10\.\d+/[^\s"\'>]+)', link['href'])
            if match:
                doi = match.group(1)
                doi = re.sub(r'[,;:)\]}]+$', '', doi)
                
                if not any(p.get('doi') == doi for p in publications):
                    publications.append({
                        'doi': doi,
                        'url': f"https://doi.org/{doi}",
                        'title': link.get_text(strip=True)
                    })
                    articles_on_page += 1
        
        print(f"  Found {articles_on_page} articles on page {page + 1}")
        
        # Check for next page
        if articles_on_page == 0:
            print(f"  No articles found, stopping pagination")
            break
        
        # Look for pagination links
        next_page_links = soup.find_all('a', href=re.compile(rf'p={page + 1}'))
        if not next_page_links:
            print(f"  No next page link found, stopping pagination")
            break
        
        if page >= 10:  # Safety limit
            print(f"  Reached safety limit")
            break
        
        page += 1
        time.sleep(1)  # Rate limiting
    
    return publications

# Usage
collection_url = "https://riojournal.com/topical_collection/280/"
publications = get_collection_publications(collection_url)
```

### Expected Output (Step 1)

Based on the collection page (2 pages), here are the publications found:

**Page 1 (12 publications):**

```python
[
    {
        'doi': '10.3897/rio.11.e174988',
        'url': 'https://doi.org/10.3897/rio.11.e174988',
        'title': 'The genome sequence of the Common Brassy Ringlet, Erebia cassioides'
    },
    {
        'doi': '10.3897/arphapreprints.e158720',
        'url': 'https://doi.org/10.3897/arphapreprints.e158720',
        'title': 'ERGA-BGE Reference Genome of Gluvia dorsalis'
    },
    # ... (continues with all 12 publications from page 1)
]
```

**Page 2 (4 publications):**

```python
[
    {
        'doi': '10.3897/rio.11.e173880',
        'url': 'https://doi.org/10.3897/rio.11.e173880',
        'title': 'The genome sequence of the Small Elephant Hawk-moth, Deilephila porcellus'
    },
    {
        'doi': '10.3897/rio.11.e170925',
        'url': 'https://doi.org/10.3897/rio.11.e170925',
        'title': 'The genome sequence of the Scarce Forester, Jordanita globulariae'
    },
    {
        'doi': '10.3897/rio.11.e166774',
        'url': 'https://doi.org/10.3897/rio.11.e166774',
        'title': 'The genome sequence of the Beautiful Yellow Underwing, Anarta myrtilli'
    },
    {
        'doi': '10.3897/rio.11.e166688',
        'url': 'https://doi.org/10.3897/rio.11.e166688',
        'title': 'The genome sequence of the Lappet Moth, Gastropacha quercifolia'
    }
]
```

**Total: 16 publications**

## Step 2: Extract Taxonomic Data from XML

### API Call Pattern for Each Publication

```python
import xml.etree.ElementTree as ET
import re

def get_xml_from_doi(doi):
    """
    Fetch XML content for a publication.
    
    Args:
        doi: The DOI of the publication
    
    Returns:
        XML content as string
    """
    session = requests.Session()
    
    if 'arphapreprints' in doi:
        # For Arpha Preprints, get the XML download link
        response = session.get(f"https://doi.org/{doi}")
        soup = BeautifulSoup(response.content, 'html.parser')
        xml_link = soup.find('a', href=re.compile(r'download/xml'))
        if xml_link:
            xml_url = xml_link['href']
            if not xml_url.startswith('http'):
                xml_url = f"https://arphapreprints.com{xml_url}"
    elif 'rio' in doi:
        # For RIO journal articles
        article_id = doi.split('.')[-1].replace('e', '')
        xml_url = f"https://riojournal.com/article/{article_id}/download/xml/"
    else:
        # For other publishers, try common patterns
        xml_url = f"https://doi.org/{doi}"
    
    response = session.get(xml_url)
    return response.text


def extract_taxa_from_xml(xml_content):
    """
    Extract genus and species from XML.
    
    Args:
        xml_content: XML string
    
    Returns:
        List of dicts with 'genus' and 'species'
    """
    taxa = []
    root = ET.fromstring(xml_content)
    
    # Method 1: Look for taxonomic markup (JATS/TaxPub format)
    namespaces = {
        'tp': 'http://www.plazi.org/taxpub',
    }
    
    for taxon in root.findall('.//tp:taxon-name', namespaces):
        genus_elem = taxon.find('.//tp:taxon-name-part[@taxon-name-part-type="genus"]', namespaces)
        species_elem = taxon.find('.//tp:taxon-name-part[@taxon-name-part-type="species"]', namespaces)
        
        if genus_elem is not None and species_elem is not None:
            taxa.append({
                'genus': genus_elem.text.strip(),
                'species': species_elem.text.strip()
            })
    
    # Method 2: Look for italic binomial names
    for italic in root.findall('.//italic'):
        text = ''.join(italic.itertext()).strip()
        match = re.match(r'^([A-Z][a-z]+)\s+([a-z]+)$', text)
        if match:
            taxa.append({
                'genus': match.group(1),
                'species': match.group(2)
            })
    
    # Method 3: Extract from article title
    for title in root.findall('.//article-title'):
        text = ''.join(title.itertext())
        # Find all binomial names
        matches = re.findall(r'\b([A-Z][a-z]+)\s+([a-z]+)\b', text)
        for match in matches:
            taxa.append({
                'genus': match[0],
                'species': match[1]
            })
    
    # Deduplicate
    unique_taxa = []
    seen = set()
    for taxon in taxa:
        key = (taxon['genus'], taxon['species'])
        if key not in seen and taxon['genus'] and taxon['species']:
            seen.add(key)
            unique_taxa.append(taxon)
    
    return unique_taxa


# Usage for each publication
def process_publication(doi):
    """Process a single publication to extract taxa."""
    xml_content = get_xml_from_doi(doi)
    taxa = extract_taxa_from_xml(xml_content)
    return taxa
```

## Complete Example Workflow

```python
# Step 1: Get all publications
collection_url = "https://riojournal.com/topical_collection/280/"
publications = get_collection_publications(collection_url)

print(f"Found {len(publications)} publications")

# Step 2: Process each publication
results = []
for pub in publications:
    print(f"Processing: {pub['title']}")
    try:
        xml_content = get_xml_from_doi(pub['doi'])
        taxa = extract_taxa_from_xml(xml_content)
        
        results.append({
            'doi': pub['doi'],
            'url': pub['url'],
            'title': pub['title'],
            'taxa': taxa
        })
        
        print(f"  Found {len(taxa)} taxa:")
        for taxon in taxa:
            print(f"    - {taxon['genus']} {taxon['species']}")
    
    except Exception as e:
        print(f"  Error: {e}")
        results.append({
            'doi': pub['doi'],
            'url': pub['url'],
            'title': pub['title'],
            'taxa': [],
            'error': str(e)
        })

# Display final results
import json
print(json.dumps(results, indent=2))
```

## Expected Taxa Output (Based on Titles)

From the collection, here are the species that should be found:

1. **Erebia cassioides** - Common Brassy Ringlet (butterfly)
2. **Gluvia dorsalis** - Sun spider
3. **Coenonympha oedippus** - False Ringlet butterfly
4. **Cheirolophus tagananensis** - Canary Islands shrub
5. **Malpolon monspessulanus** - Western Montpellier Snake
6. **Apodemus agrarius** - Striped Field Mouse
7. **Rupicapra rupicapra** - Northern chamois
8. **Arca noae** - Noah's Ark shell
9. **Pinctada radiata** - Rayed pearl oyster
10. **Acomys minous** - Crete spiny mouse
11. **Valencia hispanica** - Spanish toothcarp
12. **Lepus timidus** - Mountain hare
13. **Deilephila porcellus** - Small Elephant Hawk-moth
14. **Jordanita globulariae** - Scarce Forester
15. **Anarta myrtilli** - Beautiful Yellow Underwing
16. **Gastropacha quercifolia** - Lappet Moth

## Alternative: Using Pensoft's API

Pensoft may also provide direct API access. Check their documentation:
- https://pensoft.net/web-services
- Contact: tech@pensoft.net

## Notes

- Some publications may be in different formats (Arpha Preprints vs RIO Journal)
- XML structure may vary between publishers
- **Pagination**: The collection spans multiple pages. Page 1 uses the direct collection URL, while subsequent pages use the browse_topical_collection_documents.php endpoint with the `p` parameter
- Additional pages format: `https://riojournal.com/browse_topical_collection_documents.php?journal_name=rio&collection_id=280&lang=&journal_id=17&p=1`
- Rate limiting: Add delays between requests (e.g., `time.sleep(1)`)
- Some DOIs may redirect to external sites (e.g., Peer Community Journal)
