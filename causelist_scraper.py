#!/usr/bin/env python3
"""
District Court Cause List Scraper
Download daily cause lists as PDFs from Indian district courts
Author: [Your Name]
Date: October 2025
"""

import requests
from bs4 import BeautifulSoup
import os
import sys
from datetime import datetime, timedelta
import argparse
import time
import json
from urllib.parse import urljoin
import re

class DistrictCourtCauseListScraper:
    """
    Scraper for downloading cause list PDFs from district courts
    """
    
    def __init__(self, output_dir='cause_lists'):
        """Initialize scraper with output directory"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Session for maintaining cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf,text/html,application/xhtml+xml',
        })
        
        # Statistics
        self.stats = {
            'total_attempted': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'total_size_kb': 0
        }
    
    def get_delhi_courts(self):
        """Get list of Delhi district courts"""
        # Delhi district courts
        courts = [
            {'name': 'Tis Hazari Courts', 'code': 'tis_hazari'},
            {'name': 'Karkardooma Courts', 'code': 'karkardooma'},
            {'name': 'Rohini Courts', 'code': 'rohini'},
            {'name': 'Dwarka Courts', 'code': 'dwarka'},
            {'name': 'Saket Courts', 'code': 'saket'},
            {'name': 'Patiala House Courts', 'code': 'patiala_house'},
        ]
        return courts
    
    def download_cause_list_pdf(self, court_name, court_code, date_str):
        """
        Download cause list PDF for a specific court and date
        
        Args:
            court_name: Name of the court
            court_code: Court identifier
            date_str: Date in DD-MM-YYYY format
            
        Returns:
            Path to downloaded PDF or None if failed
        """
        self.stats['total_attempted'] += 1
        
        print(f"\n{'='*70}")
        print(f"📥 Downloading: {court_name}")
        print(f"📅 Date: {date_str}")
        print(f"{'='*70}")
        
        # Possible URL patterns for cause list PDFs
        base_urls = [
            f"https://districts.ecourts.gov.in/delhi/{court_code}/causelist_{date_str}.pdf",
            f"https://delhicourts.nic.in/{court_code}/causelist.pdf?date={date_str}",
            f"https://delhihighcourt.nic.in/dhc_case_status/causelist/{court_code}_{date_str}.pdf",
        ]
        
        for url in base_urls:
            try:
                print(f"  🔗 Trying: {url}")
                response = self.session.get(url, timeout=30, allow_redirects=True)
                
                if response.status_code == 200:
                    # Check if response is actually a PDF
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    if 'pdf' in content_type or response.content[:4] == b'%PDF':
                        # Save PDF
                        filename = self._save_pdf(response.content, court_name, court_code, date_str)
                        
                        self.stats['successful_downloads'] += 1
                        self.stats['total_size_kb'] += len(response.content) / 1024
                        
                        print(f"  ✅ SUCCESS: Downloaded {len(response.content)/1024:.1f} KB")
                        print(f"  📄 Saved as: {filename}")
                        return filename
                    
                    # If HTML response, try to find PDF link
                    elif 'html' in content_type:
                        print(f"  📄 Got HTML page, searching for PDF link...")
                        pdf_link = self._extract_pdf_link_from_html(response.text, url)
                        
                        if pdf_link:
                            print(f"  🔗 Found PDF link: {pdf_link}")
                            pdf_response = self.session.get(pdf_link, timeout=30)
                            
                            if pdf_response.status_code == 200 and pdf_response.content[:4] == b'%PDF':
                                filename = self._save_pdf(pdf_response.content, court_name, court_code, date_str)
                                
                                self.stats['successful_downloads'] += 1
                                self.stats['total_size_kb'] += len(pdf_response.content) / 1024
                                
                                print(f"  ✅ SUCCESS: Downloaded {len(pdf_response.content)/1024:.1f} KB")
                                print(f"  📄 Saved as: {filename}")
                                return filename
                
                elif response.status_code == 404:
                    print(f"  ⚠️  Not found (404)")
                else:
                    print(f"  ⚠️  HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"  ⏱️  Timeout")
            except requests.exceptions.ConnectionError:
                print(f"  🌐 Connection error")
            except Exception as e:
                print(f"  ❌ Error: {type(e).__name__}")
        
        # All attempts failed
        self.stats['failed_downloads'] += 1
        print(f"  ❌ FAILED: Could not download from any source")
        return None
    
    def _extract_pdf_link_from_html(self, html_content, base_url):
        """Extract PDF download link from HTML page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for links containing 'pdf', 'causelist', 'download'
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            text = link.get_text().lower()
            
            if any(keyword in href or keyword in text for keyword in ['pdf', 'causelist', 'download']):
                return urljoin(base_url, link['href'])
        
        # Look for buttons/forms
        for form in soup.find_all('form'):
            action = form.get('action', '')
            if 'pdf' in action.lower() or 'causelist' in action.lower():
                return urljoin(base_url, action)
        
        return None
    
    def _save_pdf(self, pdf_content, court_name, court_code, date_str):
        """Save PDF content to file with proper naming"""
        # Clean filename
        safe_court = re.sub(r'[^\w\s-]', '', court_name).strip().replace(' ', '_')
        safe_date = date_str.replace('-', '_').replace('/', '_')
        
        filename = f"{self.output_dir}/{safe_court}_{safe_date}.pdf"
        
        # Save file
        with open(filename, 'wb') as f:
            f.write(pdf_content)
        
        return filename
    
    def batch_download(self, date_str, courts=None):
        """
        Download cause lists from multiple courts
        
        Args:
            date_str: Date in DD-MM-YYYY format
            courts: List of court dicts (if None, uses Delhi courts)
        """
        if courts is None:
            courts = self.get_delhi_courts()
        
        print("\n" + "="*70)
        print("🏛️  DISTRICT COURT CAUSE LIST SCRAPER")
        print("="*70)
        print(f"📅 Date: {date_str}")
        print(f"🏢 Courts: {len(courts)}")
        print(f"📁 Output: {self.output_dir}/")
        print("="*70)
        
        downloaded_files = []
        
        for i, court in enumerate(courts, 1):
            print(f"\n[{i}/{len(courts)}] Processing...")
            
            filename = self.download_cause_list_pdf(
                court['name'],
                court['code'],
                date_str
            )
            
            if filename:
                downloaded_files.append({
                    'court': court['name'],
                    'file': filename,
                    'status': 'success'
                })
            else:
                downloaded_files.append({
                    'court': court['name'],
                    'file': None,
                    'status': 'failed'
                })
            
            # Rate limiting - be respectful to servers
            if i < len(courts):
                time.sleep(2)
        
        # Generate summary
        self._print_summary(date_str, downloaded_files)
        self._save_report(date_str, downloaded_files)
        
        return downloaded_files
    
    def _print_summary(self, date_str, results):
        """Print download summary"""
        print("\n" + "="*70)
        print("📊 DOWNLOAD SUMMARY")
        print("="*70)
        print(f"📅 Date: {date_str}")
        print(f"📁 Output Directory: {self.output_dir}/")
        print(f"\n📈 Statistics:")
        print(f"  Total Attempted:  {self.stats['total_attempted']}")
        print(f"  ✅ Successful:     {self.stats['successful_downloads']}")
        print(f"  ❌ Failed:         {self.stats['failed_downloads']}")
        print(f"  📦 Total Size:     {self.stats['total_size_kb']:.1f} KB")
        
        if self.stats['successful_downloads'] > 0:
            success_rate = (self.stats['successful_downloads'] / self.stats['total_attempted']) * 100
            print(f"  📊 Success Rate:   {success_rate:.1f}%")
        
        print("\n📄 Downloaded Files:")
        for result in results:
            if result['status'] == 'success':
                print(f"  ✅ {result['file']}")
            else:
                print(f"  ❌ {result['court']} - FAILED")
        
        print("="*70)
    
    def _save_report(self, date_str, results):
        """Save JSON report of downloads"""
        report = {
            'date': date_str,
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'results': results
        }
        
        report_file = f"{self.output_dir}/report_{date_str.replace('-', '_')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Report saved: {report_file}")


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(
        description='District Court Cause List Scraper - Download daily cause lists as PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download today's cause lists
  python causelist_scraper.py --today
  
  # Download tomorrow's cause lists
  python causelist_scraper.py --tomorrow
  
  # Download for specific date
  python causelist_scraper.py --date 20-10-2025
  
  # Specify output directory
  python causelist_scraper.py --today --output downloads
        """
    )
    
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--today', action='store_true',
                          help='Download today\'s cause lists')
    date_group.add_argument('--tomorrow', action='store_true',
                          help='Download tomorrow\'s cause lists')
    date_group.add_argument('--date',
                          help='Specific date (DD-MM-YYYY format)')
    
    parser.add_argument('--output', default='cause_lists',
                       help='Output directory (default: cause_lists)')
    
    args = parser.parse_args()
    
    # Determine date
    if args.tomorrow:
        date_obj = datetime.now() + timedelta(days=1)
        date_str = date_obj.strftime('%d-%m-%Y')
    elif args.date:
        # Validate date format
        try:
            datetime.strptime(args.date, '%d-%m-%Y')
            date_str = args.date
        except ValueError:
            print("❌ Error: Date must be in DD-MM-YYYY format")
            sys.exit(1)
    else:  # --today
        date_str = datetime.now().strftime('%d-%m-%Y')
    
    # Initialize scraper
    scraper = DistrictCourtCauseListScraper(output_dir=args.output)
    
    try:
        # Download cause lists
        results = scraper.batch_download(date_str)
        
        # Exit code based on success
        if scraper.stats['successful_downloads'] > 0:
            print("\n✅ Process completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  No cause lists were downloaded")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()