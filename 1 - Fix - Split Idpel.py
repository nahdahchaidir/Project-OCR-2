from pathlib import Path
import sys

# Paksa encoding output UTF-8 (agar tidak error di Windows cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

INPUT_FILE = Path("idpel.txt")
OUTPUT_DIR = Path("1_split_idpel")
LINES_PER_FILE = 50000

def split_file(input_file: Path, lines_per_file: int = LINES_PER_FILE) -> None:
    if not input_file.exists():
        raise FileNotFoundError(f"File not found: {input_file}")

    # Pastikan folder output ada
    OUTPUT_DIR.mkdir(exist_ok=True)

    with input_file.open("r", encoding="utf-8") as f:
        part = 1
        buffer = []
        for i, line in enumerate(f, start=1):
            buffer.append(line)
            if i % lines_per_file == 0:
                output_file = OUTPUT_DIR / f"idpel_part{part}.txt"
                with output_file.open("w", encoding="utf-8") as out:
                    out.writelines(buffer)
                buffer.clear()
                part += 1

        # Sisa baris terakhir
        if buffer:
            output_file = OUTPUT_DIR / f"idpel_part{part}.txt"
            with output_file.open("w", encoding="utf-8") as out:
                out.writelines(buffer)

    print(f"Split selesai. File hasil disimpan di folder: {OUTPUT_DIR}")

if __name__ == "__main__":
    split_file(INPUT_FILE)
