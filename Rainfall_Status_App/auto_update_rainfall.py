import os
import sys
import glob
import json
import datetime
import webbrowser
import pandas as pd

PERIOD_KEYS = [
    'jan', 'feb', 'jan_feb', 'mar', 'apr', 'may', 'pre_monsoon',
    'june', 'last_24h', 'last_7d', 'july_mtd', 'sw_monsoon', 'ytd'
]

def safe_float(v):
    try:
        if pd.isna(v): return 0.0
        return round(float(v), 1)
    except:
        return 0.0

def safe_str(v):
    if pd.isna(v): return ""
    return str(v).strip()

def parse_ksndmc_excel(excel_path):
    print(f"[INFO] Reading KSNDMC Excel: {excel_path}")
    
    # 1. Parse District Sheet
    df_dist = pd.read_excel(excel_path, sheet_name='District')
    districts_data = {}
    
    # District data rows start at row index 5
    for idx in range(5, len(df_dist)):
        row = df_dist.iloc[idx]
        dist_name = safe_str(row.iloc[6])
        if not dist_name or dist_name.lower().startswith('total') or dist_name.lower().startswith('sl.'):
            continue
        
        sl_no = safe_str(row.iloc[0])
        code = safe_str(row.iloc[1])
        region = safe_str(row.iloc[2])
        division = safe_str(row.iloc[5])
        
        dist_entry = {
            "slNo": int(sl_no) if sl_no.isdigit() else idx - 4,
            "code": code,
            "region": region,
            "division": division
        }
        
        # 13 periods, each taking 3 columns starting at col index 7
        col_offset = 7
        for pkey in PERIOD_KEYS:
            norm = safe_float(row.iloc[col_offset])
            act = safe_float(row.iloc[col_offset + 1])
            dep = safe_float(row.iloc[col_offset + 2])
            dist_entry[pkey] = {"normal": norm, "actual": act, "dep": dep}
            col_offset += 3
            
        districts_data[dist_name] = dist_entry

    # 2. Parse Taluk Sheet
    df_taluk = pd.read_excel(excel_path, sheet_name='Taluk')
    taluks_data = []
    
    # Taluk data rows start at row index 4
    for idx in range(4, len(df_taluk)):
        row = df_taluk.iloc[idx]
        dist_name = safe_str(row.iloc[8])
        taluk_name = safe_str(row.iloc[9])
        if not dist_name or not taluk_name or taluk_name.lower().startswith('total'):
            continue
        
        region = safe_str(row.iloc[4])
        division = safe_str(row.iloc[7])
        
        taluk_entry = {
            "dist": dist_name,
            "taluk": taluk_name,
            "region": region,
            "division": division
        }
        
        # 13 periods, each taking 3 columns starting at col index 11
        col_offset = 11
        for pkey in PERIOD_KEYS:
            norm = safe_float(row.iloc[col_offset])
            act = safe_float(row.iloc[col_offset + 1])
            dep = safe_float(row.iloc[col_offset + 2])
            taluk_entry[pkey] = {"normal": norm, "actual": act, "dep": dep}
            col_offset += 3
            
        taluks_data.append(taluk_entry)
        
    return {"districts": districts_data, "taluks": taluks_data}

def update_html_from_json(json_data, base_dir):
    json_path = os.path.join(base_dir, 'data_embedded.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    print(f"[SUCCESS] Updated {json_path}")
    
    json_districts = json.dumps(json_data['districts'])
    json_taluks = json.dumps(json_data['taluks'])
    
    template_path = os.path.join(base_dir, 'template_rainfall_status.html')
    if not os.path.exists(template_path):
        template_path = os.path.join(os.path.dirname(base_dir), 'template_rainfall_status.html')
        
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    html = html.replace('__JSON_DISTRICTS__', json_districts)
    html = html.replace('__JSON_TALUKS__', json_taluks)
    
    for fname in ['rainfall status.html', 'rainfall_status.html']:
        out_path = os.path.join(base_dir, fname)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[SUCCESS] Updated {fname}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    
    print("=" * 60)
    print("  KSNDMC DAILY RAINFALL STATUS AUTOMATED UPDATER")
    print("=" * 60)
    
    # Find candidate excel files
    search_paths = [
        os.path.join(script_dir, "*.xlsx"),
        os.path.join(script_dir, "*.xls"),
        os.path.join(parent_dir, "*.xlsx"),
        os.path.join(downloads_dir, "*Rainfall*.xlsx"),
        os.path.join(downloads_dir, "*Rainfall*.xls"),
        os.path.join(downloads_dir, "*KSNDMC*.xlsx"),
        os.path.join(downloads_dir, "*KSNDMC*.xls"),
        os.path.join(downloads_dir, "*Karnataka*.xlsx"),
        os.path.join(downloads_dir, "*Karnataka*.xls"),
    ]
    
    candidate_files = []
    for pattern in search_paths:
        candidate_files.extend(glob.glob(pattern))
        
    # Exclude temp Excel files (~$)
    candidate_files = [f for f in candidate_files if not os.path.basename(f).startswith("~$")]
    
    if not candidate_files:
        print("[ERROR] No Rainfall Excel file found!")
        print("Please download the report from https://www.ksndmc.org/ into your Downloads or Rainfall_Status_App folder.")
        input("Press Enter to exit...")
        return
        
    latest_excel = max(candidate_files, key=os.path.getmtime)
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(latest_excel)).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO] Using Latest Excel File: {latest_excel}")
    print(f"[INFO] File Modified Time: {mtime}")
    
    json_data = parse_ksndmc_excel(latest_excel)
    print(f"[INFO] Parsed {len(json_data['districts'])} Districts & {len(json_data['taluks'])} Taluks.")
    
    update_html_from_json(json_data, script_dir)
    
    target_html = os.path.join(script_dir, 'rainfall_status.html')
    print(f"\n[INFO] Launching Karnataka Current Status of Rainfall App in browser...")
    webbrowser.open(f"file:///{target_html}")
    print("[DONE] Update process completed successfully!\n")

if __name__ == '__main__':
    main()
