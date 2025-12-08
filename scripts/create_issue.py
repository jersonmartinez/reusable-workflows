import json, os, re, subprocess
from datetime import datetime, timezone

debug_path = os.path.join('docs','output.txt')

def log(msg):
    try:
        with open(debug_path,'a') as df:
            df.write(msg + "\n")
    except Exception:
        pass

def pr_details(num, repo):
    try:
        r = subprocess.run(['gh','pr','view',str(num),'--repo',repo,'--json','body'], capture_output=True, text=True)
        if r.returncode == 0:
            data = json.loads(r.stdout)
            return data.get('body','')
        return ''
    except Exception:
        return ''

def parse_title(t):
    m = re.search(r"bump\s+([^\s]+)\s+from\s+([^\s]+)\s+to\s+([^\s]+)(?:\s+in\s+(.+))?", t, re.IGNORECASE)
    if m:
        return {'name': m.group(1), 'from': m.group(2), 'to': m.group(3), 'dir': m.group(4) or ''}
    return None

def semver_tuple(s):
    parts = re.findall(r"\d+", s)
    nums = [int(x) for x in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)

def update_type(f, t):
    fM,fm,fp = semver_tuple(f)
    tM,tm,tp = semver_tuple(t)
    if tM != fM:
        return 'major'
    if tm != fm:
        return 'minor'
    if tp != fp:
        return 'patch'
    return 'other'

def build_body(prs, date, repo):
    lines = []
    run_id = os.getenv('RUN_ID','')
    server_url = os.getenv('SERVER_URL','https://github.com')
    if run_id:
        lines.append(f"**Descargar reportes (PDF/HTML):** {server_url}/{repo}/actions/runs/{run_id}\n\n")
    lines.append(f"### Reporte de actualizaciones ({date})\n")
    if prs:
        agg = {'major':0,'minor':0,'patch':0,'other':0}
        lines.append("\n| PR | Paquete | Desde | Hasta | Dir | Labels |\n")
        lines.append("|:--:|:-------|:-----:|:-----:|:---:|:------:|\n")
        for pr in prs:
            num = pr.get('number')
            url = pr.get('url')
            title_pr = pr.get('title','')
            meta = parse_title(title_pr) or {'name':'—','from':'—','to':'—','dir':''}
            labels_pr = ', '.join([l.get('name','') for l in pr.get('labels',[])]) or '—'
            lines.append(f"| [#{num}]({url}) | {meta['name']} | {meta['from']} | {meta['to']} | {meta['dir']} | {labels_pr} |\n")
            if meta['from'] != '—' and meta['to'] != '—':
                agg[update_type(meta['from'], meta['to'])] += 1
        lines.append("\n#### Resumen por tipo\n")
        lines.append(f"- Major: {agg['major']}\n- Minor: {agg['minor']}\n- Patch: {agg['patch']}\n- Other: {agg['other']}\n")
        lines.append("\n#### Detalles\n")
        for pr in prs:
            num = pr.get('number')
            url = pr.get('url')
            title_pr = pr.get('title','')
            body = pr_details(num, repo)
            snippet = (body or '').strip()
            if len(snippet) > 1200:
                snippet = snippet[:1200] + '…'
            lines.append(f"- [#{num}]({url}) {title_pr}\n")
            if snippet:
                lines.append(f"  \n  {snippet}\n")
    else:
        lines.append("\nNo se encontraron PRs de Dependabot en este momento.\n")
    return ''.join(lines)

def find_existing_issue(title, repo):
    try:
        r = subprocess.run(['gh','issue','list','--repo',repo,'--state','open','--limit','100','--json','number,title,url'], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            items = json.loads(r.stdout)
            for it in items:
                if it.get('title','') == title:
                    return it.get('url','')
        return ''
    except Exception:
        return ''

def main():
    prs_raw = os.getenv('PRS_DATA','[]')
    prs = json.loads(prs_raw) if prs_raw.strip() else []
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    title_tpl = os.getenv('ISSUE_TITLE_TPL','Reporte Dependabot: ${date}')
    title = title_tpl.replace('${date}', date)
    labels = [l.strip() for l in os.getenv('ISSUE_LABELS','').split(',') if l.strip()]
    repo = os.getenv('GITHUB_REPOSITORY')
    existing = find_existing_issue(title, repo)
    if existing:
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:
            f.write(f"issue_url={existing}\n")
        log(f"Issue existente reutilizado: {existing}")
        print(f"🧾 Issue reutilizado: {existing}")
        return
    body = build_body(prs, date, repo)
    cmd = ['gh','issue','create','--repo',repo,'--title',title,'--body',body]
    for l in labels:
        cmd += ['--label', l]
    result = subprocess.run(cmd, capture_output=True, text=True)
    url = ''
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.strip().startswith('https://'):
                url = line.strip()
                break
    else:
        log(f"Fallo al crear issue con labels. stderr: {result.stderr.strip()}")
        result2 = subprocess.run(['gh','issue','create','--repo',repo,'--title',title,'--body',body], capture_output=True, text=True)
        if result2.returncode == 0:
            for line in result2.stdout.splitlines():
                if line.strip().startswith('https://'):
                    url = line.strip()
                    break
        else:
            log(f"Intento sin labels también falló. stderr: {result2.stderr.strip()}")
    with open(os.environ['GITHUB_OUTPUT'],'a') as f:
        f.write(f"issue_url={url}\n")
    log(f"Issue title: {title}")
    log(f"Issue created: {url if url else 'N/A'}")
    print(f"🧾 Issue creado: {url if url else 'N/A'}")

if __name__ == '__main__':
    main()
