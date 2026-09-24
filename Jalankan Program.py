import os
import sys
import glob
import subprocess


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if os.path.basename(current_dir) == 'Dapur':
        dapur_dir = current_dir
    else:
        dapur_dir = os.path.join(current_dir, 'Dapur')

    print("--> === OTOMATISASI PENGECEKAN & EKSEKUSI PROGRAM ===")

    if not os.path.exists(dapur_dir):
        print(f"--> [ERROR] Folder '{dapur_dir}' tidak ditemukan!")
        input("Program telah selesai di jalankan dan tekan enter untuk keluar.")
        return

    required_files = [
        '1_TarikData.py',
        '2_CekData&Tulis.py',
        'config.conf',
        'credentials.json',
    ]

    missing_files = [
        f
        for f in required_files
        if not os.path.exists(os.path.join(dapur_dir, f))
    ]

    if missing_files:
        print(
            "--> [ERROR] Proses digagalkan! Berkas berikut tidak ditemukan di folder Dapur:"
        )
        for mf in missing_files:
            print(f"--> - {mf}")
        input("Program telah selesai di jalankan dan tekan enter untuk keluar.")
        return

    print("--> [OK] Semua berkas persyaratan lengkap.")

    xlsx_files = glob.glob(os.path.join(dapur_dir, '*.xlsx'))
    if xlsx_files:
        print(
            f"--> [INFO] Ditemukan {len(xlsx_files)} berkas Excel sisa. Menghapus..."
        )
        for xfile in xlsx_files:
            try:
                os.remove(xfile)
                print(f"--> - Berhasil menghapus: {os.path.basename(xfile)}")
            except Exception as e:
                print(f"--> - Gagal menghapus {os.path.basename(xfile)}: {e}")
    else:
        print("--> [INFO] Tidak ada berkas .xlsx yang perlu dihapus.")

    scripts_to_run = ['1_TarikData.py', '2_CekData&Tulis.py']

    for script_name in scripts_to_run:
        print(f"--> MENJALANKAN: {script_name}")
        
        result = subprocess.run([sys.executable, script_name], cwd=dapur_dir)

        if result.returncode != 0:
            print(
                f"--> [ERROR] Skrip {script_name} berhenti dengan kesalahan (Code: {result.returncode})."
            )
            break

    input("Program telah selesai di jalankan dan tekan enter untuk keluar.")


if __name__ == '__main__':
    main()
