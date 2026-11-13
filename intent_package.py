"""Portable, lossless evidence with cross-file compression. No model calls.

Run after intent_analysis.py. Existing archives are verified, never overwritten.
"""
import tarfile

import intent_probe as i


def package():
    if not (i.ROOT/'intent_evidence.json').exists():
        raise RuntimeError('Complete offline analysis before packaging')
    files={str(p.relative_to(i.ROOT)):p for p in sorted(i.RUNS.rglob('*')) if p.is_file()
           and p.suffix not in ('.sqlite3','.lock') and not p.name.endswith(('-wal','-shm','.tmp'))}
    for name in ('catalog.json','data_receipt.json'):
        files['intent_data/'+name]=i.CACHE/name
    path=i.ROOT/'intent_runs.tar.xz'
    if not path.exists():
        with tarfile.open(path,'w:xz',preset=3) as archive:
            for name,source in files.items():
                archive.add(source,arcname=name,recursive=False)
    with tarfile.open(path,'r:xz') as archive:
        names=set()
        for member in archive:
            if not member.isfile() or member.name not in files or member.name in names:
                raise RuntimeError('Unexpected archive member: '+member.name)
            names.add(member.name)
            if i.digest(archive.extractfile(member).read()) != i.digest(files[member.name].read_bytes()):
                raise RuntimeError('Archive content differs: '+member.name)
        if names!=set(files):
            raise RuntimeError('Archive is incomplete')
    part=dict(file=path.name,bytes=path.stat().st_size,sha256=i.digest(path.read_bytes()))
    i.dump(i.ROOT/'intent_archives.json',dict(parts=[part],files=len(files),format='tar.xz',
        unpack='python3 -m tarfile -e intent_runs.tar.xz .; python3 intent_probe.py prepare; python3 intent_analysis.py (no model calls).',
        evidence_sha256=i.digest((i.ROOT/'intent_evidence.json').read_bytes()),
        analysis_sha256=i.digest((i.ROOT/'intent_analysis.py').read_bytes())))
    print(part)


if __name__=='__main__':
    package()
