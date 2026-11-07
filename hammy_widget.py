"""
Safe Route Lahore - Hammy 2.0: a 3D little brother you can talk to
==================================================================

WHAT THIS FILE DOES:
  Builds ONE web widget (HTML + JavaScript) that contains:
    1. A 3D cartoon boy, Hammy (big head, big brown eyes, messy brown hair,
       light grey hoodie), drawn with three.js. Transparent background, so he
       stands in front of the page. He is made only from
       simple shapes (spheres, cylinders), so there are no borrowed models
       or copyright issues. He breathes, blinks, waves hello, and his
       mouth moves while he talks.
    2. Text chat: type a message and press Enter.
    3. Voice chat:
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
<style>
  :root { --bg:#f6f7fb; --card:#ffffff; --ink:#1f2430; --muted:#6b7280; --me:#e8f0ff; --him:#fff3df; --accent:#1f5fd1; }
  @media (prefers-color-scheme: dark) { :root { --bg:#14161c; --card:#1d2029; --ink:#e8eaf0; --muted:#9aa3b2; --me:#22324f; --him:#3a2f1c; } }
  * { box-sizing:border-box; font-family: "Source Sans Pro", system-ui, sans-serif; }
  body { margin:0; background:transparent; color:var(--ink); }
  .wrap { display:flex; flex-direction:column; gap:10px; }
  .chat { background:var(--card); border-radius:14px; padding:10px; border:1px solid #8882; }
  #stage { width:100%; height:340px; flex:none; overflow:hidden; position:relative; }
  #status { position:absolute; bottom:2px; left:0; right:0; text-align:center; font-size:12px; color:var(--muted); }
  .chat { flex:1; display:flex; flex-direction:column; min-width:0; }
  #log { flex:1; overflow-y:auto; height:200px; padding:4px; }
  .msg { padding:7px 10px; border-radius:12px; margin:4px 0; max-width:92%; line-height:1.35; font-size:14px; }
  .him { background:var(--him); }
  .me { background:var(--me); margin-left:auto; }
  .row { display:flex; gap:6px; margin-top:6px; }
  input { flex:1; min-width:0; padding:9px 10px; border-radius:10px; border:1px solid #8885; background:transparent; color:var(--ink); font-size:14px; }
  button { border:none; border-radius:10px; padding:0 12px; cursor:pointer; font-size:18px; background:var(--accent); color:white; }
  button.mic.on { background:#d63b3b; }
  button.ghost { background:#8882; color:var(--ink); font-size:14px; }
  .note { font-size:11px; color:var(--muted); margin-top:4px; }
</style></head>
<body>
<div class="wrap">
  <div id="stage"><div id="status">Hammy 🐹</div></div>
  <div class="chat">
    <div id="log"></div>
    <div class="row">
      <input id="text" placeholder="Type to Hammy… (English or Roman Urdu)">
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
  u.onend = u.onerror = () => { talking = false; setStatus("Hammy 🐹"); };
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
  setTimeout(() => { add("him", r.text); speak(r.text); if (r.intent === "greeting") wave = 1.6; }, 350);
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
  rec.onend = () => { listening = false; mic.classList.remove("on"); setStatus("Hammy 🐹"); };
  rec.onerror = e => { document.getElementById("note").textContent =
      e.error === "not-allowed" ? "Microphone blocked. Allow it in the browser, or just type." : "Didn't catch that. Try again or type."; };
  const start = () => { if (listening) return; try { rec.start(); listening = true; mic.classList.add("on"); setStatus("Listening…"); } catch (_) {} };
  const stop = () => { if (listening) rec.stop(); };
  mic.addEventListener("mousedown", start); mic.addEventListener("touchstart", e => { e.preventDefault(); start(); });
  mic.addEventListener("mouseup", stop); mic.addEventListener("mouseleave", stop); mic.addEventListener("touchend", stop);
}
function setStatus(s) { document.getElementById("status").textContent = s; }

/* ---------------- the 3D boy (three.js, built from simple shapes) ---------------- */
let wave = 0;
(function build() {
  // Hammy's look: a cute chibi boy (big head, big brown eyes, messy brown
  // hair, light grey hoodie). Original design, made only from basic shapes.
  if (!window.THREE) { setStatus("🐹 (3D needs internet)"); return; }
  const stage = document.getElementById("stage");
  const W = stage.clientWidth, H = stage.clientHeight;
  const scene = new THREE.Scene();                  // no background: he stands in front of the page
  const camera = new THREE.PerspectiveCamera(28, W / H, 0.1, 100);
  camera.position.set(0, 1.45, 6.4); camera.lookAt(0, 1.3, 0);
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
  renderer.setClearColor(0x000000, 0);
  renderer.setSize(W, H); renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  stage.prepend(renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xfff6ee, 0x9a8f99, 0.85));
  const key = new THREE.DirectionalLight(0xffffff, 0.6); key.position.set(2, 4, 5); scene.add(key);
  const rim = new THREE.DirectionalLight(0xffd9c2, 0.45); rim.position.set(-3, 2, -3); scene.add(rim);

  const mat = (c, r = 0.55) => new THREE.MeshStandardMaterial({color: c, roughness: r});
  const skin = mat(0xf2c4a6), hairM = mat(0x7b4a2c, 0.7), hoodie = mat(0xb4b7bf, 0.85),
        hoodieDark = mat(0x9fa3ac, 0.85), jeans = mat(0x3c4a63), white = mat(0xffffff, 0.3),
        iris = mat(0x6b3d1f, 0.3), dark = mat(0x1b120c, 0.3), brow = mat(0x5c3620),
        cheekM = mat(0xf29a8f), mouthM = mat(0x8a3434), sole = mat(0x555555);
  const S = (r, m, w = 32, h = 24) => new THREE.Mesh(new THREE.SphereGeometry(r, w, h), m);
  const C = (r1, r2, h, m) => new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, 28), m);
  const at = (o, x, y, z) => { o.position.set(x, y, z); return o; };

  const boy = new THREE.Group(); scene.add(boy);
  // legs and shoes (feet stand on y = 0)
  for (const x of [-0.17, 0.17]) {
    boy.add(at(C(0.14, 0.13, 0.5, jeans), x, 0.35, 0));
    const shoe = at(S(0.16, white), x, 0.09, 0.06); shoe.scale.set(1, 0.55, 1.45); boy.add(shoe);
    const s2 = at(S(0.16, sole), x, 0.05, 0.06); s2.scale.set(1.02, 0.3, 1.47); boy.add(s2);
  }
  // hoodie body
  boy.add(at(C(0.36, 0.42, 0.62, hoodie), 0, 0.88, 0));
  const shoulders = at(S(0.37, hoodie), 0, 1.15, 0); shoulders.scale.set(1.05, 0.45, 0.85); boy.add(shoulders);
  const band = at(C(0.43, 0.43, 0.08, hoodieDark), 0, 0.6, 0); boy.add(band);
  const pocket = at(new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.2, 0.05), hoodieDark), 0, 0.76, 0.39);
  pocket.rotation.x = -0.1; boy.add(pocket);
  const hood = at(S(0.33, hoodieDark), 0, 1.22, -0.22); hood.scale.set(1.2, 0.6, 0.7); boy.add(hood);
  for (const x of [-0.08, 0.08]) {               // hoodie strings
    const str = at(C(0.014, 0.014, 0.28, white), x, 1.02, 0.36); str.rotation.x = -0.15; boy.add(str);
    boy.add(at(S(0.025, white), x, 0.88, 0.38));
  }
  // arms (pivot at the shoulder so he can wave)
  const arms = [];
  for (const side of [-1, 1]) {
    const pivot = at(new THREE.Group(), 0.4 * side, 1.12, 0); boy.add(pivot);
    pivot.add(at(C(0.11, 0.12, 0.5, hoodie), 0, -0.25, 0));
    pivot.add(at(C(0.12, 0.12, 0.07, hoodieDark), 0, -0.5, 0));
    pivot.add(at(S(0.1, skin), 0, -0.6, 0));
    pivot.rotation.z = 0.22 * side; arms.push(pivot);
  }
  // head: big and round (chibi style)
  const head = at(new THREE.Group(), 0, 1.85, 0); boy.add(head);
  boy.add(at(C(0.1, 0.12, 0.2, skin), 0, 1.25, 0));
  const face = S(0.62, skin, 48, 36); face.scale.set(1, 0.95, 0.92); head.add(face);
  for (const x of [-0.6, 0.6]) { const ear = at(S(0.12, skin), x, -0.05, 0); ear.scale.set(0.55, 1, 0.8); head.add(ear); }
  // big brown eyes, each in its own group so it can blink
  const eyes = [];
  for (const x of [-0.24, 0.24]) {
    const eye = at(new THREE.Group(), x, -0.03, 0.47); head.add(eye);
    const w = S(0.155, white); w.scale.set(0.92, 1.08, 0.5); eye.add(w);
    const ir = at(S(0.12, iris), 0, -0.01, 0.045); ir.scale.set(0.95, 1.05, 0.45); eye.add(ir);
    const pu = at(S(0.065, dark), 0, -0.01, 0.075); pu.scale.set(1, 1, 0.4); eye.add(pu);
    eye.add(at(S(0.035, white), 0.04, 0.045, 0.1));
    eye.add(at(S(0.018, white), -0.04, -0.05, 0.1));
    eyes.push(eye);
    const b = at(new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.15, 8), brow), x * 1.02, 0.2, 0.52);
    b.rotation.z = Math.PI / 2 + (x < 0 ? -0.12 : 0.12); head.add(b);
    const cheek = at(S(0.085, cheekM), x * 1.45, -0.2, 0.45); cheek.scale.set(1, 0.6, 0.3);
    cheek.material = cheekM.clone(); cheek.material.transparent = true; cheek.material.opacity = 0.7; head.add(cheek);
  }
  const nose = at(S(0.045, skin), 0, -0.14, 0.565); head.add(nose);
  const smile = at(new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.017, 8, 20, Math.PI), mouthM), 0, -0.24, 0.535);
  smile.rotation.z = Math.PI; head.add(smile);
  const mouth = at(S(0.07, mouthM), 0, -0.27, 0.53); mouth.scale.set(1.1, 0.05, 0.4); head.add(mouth);
  // messy brown hair: a cap plus lots of soft tufts, fringe swept to one side
  const cap = at(new THREE.Mesh(new THREE.SphereGeometry(0.66, 40, 30, 0, Math.PI * 2, 0, Math.PI * 0.58), hairM), 0, 0.04, -0.03);
  cap.rotation.x = -0.32; head.add(cap);
  const back = at(S(0.6, hairM), 0, 0.02, -0.12); back.scale.set(1.02, 0.95, 0.85); head.add(back);
  // soft tufts placed all over the top and back of the head, each pointing outwards
  const rnd = (i) => (Math.sin(i * 12.9898) * 43758.5453) % 1;   // fixed "random", same every time
  let i = 0;
  for (const [phi, count] of [[0.45, 6], [0.85, 11], [1.2, 12], [1.6, 10]]) {
    for (let k = 0; k < count; k++, i++) {
      const theta = (k / count) * Math.PI * 2 + phi;              // angle around the head (0 = front)
      const front = Math.cos(theta);                               // 1 = facing us
      if (phi >= 0.85 && front > -0.05 && Math.abs(Math.sin(theta)) < 0.75) continue;  // keep the face clear
      if (phi >= 1.2 && front > -0.3) continue;
      const dir = new THREE.Vector3(Math.sin(phi) * Math.sin(theta), Math.cos(phi), Math.sin(phi) * Math.cos(theta));
      const size = 0.17 + Math.abs(rnd(i)) * 0.06;
      const t = new THREE.Mesh(new THREE.ConeGeometry(size, size * 1.5, 12), hairM);
      t.position.copy(dir.clone().multiplyScalar(0.57)); t.position.y += 0.06;
      t.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().add(new THREE.Vector3(0.25, -0.15, 0.45)).normalize());
      t.scale.set(1, 1, 0.6); head.add(t);
    }
  }
  // fringe: soft locks swept to one side over the forehead
  for (const [x, y, rz, len] of [[-0.3, 0.33, -0.9, 0.34], [-0.1, 0.36, -1.05, 0.38], [0.12, 0.35, -1.15, 0.36], [0.33, 0.3, -1.25, 0.3]]) {
    const f = new THREE.Mesh(new THREE.ConeGeometry(0.1, len, 12), hairM);
    f.position.set(x, y, 0.5); f.rotation.set(0.5, 0, rz + Math.PI); f.scale.set(1, 1, 0.5); head.add(f);
  }

  let mouseX = 0, mouseY = 0;
  document.addEventListener("mousemove", e => { mouseX = e.clientX / innerWidth - 0.5; mouseY = e.clientY / innerHeight - 0.5; });
  let nextBlink = 2, t0 = performance.now();
  wave = 2.0;                                       // wave hello when he appears
  function tick() {
    const t = (performance.now() - t0) / 1000;
    boy.position.y = Math.sin(t * 2) * 0.02;        // breathing
    boy.rotation.y = Math.sin(t * 0.6) * 0.06;      // gentle sway
    head.rotation.y += ((mouseX * 0.7) - head.rotation.y) * 0.08;   // looks towards your mouse
    head.rotation.x += ((mouseY * 0.35) - head.rotation.x) * 0.08;
    head.rotation.z = Math.sin(t * 1.3) * 0.03;
    const blinking = t > nextBlink && t < nextBlink + 0.13;
    for (const e of eyes) e.scale.y = blinking ? 0.08 : 1;
    if (t > nextBlink + 0.13) nextBlink = t + 2 + Math.random() * 3;
    // talking: open and close the mouth (the smile hides while the mouth is open)
    const open = talking ? 0.25 + Math.abs(Math.sin(t * 14)) * 0.75 : 0.05;
    mouth.scale.y += (open - mouth.scale.y) * 0.4;
    smile.visible = mouth.scale.y < 0.2;
    if (wave > 0) { wave -= 1 / 60; arms[1].rotation.z = -2.5 + Math.sin(t * 10) * 0.35; }
    else arms[1].rotation.z += (0.22 - arms[1].rotation.z) * 0.1;
    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  tick();
})();

add("him", GREETING);
</script></body></html>
"""


def hammy_widget(height=740):
    """Show Hammy 2.0 in the Streamlit page."""
    intents = [[name, keywords, answers] for name, keywords, answers in INTENTS]
    html = (HTML.replace("__INTENTS__", json.dumps(intents))
                .replace("__FALLBACK__", json.dumps(FALLBACK))
                .replace("__GREETING__", json.dumps(GREETING)))
    components.html(html, height=height)
