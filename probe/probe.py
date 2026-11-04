import urllib.request, re, sys
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
H={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml","Accept-Language":"fr-FR,fr;q=0.9"}
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k): return None
def get(url, follow=True):
    op = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedir)
    try:
        r=op.open(urllib.request.Request(url,headers=H),timeout=20); return r.status, r.geturl(), r.read().decode("utf-8","ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location",""), e.read().decode("utf-8","ignore")
    except Exception as e:
        return 0,"",str(e)
for name,url in [("redir fnac","http://hmstr.biz/3GXct6"),
                 ("amazon","https://www.amazon.fr/dp/B0F2TN43GH"),
                 ("fnac search","https://www.fnac.com/SearchResult/ResultList.aspx?Search=switch+2+zelda+40e+anniversaire+console"),
                 ("fnac home","https://www.fnac.com/")]:
    follow = not name.startswith("redir")
    st,u,b=get(url,follow)
    t=re.search(r"<title[^>]*>(.*?)</title>",b,re.S)
    flags=[k for k in ["captcha","datadome","Robot Check","api-services-support","Disponible","Indisponible","add-to-cart","availability"] if k.lower() in b.lower()]
    print(f"::notice title={name}::status={st} url={u[:200]} len={len(b)} title={(t.group(1).strip()[:120] if t else '')} flags={flags}")
