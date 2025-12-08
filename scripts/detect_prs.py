import json, os, subprocess, time

def main():
    wait_minutes = int(os.getenv('WAIT_MINUTES', '10'))
    poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
    repo = os.getenv('GITHUB_REPOSITORY')
    debug_path = os.path.join('docs','output.txt')
    dep_logins = [s.strip() for s in os.getenv('DEP_LOGINS','dependabot,dependabot[bot],app/dependabot').split(',') if s.strip()]

    def log(msg):
        try:
            os.makedirs(os.path.dirname(debug_path), exist_ok=True)
            with open(debug_path,'a') as df:
                df.write(msg + "\n")
        except Exception:
            pass

    def list_prs_api():
        try:
            state = os.getenv('PRS_STATE','open')
            path = f"repos/{repo}/pulls?state={state}&per_page=100"
            args = ['gh','api',path,'--method','GET']
            result = subprocess.run(args, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                filtered = []
                for pr in data:
                    login = (pr.get('user',{}) or {}).get('login','')
                    if login in dep_logins:
                        filtered.append({
                            'number': pr.get('number'),
                            'title': pr.get('title'),
                            'url': pr.get('html_url'),
                            'labels': pr.get('labels',[]),
                            'createdAt': pr.get('created_at',''),
                            'headRefName': (pr.get('head',{}) or {}).get('ref',''),
                            'state': pr.get('state','')
                        })
                return filtered
            log(f"list_prs_api non-0 returncode: {result.returncode} stderr={result.stderr.strip()}")
            return []
        except Exception as e:
            log(f"list_prs_api exception: {e}")
            return []

    def list_prs_search():
        try:
            state = os.getenv('PRS_STATE','open')
            qp = [f"repo:{repo}", "is:pr", "(author:app/dependabot OR author:dependabot OR author:dependabot[bot])"]
            if state == 'all':
                qp.append("(is:open OR is:closed)")
            elif state in ('open','closed'):
                qp.append(f"is:{state}")
            q = " ".join(qp)
        except Exception:
            q = ""
        if not q:
            return []
        try:
            result = subprocess.run(['gh','api','search/issues','-f',f"q={q}",'-f','per_page=100'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                items = data.get('items',[])
                out = []
                for it in items:
                    out.append({
                        'number': it.get('number'),
                        'title': it.get('title'),
                        'url': it.get('html_url'),
                        'labels': it.get('labels',[]),
                        'createdAt': it.get('created_at',''),
                        'headRefName': '',
                        'state': it.get('state','')
                    })
                return out
            log(f"list_prs_search non-0 returncode: {result.returncode} stderr={result.stderr.strip()}")
        except Exception as e:
            log(f"list_prs_search exception: {e}")
        return []

    def list_prs_search_label_only():
        try:
            state = os.getenv('PRS_STATE','open')
            qp = [f"repo:{repo}", "is:pr", "label:dependencies"]
            if state == 'all':
                qp.append("(is:open OR is:closed)")
            elif state in ('open','closed'):
                qp.append(f"is:{state}")
            q = " ".join(qp)
        except Exception:
            q = ""
        if not q:
            return []
        try:
            result = subprocess.run(['gh','api','search/issues','-f',f"q={q}",'-f','per_page=100'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                items = data.get('items',[])
                out = []
                for it in items:
                    out.append({
                        'number': it.get('number'),
                        'title': it.get('title'),
                        'url': it.get('html_url'),
                        'labels': it.get('labels',[]),
                        'createdAt': it.get('created_at',''),
                        'headRefName': '',
                        'state': it.get('state','')
                    })
                return out
            log(f"list_prs_search_label_only non-0 returncode: {result.returncode} stderr={result.stderr.strip()}")
        except Exception as e:
            log(f"list_prs_search_label_only exception: {e}")
        return []

    prs = list_prs_api()
    log(f"Initial PRs count: {len(prs)}")
    if prs:
        for pr in prs:
            log(f"PR #{pr['number']} - {pr['title']} - {pr['url']}")
    
    if len(prs) == 0:
        fb = list_prs_search()
        if fb:
            prs = fb
        else:
            fb2 = list_prs_search_label_only()
            if fb2:
                prs = fb2
        log(f"Immediate fallback PRs count: {len(prs)}")

    should_wait = (os.getenv('TRIGGER_DEPENDABOT_NOW','false') == 'true' and os.getenv('PRS_STATE','open') == 'open' and wait_minutes > 0)
    deadline = time.time() + (wait_minutes*60 if should_wait else 0)
    
    while should_wait and len(prs) == 0 and time.time() < deadline:
        time.sleep(poll_interval)
        prs = list_prs_api()
        log(f"Polling... PRs count: {len(prs)}")

    if len(prs) == 0:
        fallback = list_prs_search()
        if fallback:
            prs = fallback
        else:
            fallback2 = list_prs_search_label_only()
            if fallback2:
                prs = fallback2
        log(f"Fallback PRs count: {len(prs)}")

    with open(os.environ['GITHUB_OUTPUT'],'a') as f:
        f.write('prs_data<<EOF\n')
        f.write(json.dumps(prs))
        f.write('\nEOF\n')
        f.write(f"prs_count={len(prs)}\n")
    
    print(f"📊 PRs detectados: {len(prs)}")

if __name__ == '__main__':
    main()
