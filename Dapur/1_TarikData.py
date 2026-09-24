import configparser
from datetime import date, datetime, timedelta
from pathlib import Path
import re
import shutil

BULAN_ALIAS = {
    "JAN": 1,
    "JANI": 1,
    "JANUARI": 1,
    "FEB": 2,
    "FEBT": 2,
    "FEBRUARI": 2,
    "MAR": 3,
    "MRT": 3,
    "MARET": 3,
    "APR": 4,
    "APRL": 4,
    "APRIL": 4,
    "MEI": 5,
    "MAY": 5,
    "JUN": 6,
    "JNI": 6,
    "JUNI": 6,
    "JUL": 7,
    "JLI": 7,
    "JULI": 7,
    "AGU": 8,
    "AUG": 8,
    "AGT": 8,
    "AGUSTUS": 8,
    "SEP": 9,
    "SEPT": 9,
    "SPT": 9,
    "SEPTEMBER": 9,
    "OKT": 10,
    "OCT": 10,
    "OKTOBER": 10,
    "NOV": 11,
    "NVB": 11,
    "NOVEMBER": 11,
    "DES": 12,
    "DEC": 12,
    "DESEMBER": 12,
}


def deteksi_bulan(teks_bulan, bulan_default):
    if not teks_bulan:
        return bulan_default

    teks_clean = teks_bulan.strip().upper()

    if teks_clean in BULAN_ALIAS:
        return BULAN_ALIAS[teks_clean]

    tiga_huruf = teks_clean[:3]
    if tiga_huruf in BULAN_ALIAS:
        return BULAN_ALIAS[tiga_huruf]

    print(
        f"--> [PERTINGATAN] Bulan '{teks_bulan}' tidak dikenali. Menggunakan bulan berjalan ({bulan_default})."
    )
    return bulan_default


def ekstrak_tanggal_dari_nama_file(nama_file, tanggal_acuan=None):
    if tanggal_acuan is None:
        tanggal_acuan = date.today()

    tahun_default = tanggal_acuan.year
    bulan_default = tanggal_acuan.month

    pola = r"([A-Za-z]+)\s+(\d+)\s+(\d{1,2})\s*(?:-\s*(\d{1,2}))?\s*([A-Za-z]+)?"
    match = re.search(pola, nama_file)

    if not match:
        return None

    nama_bank = match.group(1)
    no_rek = match.group(2)
    tgl_awal = int(match.group(3))
    tgl_akhir = int(match.group(4)) if match.group(4) else tgl_awal
    teks_bulan = match.group(5)

    bulan = deteksi_bulan(teks_bulan, bulan_default)

    try:
        tanggal_mulai = date(tahun_default, bulan, tgl_awal)
        tanggal_selesai = date(tahun_default, bulan, tgl_akhir)
        return tanggal_mulai, tanggal_selesai
    except ValueError:
        return None


def salin_file_berdasarkan_config(file_config="config.conf"):
    config = configparser.ConfigParser(strict=False)
    config.read(file_config, encoding="utf-8")

    try:
        path_asal = config.get("DIR", "dir_mut")
        gen_before = config.getint("GEN", "gen_before", fallback=5)
        gen_after = config.getint("GEN", "gen_after", fallback=5)
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"--> Error pada file config: {e}")
        return

    folder_asal = Path(path_asal)
    folder_tujuan = Path.cwd()

    if not folder_asal.exists():
        print(
            f"--> Error: Folder asal tidak ditemukan atau jaringan terputus:{folder_asal}"
        )
        return

    hari_ini = date.today()
    target_mulai = hari_ini - timedelta(days=gen_before)
    target_selesai = hari_ini + timedelta(days=gen_after)

    print(f"--> Tanggal Hari Ini : {hari_ini.strftime('%d-%m-%Y')}")
    print(
        f"--> Rentang Target   : {target_mulai.strftime('%d-%m-%Y')} s/d {target_selesai.strftime('%d-%m-%Y')}"
    )
    print(f"--> Folder Asal      : {folder_asal}")

    daftar_file = list(folder_asal.glob("*.xlsx")) + list(
        folder_asal.glob("*.xls")
    )
    file_tertempel = 0

    for file_path in daftar_file:
        if file_path.name.startswith("~$"):
            continue

        hasil_tanggal = ekstrak_tanggal_dari_nama_file(
            file_path.name, tanggal_acuan=hari_ini
        )

        if hasil_tanggal is None:
            print(f"--> [LEWAT] Struktur nama file tidak sesuai: {file_path.name}")
            continue

        f_mulai, f_selesai = hasil_tanggal

        is_overlap = (f_mulai <= target_selesai) and (f_selesai >= target_mulai)

        if is_overlap:
            tujuan_file = folder_tujuan / file_path.name
            shutil.copy2(file_path, tujuan_file)
            print(f"--> [SALIN] {file_path.name} ({f_mulai} s/d {f_selesai})")
            file_tertempel += 1
        else:
            print(f"--> [OUT  ] {file_path.name} ({f_mulai} s/d {f_selesai})")

    print(
        f"--> Selesai! Total {file_tertempel} file berhasil disalin ke folder lokal."
    )


if __name__ == "__main__":
    salin_file_berdasarkan_config()