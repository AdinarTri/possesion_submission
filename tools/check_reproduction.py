"""Compare two generated files without inspecting their contents or any video."""
import hashlib
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python tools/check_reproduction.py first.csv second.csv')
    if sha(sys.argv[1]) != sha(sys.argv[2]):
        raise SystemExit('FAIL: output differs')
    print('PASS: independently generated CSVs are byte-identical')
