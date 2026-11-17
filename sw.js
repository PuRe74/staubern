// Hält die App-Dateien und Schriften offline verfügbar. Strava-Abfragen laufen immer direkt übers Netz.
const CACHE="staubern-v2", FONTS="staubern-fonts-v1";
const FILES=["./","index.html","manifest.webmanifest","icon-180.png","icon-512.png"];
const FONT_HOSTS=["fonts.googleapis.com","fonts.gstatic.com"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(n=>n!==CACHE&&n!==FONTS).map(n=>caches.delete(n)))));self.clients.claim()});
self.addEventListener("fetch",e=>{
  const req=e.request, u=new URL(req.url);
  if(req.method!=="GET") return;
  // Schriften ändern sich nie: aus dem Cache, sonst einmal laden und behalten
  if(FONT_HOSTS.includes(u.hostname)){
    e.respondWith(caches.open(FONTS).then(c=>c.match(req).then(hit=>hit||fetch(req).then(r=>{if(r.ok)c.put(req,r.clone());return r}))));
    return;
  }
  // Videos nicht anfassen: der Browser lädt sie in Teilstücken, die sich nicht cachen lassen
  if(u.origin!==location.origin||req.headers.has("range")||u.pathname.includes("/video/")) return;
  // Netz zuerst, damit Updates sofort ankommen. Antwortet es nach 3 Sekunden nicht (schwacher Empfang am Berg), kommt die gespeicherte Fassung.
  const net=fetch(req).then(r=>{if(r.status===200){const c=r.clone();caches.open(CACHE).then(x=>x.put(req,c))}return r});
  const cached=()=>caches.match(req,{ignoreSearch:true});
  e.respondWith(Promise.race([net.catch(()=>null),new Promise(res=>setTimeout(res,3000))]).then(r=>r||cached().then(c=>c||net)));
  e.waitUntil(net.catch(()=>{}));
});
