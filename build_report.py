"""Regenerate the report's measured table, then compile its ICLR source."""
import json
import os
from pathlib import Path
import shutil
import subprocess

root=Path(__file__).resolve().parent
evidence=json.loads((root/'midpoint_evidence.json').read_text())
lines=[]
for policy,label in [('cheap','Always cheap'),('strong','Always strong'),('jev','Jev gate ($\\tau=0.90$)')]:
    r=evidence['policy_summary'][policy]
    lines.append(f"{label} & {r['successful_tasks']}/{r['tasks']} & {r['mean_billed_cost_usd']:.6f} & {r['mean_elapsed_s']:.2f} \\\\")
table='''\\begin{table}[t]
\\centering
\\caption{Synthetic development pilot. Each row contains the same three tasks, one rollout per task. Cost includes all captured model calls and the gate where applicable. These are engineering checks, not benchmark results.}
\\label{tab:pilot}
\\begin{tabular}{lrrr}
\\toprule
Policy & Passed & Mean cost (USD) & Mean time (s) \\\\
\\midrule
'''+ '\n'.join(lines)+'''
\\bottomrule
\\end{tabular}
\\end{table}
'''
(root/'report'/'results.tex').write_text(table)
compiler=shutil.which('pdflatex') or '/Library/TeX/texbin/pdflatex'
environment=os.environ.copy()
# Optional local static fonts for minimal TeX distributions. Full TeX Live and
# Overleaf do not need this cache; the official ICLR style is unchanged.
if (root/'.runtime'/'texmf').exists():
    environment['TEXMFHOME']=str(root/'.runtime'/'texmf')
    environment['TEXMFVAR']=str(root/'.runtime'/'texmf-var')
for _ in range(2):
    tex_input=r'\pdfmapfile{+uhv.map}\pdfmapfile{+utm.map}\pdfmapfile{+ucr.map}\input{main.tex}' if (root/'.runtime'/'texmf').exists() else 'main.tex'
    subprocess.run([compiler,'-interaction=nonstopmode','-halt-on-error',tex_input],cwd=root/'report',env=environment,check=True)
print(root/'report'/'main.pdf')
