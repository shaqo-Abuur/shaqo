const V="shaqo-v3",SHELL=["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{const r=e.request;if(r.method!=="GET")return;
if(new URL(r.url).pathname.startsWith("/api/")){e.respondWith(fetch(r).catch(()=>caches.match(r)));return}
if(r.mode==="navigate"){e.respondWith(fetch(r).then(x=>{const c=x.clone();caches.open(V).then(h=>h.put("./index.html",c));return x}).catch(()=>caches.match("./index.html")));return}
e.respondWith(caches.match(r).then(h=>{const n=fetch(r).then(x=>{if(x&&(x.ok||x.type==="opaque")){const c=x.clone();caches.open(V).then(k=>k.put(r,c))}return x}).catch(()=>h);return h||n}))});
