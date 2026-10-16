from flask import Flask, request, render_template_string, send_from_directory, abort
import subprocess, os, json

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD = os.path.join(BASE, 'uploads')
OUT = os.path.join(BASE, 'out')
os.makedirs(UPLOAD, exist_ok=True)
TOKEN = os.environ.get('EAR_TOKEN', 'xiaoyi2026')

PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ears</title><style>
body{font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px;background:#1a1a2e;color:#eee}
h1{text-align:center}h2{margin-top:24px}
.box{border:2px dashed #555;border-radius:12px;padding:40px;text-align:center;margin:20px 0}
button{background:#e94560;color:#fff;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:16px}
img{max-width:100%;border-radius:8px;margin:10px 0}
pre{background:#0f3460;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;white-space:pre-wrap}
input[type=text]{padding:10px;border-radius:8px;border:1px solid #555;background:#16213e;color:#eee;width:200px}
</style></head><body>
<h1>ears</h1>
{% if not authed %}
<div class="box"><form method="post"><input type="text" name="token" placeholder="password"><br><br>
<button type="submit">enter</button></form></div>
{% elif result %}
<h2>spectrogram</h2><img src="/out/{{name}}/listen.png?t={{token}}">
<h2>prosody</h2><pre>{{summary}}</pre>
<h2>transcript</h2><pre>{{transcript}}</pre>
<br><a href="/?t={{token}}"><button>another</button></a>
{% else %}
<div class="box">
<form method="post" enctype="multipart/form-data">
<input type="file" name="audio" accept="audio/*,.m4a,.mp3,.wav,.webm,.ogg,.flac"><br><br>
<button type="submit">upload & analyze</button></form>
<p style="color:#888">m4a / mp3 / wav / webm / ogg / flac</p></div>
{% endif %}
</body></html>"""

@app.route('/out/<path:path>')
def serve_out(path):
    if request.args.get('t','') != TOKEN: abort(403)
    return send_from_directory(OUT, path)

@app.route('/', methods=['GET','POST'])
def index():
    token = request.args.get('t','') or request.form.get('token','')
    if token != TOKEN:
        return render_template_string(PAGE, authed=False, result=False)
    if request.method=='POST' and 'audio' in request.files:
        f = request.files['audio']
        if f.filename:
            fp = os.path.join(UPLOAD, f.filename)
            f.save(fp)
            vpy = os.path.join(BASE,'venv','bin','python')
            env = os.environ.copy()
            env['HF_ENDPOINT'] = 'https://hf-mirror.com'
            subprocess.run([vpy, os.path.join(BASE,'cochlea.py'), fp], env=env, cwd=BASE)
            subprocess.run([vpy, os.path.join(BASE,'transcribe.py'), fp], env=env, cwd=BASE)
            nm = os.path.splitext(f.filename)[0]
            rd = os.path.join(OUT, nm)
            sm = tr = '(not generated)'
            try:
                with open(os.path.join(rd,'summary.json')) as x: sm = json.dumps(json.load(x), ensure_ascii=False, indent=2)
            except: pass
            try:
                with open(os.path.join(rd,'transcript.json')) as x: tr = json.dumps(json.load(x), ensure_ascii=False, indent=2)
            except: pass
            return render_template_string(PAGE, authed=True, result=True, name=nm, summary=sm, transcript=tr, token=token)
    return render_template_string(PAGE, authed=True, result=False, token=token)

if __name__=='__main__':
    app.run(host='0.0.0.0', port=8745)
