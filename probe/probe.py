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
import time
for i in range(6):
    for name,url in [("fnac produit","https://www.fnac.com/a21424371"),("amazon","https://www.amazon.fr/dp/B0F2TN43GH")]:
        st,u,b=get(url)
        t=re.search(r"<title[^>]*>(.*?)</title>",b,re.S)
        price=re.findall(r'"price"\s*:\s*"?([0-9.,]+)',b)[:2]
        avail=re.findall(r'schema.org/(InStock|OutOfStock|PreOrder|SoldOut)',b)[:2]
        flags=[k for k in ["captcha","datadome"] if k in b.lower()]
        print(f"::notice title={name} #{i}::status={st} len={len(b)} title={(t.group(1).strip()[:90] if t else '')} price={price} avail={avail} flags={flags}")
    time.sleep(20)
