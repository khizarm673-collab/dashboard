import json, time, hashlib, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

PREVIOUS = {}
try:
 old = json.loads(Path('live.json').read_text(encoding='utf-8'))
 PREVIOUS = {(s.get('id'), f.get('id')): f.get('result', {}) for s in old.get('sources', []) for f in s.get('feeds', [])}
except Exception:
 pass

SOURCES = [
 {"id":"glint","name":"Glint Trade Terminal","url":"https://glint.trade/terminal","category":"Markets","feeds":[
  {"id":"mids","name":"All mid prices","method":"POST","url":"https://api.hyperliquid.xyz/info","body":{"type":"allMids"}},
  {"id":"meta","name":"Perpetuals metadata","method":"POST","url":"https://api.hyperliquid.xyz/info","body":{"type":"meta"}},
  {"id":"contexts","name":"Funding, open interest & mark prices","method":"POST","url":"https://api.hyperliquid.xyz/info","body":{"type":"metaAndAssetCtxs"}}]},
 {"id":"hormuz","name":"Hormuz Strait Monitor","url":"https://hormuzstraitmonitor.com/","category":"Maritime","feeds":[{"id":"dashboard","name":"Dashboard feed","url":"https://hormuzstraitmonitor.com/api/dashboard"}]},
 {"id":"mts","name":"Monitor the Situation","url":"https://monitor-the-situation.com/","category":"OSINT","feeds":[{"id":"events","name":"Live events","url":"https://monitor-the-situation.com/api/events"}]},
 {"id":"watchboard","name":"Watchboard","url":"https://watchboard.dev/","category":"Tracking","feeds":[
  {"id":"trackers","name":"Trackers","url":"https://watchboard.dev/api/v1/trackers.json"},
  {"id":"breaking","name":"Breaking news","url":"https://watchboard.dev/api/v1/breaking.json"},
  {"id":"search","name":"Search index","url":"https://watchboard.dev/api/v1/search-index.json"}]},
 {"id":"osiris","name":"OSIRIS AI","url":"https://www.osirisai.live/","category":"Global intelligence","feeds":[
  {"id":"health","name":"Health","url":"https://osirisai.live/api/health"},
  {"id":"stats","name":"Global statistics","url":"https://osirisai.live/api/stats"},
  {"id":"news","name":"Latest news","url":"https://osirisai.live/api/news"},
  {"id":"earthquakes","name":"Earthquakes","url":"https://osirisai.live/api/earthquakes"},
  {"id":"flights","name":"Flights","url":"https://osirisai.live/api/flights"},
  {"id":"cyber","name":"Cyber threats","url":"https://osirisai.live/api/cyber-threats"}]},
 {"id":"worldmonitor","name":"World Monitor","url":"https://www.worldmonitor.app/","category":"World events","feeds":[{"id":"catalogue","name":"Public product catalogue","url":"https://www.worldmonitor.app/api/product-catalog","note":"Limited public endpoint; other data may require authorised access."}]},
 {"id":"worldwatch","name":"World Watch UK","url":"https://worldwatch.uk/","category":"World intelligence","feeds":[
  {"id":"missiles","name":"Missiles with coordinates","url":"https://worldwatch.uk/missiles_with_coords.json"},
],"optionalFeeds":[{"id":"keyevents","name":"Key Events (endpoint needs provider confirmation)","url":"https://worldwatch.uk/key_events_proxy.php","status":"unavailable","reason":"HTTP 404: the supplied URL does not exist at the provider."}]}]

def fetch(feed):
 start=time.time()
 headers={"Accept":"application/json","User-Agent":"SituationDesk/1.1 (+https://github.com/khizarm673-collab/dashboard; live read-only feed collector)","Cache-Control":"no-cache, no-store, max-age=0","Pragma":"no-cache","Expires":"0"}
 body=None
 if feed.get("body") is not None:
  body=json.dumps(feed["body"]).encode()
  headers["Content-Type"]="application/json"
 method=feed.get("method","GET")
 status=0; data=None; error=None
 for attempt in range(3):
  req=urllib.request.Request(feed["url"],data=body,headers=headers,method=method)
  try:
   with urllib.request.urlopen(req,timeout=35) as response:
    raw=response.read(12_000_000).decode("utf-8","replace")
    try: data=json.loads(raw)
    except Exception: data={"raw":raw[:3000]}
    status=response.status
    if not 200 <= status < 300: error="Provider returned HTTP "+str(status)
    break
  except urllib.error.HTTPError as e:
   raw=e.read(3000).decode("utf-8","replace")
   try: data=json.loads(raw)
   except Exception: data={"raw":raw}
   status=e.code; error="Provider returned HTTP "+str(status)
   if status not in (408,425,429,500,502,503,504) or attempt == 2: break
  except Exception as e:
   error=str(e)[:500]
   if attempt == 2: break
  time.sleep(1.5*(attempt+1))
 ok=200 <= status < 300
 checked=datetime.now(timezone.utc).isoformat()
 encoded=json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(",",":"))
 fingerprint=hashlib.sha256(encoded.encode("utf-8")).hexdigest() if data is not None else None
 previous=PREVIOUS.get((feed.get("_source_id"),feed.get("id")),{})
 changed=bool(fingerprint and fingerprint != previous.get("fingerprint"))
 return {"ok":ok,"status":status,"ms":round((time.time()-start)*1000),"checked":checked,"data":data,"error":error,"url":feed["url"],"fingerprint":fingerprint,"changed":changed,"lastChangedAt":checked if changed or not previous.get("lastChangedAt") else previous.get("lastChangedAt")}

for source in SOURCES:
 for feed in source["feeds"]:
  feed["_source_id"]=source["id"]
  feed["result"]=fetch(feed)
  feed.pop("_source_id",None)
  print(source["id"],feed["id"],feed["result"]["status"],"OK" if feed["result"]["ok"] else feed["result"]["error"])
def compact(value, depth=0, max_items=80):
 if depth > 7:
  return "[nested data omitted]"
 if isinstance(value, str):
  return value if len(value) <= 2500 else value[:2500] + " …[truncated]"
 if isinstance(value, list):
  return [compact(x, depth+1, max_items) for x in value[:max_items]]
 if isinstance(value, dict):
  items=list(value.items())[:100]
  out={str(k):compact(v,depth+1,max_items) for k,v in items}
  if len(value)>len(items): out["_truncated_keys"]=len(value)-len(items)
  return out
 return value

# Keep snapshots small enough for reliable browser delivery while preserving
# useful live records for dashboard tables and detail views.
for source in SOURCES:
 for feed in source["feeds"]:
  result=feed.get("result") or {}
  data=result.get("data")
  compacted=compact(data,max_items=80)
  encoded=json.dumps(compacted,ensure_ascii=False,separators=(",",":"))
  if len(encoded.encode("utf-8")) > 250_000:
   compacted=compact(data,max_items=20)
   encoded=json.dumps(compacted,ensure_ascii=False,separators=(",",":"))
  if len(encoded.encode("utf-8")) > 250_000:
   compacted={"_preview":encoded[:12000]," _truncated":True}
  result["data"]=compacted
  result["bytes"]=len(json.dumps(compacted,ensure_ascii=False).encode("utf-8"))
  result["recordCount"]=len(data) if isinstance(data,list) else (len(data) if isinstance(data,dict) else 0)

out={"generatedAt":datetime.now(timezone.utc).isoformat(),"sources":SOURCES}
payload=json.dumps(out,ensure_ascii=False,separators=(",",":"))
# Publish at the site root (most reliable on GitHub Pages) and retain the old path.
Path("live.json").write_text(payload,encoding="utf-8")
Path("data").mkdir(exist_ok=True)
Path("data/live.json").write_text(payload,encoding="utf-8")
print("Wrote live.json and data/live.json:", len(payload), "bytes")
print("Changed feeds:", sum(1 for s in SOURCES for f in s["feeds"] if f["result"].get("changed")))

# The generated snapshots are uploaded directly as the GitHub Pages artifact
# by this workflow. Do not push commits from the collector: concurrent commits
# can race with code updates and cause non-fast-forward failures.
print("Snapshot ready for Pages deployment.")
