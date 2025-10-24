from selenium import webdriver
import chromedriver_autoinstaller
print("Using chromedriver_autoinstaller from:", chromedriver_autoinstaller.__file__)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime

def scrape_race(url, race_name):
    """Scrape a single race and return candidate data"""
    print(f"\nScraping {race_name}...")
    
    # Set up Chrome (changed from Firefox)
    chromedriver_autoinstaller.install(path=None, make_version_dir=True, check_driver=True)

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.binary_location = "/snap/bin/chromium"

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate and wait
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load
        
        # Parse HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the candidate table
        table = soup.find('table', {'role': 'table'})
        
        if not table:
            print(f"  ❌ No table found for {race_name}")
            return []
        
        candidates = []
        
        # Find all rows in tbody
        tbody = table.find('tbody')
        if not tbody:
            print(f"  ❌ No tbody found for {race_name}")
            return []
        
        rows = tbody.find_all('tr', {'role': 'row'})
        print(f"  Found {len(rows)} candidates")
        
        for row in rows:
            cells = row.find_all('td')
            
            if len(cells) >= 6:
                # Extract candidate name
                name_link = cells[0].find('a')
                name = name_link.get_text(strip=True) if name_link else cells[0].get_text(strip=True)
                
                # Extract other data
                party = cells[1].get_text(strip=True)
                contributions = cells[2].get_text(strip=True)
                loans = cells[3].get_text(strip=True)
                expenditures = cells[4].get_text(strip=True)
                status = cells[5].get_text(strip=True)
                
                candidate = {
                    'name': name,
                    'party': party,
                    'contributions': contributions,
                    'loans': loans,
                    'expenditures': expenditures,
                    'status': status
                }
                
                candidates.append(candidate)
                print(f"    ✓ {clean_candidate_name(name)} - {party} - {contributions}")
        
        return candidates
        
    finally:
        driver.quit()

def clean_candidate_name(name):
    """Clean candidate name by removing party suffixes"""
    # Remove party names that might be appended
    name = name.replace('Democratic', '').replace('Republican', '').strip()
    return name

def generate_candidate_id(name):
    """Generate a candidate ID from name (matching your existing pattern)"""
    # Clean the name first
    name = clean_candidate_name(name)
    
    # Convert to lowercase, replace spaces with underscores, remove special chars
    candidate_id = name.lower()
    candidate_id = candidate_id.replace(' ', '_')
    candidate_id = candidate_id.replace('.', '')
    candidate_id = candidate_id.replace("'", '')
    candidate_id = candidate_id.replace('-', '_')
    
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

# Define all the races you want to scrape
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
    """Scrape all races and generate output files"""
    print("=" * 60)
    print("TransparencyUSA Georgia 2026 Scraper")
    print("=" * 60)
    
    # Path to your data repo (will be different in GitHub Actions)
    DATA_REPO_PATH = os.getenv('DATA_REPO_PATH', '../ga-elections-26-data')
    
    # Load existing candidates
    existing_candidate_ids = load_existing_candidates(DATA_REPO_PATH)
    
    # Storage for all scraped data
    all_financials = {}
    pending_candidates = []
    timestamp = datetime.now().isoformat()
    
    # Scrape all races
    for race_key, race_info in RACES.items():
        candidates = scrape_race(race_info['url'], race_info['name'])
        
        # In the main() function, find this section and update it:
        for candidate in candidates:
            cleaned_name = clean_candidate_name(candidate['name']) 
            candidate_id = generate_candidate_id(candidate['name'])
            
            # Add to financials (for ALL candidates)
            all_financials[candidate_id] = {
                'name': cleaned_name,  
                'race': race_info['race_id'],
                'party': candidate['party'],
                'contributions': candidate['contributions'],
                'loans': candidate['loans'],
                'expenditures': candidate['expenditures'],
                'status': candidate['status']
            }
            
            # Check if candidate is missing from repo
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
        
        # Small delay between requests
        time.sleep(2)
    
    # Create output directories
    financials_dir = os.path.join(DATA_REPO_PATH, 'financials')
    candidates_dir = os.path.join(DATA_REPO_PATH, 'candidates')
    os.makedirs(financials_dir, exist_ok=True)
    
    # Generate state-financials.json
    state_financials = {
        'lastUpdated': timestamp,
        'candidates': all_financials
    }
    
    financials_file = os.path.join(financials_dir, 'state-financials.json')
    with open(financials_file, 'w') as f:
        json.dump(state_financials, f, indent=2)
    
    print(f"\n✅ Saved financial data for {len(all_financials)} candidates")
    print(f"📁 {financials_file}")
    
    # Generate pending-candidates.json
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