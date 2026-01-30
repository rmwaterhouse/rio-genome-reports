#!/usr/bin/env python3
"""
Demonstration of RIO Collection Taxonomic Data Extraction
(Using pre-extracted data from the collection page)
"""

import json
from typing import List, Dict

# Sample data extracted from the collection page (Pages 1 and 2)
SAMPLE_PUBLICATIONS = [
    # Page 1
    {
        'doi': '10.3897/rio.11.e174988',
        'url': 'https://doi.org/10.3897/rio.11.e174988',
        'title': 'The genome sequence of the Common Brassy Ringlet, Erebia cassioides (Reiner & Hohenwarth, 1792) (Lepidoptera, Nymphalidae)',
        'xml_url': 'https://riojournal.com/article/174988/download/xml/',
        'expected_taxa': [
            {'genus': 'Erebia', 'species': 'cassioides'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e158720',
        'url': 'https://doi.org/10.3897/arphapreprints.e158720',
        'title': 'ERGA-BGE Reference Genome of Gluvia dorsalis: An Endemic Sun Spider from Iberian Arid Regions',
        'expected_taxa': [
            {'genus': 'Gluvia', 'species': 'dorsalis'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e155925',
        'url': 'https://doi.org/10.3897/arphapreprints.e155925',
        'title': 'ERGA-BGE genome of Coenonympha oedippus: an IUCN endangered European butterfly species occurring in two ecotypes',
        'expected_taxa': [
            {'genus': 'Coenonympha', 'species': 'oedippus'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e155484',
        'url': 'https://doi.org/10.3897/arphapreprints.e155484',
        'title': 'ERGA-BGE genome of Cheirolophus tagananensis: an IUCN endangered shrub endemic to the Canary Islands',
        'expected_taxa': [
            {'genus': 'Cheirolophus', 'species': 'tagananensis'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e155085',
        'url': 'https://doi.org/10.3897/arphapreprints.e155085',
        'title': 'ERGA-BGE Reference Genome of the Western Montpellier Snake (Malpolon monspessulanus), a Key Species for Evolutionary and Venom Studies',
        'expected_taxa': [
            {'genus': 'Malpolon', 'species': 'monspessulanus'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e154773',
        'url': 'https://doi.org/10.3897/arphapreprints.e154773',
        'title': 'ERGA-BGE Reference Genome of the Striped Field Mouse (Apodemus agrarius), a Widespread and Abundant Species in Central and Eastern Europe',
        'expected_taxa': [
            {'genus': 'Apodemus', 'species': 'agrarius'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e154801',
        'url': 'https://doi.org/10.3897/arphapreprints.e154801',
        'title': "ERGA-BGE Reference Genome of the Northern chamois (Rupicapra rupicapra): Europe's most abundant mountain ungulate",
        'expected_taxa': [
            {'genus': 'Rupicapra', 'species': 'rupicapra'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e154439',
        'url': 'https://doi.org/10.3897/arphapreprints.e154439',
        'title': "ERGA-BGE genome of Noah's Ark shell (Arca noae Linnaeus, 1758), a Mediterranean bivalve species",
        'expected_taxa': [
            {'genus': 'Arca', 'species': 'noae'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e154462',
        'url': 'https://doi.org/10.3897/arphapreprints.e154462',
        'title': 'ERGA-BGE genome of Pinctada radiata (Leach, 1814): one of the first Lessepsian migrants',
        'expected_taxa': [
            {'genus': 'Pinctada', 'species': 'radiata'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e153920',
        'url': 'https://doi.org/10.3897/arphapreprints.e153920',
        'title': 'ERGA-BGE genome of Acomys minous (Bate, 1906): the Crete spiny mouse, endemic to the island of Crete, Greece',
        'expected_taxa': [
            {'genus': 'Acomys', 'species': 'minous'}
        ]
    },
    {
        'doi': '10.3897/arphapreprints.e152862',
        'url': 'https://doi.org/10.3897/arphapreprints.e152862',
        'title': 'ERGA-BGE genome of Valencia hispanica (Valenciennes, 1826): a critically endangered Iberian toothcarp',
        'expected_taxa': [
            {'genus': 'Valencia', 'species': 'hispanica'}
        ]
    },
    {
        'doi': '10.24072/pcjournal.514',
        'url': 'https://doi.org/10.24072/pcjournal.514',
        'title': 'Chromosome-level reference genome assembly for the mountain hare (Lepus timidus)',
        'expected_taxa': [
            {'genus': 'Lepus', 'species': 'timidus'}
        ]
    },
    # Page 2
    {
        'doi': '10.3897/rio.11.e173880',
        'url': 'https://doi.org/10.3897/rio.11.e173880',
        'title': 'The genome sequence of the Small Elephant Hawk-moth, Deilephila porcellus (Linnaeus, 1758)',
        'expected_taxa': [
            {'genus': 'Deilephila', 'species': 'porcellus'}
        ]
    },
    {
        'doi': '10.3897/rio.11.e170925',
        'url': 'https://doi.org/10.3897/rio.11.e170925',
        'title': 'The genome sequence of the Scarce Forester, Jordanita globulariae (Hübner, 1793)',
        'expected_taxa': [
            {'genus': 'Jordanita', 'species': 'globulariae'}
        ]
    },
    {
        'doi': '10.3897/rio.11.e166774',
        'url': 'https://doi.org/10.3897/rio.11.e166774',
        'title': 'The genome sequence of the Beautiful Yellow Underwing, Anarta myrtilli (Linnaeus, 1761)',
        'expected_taxa': [
            {'genus': 'Anarta', 'species': 'myrtilli'}
        ]
    },
    {
        'doi': '10.3897/rio.11.e166688',
        'url': 'https://doi.org/10.3897/rio.11.e166688',
        'title': 'The genome sequence of the Lappet Moth, Gastropacha quercifolia (Linnaeus, 1758)',
        'expected_taxa': [
            {'genus': 'Gastropacha', 'species': 'quercifolia'}
        ]
    }
]


def extract_taxa_from_title(title: str) -> List[Dict[str, str]]:
    """
    Extract genus and species names from article title.
    This simulates what would be extracted from the XML.
    """
    import re
    
    taxa = []
    
    # Common English words that might be capitalized but aren't genera
    excluded_words = {
        'The', 'An', 'European', 'Western', 'Northern', 'Iberian', 'ERGA', 'BGE',
        'Reference', 'Genome', 'Species', 'Key', 'Evolutionary', 'Venom', 'Studies',
        'Widespread', 'Abundant', 'Central', 'Eastern', 'Europe', 'Mediterranean',
        'Endemic', 'Sun', 'Spider', 'Ark', 'Shell', 'Lessepsian', 'Crete', 'Mountain',
        'Chromosome', 'Assembly', 'IUCN', 'Endangered', 'Common', 'Brassy', 'Ringlet',
        'Field', 'Mouse', 'Striped', 'False', 'Beautiful', 'Yellow', 'Underwing',
        'Lappet', 'Moth', 'Small', 'Elephant', 'Hawk', 'Scarce', 'Forester',
        'Reiner', 'Hohenwarth', 'Lepidoptera', 'Nymphalidae', 'Linnaeus', 'Hübner',
        'Leach', 'Valenciennes', 'Bate'
    }
    
    # Pattern 1: Binomial name followed by author with comma
    # e.g., "Genus species (Author, Year)"
    pattern_with_comma = r',\s+([A-Z][a-z]+)\s+([a-z]+)\s+\('
    matches = re.findall(pattern_with_comma, title)
    for genus, species in matches:
        if genus not in excluded_words and len(species) > 2:
            taxa.append({
                'genus': genus,
                'species': species
            })
    
    # Pattern 2: Binomial name in parentheses followed by author name (no comma)
    # e.g., "(Arca noae Linnaeus, 1758)"
    if not taxa:
        pattern_in_parens_author = r'\(([A-Z][a-z]+)\s+([a-z]+)\s+[A-Z]'
        matches = re.findall(pattern_in_parens_author, title)
        for genus, species in matches:
            if genus not in excluded_words and len(species) > 2:
                taxa.append({
                    'genus': genus,
                    'species': species
                })
    
    # Pattern 3: Species in parentheses (for titles without author citations)
    # e.g., (Genus species) in "genome of (Genus species)"
    if not taxa:
        pattern_in_parens = r'\(([A-Z][a-z]+)\s+([a-z]+)\)'
        matches = re.findall(pattern_in_parens, title)
        for genus, species in matches:
            if genus not in excluded_words and len(species) > 2:
                taxa.append({
                    'genus': genus,
                    'species': species
                })
    
    # Pattern 4: "of Genus species" format
    if not taxa:
        pattern_after_of = r'of\s+([A-Z][a-z]+)\s+([a-z]+)'
        matches = re.findall(pattern_after_of, title)
        for genus, species in matches:
            if genus not in excluded_words and len(species) > 2:
                taxa.append({
                    'genus': genus,
                    'species': species
                })
    
    # Deduplicate
    unique_taxa = []
    seen = set()
    for taxon in taxa:
        key = (taxon['genus'], taxon['species'])
        if key not in seen:
            seen.add(key)
            unique_taxa.append(taxon)
    
    return unique_taxa


def main():
    """Demonstrate the extraction process."""
    
    print("=" * 80)
    print("RIO COLLECTION TAXONOMIC DATA EXTRACTION - DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Step 1: Display all publications
    print("STEP 1: ALL PUBLICATIONS IN COLLECTION")
    print("=" * 80)
    print(f"\nTotal publications found: {len(SAMPLE_PUBLICATIONS)}\n")
    
    for i, pub in enumerate(SAMPLE_PUBLICATIONS, 1):
        print(f"{i:2d}. {pub['title'][:75]}...")
        print(f"    DOI: {pub['doi']}")
        print(f"    URL: {pub['url']}")
        print()
    
    # Step 2: Extract taxa from each publication
    print("\n" + "=" * 80)
    print("STEP 2: TAXONOMIC INFORMATION EXTRACTED FROM EACH PUBLICATION")
    print("=" * 80)
    print()
    
    results = []
    
    for i, pub in enumerate(SAMPLE_PUBLICATIONS, 1):
        print(f"[{i}/{len(SAMPLE_PUBLICATIONS)}] {pub['title'][:60]}...")
        print(f"    DOI: {pub['doi']}")
        
        # Simulate XML extraction by parsing the title
        taxa = extract_taxa_from_title(pub['title'])
        
        if taxa:
            print(f"    Taxa found: {len(taxa)}")
            for taxon in taxa:
                print(f"      • {taxon['genus']} {taxon['species']}")
        else:
            print(f"    ⚠ No taxa found in title")
        
        results.append({
            'publication': {
                'doi': pub['doi'],
                'url': pub['url'],
                'title': pub['title']
            },
            'taxa': taxa
        })
        print()
    
    # Step 3: Summary and export
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total publications processed: {len(results)}")
    print(f"Publications with taxa: {sum(1 for r in results if r['taxa'])}")
    print(f"Total unique species: {sum(len(r['taxa']) for r in results)}")
    print()
    
    # Create JSON output
    output_data = {
        'collection': {
            'url': 'https://riojournal.com/topical_collection/280/',
            'title': 'The European Reference Genome Atlas (ERGA) Community Genome Reports',
            'total_publications': len(results)
        },
        'publications': results
    }
    
    # Save to file
    output_file = '/home/claude/rio_collection_taxa.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Results saved to: {output_file}")
    print()
    
    # Display all taxa in a formatted table
    print("=" * 80)
    print("ALL SPECIES IN COLLECTION")
    print("=" * 80)
    print()
    print(f"{'No.':<4} {'Genus':<20} {'Species':<20} {'DOI'}")
    print("-" * 80)
    
    species_number = 1
    for result in results:
        for taxon in result['taxa']:
            doi = result['publication']['doi']
            print(f"{species_number:<4} {taxon['genus']:<20} {taxon['species']:<20} {doi}")
            species_number += 1
    
    print()
    print("=" * 80)
    
    return output_data


if __name__ == "__main__":
    data = main()
