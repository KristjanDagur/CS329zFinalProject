"""Package the completed intent evidence into browser-uploadable portable ZIPs.

No model calls. Run analysis first so ledger_export.json is complete. Each file
occurs in exactly one archive; unzip every part into the same repository root.
"""
from pathlib import Path
import zipfile

import intent_probe as i


def package(max_bytes=20_000_000):
    if not (i.ROOT/'intent_evidence.json').exists():
        raise RuntimeError('Complete offline analysis before packaging')
    files=[p for p in sorted(i.RUNS.rglob('*')) if p.is_file()
           and p.suffix not in ('.sqlite3','.lock') and not p.name.endswith(('-wal','-shm','.tmp'))]
    for name in ('catalog.json','data_receipt.json'):
        files.append(i.CACHE/name)
    parts=[]
    archive=None
    index=0
    def close():
        if archive:
            archive.close()
            parts.append(dict(file=path.name,bytes=path.stat().st_size,sha256=i.digest(path.read_bytes())))
    try:
        for file in files:
            if archive is None or path.stat().st_size>max_bytes-500_000:
                close()
                index+=1
                path=i.ROOT/f'intent_runs_{index:02d}.zip'
                if path.exists():
                    raise RuntimeError('Archive exists; preserve the original and use a new destination')
                archive=zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6)
            name=str(file.relative_to(i.ROOT)) if file.is_relative_to(i.RUNS) else 'intent_data/'+file.name
            archive.write(file,name)
    finally:
        close()
    assert all(p['bytes']<max_bytes for p in parts)
    i.dump(i.ROOT/'intent_archives.json',dict(parts=parts,files=len(files),
        unpack='Unzip every intent_runs_*.zip into the repository root; run python3 intent_probe.py prepare then python3 intent_analysis.py. No API calls.',
        evidence_sha256=i.digest((i.ROOT/'intent_evidence.json').read_bytes()),
        analysis_sha256=i.digest((i.ROOT/'intent_analysis.py').read_bytes())))
    print(parts)


if __name__=='__main__':
    package()
