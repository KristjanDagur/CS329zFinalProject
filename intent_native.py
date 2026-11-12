"""Persistent native OpenCode workers; fresh, explicitly titled session per task.

The OpenCode server runs the agent loop. This module only starts it and submits
native session requests. No model orchestration or generation loop lives here.
"""
import base64
import contextlib
import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import tempfile
import threading
import time
import urllib.request


class NativePool:
    def __init__(self, collector, count=2):
        self.collector = collector
        # Resolve from this source file, independent of runtime paths.
        self.root = Path(__file__).resolve().parent
        self.temp = tempfile.TemporaryDirectory(prefix='native-pool-',dir=self.root/'.runtime')
        self.workers = []
        self.available = queue.Queue()
        self.count = count
        self.lock = threading.Lock()
        self.started = False

    def request(self, worker, path, body=None, method=None, timeout=120):
        headers = {'Content-Type':'application/json','x-opencode-directory':str(worker['workspace']),
                   'Authorization':'Basic '+base64.b64encode(('opencode:'+worker['password']).encode()).decode()}
        req = urllib.request.Request(worker['url']+path,data=None if body is None else json.dumps(body).encode(),
                                     headers=headers,method=method)
        with urllib.request.urlopen(req,timeout=timeout) as response:
            return json.load(response)

    def start(self):
        with self.lock:
            if self.started:
                return
            p = self.collector.protocol
            version=subprocess.run([str((self.root/'.runtime/opencode').resolve()),'--version'],capture_output=True,text=True,timeout=15,check=True).stdout.strip()
            if version != p['opencode_version']:
                raise RuntimeError('Unexpected OpenCode version: '+version)
            for n in range(self.count):
                home = Path(self.temp.name)/str(n)
                workspace=home/'workspace'
                workspace.mkdir(parents=True)
                subprocess.run(['git','init','-q',str(workspace)],check=True,capture_output=True)
                plugin=workspace/'.opencode/plugins/intent-tools.js'
                plugin.parent.mkdir(parents=True)
                plugin.write_bytes((self.root/'intent_tools.js').read_bytes())
                env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('KEY','TOKEN','SECRET','PASSWORD','OPENCODE','XDG_'))}
                for kind in ('config','data','cache','state'):
                    path=home/kind
                    path.mkdir()
                    env['XDG_'+kind.upper()+'_HOME']=str(path)
                model=p['strong_model']
                base=f'http://127.0.0.1:{self.collector.server.server_port}/native'
                password=self.collector.native_token
                config={'$schema':'https://opencode.ai/config.json','autoupdate':False,
                    'model':'metered/'+model,'small_model':'metered/'+model,'enabled_providers':['metered'],
                    'provider':{'metered':{'npm':'@ai-sdk/openai-compatible','name':'Metered intent experiment',
                        'options':{'baseURL':base+'/v1','apiKey':password},
                        'models':{model:{'name':model,'tool_call':True,'limit':{'context':64000,'output':p['max_output_tokens']}}}}},
                    'permission':{'*':'deny','search_examples':'allow','lookup_intent':'allow'},
                    'compaction':{'auto':False},
                    'agent':{'build':{'steps':3,'prompt':p['agent_prompt'],
                        'tools':{'*':False,'search_examples':True,'lookup_intent':True}}}}
                env.update(OPENCODE_CONFIG_CONTENT=json.dumps(config),OPENCODE_DISABLE_AUTOUPDATE='true',
                    OPENCODE_DISABLE_DEFAULT_PLUGINS='true',OPENCODE_DISABLE_CLAUDE_CODE='true',
                    OPENCODE_DISABLE_LSP_DOWNLOAD='true',OPENCODE_SERVER_PASSWORD=password,
                    INTENT_TOOL_URL=base,INTENT_TOOL_TOKEN=password)
                log=(home/'server.log').open('w')
                proc=subprocess.Popen([str((self.root/'.runtime/opencode').resolve()),'serve','--hostname','127.0.0.1','--port','0'],
                    cwd=workspace,env=env,stdout=log,stderr=log,start_new_session=True)
                worker=dict(proc=proc,log=log,workspace=workspace,password=password,home=home)
                self.workers.append(worker)
                deadline=time.monotonic()+60
                while time.monotonic()<deadline:
                    content=(home/'server.log').read_text()
                    found=re.search(r'opencode server listening on (http://[^\s]+)',content)
                    if found:
                        worker['url']=found[1]
                        break
                    if proc.poll() is not None:
                        raise RuntimeError('Native server exited: '+content[-1000:])
                    time.sleep(.1)
                else:
                    raise TimeoutError('Native server startup timeout')
                # Fetch the running pinned binary's actual OpenAPI schema for evidence.
                schema=self.request(worker,'/doc',timeout=15)
                self.collector.save(self.collector.base/'native_openapi.json',schema)
                for _ in range(6):
                    self.available.put(worker)
            self.started=True

    def run(self, job, utterance):
        self.start()
        worker=self.available.get(timeout=120)
        session=None
        try:
            # A supplied title avoids the irrelevant automatic conversation-title call.
            session=self.request(worker,'/session',{'title':job['id']})['id']
            self.collector.sessions[session]=job
            prompt=json.dumps(dict(task=self.collector.protocol['agent_prompt'],catalog=self.collector.catalog,
                                   user_utterance=utterance),ensure_ascii=False)
            self.collector.save(job['out']/'agent_prompt.json',dict(prompt=prompt,session_id=session))
            response=self.request(worker,'/session/'+session+'/message',{
                'agent':'build','model':{'providerID':'metered','modelID':self.collector.protocol['strong_model']},
                'parts':[{'type':'text','text':prompt}]},timeout=self.collector.protocol['timeout_s'])
            self.collector.save(job['out']/'native_response.json',response)
            history=self.request(worker,'/session/'+session+'/message')
            self.collector.save(job['out']/'native_messages.json',history)
            texts=[p['text'] for p in response.get('parts',[]) if p.get('type')=='text']
            if not texts:
                raise ValueError('No final native agent text: '+str(response.get('info',{}).get('error'))[:200])
            return texts[-1]
        finally:
            if session:
                with contextlib.suppress(Exception):
                    self.request(worker,'/session/'+session+'/abort',{},timeout=5)
                with contextlib.suppress(Exception):
                    self.request(worker,'/session/'+session,method='DELETE',timeout=5)
                self.collector.sessions.pop(session,None)
            self.available.put(worker)

    def close(self):
        for w in self.workers:
            if w['proc'].poll() is None:
                os.killpg(w['proc'].pid,signal.SIGTERM)
                with contextlib.suppress(subprocess.TimeoutExpired):
                    w['proc'].wait(timeout=5)
                if w['proc'].poll() is None:
                    os.killpg(w['proc'].pid,signal.SIGKILL)
                    w['proc'].wait()
            w['log'].close()
        self.temp.cleanup()
