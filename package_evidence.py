"""Package small, sanitized run artifacts; never include credentials or caches."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

root=Path(__file__).resolve().parent
files=[]
for path in sorted((root/'runs').rglob('*')):
    relative=path.relative_to(root/'runs')
    if not path.is_file() or 'workspace' in relative.parts or path.name.startswith('.'):
        continue
    if path.suffix not in {'.json','.jsonl','.log','.diff','.py'}:
        continue
    raw=path.read_bytes()
    text=raw.decode('utf8')
    # Only synthetic task/model traces are included. Strip machine-local paths.
    text=text.replace(str(root),'<PROJECT_ROOT>')
    text=text.replace(str(root.parent.parent/'work'/'clean-midpoint'),'<CLEAN_SOURCE>')
    if re.search(r'sk-(?:or-)?[A-Za-z0-9_-]{20,}',text):
        raise RuntimeError(f'Possible credential in {relative}; archive was not created.')
    files.append((str(relative),text.encode()))
manifest={'format':'sanitized-midpoint-traces-v1','note':'Machine-local paths are replaced. Original run directories remain local; archive checksums describe the sanitized bytes.',
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files}}
with zipfile.ZipFile(root/'midpoint_runs.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name,raw in files: archive.writestr('runs/'+name,raw)
    archive.writestr('archive_manifest.json',json.dumps(manifest,indent=2)+'\n')
print('Sanitized archive:',len(files),'files,',(root/'midpoint_runs.zip').stat().st_size,'bytes')
