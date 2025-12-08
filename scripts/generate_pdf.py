import json, os, re
from datetime import datetime, timezone

created = False
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
except Exception as e:
    # Fallback: sin reportlab, evita fallo y marca no creado
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out,'a') as f:
            f.write('created=false\n')
    print(f"Reportlab no disponible: {e}. Saltando generación de PDF.")
    raise SystemExit(0)

try:
    prs = json.loads(os.getenv('PRS_DATA','[]'))
except Exception:
    prs = []

pdf_path = os.getenv('PDF_PATH','docs/dependabot-report.pdf')
os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
styles = getSampleStyleSheet()
TitleCenter = ParagraphStyle('TitleCenter', parent=styles['Title'], alignment=1)
Heading2Center = ParagraphStyle('Heading2Center', parent=styles['Heading2'], alignment=1)
doc = SimpleDocTemplate(pdf_path, pagesize=A4)
flow = []
brand_done = False
company = (os.getenv('COMPANY_NAME','PRB') or 'PRB').strip()
html_custom = ''
flow.append(Paragraph(company, Heading2Center))
flow.append(Spacer(1,6))
title = Paragraph('Reporte de Dependabot', TitleCenter)
flow.append(title)
flow.append(Spacer(1,12))
ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

flow.append(Spacer(1,12))

def parse_title(t):
    m = re.search(r"bump\s+([^\s]+)\s+from\s+([^\s]+)\s+to\s+([^\s]+)(?:\s+in\s+(.+))?", t, re.IGNORECASE)
    if m:
        return {'name': m.group(1), 'from': m.group(2), 'to': m.group(3), 'dir': m.group(4) or ''}
    return {'name':'—','from':'','to':'','dir':''}

def semver_tuple(s):
    nums = [int(x) for x in re.findall(r"\d+", s)[:3]]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)

def update_type(f, t):
    if not f or not t:
        return 'other'
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

def ecosystem_of(pr):
    ref = pr.get('headRefName','')
    if '/' in ref:
        parts = ref.split('/')
        try:
            idx = parts.index('dependabot')
            if idx >= 0 and len(parts) > idx+1:
                eco = parts[idx+1]
                return 'npm' if eco == 'npm_and_yarn' else eco
        except Exception:
            pass
    return 'unknown'

def sanitize_dir_path(s, eco_hint=''):
    try:
        d = (s or '/').strip().replace('\\','/')
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
        first = d.split('/')[1] if d.startswith('/') and len(d.split('/'))>1 else d.split('/')[0]
        if eco == 'github-actions' and first in ['actions','appleboy','main']:
            return '/.github/workflows'
        if '/main' in d:
            parts = [seg for seg in d.split('/') if seg and seg != 'main']
            d2 = '/' + '/'.join(parts)
            return '/' if d2 == '/' else d2
        return d
    except Exception:
        return '/'

total_agg = {'major':0,'minor':0,'patch':0,'other':0}
dir_agg = {}
eco_agg = {}
server_url = os.getenv('GITHUB_SERVER_URL','https://github.com')
repo_url = os.getenv('GITHUB_REPOSITORY','')
for pr in prs:
    meta = parse_title(pr.get('title',''))
    typ = update_type(meta.get('from',''), meta.get('to',''))
    total_agg[typ] = total_agg.get(typ,0)+1
    e = ecosystem_of(pr)
    d_raw = directory_of(pr)
    d = sanitize_dir_path(d_raw, e)
    dir_agg.setdefault(d, {'major':0,'minor':0,'patch':0,'other':0})
    dir_agg[d][typ] += 1
    eco_agg.setdefault(e, {'major':0,'minor':0,'patch':0,'other':0})
    eco_agg[e][typ] += 1

flow.append(Paragraph('■ Índice', styles['Heading2']))
flow.append(Paragraph('1. Resumen por estado de PRs', styles['Normal']))
flow.append(Paragraph('2. Resumen general', styles['Normal']))
flow.append(Paragraph('3. Métricas por directorio', styles['Normal']))
flow.append(Paragraph('4. Métricas por ecosistema', styles['Normal']))
flow.append(Paragraph('5. Alertas de seguridad', styles['Normal']))
flow.append(Paragraph('6. Recomendaciones de remediación', styles['Normal']))
flow.append(Paragraph('7. Listado de PRs', styles['Normal']))
flow.append(Paragraph('8. PRs prioritarios', styles['Normal']))
flow.append(Spacer(1,12))

def current_state_for(pr):
    st = (pr.get('state','open') or '').lower()
    if st != 'closed':
        return st
    num = pr.get('number')
    try:
        r = os.popen(f"gh api repos/{repo_url}/pulls/{num}").read()
        data = json.loads(r)
        merged_at = data.get('merged_at')
        return 'merged' if merged_at else 'closed'
    except Exception:
        return 'closed'

open_rows, merged_rows, closed_rows = [], [], []
for pr in prs:
    st = current_state_for(pr)
    if st == 'open':
        open_rows.append(pr)
    elif st == 'merged':
        merged_rows.append(pr)
    elif st == 'closed':
        closed_rows.append(pr)

flow.append(Paragraph('■ Resumen por estado de PRs', styles['Heading2']))
flow.append(Spacer(1,6))
data_kpi = [['Métrica','Cantidad'],['PRs totales',len(prs)],['Abiertos',len(open_rows)],['Fusionados',len(merged_rows)],['Cerrados',len(closed_rows)]]
tbl_kpi = Table(data_kpi, repeatRows=1, colWidths=[doc.width/2]*2)
tbl_kpi.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
flow.append(tbl_kpi)
flow.append(Spacer(1,12))

flow.append(Paragraph('■ Resumen general', styles['Heading2']))
flow.append(Spacer(1,6))
data_summary = [['Tipo','Cantidad'],['major',total_agg['major']],['minor',total_agg['minor']],['patch',total_agg['patch']],['other',total_agg['other']]]
tbl_sum = Table(data_summary, repeatRows=1, colWidths=[doc.width/2]*2)
tbl_sum.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
flow.append(tbl_sum)
flow.append(Spacer(1,6))
flow.append(Paragraph("Tipos basados en <link href='https://semver.org/'><font color='blue'>SemVer</font></link>: major • minor • patch • other", styles['Italic']))
flow.append(Spacer(1,12))

flow.append(Paragraph('■ Métricas por directorio', styles['Heading2']))
flow.append(Spacer(1,6))
data_dir = [['Directorio','major','minor','patch','other']]
for d in sorted(dir_agg.keys()):
    if d and d.startswith('/'):
        href = f"{server_url}/{repo_url}/tree/main" + ('' if d == '/' else d)
        d_cell = Paragraph(f"<link href='{href}'><font color='blue'>{d}</font></link>", styles['Normal'])
    else:
        d_cell = Paragraph(d or '/', styles['Normal'])
    row = [d_cell, dir_agg[d]['major'], dir_agg[d]['minor'], dir_agg[d]['patch'], dir_agg[d]['other']]
    data_dir.append(row)
tbl_dir = Table(data_dir, repeatRows=1, colWidths=[doc.width/5]*5)
tbl_dir.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
flow.append(tbl_dir)
flow.append(Spacer(1,12))

flow.append(Paragraph('■ Métricas por ecosistema', styles['Heading2']))
flow.append(Spacer(1,6))
data_eco = [['Ecosistema','major','minor','patch','other']]
for e in sorted(eco_agg.keys()):
    row = [e, eco_agg[e]['major'], eco_agg[e]['minor'], eco_agg[e]['patch'], eco_agg[e]['other']]
    data_eco.append(row)
tbl_eco = Table(data_eco, repeatRows=1, colWidths=[doc.width/5]*5)
tbl_eco.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
flow.append(tbl_eco)
flow.append(Spacer(1,12))

alerts = []
severity_agg = {}
repo = os.getenv('REPO','')
try:
    import json as _j
    raw = os.getenv('ALERTS_JSON','').strip()
    if raw:
        _tmp = _j.loads(raw)
        alerts = _tmp if isinstance(_tmp, list) else []
    else:
        r = os.popen(f"gh api repos/{repo}/dependabot/alerts?state=open&per_page=100").read()
        _tmp = _j.loads(r)
        alerts = _tmp if isinstance(_tmp, list) else []
except Exception:
    alerts = []
for a in alerts:
    if isinstance(a, dict):
        s = (a.get('severity','') or 'unknown').lower()
        severity_agg[s] = severity_agg.get(s,0)+1

if alerts:
    flow.append(Paragraph('■ Alertas de Seguridad (abiertas)', styles['Heading2']))
    flow.append(Spacer(1,6))
    data_sec = [['Severidad','Cantidad']]
    for k in ['critical','high','moderate','low','unknown']:
        if k in severity_agg:
            data_sec.append([k, severity_agg[k]])
    tbl_sec = Table(data_sec, repeatRows=1, colWidths=[doc.width/2]*2)
    tbl_sec.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
    flow.append(tbl_sec)
    flow.append(Spacer(1,6))
    pkg_stats = {}
    for a in alerts:
        if not isinstance(a, dict):
            continue
        dep = a.get('dependency') if isinstance(a.get('dependency'), dict) else {}
        pkg_obj = dep.get('package') if isinstance(dep.get('package'), dict) else {}
        name = pkg_obj.get('name') or '—'
        fx = a.get('fixed_version') or ''
        ps = pkg_stats.get(name, {'count':0,'fix':'—'})
        ps['count'] += 1
        if fx:
            ps['fix'] = 'Sí'
        pkg_stats[name] = ps
    flow.append(Paragraph('■ Paquetes más afectados', styles['Heading2']))
    flow.append(Spacer(1,6))
    data_pkg = [['Paquete','Cantidad','Fix']]
    for name, ps in sorted(pkg_stats.items(), key=lambda kv: kv[1]['count'], reverse=True)[:10]:
        data_pkg.append([name, ps['count'], ps['fix']])
    tbl_pkg = Table(data_pkg, repeatRows=1, colWidths=[doc.width/3]*3)
    tbl_pkg.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
    flow.append(tbl_pkg)
    flow.append(Spacer(1,6))
    dir_pr_counts = {}
    for pr in prs:
        e = ecosystem_of(pr)
        d_raw = directory_of(pr)
        d = sanitize_dir_path(d_raw, e)
        dir_pr_counts[d] = dir_pr_counts.get(d,0)+1
    alerts_dir_counts = {}
    for a in alerts:
        if not isinstance(a, dict):
            continue
        mp = (a.get('manifest_path','') or '').strip()
        dep = a.get('dependency') if isinstance(a.get('dependency'), dict) else {}
        pkg_obj = dep.get('package') if isinstance(dep.get('package'), dict) else {}
        eco_hint = (pkg_obj.get('ecosystem') or '').lower()
        d = '/'
        if mp and '/' in mp:
            parts = mp.split('/')
            raw = '/' + '/'.join(parts[:-1])
            d = sanitize_dir_path(raw, eco_hint)
        elif mp:
            d = sanitize_dir_path('/', eco_hint)
        alerts_dir_counts[d] = alerts_dir_counts.get(d,0)+1
    flow.append(Paragraph('■ Cobertura por directorio', styles['Heading2']))
    flow.append(Spacer(1,6))
    data_cov = [['Directorio','PRs','Alertas','Densidad']]
    for d in sorted(set(list(dir_pr_counts.keys()) + list(alerts_dir_counts.keys()))):
        prs_c = dir_pr_counts.get(d,0)
        alt_c = alerts_dir_counts.get(d,0)
        dens = f"{(alt_c / prs_c):.2f}" if prs_c > 0 else ('∞' if alt_c > 0 else '0')
        cell = Paragraph(f"<link href='{server_url}/{repo_url}/tree/main" + ('' if d == '/' else d) + f"'><font color='blue'>{d}</font></link>", styles['Normal']) if (d and d.startswith('/')) else Paragraph(d or '/', styles['Normal'])
        data_cov.append([cell, prs_c, alt_c, dens])
    tbl_cov = Table(data_cov, repeatRows=1, colWidths=[doc.width/4]*4)
    tbl_cov.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
    flow.append(tbl_cov)
    flow.append(Spacer(1,6))
    data_alerts = [['Paquete','Severidad','CVSS','Ecosistema','Manifest','GHSA','CVE','Resumen','Rango','Fix']]
    for a in alerts[:20]:
        if not isinstance(a, dict):
            continue
        dep = a.get('dependency') if isinstance(a.get('dependency'), dict) else {}
        pkg_obj = dep.get('package') if isinstance(dep.get('package'), dict) else {}
        pkg = pkg_obj.get('name') or '—'
        sev = a.get('severity','') or 'unknown'
        adv = a.get('security_advisory') if isinstance(a.get('security_advisory'), dict) else {}
        cvss_obj = adv.get('cvss') if isinstance(adv.get('cvss'), dict) else {}
        cvss = cvss_obj.get('score') if isinstance(cvss_obj.get('score'), (int,float)) else '—'
        eco = pkg_obj.get('ecosystem') or '—'
        manifest = a.get('manifest_path','') or '—'
        ghsa = adv.get('ghsa_id') or '—'
        cve = adv.get('cve_id') or ''
        summary = adv.get('summary') or '—'
        rng = a.get('vulnerable_version_range') or a.get('vulnerable_requirements') or '—'
        fix = a.get('fixed_version') or '—'
        ghsa_ref = Paragraph(f"<link href='https://github.com/advisories/{ghsa}'><font color='blue'>{ghsa}</font></link>", styles['Normal']) if ghsa != '—' else Paragraph('—', styles['Normal'])
        cve_ref = Paragraph(f"<link href='https://nvd.nist.gov/vuln/detail/{cve}'><font color='blue'>{cve}</font></link>", styles['Normal']) if cve else Paragraph('—', styles['Normal'])
        man_ref = Paragraph(f"<link href='{server_url}/{repo_url}/blob/main/{manifest}'><font color='blue'><code>{manifest}</code></font></link>", styles['Normal']) if manifest != '—' and isinstance(manifest,str) else Paragraph(f"<code>{manifest}</code>", styles['Normal'])
        data_alerts.append([pkg, sev, cvss, eco, man_ref, ghsa_ref, cve_ref, summary, rng, fix])
    tbl_alerts = Table(data_alerts, repeatRows=1, colWidths=[doc.width/10]*10)
    tbl_alerts.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
    flow.append(tbl_alerts)
    flow.append(Spacer(1,12))

flow.append(Paragraph('■ Recomendaciones de remediación', styles['Heading2']))
flow.append(Spacer(1,6))
ecos_present = sorted([e for e in eco_agg.keys() if e and e != 'unknown'])
recos = []
recos.append('Prioriza critical/high y aplica versiones seguras indicadas en Fix.')
recos.append('Valida compatibilidad y habilita automerge para patch/minor con checks verdes.')
recos.append('Documenta paquetes sin fix disponible y da seguimiento a mantenedores.')
if 'github_actions' in ecos_present or 'github-actions' in ecos_present:
    recos.append('Actualiza tags de Actions en /.github/workflows y aplica permisos mínimos por job.')
if 'npm' in ecos_present:
    recos.append('Actualiza package.json y lockfile; ejecuta pruebas y revisa auditorías.')
if 'pip' in ecos_present or 'python' in ecos_present:
    recos.append('Actualiza requirements.txt y lock; verifica compatibilidad de librerías.')
if 'docker' in ecos_present:
    recos.append('Actualiza imágenes base y fija digests; reconstruye y escanea vulnerabilidades.')
if 'gomod' in ecos_present or 'go' in ecos_present:
    recos.append('Actualiza go.mod/go.sum y reejecuta pruebas y builds.')
if 'maven' in ecos_present or 'gradle' in ecos_present:
    recos.append('Actualiza dependencias en pom.xml/build.gradle y ejecuta la suite de pruebas.')
if 'cargo' in ecos_present or 'rust' in ecos_present:
    recos.append('Actualiza Cargo.toml con cargo update; valida binarios y pruebas.')
items = [ListItem(Paragraph(r, styles['Normal'])) for r in recos]
flow.append(ListFlowable(items, bulletType='bullet'))
flow.append(Spacer(1,12))

flow.append(Paragraph('■ Listado de PRs', styles['Heading2']))
flow.append(Spacer(1,6))
from urllib.parse import quote_plus
def age_days(iso):
    try:
        dt = datetime.fromisoformat((iso or '').replace('Z','+00:00'))
        now = datetime.now(timezone.utc)
        return (now - dt).days
    except Exception:
        return None
def risk_level(typ, age, labels):
    base = {'major':3,'minor':2,'patch':1,'other':1}.get(typ,1)
    extra = 0
    if isinstance(age,int) and age >= 60:
        extra = 2
    elif isinstance(age,int) and age >= 30:
        extra = 1
    has_sec = any((l.get('name','').lower().find('sec') >= 0) for l in (labels or []))
    if has_sec:
        extra += 1
    score = base + extra
    if score >= 5:
        return 'critical'
    if score >= 4:
        return 'high'
    if score >= 3:
        return 'medium'
    return 'low'

data = [['PR','Paquete','Versiones','Estado','Riesgo','Creado']]
for pr in prs:
    num = pr.get('number','')
    title = pr.get('title','')
    meta = parse_title(title)
    created = pr.get('createdAt','')
    try:
        created_fmt = datetime.fromisoformat(created.replace('Z','+00:00')).strftime('%Y-%m-%d')
    except Exception:
        created_fmt = 'N/A'
    labels_list = pr.get('labels',[])
    state = current_state_for(pr)
    d = meta.get('dir') or directory_of(pr)
    typ = 'other'
    try:
        if meta and meta.get('from') and meta.get('to'):
            typ = update_type(meta.get('from',''), meta.get('to',''))
    except Exception:
        typ = 'other'
    age = age_days(created)
    risklev = risk_level(typ, age, labels_list)
    risk_txt = {'critical':'Crítico','high':'Alto','medium':'Medio','low':'Bajo'}.get(risklev,'Bajo')
    vers_cell = Paragraph(f"{meta.get('from','')} → {meta.get('to','')}", styles['Normal'])
    pr_cell = Paragraph(f"<link href='{server_url}/{repo_url}/pull/{num}'><font color='blue'>#{num}</font></link>", styles['Normal'])
    risk_cell = Paragraph(risk_txt, styles['Normal'])
    data.append([pr_cell, meta.get('name','—'), vers_cell, state, risk_cell, created_fmt])
table = Table(
    data,
    repeatRows=1,
    colWidths=[
        doc.width*0.10,
        doc.width*0.32,
        doc.width*0.24,
        doc.width*0.12,
        doc.width*0.10,
        doc.width*0.12
    ]
)
table.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
    ('TEXTCOLOR',(0,0),(-1,0),colors.black),
    ('GRID',(0,0),(-1,-1),0.5,colors.grey),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
    ('ALIGN',(0,0),(-1,-1),'LEFT'),
    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
]))
flow.append(table)

if open_rows:
    prio = []
    for r in open_rows:
        meta = parse_title(r.get('title',''))
        typ = update_type(meta.get('from',''), meta.get('to','')) if meta.get('from') and meta.get('to') else 'other'
        age = age_days(r.get('createdAt',''))
        rv = risk_level(typ, age, r.get('labels',[]))
        prio.append({'pr': r, 'age': (age if isinstance(age,int) else 0), 'risk': rv, 'riskw': (3 if rv=='critical' else 2 if rv=='high' else 1 if rv=='medium' else 0)})
    prio = sorted(prio, key=lambda x: (x['riskw'], x['age']), reverse=True)[:10]
    if prio:
        flow.append(Spacer(1,12))
        flow.append(Paragraph('■ PRs prioritarios', styles['Heading2']))
        flow.append(Spacer(1,6))
        data_prio = [['PR','Paquete','Tipo','Riesgo','Edad','Dir']]
        for it in prio:
            r = it['pr']
            num = r.get('number','')
            meta = parse_title(r.get('title','')) or {'name':'—','from':'','to':'','dir':''}
            typ = update_type(meta.get('from',''), meta.get('to','')) if meta.get('from') and meta.get('to') else 'other'
            risk_txt = {'critical':'Crítico','high':'Alto','medium':'Medio','low':'Bajo'}.get(it['risk'],'Bajo')
            age_txt = ((str(it['age'])+' d') if isinstance(it['age'],int) else 'N/A')
            d = meta.get('dir') or directory_of(r)
            pr_cell = Paragraph(f"<link href='{server_url}/{repo_url}/pull/{num}'><font color='blue'>#{num}</font></link>", styles['Normal'])
            dir_cell = Paragraph(f"<link href='{server_url}/{repo_url}/tree/main" + ('' if d == '/' else d) + f"'><font color='blue'>{d}</font></link>", styles['Normal']) if (d and d.startswith('/')) else Paragraph(d or '/', styles['Normal'])
            data_prio.append([pr_cell, meta.get('name','—'), typ, risk_txt, age_txt, dir_cell])
        tbl_prio = Table(data_prio, repeatRows=1, colWidths=[doc.width/6]*6)
        tbl_prio.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
        flow.append(tbl_prio)

flow.append(Spacer(1,12))
flow.append(Paragraph('■ Información del repositorio', styles['Heading2']))
flow.append(Spacer(1,6))
owner = (repo_url.split('/')[0] if '/' in (repo_url or '') else (repo_url or ''))
repo_link_p = Paragraph(f"<link href='{server_url}/{repo_url}'><font color='blue'>{repo_url}</font></link>", styles['Normal'])
org_link_p = Paragraph(f"<link href='{server_url}/{owner}'><font color='blue'>{owner}</font></link>", styles['Normal']) if owner else Paragraph('—', styles['Normal'])
run_id = os.getenv('GITHUB_RUN_ID','') or os.getenv('RUN_ID','')
run_link_p = Paragraph(f"<link href='{server_url}/{repo_url}/actions/runs/{run_id}'><font color='blue'>Run de GitHub Actions</font></link>", styles['Normal']) if run_id else Paragraph('—', styles['Normal'])
info_tbl = [['Campo','Valor'],['Repositorio', repo_link_p],['Organización', org_link_p],['Último run', run_link_p]]
tbl_info = Table(info_tbl, repeatRows=1, colWidths=[doc.width/3, doc.width*2/3])
tbl_info.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
flow.append(tbl_info)
flow.append(Spacer(1,12))

flow.append(Paragraph('■ Enlaces útiles', styles['Heading2']))
flow.append(Spacer(1,6))
config_url = f"{server_url}/{repo}/blob/main/.github/dependabot.yml"
security_url = f"{server_url}/{repo}/settings/security_analysis"
insights_url = f"{server_url}/{repo}/network/dependencies"
labels_url = f"{server_url}/{repo}/labels"
prs_url = f"{server_url}/{repo}/pulls?q=is%3Apr+author%3Aapp%2Fdependabot"
advisories_url = f"{server_url}/{repo}/security/dependabot"
doc_url = f"{server_url}/{repo}/blob/main/docs/security/dependency-check/dependabot-report.md"
links_tbl = [['Nombre','Enlace'],
                ['Ver Configuración', Paragraph(f"<link href='{config_url}'><font color='blue'>Config</font></link>", styles['Normal'])],
                ['Security Settings', Paragraph(f"<link href='{security_url}'><font color='blue'>Security</font></link>", styles['Normal'])],
                ['Dependency Graph', Paragraph(f"<link href='{insights_url}'><font color='blue'>Graph</font></link>", styles['Normal'])],
                ['Labels', Paragraph(f"<link href='{labels_url}'><font color='blue'>Labels</font></link>", styles['Normal'])],
                ['PRs de Dependabot', Paragraph(f"<link href='{prs_url}'><font color='blue'>PRs</font></link>", styles['Normal'])],
                ['Security Alerts', Paragraph(f"<link href='{advisories_url}'><font color='blue'>Alerts</font></link>", styles['Normal'])],
                ['Documentación', Paragraph(f"<link href='{doc_url}'><font color='blue'>Doc</font></link>", styles['Normal'])]]
tbl_links = Table(links_tbl, repeatRows=1, colWidths=[doc.width/3, doc.width*2/3])
tbl_links.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
flow.append(tbl_links)
flow.append(Spacer(1,12))

flow.append(Paragraph('■ Reporte interactivo (HTML)', styles['Heading2']))
flow.append(Spacer(1,6))
flow.append(Paragraph('Para mejor visualización y navegación, utiliza el reporte HTML disponible como artefacto en el run de GitHub Actions.', styles['Italic']))
if run_id:
    flow.append(Paragraph(f"<link href='{server_url}/{repo}/actions/runs/{run_id}'><font color='blue'>Descargar HTML</font></link>", styles['Normal']))
flow.append(Spacer(1,12))

flow.append(Paragraph('■ Recomendaciones finales', styles['Heading2']))
flow.append(Spacer(1,6))
items2 = [
    ListItem(Paragraph('Prioriza critical/high y aplica versiones seguras.', styles['Normal'])),
    ListItem(Paragraph('Habilita automerge en patch/minor con checks verdes.', styles['Normal'])),
    ListItem(Paragraph('Documenta paquetes sin fix y da seguimiento.', styles['Normal']))
]
flow.append(ListFlowable(items2, bulletType='bullet'))
flow.append(Spacer(1,6))
flow.append(Paragraph('Creado por el equipo de DevOps', styles['Italic']))
doc.build(flow)
created = True
out = os.environ.get('GITHUB_OUTPUT')
if out:
    with open(out,'a') as f:
        f.write('created=true\n')
print(f"PDF generado en {pdf_path}")
