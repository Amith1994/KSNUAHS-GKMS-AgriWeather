import os
import glob
import sys
import datetime
import json
import webbrowser
import subprocess
import pandas as pd

def excel_date_to_str(val):
    if isinstance(val, (datetime.datetime, datetime.date, pd.Timestamp)):
        return val.strftime("%d/%m/%Y")
    val_str = str(val).strip()
    if "/" in val_str or "-" in val_str:
        try:
            dt = pd.to_datetime(val_str)
            return dt.strftime("%d/%m/%Y")
        except:
            pass
    return val_str

def parse_weather_excel(excel_path):
    print(f"Reading Excel file: {excel_path} ...")
    df = pd.read_excel(excel_path)
    
    col_map = {}
    for col in df.columns:
        c_upper = str(col).upper()
        if 'DIST_NAME' in c_upper or 'DISTRICT' in c_upper:
            col_map['distName'] = col
        elif 'BLOCK_NAME' in c_upper or 'BLOCK' in c_upper:
            col_map['blockName'] = col
        elif 'RAINFALL' in c_upper:
            col_map['rainfall'] = col
        elif 'TEMPMAX' in c_upper or 'TMAX' in c_upper:
            col_map['tempMax'] = col
        elif 'TEMPMIN' in c_upper or 'TMIN' in c_upper:
            col_map['tempMin'] = col
        elif 'HUMIDITYI' in c_upper and 'II' not in c_upper:
            col_map['humidityI'] = col
        elif 'HUMIDITYII' in c_upper or 'HUMIDITY2' in c_upper:
            col_map['humidityII'] = col
        elif 'WINDSPEED' in c_upper or 'WIND_SPEED' in c_upper:
            col_map['windSpeed'] = col
        elif 'WINDDIRECTION' in c_upper or 'WIND_DIR' in c_upper:
            col_map['windDir'] = col
        elif 'CLOUDCOVER' in c_upper or 'CLOUD' in c_upper:
            col_map['cloudCover'] = col
        elif 'WARNING' in c_upper:
            col_map['warning'] = col
        elif 'FORECAST' in c_upper and 'DATE' in c_upper:
            col_map['forecastDate'] = col

    weather_data = {}
    date_set = set()

    for idx, row in df.iterrows():
        dist_val = row.get(col_map.get('distName'))
        block_val = row.get(col_map.get('blockName'))
        if pd.isna(dist_val) or pd.isna(block_val):
            continue

        dist = str(dist_val).strip()
        block = str(block_val).strip()
        date_raw = row.get(col_map.get('forecastDate'))
        date_str = excel_date_to_str(date_raw)
        date_set.add(date_str)

        if dist not in weather_data:
            weather_data[dist] = {}
        if block not in weather_data[dist]:
            weather_data[dist][block] = {}

        def safe_float(v):
            try:
                if pd.isna(v): return 0.0
                return round(float(v), 1)
            except:
                return 0.0

        def safe_str(v):
            if pd.isna(v): return ""
            return str(v).strip()

        weather_data[dist][block][date_str] = {
            "tempMax": safe_float(row.get(col_map.get('tempMax'))),
            "tempMin": safe_float(row.get(col_map.get('tempMin'))),
            "rainfall": safe_float(row.get(col_map.get('rainfall'))),
            "humidityI": safe_float(row.get(col_map.get('humidityI'))),
            "humidityII": safe_float(row.get(col_map.get('humidityII'))),
            "windSpeed": safe_float(row.get(col_map.get('windSpeed'))),
            "windDir": safe_float(row.get(col_map.get('windDir'))),
            "cloudCover": safe_float(row.get(col_map.get('cloudCover'))),
            "warning": safe_str(row.get(col_map.get('warning')))
        }

    dates_list = sorted(list(date_set), key=lambda d: datetime.datetime.strptime(d, "%d/%m/%Y") if "/" in d else d)
    return weather_data, dates_list

def generate_weather_data_js(weather_data):
    lines = ['{\n']
    districts = sorted(list(weather_data.keys()))

    for di, dist in enumerate(districts):
        lines.append(f"          '{dist}': {{\n")
        blocks = sorted(list(weather_data[dist].keys()))
        for bi, block in enumerate(blocks):
            lines.append(f"            '{block}': {{\n")
            dates = sorted(list(weather_data[dist][block].keys()), key=lambda d: datetime.datetime.strptime(d, "%d/%m/%Y") if "/" in d else d)
            for dti, date in enumerate(dates):
                d = weather_data[dist][block][date]
                escaped_warning = d['warning'].replace("'", "\\'")
                lines.append(f"              '{date}':{{tempMax:{d['tempMax']},tempMin:{d['tempMin']},rainfall:{d['rainfall']},humidityI:{d['humidityI']},humidityII:{d['humidityII']},windSpeed:{d['windSpeed']},windDir:{d['windDir']},cloudCover:{d['cloudCover']},warning:'{escaped_warning}'}},\n")
            lines.append("            },\n")
        lines.append("          },\n")

    lines.append('        }')
    return "".join(lines)

def compute_district_aggregates(weather_data):
    district_data = {}
    for dist, blocks in weather_data.items():
        district_data[dist] = {}
        if not blocks:
            continue
        
        date_set = set()
        for block, dates_dict in blocks.items():
            for d in dates_dict.keys():
                date_set.add(d)

        for date in date_set:
            sum_tmax = sum_tmin = sum_rain = sum_rh1 = sum_rh2 = sum_ws = sum_wd = sum_cc = 0.0
            cnt_tmax = cnt_tmin = cnt_rain = cnt_rh1 = cnt_rh2 = cnt_ws = cnt_wd = cnt_cc = 0
            warnings = []

            for block, dates_dict in blocks.items():
                day_data = dates_dict.get(date)
                if day_data:
                    sum_tmax += day_data['tempMax']; cnt_tmax += 1
                    sum_tmin += day_data['tempMin']; cnt_tmin += 1
                    sum_rain += day_data['rainfall']; cnt_rain += 1
                    sum_rh1 += day_data['humidityI']; cnt_rh1 += 1
                    sum_rh2 += day_data['humidityII']; cnt_rh2 += 1
                    sum_ws += day_data['windSpeed']; cnt_ws += 1
                    sum_wd += day_data['windDir']; cnt_wd += 1
                    sum_cc += day_data['cloudCover']; cnt_cc += 1
                    if day_data['warning']:
                        warnings.append(day_data['warning'])

            def avg(s, c): return round(s / c, 1) if c > 0 else 0.0

            district_data[dist][date] = {
                "tempMax": avg(sum_tmax, cnt_tmax),
                "tempMin": avg(sum_tmin, cnt_tmin),
                "rainfall": avg(sum_rain, cnt_rain),
                "humidityI": avg(sum_rh1, cnt_rh1),
                "humidityII": avg(sum_rh2, cnt_rh2),
                "windSpeed": avg(sum_ws, cnt_ws),
                "windDir": avg(sum_wd, cnt_wd),
                "cloudCover": avg(sum_cc, cnt_cc),
                "warning": "; ".join(set(warnings)) if warnings else None
            }
    return district_data

def generate_dates_meta(dates_list):
    day_names = []
    forecast_labels = []
    months_abbr = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

    for d_str in dates_list:
        parts = d_str.split('/')
        day = int(parts[0])
        month = int(parts[1]) - 1
        year = int(parts[2])
        dt = datetime.date(year, month + 1, day)
        
        day_names.append(dt.strftime("%a").upper())
        forecast_labels.append(f"{day} {months_abbr[month]}")

    return {
        "DATES": dates_list,
        "DAY_NAMES": day_names,
        "FORECAST_LABELS": forecast_labels
    }

def find_statement_end(text, marker_idx):
    i = marker_idx
    while i < len(text) and text[i] not in ('{', '['):
        i += 1
    if i >= len(text):
        return -1
    open_ch = text[i]
    close_ch = '}' if open_ch == '{' else ']'
    depth = 0
    in_str = False
    str_char = ''
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == '\\':
                i += 2
                continue
            if ch == str_char:
                in_str = False
        else:
            if ch in ('\'', '"', '`'):
                in_str = True
                str_char = ch
            elif ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    j = i + 1
                    while j < len(text) and text[j] in ' \t\r\n':
                        j += 1
                    if j < len(text) and text[j] == ';':
                        return j + 1
                    return i + 1
        i += 1
    return -1

def update_html_files(weather_data, dates_list, base_dir):
    data_js = generate_weather_data_js(weather_data)
    district_taluks = {dist: sorted(list(weather_data[dist].keys())) for dist in sorted(list(weather_data.keys()))}
    dist_aggregates = compute_district_aggregates(weather_data)
    dates_meta = generate_dates_meta(dates_list)

    # 1. Update 1st_updated.html
    html_path = os.path.join(base_dir, '1st_updated.html')
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        start_marker = "const WEATHER_DATA = "
        start_idx = html.find(start_marker)
        if start_idx != -1:
            end_idx = find_statement_end(html, start_idx)
            if end_idx != -1:
                html = html[:start_idx] + f"const WEATHER_DATA = {data_js};\n" + html[end_idx:]

        dte_marker = "const DISTRICT_TALUKS_EXCEL = "
        dte_idx = html.find(dte_marker)
        if dte_idx != -1:
            dte_end = find_statement_end(html, dte_idx)
            if dte_end != -1:
                html = html[:dte_idx] + f"const DISTRICT_TALUKS_EXCEL = {json.dumps(district_taluks)};" + html[dte_end:]

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print("[SUCCESS] 1st_updated.html updated successfully!")

    # 2. Update index.html
    index_path = os.path.join(base_dir, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            index_html = f.read()

        bd_marker = "const BLOCK_DATA = "
        bd_idx = index_html.find(bd_marker)
        if bd_idx != -1:
            bd_end = find_statement_end(index_html, bd_idx)
            if bd_end != -1:
                index_html = index_html[:bd_idx] + f"const BLOCK_DATA = {data_js};" + index_html[bd_end:]

        wd_marker = "const WEATHER_DATA = "
        wd_idx = index_html.find(wd_marker)
        if wd_idx != -1:
            wd_end = find_statement_end(index_html, wd_idx)
            if wd_end != -1:
                index_html = index_html[:wd_idx] + f"const WEATHER_DATA = {json.dumps(dist_aggregates)};" + index_html[wd_end:]

        dates_marker = "const DATES = "
        dates_idx = index_html.find(dates_marker)
        if dates_idx != -1:
            dates_end = find_statement_end(index_html, dates_idx)
            if dates_end != -1:
                index_html = index_html[:dates_idx] + f"const DATES = {json.dumps(dates_meta['DATES'])};" + index_html[dates_end:]

        dn_marker = "const DAY_NAMES = "
        dn_idx = index_html.find(dn_marker)
        if dn_idx != -1:
            dn_end = find_statement_end(index_html, dn_idx)
            if dn_end != -1:
                index_html = index_html[:dn_idx] + f"const DAY_NAMES = {json.dumps(dates_meta['DAY_NAMES'])};" + index_html[dn_end:]

        fl_marker = "const FORECAST_LABELS = "
        fl_idx = index_html.find(fl_marker)
        if fl_idx != -1:
            fl_end = find_statement_end(index_html, fl_idx)
            if fl_end != -1:
                index_html = index_html[:fl_idx] + f"const FORECAST_LABELS = {json.dumps(dates_meta['FORECAST_LABELS'])};" + index_html[fl_end:]

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        print("[SUCCESS] index.html updated successfully!")

    # 3. Update map.html
    map_path = os.path.join(base_dir, 'map.html')
    if os.path.exists(map_path):
        with open(map_path, 'r', encoding='utf-8') as f:
            map_html = f.read()

        bd_marker = "let BLOCK_DATA = "
        bd_idx = map_html.find(bd_marker)
        if bd_idx != -1:
            bd_end = find_statement_end(map_html, bd_idx)
            if bd_end != -1:
                map_html = map_html[:bd_idx] + f"let BLOCK_DATA = {json.dumps(weather_data)};" + map_html[bd_end:]

        dd_marker = "let DISTRICT_DATA = "
        dd_idx = map_html.find(dd_marker)
        if dd_idx != -1:
            dd_end = find_statement_end(map_html, dd_idx)
            if dd_end != -1:
                map_html = map_html[:dd_idx] + f"let DISTRICT_DATA = {json.dumps(dist_aggregates)};" + map_html[dd_end:]

        dm_marker = "let DATES_META = "
        dm_idx = map_html.find(dm_marker)
        if dm_idx != -1:
            dm_end = find_statement_end(map_html, dm_idx)
            if dm_end != -1:
                map_html = map_html[:dm_idx] + f"let DATES_META = {json.dumps(dates_meta)};" + map_html[dm_end:]

        with open(map_path, 'w', encoding='utf-8') as f:
            f.write(map_html)
        print("[SUCCESS] map.html updated successfully!")

def is_valid_weather_excel(excel_path):
    try:
        df = pd.read_excel(excel_path)
        cols = [str(c).upper() for c in df.columns]
        has_dist = any('DIST' in c for c in cols)
        has_block = any('BLOCK' in c for c in cols)
        return has_dist and has_block
    except Exception:
        return False

def sync_to_github(base_dir):
    print("\n[INFO] Syncing forecast updates to GitHub account...")
    try:
        # Check git status
        res = subprocess.run(["git", "status", "--porcelain"], cwd=base_dir, capture_output=True, text=True)
        if not res.stdout.strip():
            print("[INFO] No file changes detected. GitHub is already up to date.")
            return

        print("[INFO] Staging updated files for Git...")
        subprocess.run(["git", "add", "."], cwd=base_dir, check=True)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"Auto-update IMD weather forecast data ({timestamp})"
        print(f"[INFO] Committing changes: '{commit_msg}'...")
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=base_dir, check=True)

        print("[INFO] Pushing updates to GitHub (origin main)...")
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=base_dir, capture_output=True, text=True)
        
        if push_res.returncode == 0:
            print("[SUCCESS] Successfully updated and pushed all changes to your GitHub account!")
        else:
            push_res2 = subprocess.run(["git", "push"], cwd=base_dir, capture_output=True, text=True)
            if push_res2.returncode == 0:
                print("[SUCCESS] Successfully updated and pushed all changes to your GitHub account!")
            else:
                err = push_res.stderr.strip() or push_res2.stderr.strip()
                print(f"[WARNING] Could not push to GitHub. Error details:\n{err}")

    except Exception as e:
        print(f"[WARNING] GitHub sync encountered an error: {e}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Search for candidate excel files in workspace or Downloads
    excel_files = glob.glob(os.path.join(base_dir, "*.xls")) + glob.glob(os.path.join(base_dir, "*.xlsx"))
    
    user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.exists(user_downloads):
        excel_files += glob.glob(os.path.join(user_downloads, "*blwf*.xls")) + glob.glob(os.path.join(user_downloads, "*blwf*.xlsx"))
        excel_files += glob.glob(os.path.join(user_downloads, "*Weather*.xls")) + glob.glob(os.path.join(user_downloads, "*Weather*.xlsx"))
        excel_files += glob.glob(os.path.join(user_downloads, "Karnataka*.xls")) + glob.glob(os.path.join(user_downloads, "Karnataka*.xlsx"))

    # Exclude temporary Excel files and non-weather files
    valid_files = [f for f in excel_files if not os.path.basename(f).startswith("~$") and is_valid_weather_excel(f)]

    if not valid_files:
        print("[ERROR] No valid weather forecast Excel file (.xls / .xlsx) found in workspace or Downloads!")
        print("Please ensure your IMD weather Excel file has 'DIST_NAME' and 'BLOCK_NAME' columns.")
        input("Press Enter to exit...")
        return

    latest_excel = max(valid_files, key=os.path.getmtime)
    print(f"[INFO] Found Weather Excel file: {os.path.basename(latest_excel)}")
    
    weather_data, dates_list = parse_weather_excel(latest_excel)
    print(f"[INFO] Parsed {len(weather_data)} districts for dates: {dates_list}")

    if not weather_data or not dates_list:
        print("[ERROR] Weather data parsed as empty. Aborting HTML update to prevent data loss.")
        input("Press Enter to exit...")
        return

    update_html_files(weather_data, dates_list, base_dir)
    
    # Sync updated files to GitHub repository
    sync_to_github(base_dir)

    target_url = os.path.join(base_dir, '1st_updated.html')
    print(f"[INFO] Launching updated forecast app in browser...")
    webbrowser.open(f"file:///{target_url}")

if __name__ == '__main__':
    main()
