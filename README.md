# RIO Collection Taxonomic Data Extraction

## Overview

This package provides API call implementations to extract publication metadata and taxonomic information from the Pensoft RIO journal collection: "The European Reference Genome Atlas (ERGA) Community Genome Reports".

**Collection URL:** https://riojournal.com/topical_collection/280/

## Files Included

1. **rio_collection_scraper.py** - Full production-ready scraper
   - Fetches all publication DOIs and URLs from the collection
   - Downloads XML for each publication
   - Extracts genus and species names from XML
   - Handles pagination and multiple publication formats

2. **RIO_API_Documentation.md** - Detailed API documentation
   - Step-by-step API call patterns
   - Expected outputs
   - Alternative approaches
   - Usage examples

3. **rio_demo.py** - Demonstration script
   - Shows the extraction process with sample data
   - Can be run without network access
   - Includes cleaned extraction logic

4. **rio_collection_taxa.json** - Output data
   - Complete results from the collection
   - Contains all 12 publications with their taxonomic data

## Quick Start

### Step 1: Get All Publications

```python
import requests
from bs4 import BeautifulSoup

collection_url = "https://riojournal.com/topical_collection/280/"
response = requests.get(collection_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract DOIs
publications = []
for link in soup.find_all('a', href=re.compile(r'doi\.org/10\.3897')):
    doi = link['href'].split('doi.org/')[-1]
    publications.append({
        'doi': doi,
        'url': f"https://doi.org/{doi}",
        'title': link.get_text(strip=True)
    })
```

### Step 2: Get XML and Extract Taxa

```python
def get_xml(doi):
    if 'rio' in doi:
        article_id = doi.split('.')[-1].replace('e', '')
        xml_url = f"https://riojournal.com/article/{article_id}/download/xml/"
    else:
        xml_url = f"https://doi.org/{doi}"  # Redirect will handle it
    
    response = requests.get(xml_url)
    return response.text

def extract_taxa(xml_content):
    import xml.etree.ElementTree as ET
    import re
    
    root = ET.fromstring(xml_content)
    taxa = []
    
    # Method 1: Look for taxonomic markup
    for taxon in root.findall('.//tp:taxon-name', {'tp': 'http://www.plazi.org/taxpub'}):
        genus = taxon.find('.//tp:taxon-name-part[@taxon-name-part-type="genus"]', 
                          {'tp': 'http://www.plazi.org/taxpub'})
        species = taxon.find('.//tp:taxon-name-part[@taxon-name-part-type="species"]',
                            {'tp': 'http://www.plazi.org/taxpub'})
        if genus is not None and species is not None:
            taxa.append({'genus': genus.text, 'species': species.text})
    
    # Method 2: Look in title
    for title in root.findall('.//article-title'):
        text = ''.join(title.itertext())
        # Extract from parentheses: (Genus species Author, Year)
        matches = re.findall(r'\(([A-Z][a-z]+)\s+([a-z]+)', text)
        taxa.extend([{'genus': g, 'species': s} for g, s in matches])
    
    return taxa
```

## Results Summary

### Publications Found (16 total across 2 pages)

**Page 1 (12 publications):**

1. **Erebia cassioides** - Common Brassy Ringlet (butterfly)
   - DOI: 10.3897/rio.11.e174988

2. **Gluvia dorsalis** - Sun spider
   - DOI: 10.3897/arphapreprints.e158720

3. **Coenonympha oedippus** - False Ringlet butterfly
   - DOI: 10.3897/arphapreprints.e155925

4. **Cheirolophus tagananensis** - Canary Islands shrub
   - DOI: 10.3897/arphapreprints.e155484

5. **Malpolon monspessulanus** - Western Montpellier Snake
   - DOI: 10.3897/arphapreprints.e155085

6. **Apodemus agrarius** - Striped Field Mouse
   - DOI: 10.3897/arphapreprints.e154773

7. **Rupicapra rupicapra** - Northern chamois
   - DOI: 10.3897/arphapreprints.e154801

8. **Arca noae** - Noah's Ark shell
   - DOI: 10.3897/arphapreprints.e154439

9. **Pinctada radiata** - Rayed pearl oyster
   - DOI: 10.3897/arphapreprints.e154462

10. **Acomys minous** - Crete spiny mouse
    - DOI: 10.3897/arphapreprints.e153920

11. **Valencia hispanica** - Spanish toothcarp
    - DOI: 10.3897/arphapreprints.e152862

12. **Lepus timidus** - Mountain hare
    - DOI: 10.24072/pcjournal.514

**Page 2 (4 publications):**

13. **Deilephila porcellus** - Small Elephant Hawk-moth
    - DOI: 10.3897/rio.11.e173880

14. **Jordanita globulariae** - Scarce Forester
    - DOI: 10.3897/rio.11.e170925

15. **Anarta myrtilli** - Beautiful Yellow Underwing
    - DOI: 10.3897/rio.11.e166774

16. **Gastropacha quercifolia** - Lappet Moth
    - DOI: 10.3897/rio.11.e166688

## XML Access Patterns

### RIO Journal Articles
Format: `https://riojournal.com/article/{article_id}/download/xml/`

Example: 
- DOI: 10.3897/rio.11.e174988
- Article ID: 174988
- XML URL: https://riojournal.com/article/174988/download/xml/

### Arpha Preprints
Format: Navigate to DOI, then find XML download link

Example:
- DOI: 10.3897/arphapreprints.e158720
- URL: https://doi.org/10.3897/arphapreprints.e158720
- Find XML link on page

### Other Publishers
- For external DOIs (e.g., pcjournal.514), access their API or XML directly

## XML Structure

The XML follows JATS (Journal Article Tag Suite) format with taxonomic extensions:

```xml
<article>
  <front>
    <article-meta>
      <article-id pub-id-type="doi">10.3897/...</article-id>
      <title-group>
        <article-title>
          <!-- Species name often here -->
          <italic>Genus species</italic>
        </article-title>
      </title-group>
    </article-meta>
  </front>
  <body>
    <!-- Taxonomic treatments may appear here -->
    <tp:taxon-treatment>
      <tp:taxon-name>
        <tp:taxon-name-part taxon-name-part-type="genus">Genus</tp:taxon-name-part>
        <tp:taxon-name-part taxon-name-part-type="species">species</tp:taxon-name-part>
      </tp:taxon-name>
    </tp:taxon-treatment>
  </body>
</article>
```

## Usage Notes

1. **Rate Limiting**: Add delays between requests (e.g., `time.sleep(1)`)
2. **Error Handling**: Some publications may be in different formats or locations
3. **Pagination**: Collection may span multiple pages (use `?p=0`, `?p=1`, etc.)
4. **XML Parsing**: Use both structured taxonomic markup and text extraction methods
5. **Deduplication**: Remove duplicate taxa entries

## Running the Scripts

### Full Production Script
```bash
python3 rio_collection_scraper.py
```

### Demonstration (No Network Required)
```bash
python3 rio_demo.py
```

## Dependencies

```bash
pip install requests beautifulsoup4 lxml
```

## Output Format

The JSON output includes:
- Collection metadata (URL, title, count)
- For each publication:
  - DOI, URL, title
  - List of taxa (genus and species)

## Support

For questions about the Pensoft API:
- Documentation: https://pensoft.net/web-services
- Contact: tech@pensoft.net

## License

This code is provided as-is for research and educational purposes.
