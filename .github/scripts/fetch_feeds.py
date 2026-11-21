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
  {"id":"keyevents","name":"Key events (unverified endpoint)","url":"https://worldwatch.uk/key_events_proxy.php","note":"Endpoint path supplied in uploaded configuration but not verified."}]}
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
  with urllib.request.urlopen(req,timeout=18) as response:
   raw=response.read(2_000_000).decode("utf-8","replace")
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
