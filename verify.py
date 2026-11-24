#!/usr/bin/env python3
import os
import subprocess
import hashlib
import tempfile
import shutil
from pathlib import Path
from PIL import Image

def check_entry_png():
    """Check entry.png exists, is valid PNG, format PNG, exactly 1024x1024, under 1048576 bytes"""
    png_path = Path('entry.png')
    if not png_path.exists():
        print("ERROR: entry.png does not exist")
        return False
    
    try:
        img = Image.open(png_path)
        if img.format != 'PNG':
            print("ERROR: entry.png is not PNG format")
            return False
        
        if img.size != (1024, 1024):
            print(f"ERROR: entry.png is {img.size}, not 1024x1024")
            return False
        
        if png_path.stat().st_size >= 1048576:
            print(f"ERROR: entry.png is {png_path.stat().st_size} bytes, >= 1048576")
            return False
        
        print("OK: entry.png exists, valid PNG, 1024x1024, < 1048576 bytes")
        return True
    except Exception as e:
        print(f"ERROR: Failed to validate entry.png: {e}")
        return False

def check_determinism():
    """Run 'python3 render.py' twice, check sha256 identical"""
    try:
        # Run render.py twice
        subprocess.run(['python3', 'render.py'], check=True, capture_output=True)
        hash1 = hashlib.sha256(Path('entry.png').read_bytes()).hexdigest()
        
        subprocess.run(['python3', 'render.py'], check=True, capture_output=True)
        hash2 = hashlib.sha256(Path('entry.png').read_bytes()).hexdigest()
        
        if hash1 != hash2:
            print(f"ERROR: Determinism failed - hashes differ: {hash1} vs {hash2}")
            return False
        
        print(f"OK: Determinism passed - both runs produced hash {hash1}")
        return True
    except Exception as e:
        print(f"ERROR: Determinism check failed: {e}")
        return False

def check_stories():
    """Check stories.py has 20 CARDS and 50 BRIEFS, region counts, data validation"""
    try:
        import stories
        
        if len(stories.CARDS) != 20:
            print(f"ERROR: Expected 20 CARDS, got {len(stories.CARDS)}")
            return False
        
        if len(stories.BRIEFS) != 50:
            print(f"ERROR: Expected 50 BRIEFS, got {len(stories.BRIEFS)}")
            return False
        
        # Check region counts
        expected_regions = {
            'EUROPE': 12, 'THE AMERICAS': 12, 'ASIA-PACIFIC': 14,
            'MIDDLE EAST': 10, 'AFRICA': 8, 'OCEANIA': 7, 'WORLD': 7
        }
        
        region_counts = {}
        for card in stories.CARDS:
            region = card.get('region', '')
            region_counts[region] = region_counts.get(region, 0) + 1
        
        for brief in stories.BRIEFS:
            region = brief.get('region', '')
            region_counts[region] = region_counts.get(region, 0) + 1
        
        for region, expected in expected_regions.items():
            if region_counts.get(region, 0) != expected:
                print(f"ERROR: Region {region} count: expected {expected}, got {region_counts.get(region, 0)}")
                return False
        
        # Check card data
        for card in stories.CARDS:
            if not card.get('headline'):
                print("ERROR: Card missing headline")
                return False
            if not card.get('deck'):
                print("ERROR: Card missing deck")
                return False
        
        # Check brief data
        for brief in stories.BRIEFS:
            if not brief.get('text'):
                print("ERROR: Brief missing text")
                return False
            if not brief.get('source'):
                print("ERROR: Brief missing source")
                return False
        
        print("OK: Stories validation passed - 20 cards, 50 briefs, correct regions, all data present")
        return True
    except Exception as e:
        print(f"ERROR: Stories validation failed: {e}")
        return False

def check_main_ts():
    """Copy entry.png and main.ts to temp dir, run node main.ts, check output"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy files
            shutil.copy2('entry.png', temp_path / 'entry.png')
            shutil.copy2('main.ts', temp_path / 'main.ts')
            
            # Run main.ts
            result = subprocess.run(['node', 'main.ts'], cwd=temp_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"ERROR: main.ts failed with exit code {result.returncode}")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                return False
            
            # Check output file exists
            output_file = temp_path / 'output' / 'entry.png'
            if not output_file.exists():
                print("ERROR: output/entry.png was not created")
                return False
            
            # Check byte-identical
            original_hash = hashlib.sha256(Path('entry.png').read_bytes()).hexdigest()
            output_hash = hashlib.sha256(output_file.read_bytes()).hexdigest()
            
            if original_hash != output_hash:
                print("ERROR: output/entry.png is not byte-identical to original")
                return False
            
            print("OK: main.ts validation passed - created identical output")
            return True
    except Exception as e:
        print(f"ERROR: main.ts validation failed: {e}")
        return False

def main():
    """Run all checks and report results"""
    print("Running verification checks...")
    
    checks = [
        ("Entry PNG", check_entry_png),
        ("Determinism", check_determinism),
        ("Stories", check_stories),
        ("Main TS", check_main_ts),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n--- {name} Check ---")
        if not check_func():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("ALL CHECKS PASSED")
        return 0
    else:
        print("SOME CHECKS FAILED")
        return 1

if __name__ == "__main__":
    exit(main())
