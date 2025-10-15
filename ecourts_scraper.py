#!/usr/bin/env python3
"""
eCourts Scraper - Fixed version with actual eCourts website integration
"""

import requests
import json
import argparse
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import os
import time
import re

class ECourtsScraper:
    def __init__(self):
        self.base_url = "https://services.ecourts.gov.in/ecourtindia_v6/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.captcha_token = None
        
    def _get_captcha(self):
        """Get CAPTCHA (if required) - placeholder for manual entry"""
        print("\n⚠️  Note: eCourts may require CAPTCHA verification")
        print("If you see a CAPTCHA on the website, this script may need manual intervention")
        return None
    
    def _init_session(self):
        """Initialize session by visiting the homepage"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                print("✓ Session initialized successfully")
                return True
            else:
                print(f"⚠️  Session initialization warning: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error initializing session: {e}")
            return False
    
    def search_by_cnr(self, state_code: str, cnr_number: str) -> Optional[Dict]:
        """Search case by CNR number"""
        try:
            print(f"\n🔍 Searching for CNR: {cnr_number}")
            
            # Initialize session first
            if not self._init_session():
                print("⚠️  Continuing despite session initialization issue...")
            
            # CNR search URL structure
            search_url = f"{self.base_url}CNRSearch"
            
            # Prepare the request payload based on eCourts structure
            payload = {
                'CNR_number': cnr_number,
                'cino': cnr_number,
            }
            
            # Add state code to headers or payload as needed
            self.session.headers.update({
                'Referer': self.base_url,
                'Origin': self.base_url.rstrip('/')
            })
            
            print("📡 Sending request to eCourts...")
            response = self.session.post(search_url, data=payload, timeout=15, allow_redirects=True)
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Check if we got valid HTML
                if len(response.text) < 100:
                    print("⚠️  Received empty or very short response")
                    return self._create_error_response(cnr_number, "Empty response from server")
                
                return self._parse_case_details(response.text, cnr_number)
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return self._create_error_response(cnr_number, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("⏱️  Request timeout - eCourts server may be slow or down")
            return self._create_error_response(cnr_number, "Request timeout")
        except requests.exceptions.ConnectionError:
            print("🌐 Connection error - Check internet connection")
            return self._create_error_response(cnr_number, "Connection failed")
        except Exception as e:
            print(f"❌ Unexpected error: {type(e).__name__}: {e}")
            return self._create_error_response(cnr_number, str(e))
    
    def search_by_case_number(self, state_code: str, dist_code: str, 
                             case_type: str, case_no: str, case_year: str) -> Optional[Dict]:
        """Search case by case type, number, and year"""
        try:
            case_id = f"{case_type}/{case_no}/{case_year}"
            print(f"\n🔍 Searching for Case: {case_id}")
            
            # Initialize session
            if not self._init_session():
                print("⚠️  Continuing despite session initialization issue...")
            
            search_url = f"{self.base_url}CaseNumberSearch"
            
            payload = {
                'state_code': state_code,
                'dist_code': dist_code,
                'court_code': '',  # May need to be filled
                'case_type': case_type,
                'case_no': case_no,
                'case_year': case_year,
            }
            
            print("📡 Sending request to eCourts...")
            response = self.session.post(search_url, data=payload, timeout=15)
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                return self._parse_case_details(response.text, case_id)
            else:
                return self._create_error_response(case_id, f"HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            case_id = f"{case_type}/{case_no}/{case_year}"
            return self._create_error_response(case_id, str(e))
    
    def _create_error_response(self, case_id: str, error_msg: str) -> Dict:
        """Create a structured error response"""
        return {
            'case_id': case_id,
            'found': False,
            'error': error_msg,
            'listing_info': None,
            'court_name': None,
            'serial_number': None,
            'timestamp': datetime.now().isoformat(),
            'note': 'The eCourts website may require CAPTCHA or be temporarily unavailable'
        }
    
    def _parse_case_details(self, html_content: str, case_id: str) -> Dict:
        """Parse case details from HTML response"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        case_info = {
            'case_id': case_id,
            'found': False,
            'listing_info': None,
            'court_name': None,
            'serial_number': None,
            'party_names': None,
            'case_status': None,
            'next_hearing_date': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Debug: Save HTML to file for inspection
        debug_file = 'debug_response.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 Response saved to {debug_file} for inspection")
        
        # Check for common error messages
        text_lower = html_content.lower()
        if 'not found' in text_lower or 'no record' in text_lower:
            print("⚠️  Case not found in eCourts database")
            case_info['error'] = "Case not found"
            return case_info
        
        if 'captcha' in text_lower:
            print("🔐 CAPTCHA detected - manual intervention may be required")
            case_info['error'] = "CAPTCHA required"
            return case_info
        
        # Try to find case information in various table structures
        tables = soup.find_all('table')
        print(f"📋 Found {len(tables)} tables in response")
        
        for idx, table in enumerate(tables):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    header = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    # Map common field names
                    if any(x in header for x in ['court name', 'court', 'bench']):
                        case_info['court_name'] = value
                        case_info['found'] = True
                    elif any(x in header for x in ['serial', 'sr. no', 'sl. no']):
                        case_info['serial_number'] = value
                    elif any(x in header for x in ['petitioner', 'party', 'parties']):
                        case_info['party_names'] = value
                        case_info['found'] = True
                    elif any(x in header for x in ['status', 'case status']):
                        case_info['case_status'] = value
                    elif any(x in header for x in ['next date', 'hearing date', 'next hearing']):
                        case_info['next_hearing_date'] = value
        
        # If we found any data, mark as found
        if case_info['court_name'] or case_info['party_names']:
            case_info['found'] = True
            print("✓ Case information extracted successfully")
        else:
            print("⚠️  Could not extract case details from response")
            case_info['error'] = "Could not parse case details (check debug_response.html)"
        
        return case_info
    
    def check_listing(self, case_info: Dict, check_date: str = 'today') -> Dict:
        """Check if case is listed for today or tomorrow"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        target_date = today if check_date == 'today' else tomorrow
        
        result = {
            'check_date': target_date.isoformat(),
            'is_listed': False,
            'serial_number': case_info.get('serial_number'),
            'court_name': case_info.get('court_name'),
            'case_id': case_info.get('case_id'),
            'hearing_date': case_info.get('next_hearing_date')
        }
        
        # Check if next hearing matches target date
        if case_info.get('next_hearing_date'):
            try:
                # Try to parse the date (format may vary)
                hearing_date_str = case_info['next_hearing_date']
                # Common formats: DD-MM-YYYY, DD/MM/YYYY, etc.
                for date_format in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                    try:
                        hearing_date = datetime.strptime(hearing_date_str, date_format).date()
                        if hearing_date == target_date:
                            result['is_listed'] = True
                            print(f"✓ Case is listed for {check_date}")
                        break
                    except ValueError:
                        continue
            except Exception as e:
                print(f"⚠️  Could not parse hearing date: {e}")
        
        return result
    
    def download_case_pdf(self, case_id: str, output_dir: str = 'downloads') -> Optional[str]:
        """Download case PDF if available"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Note: PDF download URLs vary by court system
            pdf_url = f"{self.base_url}GetCasePDF"
            
            print("\n📥 Attempting to download case PDF...")
            
            response = self.session.get(pdf_url, stream=True, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' in content_type.lower():
                    filename = f"{output_dir}/{case_id.replace('/', '_')}.pdf"
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✓ PDF downloaded: {filename}")
                    return filename
                else:
                    print(f"⚠️  Response is not a PDF (Content-Type: {content_type})")
                    return None
            else:
                print(f"❌ PDF download failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading PDF: {e}")
            return None
    
    def download_cause_list(self, state_code: str, dist_code: str, 
                           court_code: str, date: str = None, 
                           output_dir: str = 'downloads') -> Optional[str]:
        """Download entire cause list for specified date"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            if not date:
                date = datetime.now().strftime('%d-%m-%Y')
            
            print(f"\n📥 Downloading cause list for {date}...")
            
            causelist_url = f"{self.base_url}ViewCauseList"
            
            payload = {
                'state_code': state_code,
                'dist_code': dist_code,
                'court_code': court_code,
                'hearing_date': date,
            }
            
            response = self.session.post(causelist_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                cause_list_data = self._parse_cause_list(response.text)
                
                filename = f"{output_dir}/causelist_{date.replace('/', '_').replace('-', '_')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(cause_list_data, f, indent=2, ensure_ascii=False)
                
                print(f"✓ Cause list saved: {filename}")
                return filename
            else:
                print(f"❌ Failed to fetch cause list: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading cause list: {e}")
            return None
    
    def _parse_cause_list(self, html_content: str) -> List[Dict]:
        """Parse cause list from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        cases = []
        
        # Save for debugging
        with open('debug_causelist.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    case_entry = {
                        'serial_no': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                        'case_number': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                        'parties': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        'purpose': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                    }
                    if case_entry['case_number']:  # Only add if has case number
                        cases.append(case_entry)
        
        print(f"✓ Parsed {len(cases)} cases from cause list")
        return cases
    
    def save_results(self, data: Dict, filename: str = 'results.json'):
        """Save results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='eCourts Scraper - Fetch court listings from eCourts India',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search by CNR
  python ecourts_scraper.py --cnr DLCT01-123456-2024 --state DL --today
  
  # Search by case number
  python ecourts_scraper.py --case-number CS 123 2024 --state DL --dist 01
        """
    )
    
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument('--cnr', help='CNR number of the case')
    search_group.add_argument('--case-number', nargs=3, metavar=('TYPE', 'NO', 'YEAR'),
                            help='Case type, number, and year')
    
    parser.add_argument('--state', required=True, help='State code (e.g., DL)')
    parser.add_argument('--dist', help='District code')
    
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument('--today', action='store_true', help='Check if listed today')
    date_group.add_argument('--tomorrow', action='store_true', help='Check if listed tomorrow')
    
    parser.add_argument('--download-pdf', action='store_true', help='Download case PDF')
    parser.add_argument('--causelist', action='store_true', help='Download cause list')
    parser.add_argument('--court', help='Court code')
    parser.add_argument('--output', default='results.json', help='Output file')
    parser.add_argument('--output-dir', default='downloads', help='Download directory')
    
    args = parser.parse_args()
    
    scraper = ECourtsScraper()
    
    print("=" * 70)
    print("⚖️  eCourts Scraper v2.0")
    print("=" * 70)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'query': {},
        'case_info': None,
        'listing_info': None,
        'downloads': []
    }
    
    # Search
    if args.cnr:
        results['query'] = {'type': 'cnr', 'cnr': args.cnr}
        case_info = scraper.search_by_cnr(args.state, args.cnr)
    else:
        case_type, case_no, case_year = args.case_number
        if not args.dist:
            print("❌ Error: --dist is required for case number search")
            sys.exit(1)
        
        results['query'] = {
            'type': 'case_number',
            'case_type': case_type,
            'case_number': case_no,
            'case_year': case_year
        }
        case_info = scraper.search_by_case_number(
            args.state, args.dist, case_type, case_no, case_year
        )
    
    if not case_info:
        print("\n❌ Failed to fetch case information")
        sys.exit(1)
    
    results['case_info'] = case_info
    
    # Display results
    print("\n" + "=" * 70)
    print("📋 CASE INFORMATION")
    print("=" * 70)
    print(f"Case ID: {case_info['case_id']}")
    print(f"Found: {'✓ Yes' if case_info['found'] else '✗ No'}")
    
    if case_info.get('error'):
        print(f"Error: {case_info['error']}")
    if case_info.get('court_name'):
        print(f"Court: {case_info['court_name']}")
    if case_info.get('serial_number'):
        print(f"Serial: {case_info['serial_number']}")
    if case_info.get('party_names'):
        print(f"Parties: {case_info['party_names']}")
    if case_info.get('next_hearing_date'):
        print(f"Next Hearing: {case_info['next_hearing_date']}")
    
    # Check listing
    if args.today or args.tomorrow:
        check_date = 'tomorrow' if args.tomorrow else 'today'
        listing_info = scraper.check_listing(case_info, check_date)
        results['listing_info'] = listing_info
        
        print(f"\n📅 LISTING STATUS - {check_date.upper()}")
        print("=" * 70)
        print(f"Date: {listing_info['check_date']}")
        print(f"Listed: {'✓ Yes' if listing_info['is_listed'] else '✗ No'}")
    
    # Downloads
    if args.download_pdf and case_info['found']:
        pdf_file = scraper.download_case_pdf(case_info['case_id'], args.output_dir)
        if pdf_file:
            results['downloads'].append({'type': 'pdf', 'file': pdf_file})
    
    if args.causelist and args.dist and args.court:
        cl_file = scraper.download_cause_list(
            args.state, args.dist, args.court, output_dir=args.output_dir
        )
        if cl_file:
            results['downloads'].append({'type': 'causelist', 'file': cl_file})
    
    # Save
    scraper.save_results(results, args.output)
    
    print("\n" + "=" * 70)
    print("✓ Process completed!")
    print("=" * 70)


if __name__ == '__main__':
    main()