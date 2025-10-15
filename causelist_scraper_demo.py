#!/usr/bin/env python3
"""
District Court Cause List Scraper - DEMO VERSION
This version demonstrates the concept with sample data
Update with real URLs once discovered
"""

import os
import sys
from datetime import datetime, timedelta
import argparse
import json
import time

# Sample PDF content (minimal valid PDF)
SAMPLE_PDF = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
50 700 Td
(DAILY CAUSE LIST) Tj
0 -20 Td
(Court: Tis Hazari Courts, Delhi) Tj
0 -20 Td
(Date: 15-10-2025) Tj
0 -40 Td
(Sr. No. | Case No. | Parties | Purpose) Tj
0 -20 Td
(1 | CS 123/2024 | ABC vs XYZ | Arguments) Tj
0 -20 Td
(2 | CRL 456/2024 | PQR vs LMN | Hearing) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000576 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
665
%%EOF
"""

class DemoScraper:
    def __init__(self, output_dir='cause_lists'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.stats = {
            'total_attempted': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'total_size_kb': 0
        }
    
    def get_courts(self):
        """List of Delhi district courts"""
        return [
            {'name': 'Tis Hazari Courts', 'code': 'tis_hazari', 'has_pdf': True},
            {'name': 'Karkardooma Courts', 'code': 'karkardooma', 'has_pdf': True},
            {'name': 'Rohini Courts', 'code': 'rohini', 'has_pdf': True},
            {'name': 'Saket Courts', 'code': 'saket', 'has_pdf': False},
            {'name': 'Dwarka Courts', 'code': 'dwarka', 'has_pdf': True},
            {'name': 'Patiala House Courts', 'code': 'patiala_house', 'has_pdf': False},
        ]
    
    def download_cause_list(self, court_name, court_code, date_str, has_pdf):
        """Simulate downloading cause list PDF"""
        self.stats['total_attempted'] += 1
        
        print(f"\n{'='*70}")
        print(f"📥 Downloading: {court_name}")
        print(f"📅 Date: {date_str}")
        print(f"{'='*70}")
        
        # Simulate trying different URLs
        urls = [
            f"https://delhidistrictcourts.nic.in/causelist/{court_code}_{date_str}.pdf",
            f"https://districts.ecourts.gov.in/delhi/{court_code}/causelist.pdf",
            f"https://delhicourts.nic.in/writereaddata/Upload/CauseList/{court_code}.pdf",
        ]
        
        for i, url in enumerate(urls, 1):
            print(f"  🔗 Trying [{i}/3]: {url}")
            time.sleep(0.5)  # Simulate network delay
            
            if has_pdf and i == 2:  # Succeed on second try for demo
                # Save sample PDF
                filename = f"{self.output_dir}/{court_name.replace(' ', '_')}_{date_str.replace('-', '_')}.pdf"
                
                with open(filename, 'wb') as f:
                    f.write(SAMPLE_PDF)
                
                size_kb = len(SAMPLE_PDF) / 1024
                self.stats['successful_downloads'] += 1
                self.stats['total_size_kb'] += size_kb
                
                print(f"  ✅ SUCCESS: Downloaded {size_kb:.1f} KB")
                print(f"  📄 Saved as: {filename}")
                return filename
            else:
                print(f"  ⚠️  Not found (404)" if i < 3 else "  ⚠️  Timeout")
        
        self.stats['failed_downloads'] += 1
        print(f"  ❌ FAILED: Could not download from any source")
        return None
    
    def batch_download(self, date_str):
        """Download from multiple courts"""
        courts = self.get_courts()
        
        print("\n" + "="*70)
        print("🏛️  DISTRICT COURT CAUSE LIST SCRAPER - DEMO")
        print("="*70)
        print(f"📅 Date: {date_str}")
        print(f"🏢 Courts: {len(courts)}")
        print(f"📁 Output: {self.output_dir}/")
        print("="*70)
        print("\n⚠️  NOTE: This is a DEMO version using sample data")
        print("    Real version will use actual court website URLs")
        print("="*70)
        
        results = []
        
        for i, court in enumerate(courts, 1):
            print(f"\n[{i}/{len(courts)}] Processing...")
            
            filename = self.download_cause_list(
                court['name'],
                court['code'],
                date_str,
                court['has_pdf']
            )
            
            results.append({
                'court': court['name'],
                'file': filename,
                'status': 'success' if filename else 'failed'
            })
            
            if i < len(courts):
                time.sleep(1)
        
        self._print_summary(date_str, results)
        self._save_report(date_str, results)
        
        return results
    
    def _print_summary(self, date_str, results):
        """Print summary"""
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
        """Save JSON report"""
        report = {
            'date': date_str,
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'results': results,
            'note': 'DEMO VERSION - Using sample data for demonstration'
        }
        
        report_file = f"{self.output_dir}/report_{date_str.replace('-', '_')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Report saved: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description='District Court Cause List Scraper - DEMO VERSION',
        epilog='NOTE: This demo uses sample data. Update with real URLs for production.'
    )
    
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--today', action='store_true')
    date_group.add_argument('--tomorrow', action='store_true')
    date_group.add_argument('--date', help='DD-MM-YYYY')
    
    parser.add_argument('--output', default='cause_lists')
    
    args = parser.parse_args()
    
    # Determine date
    if args.tomorrow:
        date_str = (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y')
    elif args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime('%d-%m-%Y')
    
    # Run scraper
    scraper = DemoScraper(output_dir=args.output)
    
    try:
        results = scraper.batch_download(date_str)
        
        if scraper.stats['successful_downloads'] > 0:
            print("\n✅ Process completed successfully!")
            print(f"\n💡 TIP: Check {args.output}/ folder for downloaded PDFs")
            print("    You can open them to see the sample cause list data")
            sys.exit(0)
        else:
            print("\n⚠️  No PDFs downloaded in this demo run")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == '__main__':
    main()