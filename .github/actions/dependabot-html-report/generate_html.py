import json, os, re
from datetime import datetime, timezone

def main():
    try:
        raw = os.getenv('PRS_DATA', '')
        if raw.strip():
            prs = json.loads(raw)
        elif os.path.exists('docs/prs.json'):
            with open('docs/prs.json', 'r') as f:
                prs = json.load(f)
        else:
            prs = []
    except Exception:
        prs = []

    html_path = os.getenv('HTML_PATH', 'docs/dependabot-report.html')
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    issue_url = os.getenv('ISSUE_URL', '')
    action_path = os.getenv('ACTION_PATH', '.')

    # Helper functions
    def parse_title(t):
        m = re.search(r"bump\s+([^\s]+)\s+from\s+([^\s]+)\s+to\s+([^\s]+)(?:\s+in\s+(.+))?", t, re.IGNORECASE)
        if m:
            return {'name': m.group(1), 'from': m.group(2), 'to': m.group(3), 'dir': m.group(4) or ''}
        return {'name': '—', 'from': '', 'to': '', 'dir': ''}

    def semver_tuple(s):
        nums = [int(x) for x in re.findall(r"\d+", s)[:3]]
        while len(nums) < 3:
            nums.append(0)
        return tuple(nums)

    def update_type(f, t):
        if not f or not t:
            return 'other'
        fM, fm, fp = semver_tuple(f)
        tM, tm, tp = semver_tuple(t)
        if tM != fM:
            return 'major'
        if tm != fm:
            return 'minor'
        if tp != fp:
            return 'patch'
        return 'other'

    def directory_of(pr):
        meta = parse_title(pr.get('title', ''))
        if meta.get('dir'):
            return meta['dir']
        ref = pr.get('headRefName', '')
        if '/' in ref:
            parts = ref.split('/')
            try:
                idx = parts.index('dependabot')
                if idx >= 0 and len(parts) > idx + 2:
                    return '/' + '/'.join(parts[idx + 2:-1])
            except Exception:
                pass
        return '/'

    def ecosystem_of(pr):
        ref = pr.get('headRefName', '')
        if '/' in ref:
            parts = ref.split('/')
            try:
                idx = parts.index('dependabot')
                if idx >= 0 and len(parts) > idx + 1:
                    eco = parts[idx + 1]
                    return 'npm' if eco == 'npm_and_yarn' else eco
            except Exception:
                pass
        return 'unknown'

    def sanitize_dir_path(s, eco_hint=''):
        try:
            d = (s or '/').strip().replace('\\', '/')
            if not d:
                d = '/'
            if d == '/':
                return '/'
            eco = (eco_hint or '').lower()
            eco = 'github-actions' if eco == 'github_actions' else eco
            if d.startswith('/main/') or d == '/main':
                return '/.github/workflows' if eco == 'github-actions' else '/'
            if ' ' in d:
                return '/.github/workflows' if eco == 'github-actions' else '/'
            first = d.split('/')[1] if d.startswith('/') and len(d.split('/')) > 1 else d.split('/')[0]
            if eco == 'github-actions' and first in ['actions', 'appleboy', 'main']:
                return '/.github/workflows'
            if '/main' in d:
                parts = [seg for seg in d.split('/') if seg and seg != 'main']
                d2 = '/' + '/'.join(parts)
                return '/' if d2 == '/' else d2
            return d
        except Exception:
            return '/'

    # Aggregation logic
    total_agg = {'major': 0, 'minor': 0, 'patch': 0, 'other': 0}
    dir_agg = {}
    eco_agg = {}
    rows = []

    for pr in prs:
        meta = parse_title(pr.get('title', ''))
        typ = update_type(meta.get('from', ''), meta.get('to', ''))
        total_agg[typ] = total_agg.get(typ, 0) + 1
        e = ecosystem_of(pr)
        d_raw = directory_of(pr)
        d = sanitize_dir_path(d_raw, e)
        dir_agg.setdefault(d, {'major': 0, 'minor': 0, 'patch': 0, 'other': 0})
        dir_agg[d][typ] += 1
        eco_agg.setdefault(e, {'major': 0, 'minor': 0, 'patch': 0, 'other': 0})
        eco_agg[e][typ] += 1
        labels = ', '.join([l.get('name', '') for l in pr.get('labels', [])]) or '—'
        created = pr.get('createdAt', '')
        try:
            created_fmt = datetime.fromisoformat(created.replace('Z', '+00:00')).strftime('%Y-%m-%d')
        except Exception:
            created_fmt = 'N/A'
        rows.append({
            'num': pr.get('number', ''),
            'name': meta['name'],
            'from': meta['from'],
            'to': meta['to'],
            'dir': d,
            'eco': e,
            'state': pr.get('state', 'open'),
            'labels': labels,
            'labels_list': pr.get('labels', []),
            'created': created_fmt,
            'created_iso': created,
            'url': pr.get('url', '#')
        })

    # Prepare HTML content
    repo = os.getenv('GITHUB_REPOSITORY', '')
    server_url = os.getenv('GITHUB_SERVER_URL', 'https://github.com')
    run_id = os.getenv('GITHUB_RUN_ID', '') or os.getenv('RUN_ID', '')
    run_link = f"{server_url}/{repo}/actions/runs/{run_id}" if run_id else ''
    owner = repo.split('/')[0] if '/' in (repo or '') else (repo or '')
    org_link = f"{server_url}/{owner}" if owner else ''
    company = (os.getenv('COMPANY_NAME', 'PRB') or 'PRB').strip()
    logo_url = os.getenv('LOGO_URL', 'https://extranet.prb.com.mx/Prb1.2/images/logos/logo_PRB.svg')

    # Read CSS and JS
    try:
        with open(os.path.join(action_path, 'style.css'), 'r') as f:
            css_content = f.read()
    except FileNotFoundError:
        css_content = ''
    
    try:
        with open(os.path.join(action_path, 'script.js'), 'r') as f:
            js_content = f.read()
    except FileNotFoundError:
        js_content = ''

    html = []
    html.append('<!doctype html><html data-bs-theme="dark"><head><meta charset="utf-8"><title>Reporte Dependabot</title>')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    html.append('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">')
    html.append(f'<style>{css_content}</style>')
    html.append('</head><body>')
    
    # Navbar
    html.append(f'<nav class="navbar navbar-expand-md fixed-top bg-body-tertiary border-bottom"><div class="container"><a class="navbar-brand d-flex align-items-center" href="#"><img src="{logo_url}" alt="{company}" height="24" class="me-2">{company}</a><button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#topNav" aria-controls="topNav" aria-expanded="false" aria-label="Toggle navigation"><span class="navbar-toggler-icon"></span></button><div class="collapse navbar-collapse" id="topNav"><ul class="navbar-nav ms-auto me-2"><li class="nav-item"><a class="nav-link" href="#listado">PRs</a></li><li class="nav-item"><a class="nav-link" href="#resumen">Resumen</a></li><li class="nav-item"><a class="nav-link" href="#dir">Directorios</a></li><li class="nav-item"><a class="nav-link" href="#eco">Ecosistemas</a></li><li class="nav-item"><a class="nav-link" href="#alertas">Alertas</a></li><li class="nav-item"><a class="nav-link" href="#recomendaciones">Recomendaciones</a></li><li class="nav-item"><a class="nav-link" href="#dir-detalles">Detalles</a></li><li class="nav-item"><a class="nav-link" href="{server_url}/{repo}" target="_blank" rel="noopener"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 16 16" fill="currentColor" class="me-1"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01 .37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33 .66 .07-.52 .28-.87 .51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87 .31-1.59 .82-2.15-.08-.2-.36-1.02 .08-2.12 0 0 .67-.21 2.2 .82 .64-.18 1.32-.27 2-.27s1.36 .09 2 .27c1.53-1.04 2.2-.82 2.2-.82 .44 1.1 .16 1.92 .08 2.12 .51 .56 .82 1.27 .82 2.15 0 3.07-1.87 3.75-3.65 3.95 .29 .25 .54 .73 .54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21 .15 .46 .55 .38A8.013 8.013 0"></path></svg><code>{repo or "—"}</code></a></li></ul></div></div></nav>')
    
    html.append('<div class="container my-4">')
    if issue_url:
        html.append(f'<div class="alert alert-secondary py-2">🧾 Reporte consolidado: <a href="{issue_url}" target="_blank" rel="noopener" class="text-decoration-none">{issue_url}</a></div>')
    
    html.append(f'<h1 class="mb-3">Reporte Dependabot</h1><p class="text-muted">Repositorio: <a href="{server_url}/{repo}" target="_blank" rel="noopener" class="text-decoration-none"><code>{repo or "—"}</code></a></p>')

    # KPIs
    open_rows = [r for r in rows if r['state'] == 'open']
    merged_rows = [r for r in rows if r['state'] == 'merged']
    closed_rows = [r for r in rows if r['state'] == 'closed']

    html.append('<div class="row g-3 mb-2">')
    html.append(f'<div class="col-md-3"><div class="kpi kpi-primary"><div class="fw-bold">📦 PRs totales</div><div class="display-6">{len(rows)}</div></div></div>')
    html.append(f'<div class="col-md-3"><div class="kpi kpi-warning"><div class="fw-bold">🔓 Abiertos</div><div class="display-6">{len(open_rows)}</div></div></div>')
    html.append(f'<div class="col-md-3"><div class="kpi kpi-success"><div class="fw-bold">✅ Fusionados</div><div class="display-6">{len(merged_rows)}</div></div></div>')
    html.append(f'<div class="col-md-3"><div class="kpi kpi-danger"><div class="fw-bold">❌ Cerrados</div><div class="display-6">{len(closed_rows)}</div></div></div>')
    html.append('</div>')

    # Helper for badges
    def badge_for(ver, typ, kind):
        emoji = {'major':'🔺','minor':'🟡','patch':'🟢','other':'🔹'}.get(typ,'🔹')
        color = {'major':'danger','minor':'warning','patch':'success','other':'secondary'}.get(typ,'secondary')
        if kind == 'from':
            return f'<span class="badge text-bg-secondary badge-ver">↩️ {ver}</span>'
        return f'<span class="badge text-bg-{color} badge-ver">{emoji} {ver}</span>'

    def label_tags(labels_list):
        if not labels_list: return '—'
        parts = []
        for l in labels_list:
            name = l.get('name','')
            color = l.get('color','0d6efd')
            parts.append(f'<span class="badge rounded-pill" style="background-color: #{color}; color: #fff;">{name}</span>')
        return ' '.join(parts)

    def render_rows(items):
        html.append('<div class="table-responsive"><table class="table table-striped table-bordered table-sm mb-2 pr-table"><thead><tr><th data-sort="num">PR</th><th data-sort="name">Paquete</th><th data-sort="from">Desde</th><th data-sort="to">Hasta</th><th data-sort="dir">Dir</th><th data-sort="eco">Eco</th><th data-sort="state">Estado</th><th data-sort="labels">Labels</th><th data-sort="created">Creado</th></tr></thead><tbody>')
        for r in items:
            typ = update_type(r.get('from',''), r.get('to',''))
            html.append(f'<tr data-num="{r["num"]}" data-name="{r["name"]}" data-created="{r["created"]}">'
                        f'<td><a href="{r["url"]}" target="_blank">#{r["num"]}</a></td>'
                        f'<td>{r["name"]}</td>'
                        f'<td>{badge_for(r.get("from",""), typ, "from")}</td>'
                        f'<td>{badge_for(r.get("to",""), typ, "to")}</td>'
                        f'<td><code>{r.get("dir","/")}</code></td>'
                        f'<td><code>{r.get("eco","unknown")}</code></td>'
                        f'<td>{r["state"]}</td>'
                        f'<td>{label_tags(r.get("labels_list",[]))}</td>'
                        f'<td>{r["created"]}</td></tr>')
        html.append('</tbody></table></div>')

    html.append('<h2 id="listado" class="mt-4">PRs por estado</h2>')
    html.append('<div class="accordion" id="prAccordion">')
    
    # Open
    html.append('<div class="accordion-item"><h2 class="accordion-header" id="headingOpen"><button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOpen">PRs Abiertos ({})</button></h2>'.format(len(open_rows)))
    html.append('<div id="collapseOpen" class="accordion-collapse collapse show" data-bs-parent="#prAccordion"><div class="accordion-body">')
    render_rows(open_rows)
    html.append('</div></div></div>')

    # Merged
    html.append('<div class="accordion-item"><h2 class="accordion-header" id="headingMerged"><button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseMerged">PRs Fusionados ({})</button></h2>'.format(len(merged_rows)))
    html.append('<div id="collapseMerged" class="accordion-collapse collapse" data-bs-parent="#prAccordion"><div class="accordion-body">')
    render_rows(merged_rows)
    html.append('</div></div></div>')

    # Closed
    html.append('<div class="accordion-item"><h2 class="accordion-header" id="headingClosed"><button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseClosed">PRs Cerrados ({})</button></h2>'.format(len(closed_rows)))
    html.append('<div id="collapseClosed" class="accordion-collapse collapse" data-bs-parent="#prAccordion"><div class="accordion-body">')
    render_rows(closed_rows)
    html.append('</div></div></div>')
    html.append('</div>')

    # Resumen
    html.append('<h2 id="resumen" class="mt-4">📊 Resumen general</h2>')
    html.append('<div class="row g-3 mb-2"><div class="col-md-6"><table class="table table-striped table-bordered table-sm mb-2"><thead><tr><th>Tipo</th><th>Cantidad</th></tr></thead><tbody>')
    for k in ['major','minor','patch','other']:
        html.append(f'<tr><td>{k}</td><td>{total_agg[k]}</td></tr>')
    html.append('</tbody></table></div>')
    html.append('<div class="col-md-6"><div class="section-card"><canvas id="chartTypes" style="max-height:200px"></canvas></div></div></div>')

    # Ecosistemas
    html.append('<h2 id="eco" class="mt-4">Métricas por ecosistema</h2>')
    html.append('<div class="row g-3 mb-2"><div class="col-md-6"><table class="table table-striped table-bordered table-sm mb-2"><thead><tr><th>Ecosistema</th><th>major</th><th>minor</th><th>patch</th><th>other</th></tr></thead><tbody>')
    for e in sorted(eco_agg.keys()):
        v = eco_agg[e]
        html.append(f'<tr><td><code>{e}</code></td><td>{v["major"]}</td><td>{v["minor"]}</td><td>{v["patch"]}</td><td>{v["other"]}</td></tr>')
    html.append('</tbody></table></div>')
    html.append('<div class="col-md-6"><div class="section-card"><canvas id="chartEcos" style="max-height:200px"></canvas></div></div></div>')

    # Alertas
    html.append('<h2 id="alertas" class="mt-4">🛡️ Alertas de Seguridad</h2>')
    try:
        raw_alerts = os.getenv('ALERTS_JSON', '').strip()
        alerts = json.loads(raw_alerts) if raw_alerts else []
    except:
        alerts = []
    
    if alerts:
        html.append(f'<div class="alert alert-warning">Se encontraron {len(alerts)} alertas de seguridad.</div>')
        # Simple table for alerts
        html.append('<div class="table-responsive"><table class="table table-striped table-bordered table-sm mb-2"><thead><tr><th>Paquete</th><th>Severidad</th><th>Ecosistema</th><th>Resumen</th></tr></thead><tbody>')
        for a in alerts[:50]:
            if not isinstance(a, dict): continue
            dep = a.get('dependency', {}).get('package', {})
            pkg = dep.get('name', '—')
            eco = dep.get('ecosystem', '—')
            sev = a.get('severity', 'unknown')
            summary = a.get('security_advisory', {}).get('summary', '—')
            html.append(f'<tr><td>{pkg}</td><td>{sev}</td><td>{eco}</td><td>{summary}</td></tr>')
        html.append('</tbody></table></div>')
    else:
        html.append('<div class="alert alert-success">No se detectaron alertas de seguridad.</div>')

    # Footer
    html.append('<footer class="bg-body-tertiary border-top mt-4"><div class="container py-4"><div class="text-center small text-muted">Generado automáticamente por Dependabot Report Workflow</div></div></footer>')

    # Scripts
    html.append('<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>')
    html.append('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')
    
    # Inject Data for Charts
    chart_types_data = [total_agg[k] for k in ['major','minor','patch','other']]
    eco_labels = sorted(list(eco_agg.keys()))
    eco_values = [eco_agg[e]['major']+eco_agg[e]['minor']+eco_agg[e]['patch']+eco_agg[e]['other'] for e in eco_labels]
    
    html.append('<script>')
    html.append(f'window.reportData = {{ types: {json.dumps(chart_types_data)}, ecos: {{ labels: {json.dumps(eco_labels)}, values: {json.dumps(eco_values)} }} }};')
    html.append('</script>')
    
    html.append(f'<script>{js_content}</script>')
    html.append('</body></html>')

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(''.join(html))
    print(f"HTML generado en {html_path}")

if __name__ == '__main__':
    main()
