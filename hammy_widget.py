"""
Safe Route Lahore - Hammy 2.0: a 3D little brother you can talk to
==================================================================

WHAT THIS FILE DOES:
  Builds ONE web widget (HTML + JavaScript) that contains:
    1. A 3D cartoon boy, Hammy (very big round head, glossy brown eyes,
       fluffy brown hair with one curl, light grey hoodie with a star patch),
       drawn with three.js. Cartoon ("toon") shading and a thin outline make
       him look hand-drawn. He is made only from simple shapes (spheres,
       cylinders), so there are no borrowed models or copyright issues. He
       bounces, blinks, waves hello, hops when you tap him, and his mouth
       moves while he talks.
    2. Text chat: type a message and press Enter.
    3. He also listens to the map: during "Walk me home" the map sends him
       a line for each street (BroadcastChannel), and he cheers on arrival.
    4. Voice chat:
         - 🎤 Hold-to-talk: the browser turns your speech into text
           (Web Speech API, works best in Chrome / Edge).
         - 🔊 Hammy reads every reply out loud (browser text-to-speech).

WHERE HAMMY'S "BRAIN" LIVES:
  The replies still come from hammy.py (the rule-based agent). We send its
  INTENTS list into the widget as JSON, and a tiny JavaScript copy of
  detect_intent() picks the reply inside the browser. So:
    - chatting never reloads the page or the map, and
    - there is still ONE place to edit Hammy's words: hammy.py.

LIMITS TO MENTION (honest trade-offs):
  - Voice input needs Chrome or Edge and microphone permission; Safari and
    Firefox may not support it. Typing always works.
  - The voice is the browser's built-in one, so it sounds different on
    each device.
"""

import json

import streamlit.components.v1 as components

from hammy import FALLBACK, INTENTS

GREETING = "Salam apa! I'm Hammy, your little brother for the walk. Talk to me or type, I'm listening!"

HTML = r"""
<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito:wght@500;700;800&display=swap" rel="stylesheet">
<style>
  :root { --card:#ffffff; --ink:#2b2140; --muted:#8a7f9e; --me:#ffe6da; --him:#efe8ff; --accent:#7c5cff; --rose:#ff4f7b; }
  * { box-sizing:border-box; font-family:"Nunito", system-ui, sans-serif; }
  body { margin:0; background:transparent; color:var(--ink); }
  .wrap { display:flex; flex-direction:column; gap:10px; }
  #stage { width:100%; height:330px; flex:none; overflow:hidden; position:relative; border-radius:26px;
           background: radial-gradient(circle at 50% 42%, #fff4fb 0%, #ffe3ef 38%, #eadfff 72%, rgba(234,223,255,0) 100%); }
  #stage canvas { display:block; }
  #name { position:absolute; top:12px; left:14px; font:600 18px "Fredoka", sans-serif; color:var(--accent);
          background:#fff; border-radius:999px; padding:3px 12px; box-shadow:0 4px 12px rgba(124,92,255,.15); }
  #status { position:absolute; bottom:10px; left:0; right:0; text-align:center; font:600 13px "Fredoka", sans-serif; color:var(--muted); }
  #bubble { position:absolute; top:12px; right:10px; max-width:40%; background:#fff; border-radius:18px 18px 4px 18px; padding:7px 11px;
            font-size:12px; font-weight:700; box-shadow:0 6px 16px rgba(124,92,255,.18); opacity:0; transform:translateY(6px) scale(.95);
            transition:opacity .25s, transform .25s; pointer-events:none; }
  #bubble.on { opacity:1; transform:none; }
  .chat { background:var(--card); border-radius:22px; padding:12px; box-shadow:0 8px 24px rgba(124,92,255,.12);
          flex:1; display:flex; flex-direction:column; min-width:0; }
  #log { flex:none; overflow-y:auto; height:150px; padding:4px; scroll-behavior:smooth; }
  .msg { padding:8px 12px; border-radius:16px; margin:5px 0; max-width:90%; line-height:1.4; font-size:14px; animation:in .25s ease-out; }
  @keyframes in { from { opacity:0; transform:translateY(6px) } to { opacity:1; transform:none } }
  .him { background:var(--him); border-bottom-left-radius:4px; }
  .me { background:var(--me); margin-left:auto; border-bottom-right-radius:4px; }
  .row { display:flex; gap:6px; margin-top:8px; }
  input { flex:1; min-width:0; padding:10px 14px; border-radius:999px; border:2px solid #eee3f7; background:#fffafd; color:var(--ink); font-size:14px; outline:none; }
  input:focus { border-color:#c9b8ff; }
  button { border:none; border-radius:999px; width:42px; height:42px; cursor:pointer; font-size:17px; color:white; flex:none;
           background:linear-gradient(135deg,#7c5cff,#a46bff); transition:transform .12s; }
  button:hover { transform:scale(1.06); }
  button.mic { background:linear-gradient(135deg,#ff4f7b,#ff7a59); }
  button.mic.on { animation:pulse 1s infinite; }
  @keyframes pulse { 50% { box-shadow:0 0 0 8px rgba(255,79,123,.25) } }
  button.ghost { background:#f3eefc; color:var(--ink); font-size:15px; }
  .note { font-size:11.5px; color:var(--muted); margin-top:6px; }
</style></head>
<body>
<div class="wrap">
  <div id="stage"><div id="name">Hammy 🐹</div><div id="bubble"></div><div id="status">tap me!</div></div>
  <div class="chat">
    <div id="log"></div>
    <div class="row">
      <input id="text" placeholder="Talk to Hammy… (English or Roman Urdu)">
      <button id="send" title="Send">➤</button>
      <button id="mic" class="mic" title="Hold to talk">🎤</button>
      <button id="mute" class="ghost" title="Voice on/off">🔊</button>
    </div>
    <div class="note" id="note">Hold 🎤 and speak (Chrome / Edge). Hammy answers out loud.</div>
  </div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const INTENTS = __INTENTS__;
const FALLBACK = __FALLBACK__;
const GREETING = __GREETING__;

/* ---------------- Hammy's brain (JavaScript copy of hammy.detect_intent) ---------------- */
function detectIntent(message) {
  const text = " " + message.toLowerCase().replace(/[!,.?]/g, " ") + " ";
  for (const [name, keywords] of INTENTS) {
    for (const w of keywords) {
      if ((w.length <= 3 && text.includes(" " + w + " ")) || (w.length > 3 && text.includes(w))) return name;
    }
  }
  return null;
}
function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
function replyTo(message) {
  const intent = detectIntent(message);
  for (const [name, , answers] of INTENTS) if (name === intent) return {intent, text: pick(answers)};
  return {intent: null, text: pick(FALLBACK)};
}

/* ---------------- chat log ---------------- */
const log = document.getElementById("log");
function bold(s) { return s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>"); }
function add(who, text) {
  const d = document.createElement("div");
  d.className = "msg " + who; d.innerHTML = bold(text);
  log.appendChild(d); log.scrollTop = log.scrollHeight;
  if (who === "him") {                       // a speech bubble next to Hammy too
    const b = document.getElementById("bubble");
    b.innerHTML = bold(text.length > 90 ? text.slice(0, 88) + "…" : text); b.classList.add("on");
    clearTimeout(add.t); add.t = setTimeout(() => b.classList.remove("on"), 4500);
  }
}

/* ---------------- voice out (text-to-speech) ---------------- */
let muted = false, talking = false;
function speak(text) {
  if (muted || !("speechSynthesis" in window)) return;
  const clean = text.replace(/\*\*/g, "").replace(/[\u{1F300}-\u{1FAFF}☀-➿]/gu, "");
  const u = new SpeechSynthesisUtterance(clean);
  const voices = speechSynthesis.getVoices();
  const v = voices.find(v => /en[-_](IN|GB|US)/i.test(v.lang) && /male|boy|david|rishi|daniel|alex/i.test(v.name))
         || voices.find(v => /^en/i.test(v.lang));
  if (v) u.voice = v;
  u.pitch = 1.35; u.rate = 1.02;              // a bit higher and quicker: a little brother
  u.onstart = () => { talking = true; setStatus("Hammy is talking…"); };
  u.onend = u.onerror = () => { talking = false; setStatus(""); };
  speechSynthesis.cancel(); speechSynthesis.speak(u);
}
document.getElementById("mute").onclick = (e) => {
  muted = !muted; e.target.textContent = muted ? "🔇" : "🔊";
  if (muted && "speechSynthesis" in window) speechSynthesis.cancel();
};

function handle(message) {
  if (!message.trim()) return;
  add("me", message);
  const r = replyTo(message);
  setTimeout(() => { add("him", r.text); speak(r.text); if (r.intent === "greeting") { wave = 1.6; hop = 1; } }, 350);
}
const input = document.getElementById("text");
document.getElementById("send").onclick = () => { handle(input.value); input.value = ""; };
input.addEventListener("keydown", e => { if (e.key === "Enter") { handle(input.value); input.value = ""; } });

/* ---------------- voice in (speech recognition) ---------------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const mic = document.getElementById("mic");
let rec = null, listening = false;
if (!SR) {
  mic.disabled = true; mic.style.opacity = .4;
  document.getElementById("note").textContent = "Voice input isn't supported in this browser. Type instead (Hammy still talks back).";
} else {
  rec = new SR(); rec.lang = "en-US"; rec.interimResults = false; rec.maxAlternatives = 1;
  rec.onresult = e => handle(e.results[0][0].transcript);
  rec.onend = () => { listening = false; mic.classList.remove("on"); setStatus(""); };
  rec.onerror = e => { document.getElementById("note").textContent =
      e.error === "not-allowed" ? "Microphone blocked. Allow it in the browser, or just type." : "Didn't catch that. Try again or type."; };
  const start = () => { if (listening) return; try { rec.start(); listening = true; mic.classList.add("on"); setStatus("Listening…"); } catch (_) {} };
  const stop = () => { if (listening) rec.stop(); };
  mic.addEventListener("mousedown", start); mic.addEventListener("touchstart", e => { e.preventDefault(); start(); });
  mic.addEventListener("mouseup", stop); mic.addEventListener("mouseleave", stop); mic.addEventListener("touchend", stop);
}
function setStatus(s) { document.getElementById("status").textContent = s; }

/* ---------------- the 3D boy (three.js, built from simple shapes) ---------------- */
// Hammy's look: a cute chibi boy (very big round head, big glossy brown eyes,
// fluffy brown hair with one curl on top, light grey hoodie with a little
// star patch). Original design made only from basic shapes. "Toon" shading
// and a thin dark outline make him look hand-drawn instead of plastic.
let wave = 0, hop = 0, happy = 0;
(function build() {
  if (!window.THREE) { setStatus("🐹 (3D needs internet)"); return; }
  const stage = document.getElementById("stage");
  const W = stage.clientWidth, H = stage.clientHeight;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(26, W / H, 0.1, 100);
  camera.position.set(0, 1.25, 7.2); camera.lookAt(0, 1.12, 0);
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
  renderer.setClearColor(0x000000, 0);
  renderer.setSize(W, H); renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  stage.prepend(renderer.domElement);
  scene.add(new THREE.AmbientLight(0xffffff, 0.35));
  const key = new THREE.DirectionalLight(0xffffff, 0.7); key.position.set(1.5, 3, 6); scene.add(key);

  // toon shading: 3 flat bands of light, like a cartoon
  const grad = new THREE.DataTexture(new Uint8Array([175, 175, 175, 215, 215, 215, 240, 240, 240, 255, 255, 255]), 4, 1, THREE.RGBFormat);
  grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
  const toon = (c) => new THREE.MeshToonMaterial({color: c, gradientMap: grad});
  const flat = (c, o) => new THREE.MeshBasicMaterial(Object.assign({color: c}, o || {}));
  const lineM = new THREE.MeshBasicMaterial({color: 0x3a2418, side: THREE.BackSide});
  const outline = (m, k = 1.06) => { const o = new THREE.Mesh(m.geometry, lineM); o.scale.setScalar(k); m.add(o); return m; };

  const skin = toon(0xf6c3a2), hairM = toon(0x7a4528), hoodie = toon(0xbfc3ce), hoodieDark = toon(0xa7acb9),
        jeans = toon(0x5d7fb8), shoeM = toon(0xff7a95), soleM = toon(0xffffff), starM = toon(0xffc93c);
  const S = (r, m, w = 40, h = 30) => new THREE.Mesh(new THREE.SphereGeometry(r, w, h), m);
  const C = (r1, r2, h, m) => new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, 32), m);
  const at = (o, x, y, z) => { o.position.set(x, y, z); return o; };

  const boy = new THREE.Group(); scene.add(boy);
  const body = new THREE.Group(); boy.add(body);           // squashes and stretches as he bounces

  // soft shadow on the ground
  const sh = new THREE.Mesh(new THREE.CircleGeometry(0.62, 40), flat(0x9b7fd6, {transparent: true, opacity: 0.18}));
  sh.rotation.x = -Math.PI / 2; sh.position.y = 0.005; scene.add(sh);

  // short legs and round sneakers
  for (const x of [-0.15, 0.15]) {
    body.add(outline(at(C(0.12, 0.12, 0.3, jeans), x, 0.27, 0), 1.08));
    const shoe = outline(at(S(0.15, shoeM), x, 0.1, 0.05)); shoe.scale.set(1, 0.62, 1.35); body.add(shoe);
    const sole = at(S(0.152, soleM), x, 0.06, 0.05); sole.scale.set(1.02, 0.28, 1.37); body.add(sole);
  }
  // round, soft hoodie
  const torso = outline(at(S(0.4, hoodie), 0, 0.66, 0), 1.045); torso.scale.set(1, 1.0, 0.86); body.add(torso);
  const hem = at(C(0.36, 0.36, 0.07, hoodieDark), 0, 0.37, 0); body.add(hem);
  const hood = outline(at(S(0.3, hoodieDark), 0, 0.98, -0.2)); hood.scale.set(1.25, 0.55, 0.75); body.add(hood);
  for (const x of [-0.07, 0.07]) {                              // hoodie strings
    body.add(at(C(0.013, 0.013, 0.22, soleM), x, 0.83, 0.33));
    body.add(at(S(0.024, soleM), x, 0.71, 0.345));
  }
  // a little yellow star patch (his own thing)
  const star = new THREE.Shape();
  for (let k = 0; k < 10; k++) { const r = k % 2 ? 0.035 : 0.08, a = Math.PI / 2 + k * Math.PI / 5;
    k ? star.lineTo(Math.cos(a) * r, Math.sin(a) * r) : star.moveTo(Math.cos(a) * r, Math.sin(a) * r); }
  const patch = at(new THREE.Mesh(new THREE.ShapeGeometry(star), starM), 0.19, 0.76, 0.345);
  patch.rotation.set(-0.1, 0.35, 0.15); body.add(patch);

  // stubby arms with round hands (pivot at the shoulder so he can wave)
  const arms = [];
  for (const side of [-1, 1]) {
    const pivot = at(new THREE.Group(), 0.34 * side, 0.86, 0); body.add(pivot);
    pivot.add(outline(at(C(0.09, 0.105, 0.34, hoodie), 0, -0.17, 0), 1.08));
    pivot.add(at(C(0.105, 0.105, 0.05, hoodieDark), 0, -0.34, 0));
    pivot.add(outline(at(S(0.095, skin), 0, -0.42, 0), 1.08));
    pivot.rotation.z = 0.35 * side; arms.push(pivot);
  }

  // BIG round head
  const head = at(new THREE.Group(), 0, 1.58, 0); body.add(head);
  const face = outline(S(0.7, skin, 56, 40), 1.025); face.scale.set(1.06, 0.95, 0.92); head.add(face);
  for (const x of [-0.72, 0.72]) { const ear = outline(at(S(0.12, skin), x, -0.06, 0)); ear.scale.set(0.5, 0.9, 0.7); head.add(ear); }

  // eyes: tall glossy brown ovals, drawn flat like a cartoon
  const eyes = [];
  for (const x of [-0.25, 0.25]) {
    const eye = at(new THREE.Group(), x, -0.08, 0.59); head.add(eye);
    const iris = S(0.17, flat(0x3d1f10)); iris.scale.set(0.78, 1.1, 0.3); eye.add(iris);
    const low = at(S(0.11, flat(0x8f5129)), 0, -0.07, 0.02); low.scale.set(0.85, 0.6, 0.3); eye.add(low);
    eye.add(at(S(0.06, flat(0xffffff)), 0.045, 0.065, 0.05));    // big shine
    eye.add(at(S(0.028, flat(0xffffff)), -0.05, -0.075, 0.05));  // small shine
    eye.rotation.y = x * 0.6;
    eyes.push(eye);
    // soft eyebrows (little arcs)
    const b = at(new THREE.Mesh(new THREE.TorusGeometry(0.07, 0.014, 6, 16, Math.PI * 0.7), flat(0x6b3a20)), x, 0.15, 0.62);
    b.rotation.z = Math.PI * 0.15; b.rotation.y = x * 0.5; head.add(b);
    // blushing cheeks
    const cheek = at(new THREE.Mesh(new THREE.CircleGeometry(0.085, 24), flat(0xff8fa3, {transparent: true, opacity: 0.55})),
                     x * 1.6, -0.27, 0.55);
    cheek.scale.set(1.3, 0.75, 1); cheek.rotation.y = x * 1.3; head.add(cheek);
  }
  head.add(at(S(0.035, toon(0xf5b99a)), 0, -0.15, 0.645));                                  // tiny nose
  // happy open mouth (a half circle) with a little tongue
  const mouth = at(new THREE.Group(), 0, -0.29, 0.615); head.add(mouth);
  mouth.add(new THREE.Mesh(new THREE.CircleGeometry(0.095, 24, Math.PI, Math.PI), flat(0x7a2430)));
  mouth.add(at(new THREE.Mesh(new THREE.CircleGeometry(0.05, 20, Math.PI, Math.PI), flat(0xff7d8c)), 0, -0.04, 0.002));
  mouth.scale.set(1, 0.55, 1);

  // fluffy hair: a cap, soft round clumps, a swoopy fringe and one curl on top
  const cap = outline(at(new THREE.Mesh(new THREE.SphereGeometry(0.75, 48, 32, 0, Math.PI * 2, 0, Math.PI * 0.55), hairM), 0, 0.06, -0.03), 1.02);
  cap.rotation.x = -0.28; cap.scale.set(1.05, 1, 0.98); head.add(cap);
  const back = outline(at(S(0.7, hairM), 0, 0.02, -0.12), 1.02); back.scale.set(1.06, 0.97, 0.88); head.add(back);
  const clumps = [  // x, y, z, size, tilt   (round clumps around the sides and fringe)
    [-0.66, -0.05, 0.12, 0.2, 0.5], [0.66, -0.05, 0.12, 0.2, -0.5], [-0.6, 0.22, 0.28, 0.22, 0.6], [0.6, 0.22, 0.28, 0.22, -0.6],
    [-0.46, 0.34, 0.47, 0.21, 0.9], [-0.22, 0.4, 0.56, 0.22, 1.1], [0.04, 0.4, 0.58, 0.22, 1.2], [0.29, 0.36, 0.55, 0.21, 1.25],
    [0.5, 0.27, 0.47, 0.19, 1.3],
    [-0.32, 0.27, 0.6, 0.14, 1.0], [-0.08, 0.3, 0.64, 0.15, 1.2], [0.17, 0.28, 0.63, 0.14, 1.3],   // soft fringe
  ];
  for (const [x, y, z, r, tilt] of clumps) {
    const c = outline(at(S(r, hairM, 24, 18), x, y, z), 1.06); c.scale.set(1, 0.62, 0.62); c.rotation.z = -tilt; head.add(c);
  }
  const curl = outline(at(new THREE.Mesh(new THREE.TorusGeometry(0.11, 0.035, 10, 24, Math.PI * 1.4), hairM), 0.05, 0.8, 0.05), 1.1);
  curl.rotation.set(0, 0.4, 0.6); head.add(curl);

  // tap Hammy and he hops
  renderer.domElement.addEventListener("click", () => { hop = 1; happy = 1.2; setStatus(""); });

  let mouseX = 0, mouseY = 0;
  document.addEventListener("mousemove", e => { mouseX = e.clientX / innerWidth - 0.5; mouseY = e.clientY / innerHeight - 0.5; });
  let nextBlink = 2, t0 = performance.now(), last = t0;
  wave = 2.0;                                       // wave hello when he appears
  function tick(now) {
    const t = (now - t0) / 1000, dt = Math.min(0.05, (now - last) / 1000); last = now;
    // gentle bounce with squash and stretch
    const b = Math.sin(t * 3.2);
    body.scale.set(1 + b * 0.015, 1 - b * 0.02, 1 + b * 0.015);
    // hop: a happy jump
    let y = 0;
    if (hop > 0) { hop = Math.max(0, hop - dt * 1.6); y = Math.sin((1 - hop) * Math.PI) * 0.35; }
    boy.position.y = y; sh.scale.setScalar(1 - y * 0.8);
    boy.rotation.y = Math.sin(t * 0.7) * 0.08;
    head.rotation.y += ((mouseX * 0.8) - head.rotation.y) * 0.08;   // looks towards your mouse
    head.rotation.x += ((mouseY * 0.3) - head.rotation.x) * 0.08;
    head.rotation.z = Math.sin(t * 1.1) * 0.05 + (happy > 0 ? Math.sin(t * 9) * 0.06 : 0);
    happy = Math.max(0, happy - dt);
    curl.rotation.z = 0.6 + Math.sin(t * 4) * 0.12;                 // the curl wiggles
    const blinking = t > nextBlink && t < nextBlink + 0.12;
    for (const e of eyes) e.scale.y += ((blinking ? 0.1 : 1) - e.scale.y) * 0.6;
    if (t > nextBlink + 0.12) nextBlink = t + 1.8 + Math.random() * 3;
    // talking: the mouth opens and closes
    const open = talking ? 0.45 + Math.abs(Math.sin(t * 13)) * 0.75 : (happy > 0 ? 1 : 0.55);
    mouth.scale.y += (open - mouth.scale.y) * 0.35;
    if (wave > 0) { wave -= dt; arms[1].rotation.z = -2.4 + Math.sin(t * 11) * 0.4; }
    else arms[1].rotation.z += (0.35 - arms[1].rotation.z) * 0.1;
    arms[0].rotation.z = -0.35 - (hop > 0 ? 0.9 * Math.sin((1 - hop) * Math.PI) : 0);
    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();

/* ---------------- messages from the map ("Walk me home") ---------------- */
try {
  const ch = new BroadcastChannel("saferoute-hammy");
  ch.onmessage = (e) => {
    const m = e.data || {}; if (!m.text) return;
    add("him", m.text); speak(m.text);
    if (m.mood === "cheer") { hop = 1; happy = 1.5; wave = 1.2; }
  };
} catch (_) {}

add("him", GREETING);
</script></body></html>
"""


def hammy_widget(height=610):
    """Show Hammy 2.0 in the Streamlit page."""
    intents = [[name, keywords, answers] for name, keywords, answers in INTENTS]
    html = (HTML.replace("__INTENTS__", json.dumps(intents))
                .replace("__FALLBACK__", json.dumps(FALLBACK))
                .replace("__GREETING__", json.dumps(GREETING)))
    components.html(html, height=height)
