from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime

def clean_candidate_name(name):
    """Clean candidate name by removing party suffixes"""
    return name.replace('Democratic', '').replace('Republican', '').strip()

def generate_candidate_id(name):
    """Generate a candidate ID from name"""
    name = clean_candidate_name(name)
    candidate_id = name.lower().replace(' ', '_').replace('.', '').replace("'", '').replace('-', '_')
    return candidate_id

def load_existing_candidates(data_repo_path):
    """Load existing candidate IDs from index.json"""
    index_path = os.path.join(data_repo_path, 'candidates', 'index.json')
    
    if not os.path.exists(index_path):
        print(f"⚠️  candidates/index.json not found at: {index_path}")
        return set()
    
    with open(index_path, 'r') as f:
        candidates_list = json.load(f)
    
    existing_ids = {c['id'] for c in candidates_list}
    print(f"📁 Loaded {len(existing_ids)} existing candidates from index.json")
    return existing_ids

def scrape_race(page, url, race_name):
    """Scrape a single race and return candidate data"""
    print(f"\nScraping {race_name}...")
    
    page.goto(url)
    page.wait_for_timeout(5000)
    
    soup = BeautifulSoup(page.content(), 'html.parser')
    table = soup.find('table', {'role': 'table'})
    
    if not table:
        print(f"  ❌ No table found for {race_name}")
        return []
    
    tbody = table.find('tbody')
    if not tbody:
        print(f"  ❌ No tbody found for {race_name}")
        return []
    
    rows = tbody.find_all('tr', {'role': 'row'})
    print(f"  Found {len(rows)} candidates")
    
    candidates = []
    for row in rows:
        cells = row.find_all('td')
        
        if len(cells) >= 6:
            name_link = cells[0].find('a')
            name = name_link.get_text(strip=True) if name_link else cells[0].get_text(strip=True)
            
            candidate = {
                'name': name,
                'party': cells[1].get_text(strip=True),
                'contributions': cells[2].get_text(strip=True),
                'loans': cells[3].get_text(strip=True),
                'expenditures': cells[4].get_text(strip=True),
                'status': cells[5].get_text(strip=True)
            }
            
            candidates.append(candidate)
            print(f"    ✓ {clean_candidate_name(name)} - {candidate['party']} - {candidate['contributions']}")
    
    return candidates

RACES = {
    'governor': {
        'name': 'Governor',
        'url': 'https://www.transparencyusa.org/ga/race/governor-of-georgia-76665?cycle=2026-election-cycle',
        'race_id': 'ga_governor'
    },
    'lt_governor': {
        'name': 'Lieutenant Governor',
        'url': 'https://www.transparencyusa.org/ga/race/lieutenant-governor-of-georgia-76666?cycle=2026-election-cycle',
        'race_id': 'ga_lt_governor'
    },
    'attorney_general': {
        'name': 'Attorney General',
        'url': 'https://www.transparencyusa.org/ga/race/attorney-general-of-georgia-76669?cycle=2026-election-cycle',
        'race_id': 'ga_attorney_general'
    },
    'secretary_of_state': {
        'name': 'Secretary of State',
        'url': 'https://www.transparencyusa.org/ga/race/georgia-secretary-of-state-76671?cycle=2026-election-cycle',
        'race_id': 'ga_secretary_of_state'
    },
    'senate_18': {
        'name': 'State Senate District 18',
        'url': 'https://www.transparencyusa.org/ga/race/georgia-state-senate-district-18-71888?cycle=2026-election-cycle',
        'race_id': 'ga_senate_18'
    },
    'senate_20': {
        'name': 'State Senate District 20',
        'url': 'https://www.transparencyusa.org/ga/race/georgia-state-senate-district-20-71891?cycle=2026-election-cycle',
        'race_id': 'ga_senate_20'
    },
    'senate_26': {
        'name': 'State Senate District 26',
        'url': 'https://www.transparencyusa.org/ga/race/georgia-state-senate-district-26-71897?cycle=2026-election-cycle',
        'race_id': 'ga_senate_26'
    },
    'house_134': {
        'name': 'State House District 134',
        'url': 'https://www.transparencyusa.org/ga/race/georgia-house-of-representatives-district-134-71974?cycle=2026-election-cycle',
        'race_id': 'ga_house_134'
    },
    'house_143': {
        'name': 'State House District 143',
        'url': 'https://www.transparencyusa.org/ga/race/georgia-house-of-representatives-district-143-71984?cycle=2026-election-cycle',
        'race_id': 'ga_house_143'
    },
    'house_146': {
        'name': 'State House District 146',
        'url': 'https://www.transparencyusa.org/ga/race/georgia-house-of-representatives-district-146-71987?cycle=2026-election-cycle',
        'race_id': 'ga_house_146'
    }
}

def main():
    print("=" * 60)
    print("TransparencyUSA Georgia 2026 Scraper")
    print("=" * 60)
    
    DATA_REPO_PATH = os.getenv('DATA_REPO_PATH', '../election-data')
    existing_candidate_ids = load_existing_candidates(DATA_REPO_PATH)
    
    all_financials = {}
    pending_candidates = []
    timestamp = datetime.now().isoformat()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for race_key, race_info in RACES.items():
            candidates = scrape_race(page, race_info['url'], race_info['name'])
            
            for candidate in candidates:
                cleaned_name = clean_candidate_name(candidate['name']) 
                candidate_id = generate_candidate_id(candidate['name'])
                
                all_financials[candidate_id] = {
                    'name': cleaned_name,  
                    'race': race_info['race_id'],
                    'party': candidate['party'],
                    'contributions': candidate['contributions'],
                    'loans': candidate['loans'],
                    'expenditures': candidate['expenditures'],
                    'status': candidate['status']
                }
                
                if candidate_id not in existing_candidate_ids:
                    print(f"  🆕 NEW CANDIDATE: {cleaned_name} ({candidate_id})")  
                    pending_candidates.append({
                        'suggestedId': candidate_id,
                        'name': cleaned_name, 
                        'party': candidate['party'],
                        'race': race_info['race_id'],
                        'contributions': candidate['contributions'],
                        'detectedOn': timestamp
                    })
            
            time.sleep(2)
        
        browser.close()
    
    # Save files
    financials_dir = os.path.join(DATA_REPO_PATH, 'financials')
    candidates_dir = os.path.join(DATA_REPO_PATH, 'candidates')
    os.makedirs(financials_dir, exist_ok=True)
    
    state_financials = {
        'lastUpdated': timestamp,
        'candidates': all_financials
    }
    
    financials_file = os.path.join(financials_dir, 'state-financials.json')
    with open(financials_file, 'w') as f:
        json.dump(state_financials, f, indent=2)
    
    print(f"\n✅ Saved financial data for {len(all_financials)} candidates")
    print(f"📁 {financials_file}")
    
    pending_file = os.path.join(candidates_dir, 'pending-candidates.json')
    pending_data = {
        'lastChecked': timestamp,
        'pendingCandidates': pending_candidates
    }
    
    with open(pending_file, 'w') as f:
        json.dump(pending_data, f, indent=2)
    
    if pending_candidates:
        print(f"\n🆕 Found {len(pending_candidates)} new candidates!")
        print(f"📁 {pending_file}")
        for candidate in pending_candidates:
            print(f"   - {candidate['name']} ({candidate['race']})")
    else:
        print(f"\n✅ All candidates already in repo")
        print(f"📁 {pending_file}")
    
    print("\n" + "=" * 60)
    print(f"✅ Scraping complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()