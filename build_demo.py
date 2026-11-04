"""Render a silent, explicitly labeled replay of real recorded prototype runs.

Optional dependencies: Pillow and imageio-ffmpeg. No network/model calls.
"""
import json
import os
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
evidence=json.loads((ROOT/'midpoint_evidence.json').read_text())
supp={r['run_id']:r for r in evidence['supplementary_results']}
strong=next(r for r in evidence['primary_results'] if r['run_id']=='m2-stable-jev-v1')
cheap=supp['m2-stable-jev-sensitivity075']


def font(size,mono=False):
    candidates=([
        '/System/Library/Fonts/Menlo.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    ] if mono else [
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ])
    for path in candidates:
        if Path(path).exists(): return ImageFont.truetype(path,size)
    return ImageFont.load_default(size=size)


def tools(run):
    events=[]
    for line in (ROOT/'runs'/run['run_id']/'events.jsonl').read_text().splitlines():
        data=json.loads(line)
        if data.get('type')=='tool_use':
            part=data['part']; events.append(f"{part['tool']:12s} {part['state']['status']}")
    return events


scenes=[
 {'duration':8,'title':'System One routing for a coding agent',
  'subtitle':'CS329Z midpoint prototype | November 3, 2026',
  'lines':['Real OpenRouter API calls and OpenCode tool execution.',
           'This video replays saved execution records. It is not live.',
           'Synthetic development fixtures; no benchmark claim.']},
 {'duration':10,'title':'One routing decision; an existing agent harness',
  'subtitle':'Python orchestrator -> Jev -> selected model -> OpenCode -> independent grader',
  'lines':['Gate input: issue, broken code, model pair, resource limits.',
           'Cheap: qwen/qwen3-coder-next   |   Strong: openai/gpt-6.1-sol',
           'Gate: typesafe/jev-1.14; invalid response routes strong.',
           'Independent tests and reference solutions stay outside the agent workspace.',
           '$0.50 task cap / $5 session cap; request-level cost receipts.']},
 {'duration':strong['elapsed_s'],'title':'Recorded run: default threshold routes strong',
  'subtitle':f"stable_unique | Jev score {strong['gate']['score']:.2f} < threshold 0.90",
  'run':strong,'lines':tools(strong)},
 {'duration':cheap['elapsed_s'],'title':'Recorded run: lower-threshold demonstration',
  'subtitle':f"POST-HOC DEMONSTRATION ONLY | score {cheap['gate']['score']:.2f} >= threshold 0.75",
  'run':cheap,'lines':tools(cheap)},
 {'duration':9,'title':'The agent actually repaired the source file',
  'subtitle':'Independent evaluation: 6 tests passed; broken starter was rejected.',
  'lines':(ROOT/'runs'/cheap['run_id']/'patch.diff').read_text().splitlines()[:15]},
 {'duration':15,'title':'Primary pilot: all policies pass 3 / 3 tasks',
  'subtitle':'Three constructed development tasks, one rollout per policy and task.',
  'lines':[
      f"{label:15s}  ${evidence['policy_summary'][policy]['mean_billed_cost_usd']:.6f} / task   {evidence['policy_summary'][policy]['mean_elapsed_s']:.2f} s mean"
      for policy,label in [('cheap','Always cheap'),('strong','Always strong'),('jev','Jev @ 0.90')]]
      + ['Jev cheap coverage: 0%. Selective risk: undefined.',
         'All cheap baselines passed: these tasks cannot establish routing value.',
         'No calibrated risk, equivalence, or general savings conclusion.']},
 {'duration':10,'title':'What is ready, and what remains',
  'subtitle':'Runnable prototype, trace archive, 11 offline checks, clean-source repair verified.',
  'lines':['Current session metered spend: $'+f"{evidence['total_session_accounted_usd']:.6f}",
           'Next: teammate quick-start review, report review, and course submission.',
           'Final study: SWE-bench environment, larger development set, calibration,',
           'heuristic/random controls, locked evaluation, and failure analysis.',
           'Report draft and README explicitly separate completed work from plans.']},
]


def render(scene,position,elapsed,total):
    image=Image.new('RGB',(1280,720),'#f7f7f4')
    draw=ImageDraw.Draw(image)
    draw.rectangle((0,0,1280,62),fill='#172b36')
    draw.text((38,19),'CS329Z  /  RECORDED EXECUTION REPLAY',font=font(20),fill='white')
    draw.text((38,94),scene['title'],font=font(31),fill='#172b36')
    for i,line in enumerate(textwrap.wrap(scene['subtitle'],104)):
        draw.text((38,146+i*28),line,font=font(21),fill='#46565b')
    top=225
    if scene.get('run'):
        run=scene['run']
        draw.text((38,197),'Selected upstream model: '+run['selected_model'],font=font(23),fill='#172b36')
        count=max(1,min(len(scene['lines']),int(position*len(scene['lines']))+1))
        lines=scene['lines'][:count]
    else: lines=scene['lines']
    for i,line in enumerate(lines[:15]):
        draw.text((45,top+i*28),line,font=font(19,True),fill='#172b36')
    if scene.get('run'):
        run=scene['run']
        draw.text((38,565),f"Recorded result: {run['tests_run']} independent tests passed | ${run['billed_cost_usd']:.6f} | {run['elapsed_s']:.2f} s",font=font(23),fill='#172b36')
        draw.text((38,606),run['run_id'],font=font(18,True),fill='#46565b')
    draw.rectangle((38,673,1242,678),fill='#d8dddd')
    draw.rectangle((38,673,38+int(1204*elapsed/total),678),fill='#2e6171')
    draw.text((38,688),'Replay from saved traces; silence is intentional. See DEMO_SCRIPT.md.',font=font(16),fill='#46565b')
    return image


def main():
    fps=10
    total=sum(s['duration'] for s in scenes)
    target=ROOT/'demo_replay.mp4'
    writer=imageio_ffmpeg.write_frames(str(target),(1280,720),fps=fps,codec='libx264',
        pix_fmt_in='rgb24',pix_fmt_out='yuv420p',quality=8,output_params=['-movflags','+faststart'])
    writer.send(None)
    elapsed=0
    for scene in scenes:
        frames=round(scene['duration']*fps)
        for frame in range(frames):
            writer.send(render(scene,frame/max(1,frames-1),elapsed+frame/fps,total).tobytes())
        elapsed+=frames/fps
    writer.close()
    render(scenes[0],0,0,total).save(ROOT/'demo_poster.png')
    print(target,round(total,1),'seconds',target.stat().st_size,'bytes')


if __name__=='__main__': main()
