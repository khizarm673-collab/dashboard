import json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

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
]}]
 # Optional endpoint supplied by the project owner; the current URL returns 404.
 # Keep it visible as a configuration issue, not a failed live feed.
 {"optionalFeeds":[{"id":"keyevents","name":"Key Events (endpoint needs provider confirmation)","url":"https://worldwatch.uk/key_events_proxy.php","status":"unavailable","reason":"HTTP 404: the supplied URL does not exist at the provider."}]}
]

def fetch(feed):
 start=time.time()
 headers={"Accept":"application/json","User-Agent":"SituationDesk/1.0 (GitHub Actions read-only feed collector)"}
 body=None
 if feed.get("body") is not None:
  body=json.dumps(feed["body"]).encode()
  headers["Content-Type"]="application/json"
 req=urllib.request.Request(feed["url"],data=body,headers=headers,method=feed.get("method","GET"))
 try:
  with urllib.request.urlopen(req,timeout=30) as response:
   raw=response.read(12_000_000).decode("utf-8","replace")
   try: data=json.loads(raw)
   except Exception: data={"raw":raw[:3000]}
   status=response.status
   ok=200 <= status < 300
   error=None if ok else "Provider returned HTTP "+str(status)
 except urllib.error.HTTPError as e:
  raw=e.read(3000).decode("utf-8","replace")
  try: data=json.loads(raw)
  except Exception: data={"raw":raw}
  status=e.code; ok=False; error="Provider returned HTTP "+str(status)
 except Exception as e:
  status=0; ok=False; data=None; error=str(e)[:500]
 return {"ok":ok,"status":status,"ms":round((time.time()-start)*1000),"checked":datetime.now(timezone.utc).isoformat(),"data":data,"error":error,"url":feed["url"]}

for source in SOURCES:
 for feed in source["feeds"]:
  feed["result"]=fetch(feed)
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

# Persist the generated snapshot to the Pages source branch as well.
# [skip ci] prevents a push-triggered collection loop; scheduled/manual runs remain enabled.
import subprocess
subprocess.run(["git","config","user.name","github-actions[bot]"],check=True)
subprocess.run(["git","config","user.email","41898282+github-actions[bot]@users.noreply.github.com"],check=True)
subprocess.run(["git","add","live.json","data/live.json"],check=True)
changed=subprocess.run(["git","diff","--cached","--quiet"]).returncode != 0
if changed:
 subprocess.run(["git","commit","-m","chore: update live feed snapshot [skip ci]"],check=True)
 subprocess.run(["git","push","origin","HEAD:main"],check=True)
 print("Published live snapshot to main branch.")
else:
 print("Live snapshot unchanged; no branch commit needed.")
