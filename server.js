const http=require('http');
const fs=require('fs');
const path=require('path');
const PORT=Number(process.env.PORT)||5050;
const HEADERS={'Accept':'application/json','User-Agent':'SituationDesk/1.0 (read-only dashboard)'};
const SOURCES=[
{id:'glint',name:'Glint Trade Terminal',url:'https://glint.trade/terminal',category:'Markets',feeds:[
{id:'mids',name:'All mid prices',method:'POST',url:'https://api.hyperliquid.xyz/info',body:{type:'allMids'}},
{id:'meta',name:'Perpetuals metadata',method:'POST',url:'https://api.hyperliquid.xyz/info',body:{type:'meta'}},
{id:'contexts',name:'Funding, open interest & mark prices',method:'POST',url:'https://api.hyperliquid.xyz/info',body:{type:'metaAndAssetCtxs'}}]},
{id:'hormuz',name:'Hormuz Strait Monitor',url:'https://hormuzstraitmonitor.com/',category:'Maritime',feeds:[{id:'dashboard',name:'Dashboard feed',url:'https://hormuzstraitmonitor.com/api/dashboard'}]},
{id:'mts',name:'Monitor the Situation',url:'https://monitor-the-situation.com/',category:'OSINT',feeds:[{id:'events',name:'Live events',url:'https://monitor-the-situation.com/api/events'}]},
{id:'watchboard',name:'Watchboard',url:'https://watchboard.dev/',category:'Tracking',feeds:[
{id:'trackers',name:'Trackers',url:'https://watchboard.dev/api/v1/trackers.json'},
{id:'breaking',name:'Breaking news',url:'https://watchboard.dev/api/v1/breaking.json'},
{id:'search',name:'Search index',url:'https://watchboard.dev/api/v1/search-index.json'}]},
{id:'osiris',name:'OSIRIS AI',url:'https://www.osirisai.live/',category:'Global intelligence',feeds:[
{id:'health',name:'Health',url:'https://osirisai.live/api/health'},
{id:'stats',name:'Global statistics',url:'https://osirisai.live/api/stats'},
{id:'news',name:'Latest news',url:'https://osirisai.live/api/news'},
{id:'earthquakes',name:'Earthquakes',url:'https://osirisai.live/api/earthquakes'},
{id:'flights',name:'Flights',url:'https://osirisai.live/api/flights'},
{id:'cyber',name:'Cyber threats',url:'https://osirisai.live/api/cyber-threats'}]},
{id:'worldmonitor',name:'World Monitor',url:'https://www.worldmonitor.app/',category:'World events',feeds:[{id:'catalogue',name:'Public product catalogue',url:'https://www.worldmonitor.app/api/product-catalog',note:'Limited public endpoint; other data may require authorised access.'}]},
{id:'worldwatch',name:'World Watch UK',url:'https://worldwatch.uk/',category:'World intelligence',feeds:[
{id:'missiles',name:'Missiles with coordinates',url:'https://worldwatch.uk/missiles_with_coords.json'},
{id:'keyevents',name:'Key events (unverified endpoint)',url:'https://worldwatch.uk/key_events_proxy.php',note:'Endpoint path supplied in uploaded configuration but not verified.'}]}
];
const cache={};
function send(res,status,obj){res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'Content-Type','Cache-Control':'no-store'});res.end(JSON.stringify(obj))}
async function requestFeed(feed){
 const started=Date.now(),opts={method:feed.method||'GET',headers:{...HEADERS},signal:AbortSignal.timeout(14000)};
 if(feed.body){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(feed.body)}
 try{const r=await fetch(feed.url,opts);const raw=await r.text();let data;try{data=JSON.parse(raw)}catch{data={raw:raw.slice(0,3000)}}
 return {ok:r.ok,status:r.status,ms:Date.now()-started,checked:new Date().toISOString(),data,error:r.ok?null:'Provider returned HTTP '+r.status,url:feed.url};
 }catch(e){return {ok:false,status:0,ms:Date.now()-started,checked:new Date().toISOString(),data:null,error:e.name==='TimeoutError'?'Request timed out':e.message,url:feed.url}}
}
async function syncAll(){const jobs=[];for(const s of SOURCES)for(const f of s.feeds)jobs.push((async()=>{const result=await requestFeed(f);cache[s.id+':'+f.id]=result;return {source:s.id,feed:f.id,...result}})());return Promise.all(jobs)}
function snapshot(){return SOURCES.map(s=>({...s,feeds:s.feeds.map(f=>({...f,result:cache[s.id+':'+f.id]||null}))}))}
const server=http.createServer(async(req,res)=>{if(req.method==='OPTIONS'){res.writeHead(204,{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'Content-Type'});return res.end()}
 const u=new URL(req.url,'http://localhost');
 if(req.method==='GET'&&u.pathname==='/'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});return res.end(fs.readFileSync(path.join(__dirname,'index.html')))}
 if(req.method==='GET'&&u.pathname==='/api/health')return send(res,200,{ok:true,service:'Situation Desk API',sources:SOURCES.length,feeds:SOURCES.reduce((n,s)=>n+s.feeds.length,0)});
 if(req.method==='GET'&&u.pathname==='/api/sources')return send(res,200,snapshot());
 if(req.method==='GET'&&u.pathname==='/api/data')return send(res,200,Object.entries(cache).map(([key,result])=>({key,...result})));
 if(req.method==='POST'&&u.pathname==='/api/sync'){const results=await syncAll();return send(res,200,{checked:results.length,online:results.filter(x=>x.ok).length,failed:results.filter(x=>!x.ok).length,results,sources:snapshot()})}
 return send(res,404,{error:'Not found'});
});
server.listen(PORT,'0.0.0.0',()=>console.log('Situation Desk API listening on '+PORT));