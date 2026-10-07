from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from s5studio.compass_catalog import create_compass_catalog

report=create_compass_catalog(ROOT,json.loads((ROOT/'data/watchface-library.json').read_text(encoding='utf8')))
print(json.dumps({k:v for k,v in report.items() if k!='models'},ensure_ascii=False,indent=2))
