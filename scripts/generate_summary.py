import json, os
from datetime import datetime, timezone
from urllib.parse import quote_plus

repo = os.getenv('GITHUB_REPOSITORY')
server_url = os.getenv('GITHUB_SERVER_URL', 'https://github.com')
company_name = (os.getenv('COMPANY_NAME','PRB') or 'PRB').strip()

try:
    prs_raw = os.getenv('PRS_DATA', '[]')
    prs_data = json.loads(prs_raw) if prs_raw and prs_raw.strip() != '' else []
except Exception as e:
    print(f"::debug::Error parseando PRs: {e}")
    prs_data = []

prs_count = int(os.getenv('PRS_COUNT', '0'))
issue_url = os.getenv('ISSUE_URL','')

def current_state(num: int):
    try:
        r = os.popen(f"gh api repos/{repo}/pulls/{num}").read()
        data = json.loads(r)
        st = data.get('state','open')
        merged_at = data.get('merged_at')
        if st == 'closed' and merged_at:
            return 'merged'
        return st
    except Exception:
        return 'unknown'

def status_badge(state: str):
    color = {'open':'brightgreen','closed':'lightgrey','merged':'purple','unknown':'blue'}.get(state,'blue')
    return f"<img src='https://img.shields.io/badge/status-{state}-{color}?style=flat-square' alt='{state}'/>"

def label_badges(labels):
    parts = []
    for l in labels:
        name = l.get('name','')
        if not name:
            continue
        color = l.get('color','0366d6')
        href = f"{server_url}/{repo}/pulls?q=is%3Apr+label%3A{quote_plus(name)}+author%3Aapp%2Fdependabot"
        parts.append(f"<img src='https://img.shields.io/badge/{name.replace('-', '--')}-{color}?style=flat-square' alt='{name}' style='margin:2px'>")
    return ' '.join(parts) or '➖'

def days_ago(iso):
    try:
        dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        return (now - dt).days
    except Exception:
        return None

def parse_title(t):
    import re
    m = re.search(r"bump\s+([^\s]+)\s+from\s+([^\s]+)\s+to\s+([^\s]+)(?:\s+in\s+(.+))?", t, re.IGNORECASE)
    if m:
        return {'name': m.group(1), 'from': m.group(2), 'to': m.group(3), 'dir': m.group(4) or ''}
    return None

def semver_tuple(s):
    import re
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

def directory_of(pr):
    meta = parse_title(pr.get('title',''))
    if meta.get('dir'):
        return meta['dir']
    ref = pr.get('headRefName','')
    if '/' in ref:
        parts = ref.split('/')
        try:
            idx = parts.index('dependabot')
            if idx >= 0 and len(parts) > idx+2:
                return '/' + '/'.join(parts[idx+2:-1])
        except Exception:
            pass
    return '/'

def sort_key(pr):
    order = {'open':0,'merged':1,'closed':2,'unknown':3}
    st = pr.get('state','open')
    try:
        ts = datetime.fromisoformat(pr.get('createdAt','').replace('Z','+00:00')).timestamp()
    except Exception:
        ts = 0
    return (order.get(st,3), -ts)

summary = []
summary.append("# 🔄 Pull Requests de Dependabot\n\n")
if issue_url:
    summary.append(f"> 🧾 <b>Reporte consolidado:</b> <a href='{issue_url}'>{issue_url}</a>\n\n")
if company_name:
    summary.append(f"> 🏢 <b>Empresa:</b> {company_name}\n\n")
if os.getenv('TRIGGER_DEPENDABOT_NOW','false') == 'true':
    cfg_url = f"{server_url}/{repo}/blob/main/.github/dependabot.yml"
    summary.append(f"> ⚡ <b>Trigger enviado</b>: se editó <a href='{cfg_url}'>dependabot.yml</a> para forzar un job de actualización.\n\n")

if prs_data and len(prs_data) > 0:
    try:
        max_summary = int(os.getenv('MAX_SUMMARY','30'))
    except Exception:
        max_summary = 30
    prs_sorted = sorted(prs_data, key=sort_key)
    show_list = prs_sorted[:min(prs_count, max_summary)]

    agg = {'major':0,'minor':0,'patch':0,'other':0}
    for pr in show_list:
        meta = parse_title(pr.get('title',''))
        if meta and meta['from'] and meta['to']:
            agg[update_type(meta['from'], meta['to'])] += 1

    summary.append(f"Mostrando {len(show_list)} de {prs_count} PRs\n\n")
    fast = os.getenv('FAST_SUMMARY','true').lower() == 'true'

    def state_of(pr):
        st = (pr.get('state','') or '').lower()
        if st != 'closed':
            return st
        num = pr.get('number')
        return current_state(num)

    def render_table(items, title, opened):
        summary.append("<details open>\n" if opened else "<details>\n")
        summary.append(f"<summary><h2>🔄 {title} ({len(items)})</h2></summary>\n\n")
        summary.append("<table>\n")
        summary.append("<thead>\n")
        summary.append("<tr>\n")
        summary.append("<th>PR</th><th>Paquete</th><th>Desde</th><th>Hasta</th><th>Dir</th><th>Estado</th><th>Labels</th><th>Edad</th>\n")
        summary.append("</tr>\n")
        summary.append("</thead>\n")
        summary.append("<tbody>\n")
        for pr in items:
            pr_number = pr.get('number','N/A')
            pr_url = pr.get('url','#')
            pr_title = pr.get('title','Sin título')
            lbl_html = label_badges(pr.get('labels',[]))
            created = pr.get('createdAt','')
            d_ago = days_ago(created)
            state_now = state_of(pr)
            meta = parse_title(pr_title) or {'name':'—','from':'—','to':'—','dir':directory_of(pr)}
            summary.append("<tr>\n")
            summary.append(f"<td><a href='{pr_url}'><b>#{pr_number}</b></a></td>\n")
            summary.append(f"<td>{meta['name']}</td>\n")
            summary.append(f"<td>{meta['from']}</td>\n")
            summary.append(f"<td>{meta['to']}</td>\n")
            summary.append(f"<td><code>{meta['dir'] or '/'}</code></td>\n")
            summary.append(f"<td>{status_badge(state_now)}</td>\n")
            summary.append(f"<td>{lbl_html}</td>\n")
            summary.append(f"<td>{(str(d_ago)+' d') if d_ago is not None else 'N/A'}</td>\n")
            summary.append("</tr>\n")
        summary.append("</tbody>\n")
        summary.append("</table>\n\n")
        summary.append("</details>\n\n")

    open_items, merged_items, closed_items = [], [], []
    for pr in show_list:
        st = state_of(pr)
        if st == 'open':
            open_items.append(pr)
        elif st == 'merged':
            merged_items.append(pr)
        elif st == 'closed':
            closed_items.append(pr)

    render_table(open_items, 'Abiertos', True)
    render_table(merged_items, 'Fusionados', False)
    render_table(closed_items, 'Cerrados', False)

    if prs_count > len(show_list):
        prs_url = f"{server_url}/{repo}/pulls?q=is%3Apr+author%3Aapp%2Fdependabot"
        summary.append(f"> <a href='{prs_url}'>📋 <b>Ver todos los PRs ({prs_count})</b></a>\n\n")

    summary.append("<details>\n")
    summary.append("<summary><h2>📁 Detalles por directorio</h2></summary>\n\n")
    groups = {}
    for pr in show_list:
        d = directory_of(pr)
        groups.setdefault(d or '/', []).append(pr)
    for d in sorted(groups.keys()):
        items = groups[d]
        summary.append(f"<h3><code>{d or '/'}</code> ({len(items)})</h3>\n")
        summary.append("<table>\n<thead>\n<tr>\n<th>PR</th><th>Paquete</th><th>Tipo</th><th>Edad</th>\n</tr>\n</thead>\n<tbody>\n")
        for pr in items:
            pr_number = pr.get('number','N/A')
            pr_url = pr.get('url','#')
            pr_title = pr.get('title','Sin título')
            created = pr.get('createdAt','')
            d_ago = days_ago(created)
            meta = parse_title(pr_title) or {'name':'—','from':'','to':''}
            typ = '—'
            try:
                if meta and meta.get('from') and meta.get('to'):
                    typ = update_type(meta.get('from',''), meta.get('to',''))
            except Exception:
                typ = 'other'
            typ_badge = f"<img src='https://img.shields.io/badge/update-{typ}-informational?style=flat-square' alt='{typ}'/>"
            summary.append("<tr>\n")
            summary.append(f"<td><a href='{pr_url}'>#{pr_number}</a></td>\n")
            summary.append(f"<td>{meta['name']}</td>\n")
            summary.append(f"<td>{typ_badge}</td>\n")
            summary.append(f"<td>{(str(d_ago)+' d') if d_ago is not None else 'N/A'}</td>\n")
            summary.append("</tr>\n")
        summary.append("</tbody>\n</table>\n\n")
    summary.append("</details>\n\n")
else:
    summary.append("> ℹ️ No hay PRs activos de Dependabot en este momento.\n\n")

summary.append("<details>\n")
summary.append("<summary><h2>⚙️ Cómo activar manualmente</h2></summary>\n\n")
dep_graph = f"{server_url}/{repo}/network/dependencies"
prs_link = f"{server_url}/{repo}/pulls?q=is%3Apr+author%3Aapp%2Fdependabot"
summary.append("1) Ve a <b>Insights → Dependency graph → Dependabot</b>\n")
summary.append(f"2) En <b>Recent update jobs</b>, pulsa <b>Check for updates</b> • <a href='{dep_graph}'>Acceder</a>\n")
summary.append(f"3) Revisa nuevos PRs: <a href='{prs_link}'>Listado de PRs de Dependabot</a>\n\n")
summary.append("</details>\n\n")

summary.append("<details>\n")
summary.append("<summary><h2>📄 Reportes Exportados</h2></summary>\n\n")
run_id = os.getenv('GITHUB_RUN_ID','')
if run_id:
    run_link = f"{server_url}/{repo}/actions/runs/{run_id}"
    summary.append(f"- PDF/HTML: <a href='{run_link}'>Descargar desde el run</a>\n\n")
summary.append("</details>\n\n")

summary.append("<details>\n")
summary.append("<summary><h2>🔗 Enlaces Útiles</h2></summary>\n\n")
config_url = f"{server_url}/{repo}/blob/main/.github/dependabot.yml"
security_url = f"{server_url}/{repo}/settings/security_analysis"
insights_url = f"{server_url}/{repo}/network/dependencies"
labels_url = f"{server_url}/{repo}/labels"
prs_url = f"{server_url}/{repo}/pulls?q=is%3Apr+author%3Aapp%2Fdependabot"
advisories_url = f"{server_url}/{repo}/security/dependabot"
doc_url = f"{server_url}/{repo}/blob/main/docs/security/dependency-check/dependabot-report.md"
summary.append(f"- 📝 <a href='{config_url}'><b>Ver Configuración</b></a>\n")
summary.append(f"- 🛡️ <a href='{security_url}'><b>Security Settings</b></a>\n")
summary.append(f"- 📊 <a href='{insights_url}'><b>Dependency Graph</b></a>\n")
summary.append(f"- 🏷️ <a href='{labels_url}'><b>Gestionar Labels</b></a>\n")
summary.append(f"- 🔄 <a href='{prs_url}'><b>PRs de Dependabot</b></a>\n")
summary.append(f"- 🚨 <a href='{advisories_url}'><b>Security Alerts</b></a>\n")
summary.append(f"- 📘 <a href='{doc_url}'><b>Documentación del workflow reusable</b></a>\n\n")
summary.append("</details>\n\n")

summary.append("<details>\n")
summary.append("<summary><h2>ℹ️ Información</h2></summary>\n\n")
summary.append("- 🔍 Detección y resumen inteligente de PRs\n")
summary.append("- 🏷️ Badges de estado y labels\n")
summary.append("- ⏱️ Edad de PRs y ordenamiento\n")
summary.append("- 📁 Sección por directorio\n")
summary.append("- 🔗 Enlaces útiles de UI\n\n")
summary.append("</details>\n\n")

timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
workflow_url = f"{server_url}/jersonmartinez/reusable-workflows"
summary.append(f"<sub>🤖 Generado por <a href='{workflow_url}'><b>Reusable Workflows</b></a> • {timestamp}</sub>\n")

with open(os.environ['GITHUB_STEP_SUMMARY'], 'w') as f:
    f.write(''.join(summary))

print("✅ Summary generado correctamente")
print(f"📊 PRs detectados: {prs_count}")
