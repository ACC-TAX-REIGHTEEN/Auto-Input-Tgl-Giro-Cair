import os
import re
import glob
import configparser
from datetime import datetime, timedelta
import pandas as pd
import gspread


def clean_nominal(val):
    if val is None or pd.isna(val):
        return 0.0
    val_str = str(val).strip().upper()
    val_str = val_str.replace('CR', '').replace('DB', '').strip()

    if ',' in val_str and '.' in val_str:
        val_str = val_str.replace(',', '')
    elif '.' in val_str and ',' not in val_str:
        val_str = val_str.replace('.', '')
    elif ',' in val_str and '.' not in val_str:
        val_str = val_str.replace(',', '')

    try:
        return float(val_str)
    except ValueError:
        digits = re.sub(r'[^0-9.]', '', val_str)
        return float(digits) if digits else 0.0


def clean_cabang_code(val):
    if pd.isna(val) or val is None:
        return ""
    try:
        num = int(float(str(val).strip()))
        return str(num).zfill(4)
    except (ValueError, TypeError):
        digits = re.sub(r'\D', '', str(val))
        return digits.zfill(4) if digits else ""


def parse_date(date_val):
    if not date_val or pd.isna(date_val):
        return None
    if isinstance(date_val, datetime):
        return date_val
    date_str = str(date_val).strip()
    date_str = date_str.split(' ')[0]
    formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def read_mutasi_excel(file_path, cab_code, col_jumlah_name, col_cabang_name):
    try:
        df_raw = pd.read_excel(file_path, header=None)
        header_row_idx = None

        for idx, row in df_raw.iterrows():
            row_values = [str(cell).strip() for cell in row.values]
            if col_jumlah_name in row_values or 'Tanggal Transaksi' in row_values:
                header_row_idx = idx
                break

        if header_row_idx is None:
            header_row_idx = 5

        df = pd.read_excel(file_path, skiprows=header_row_idx)
        df.columns = [str(c).strip() for c in df.columns]

        if 'Tanggal Transaksi' in df.columns:
            df = df[df['Tanggal Transaksi'].notna()]
            df = df[~df['Tanggal Transaksi'].astype(str).str.contains('Saldo|Mutasi', case=False, na=False)]

        if col_cabang_name in df.columns and cab_code:
            target_cab = clean_cabang_code(cab_code)
            df['Cabang_Clean'] = df[col_cabang_name].apply(clean_cabang_code)
            df = df[df['Cabang_Clean'] == target_cab]

        return df
    except Exception as e:
        print(f"--> [!] Gagal membaca file mutasi {os.path.basename(file_path)}: {e}")
        return pd.DataFrame()


def main():
    print("--> OTOMATISASI PENCOCOKAN ACTUAL CAIR GIRO/BG")

    current_dir = os.path.dirname(os.path.abspath(__file__))

    config_file = os.path.join(current_dir, 'config.conf')
    if not os.path.exists(config_file):
        print(f"--> [ERROR] File konfigurasi '{config_file}' tidak ditemukan!")
        return

    config = configparser.ConfigParser(strict=False)
    config.read(config_file, encoding='utf-8')

    ss_url = config.get('SS', 'ss_url').split('#')[0].strip()
    gen_before = int(config.get('GEN', 'gen_before', fallback=5))
    gen_after = int(config.get('GEN', 'gen_after', fallback=5))

    print(f"--> [CONFIG] URL Spreadsheet: {ss_url}")
    print(f"--> [CONFIG] Folder Sumber  : {current_dir} (Lokal)")
    print(f"--> [CONFIG] Toleransi H-  : {gen_before} hari | H+ : {gen_after} hari")

    cred_file = os.path.join(current_dir, 'credentials.json')
    if not os.path.exists(cred_file):
        print(f"--> [ERROR] File '{cred_file}' tidak ditemukan di folder lokal.")
        return

    try:
        gc = gspread.service_account(filename=cred_file)
        sh = gc.open_by_url(ss_url)
        print("--> [SUCCESS] Berhasil terhubung ke Google Sheets!")
    except Exception as e:
        print(f"--> [ERROR] Gagal membuka Google Sheets: {e}")
        return

    sheet_keys = []
    for key in config['SS']:
        if key.startswith('ss_sheet_') and not key.startswith('ss_sheet_loc_') and not key.endswith(('_key_val', '_key_date', '_write')):
            idx = key.replace('ss_sheet_', '')
            if idx.isdigit():
                sheet_keys.append(idx)

    sheet_keys.sort(key=int)

    for idx in sheet_keys:
        sheet_name = config.get('SS', f'ss_sheet_{idx}')
        loc_file_key = config.get('SS', f'ss_sheet_loc_file_{idx}')
        key_val_col = config.get('SS', f'ss_sheet_{idx}_key_val')
        key_date_col = config.get('SS', f'ss_sheet_{idx}_key_date')
        write_col = config.get('SS', f'ss_sheet_{idx}_write')

        dir_key_col = config.get('DIR', f'dir_key_col_{idx}')
        dir_key_dtl = config.get('DIR', f'dir_key_dtl_{idx}')
        dir_key_cab = config.get('DIR', f'dir_key_cab_{idx}')

        print(f"--> PROCESSING SHEET [{sheet_name}] (Kunci File Mutasi: {loc_file_key})")

        try:
            worksheet = sh.worksheet(sheet_name)
        except Exception as e:
            print(f"--> [!] Worksheet '{sheet_name}' tidak ditemukan di Google Sheets. Lewati.")
            continue

        records = worksheet.get_all_records()
        if not records:
            print(f"--> [i] Sheet '{sheet_name}' kosong.")
            continue

        headers = worksheet.row_values(1)
        if write_col not in headers:
            print(f"--> [!] Kolom target '{write_col}' tidak ditemukan di sheet header. Lewati.")
            continue

        write_col_idx = headers.index(write_col) + 1

        pattern = os.path.join(current_dir, f"*{loc_file_key}*.xlsx")
        mutasi_files = glob.glob(pattern)

        if not mutasi_files:
            print(f"--> [!] Tidak ditemukan file mutasi lokal dengan pola: *{loc_file_key}*.xlsx")
            continue

        print(f"--> [+] Ditemukan {len(mutasi_files)} file mutasi lokal terkait.")

        list_mutasi_df = []
        for file_path in mutasi_files:
            df_temp = read_mutasi_excel(file_path, dir_key_cab, dir_key_col, dir_key_dtl)
            if not df_temp.empty:
                list_mutasi_df.append(df_temp)

        if not list_mutasi_df:
            print("--> [!] Tidak ada data mutasi yang valid untuk diproses.")
            continue

        df_mutasi_all = pd.concat(list_mutasi_df, ignore_index=True)
        updated_count = 0

        for row_num, row_data in enumerate(records, start=2):
            actual_cair_val = str(row_data.get(write_col, '')).strip()

            if actual_cair_val != "" and actual_cair_val != "None":
                continue

            nominal_bg = row_data.get(key_val_col, '')
            tgl_jatuh_tempo_raw = row_data.get(key_date_col, '')

            target_nominal = clean_nominal(nominal_bg)
            dt_jatuh_tempo = parse_date(tgl_jatuh_tempo_raw)

            if target_nominal <= 0 or dt_jatuh_tempo is None:
                continue

            min_date = dt_jatuh_tempo - timedelta(days=gen_before)
            max_date = dt_jatuh_tempo + timedelta(days=gen_after)

            match_found = False
            matched_date_str = ""

            for _, mutasi_row in df_mutasi_all.iterrows():
                mutasi_nom_raw = mutasi_row.get(dir_key_col, '')
                mutasi_nominal = clean_nominal(mutasi_nom_raw)

                mutasi_tgl_raw = mutasi_row.get('Tanggal Transaksi', '')
                dt_transaksi = parse_date(mutasi_tgl_raw)

                if dt_transaksi is None:
                    continue

                if abs(mutasi_nominal - target_nominal) < 1.0:
                    if min_date <= dt_transaksi <= max_date:
                        match_found = True
                        matched_date_str = dt_transaksi.strftime('%d/%m/%Y')
                        break

            if match_found:
                worksheet.update_cell(row_num, write_col_idx, matched_date_str)
                print(f"--> [MATCH ROW {row_num}] Nominal: Rp {target_nominal:,.0f} | JT: {dt_jatuh_tempo.strftime('%d/%m/%Y')} -> ACTUAL CAIR: {matched_date_str}")
                updated_count += 1

        print(f"--> [RESULT] Selesai untuk Sheet '{sheet_name}'. Total diperbarui: {updated_count} baris.")

    print("--> PROSES SELESAI SELURUHNYA!")


if __name__ == '__main__':
    main()