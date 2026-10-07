from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from s5studio.watchface_library import create_library
catalog=json.loads((ROOT/'docs/library-analysis/catalog.json').read_text(encoding='utf-8'))
result=create_library(ROOT,catalog)
print(json.dumps({'sources':{k:v['codes'] for k,v in result['sources'].items()},'hands':len(result['hands']),'errors':result['errors'][:15]},ensure_ascii=False,indent=2))
