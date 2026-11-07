"""
Safe Route Lahore - Hammy 2.0: a 3D little brother you can talk to
==================================================================

WHAT THIS FILE DOES:
  Builds ONE web widget (HTML + JavaScript) that contains:
    1. A 3D cartoon boy, Hammy, drawn with three.js. He is made only from
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
  .wrap { display:flex; flex-direction:column; gap:10px; background:var(--card); border-radius:14px; padding:10px; border:1px solid #8882; }
  #stage { width:100%; height:240px; flex:none; overflow:hidden; border-radius:12px; background:radial-gradient(circle at 50% 40%, #dfe9ff, #b9c9ef); position:relative; }
  #status { position:absolute; bottom:6px; left:0; right:0; text-align:center; font-size:12px; color:#334; }
  .chat { flex:1; display:flex; flex-direction:column; min-width:0; }
  #log { flex:1; overflow-y:auto; height:200px; padding:4px; }
  .msg { padding:7px 10px; border-radius:12px; margin:4px 0; max-width:92%; line-height:1.35; font-size:14px; }
  .him { background:var(--him); }
  .me { background:var(--me); margin-left:auto; }
  .row { display:flex; gap:6px; margin-top:6px; }
  input { flex:1; padding:9px 10px; border-radius:10px; border:1px solid #8885; background:transparent; color:var(--ink); font-size:14px; }
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
  if (!window.THREE) { setStatus("🐹 (3D needs internet)"); return; }
  const stage = document.getElementById("stage");
  const W = stage.clientWidth, H = stage.clientHeight;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, W / H, 0.1, 100);
  camera.position.set(0, 1.3, 4.6); camera.lookAt(0, 1.05, 0);
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
  renderer.setSize(W, H); renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  stage.prepend(renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8899bb, 0.9));
  const sun = new THREE.DirectionalLight(0xffffff, 0.7); sun.position.set(2, 4, 5); scene.add(sun);

  const mat = c => new THREE.MeshStandardMaterial({color: c, roughness: 0.6});
  const skin = mat(0xe0ac80), hair = mat(0x2b1d14), shirt = mat(0x1f5fd1), pants = mat(0x2d3748),
        white = mat(0xffffff), dark = mat(0x1a1a1a), mouthM = mat(0x8a2d2d), shoe = mat(0xf0f0f0);
  const S = (r, m) => new THREE.Mesh(new THREE.SphereGeometry(r, 32, 24), m);
  const C = (r1, r2, h, m) => new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, 24), m);

  const boy = new THREE.Group(); scene.add(boy);
  // body
  const torso = C(0.42, 0.5, 1.0, shirt); torso.position.y = 0.55; boy.add(torso);
  const hips = C(0.5, 0.48, 0.25, pants); hips.position.y = -0.05; boy.add(hips);
  for (const x of [-0.2, 0.2]) {
    const leg = C(0.16, 0.15, 0.7, pants); leg.position.set(x, -0.5, 0); boy.add(leg);
    const foot = S(0.18, shoe); foot.scale.set(1, 0.6, 1.5); foot.position.set(x, -0.88, 0.08); boy.add(foot);
  }
  const neck = C(0.13, 0.15, 0.2, skin); neck.position.y = 1.12; boy.add(neck);
  // arms (pivot at shoulder so they can wave)
  const arms = [];
  for (const side of [-1, 1]) {
    const pivot = new THREE.Group(); pivot.position.set(0.5 * side, 0.98, 0); boy.add(pivot);
    const arm = C(0.11, 0.1, 0.75, shirt); arm.position.y = -0.36; pivot.add(arm);
    const hand = S(0.12, skin); hand.position.y = -0.78; pivot.add(hand);
    pivot.rotation.z = 0.18 * side; arms.push(pivot);
  }
  // head
  const head = new THREE.Group(); head.position.y = 1.62; boy.add(head);
  const skull = S(0.55, skin); skull.scale.set(1, 1.05, 0.95); head.add(skull);
  const hairCap = new THREE.Mesh(new THREE.SphereGeometry(0.58, 32, 24, 0, Math.PI * 2, 0, Math.PI * 0.5), hair);
  hairCap.position.y = 0.08; hairCap.rotation.x = -0.25; head.add(hairCap);
  const fringe = S(0.22, hair); fringe.scale.set(1.6, 0.55, 0.8); fringe.position.set(0.12, 0.42, 0.38); head.add(fringe);
  for (const x of [-0.56, 0.56]) { const ear = S(0.12, skin); ear.scale.set(0.6, 1, 0.8); ear.position.set(x, 0, 0); head.add(ear); }
  const eyes = [];
  for (const x of [-0.2, 0.2]) {
    const eye = S(0.11, white); eye.scale.set(1, 1.15, 0.6); eye.position.set(x, 0.05, 0.47); head.add(eye);
    const pupil = S(0.065, dark); pupil.position.set(x, 0.04, 0.53); head.add(pupil);
    const shine = S(0.02, white); shine.position.set(x + 0.025, 0.07, 0.585); head.add(shine);
    const brow = C(0.02, 0.02, 0.18, hair); brow.rotation.z = Math.PI / 2 + (x < 0 ? 0.15 : -0.15);
    brow.position.set(x, 0.24, 0.5); head.add(brow);
    eyes.push(eye, pupil, shine);
  }
  const nose = S(0.06, skin); nose.position.set(0, -0.06, 0.54); head.add(nose);
  for (const x of [-0.32, 0.32]) { const cheek = S(0.08, mat(0xf0a090)); cheek.scale.set(1, 0.6, 0.3); cheek.position.set(x, -0.12, 0.45); head.add(cheek); }
  const mouth = S(0.1, mouthM); mouth.scale.set(1.3, 0.35, 0.4); mouth.position.set(0, -0.25, 0.49); head.add(mouth);

  let mouseX = 0, mouseY = 0;
  document.addEventListener("mousemove", e => { mouseX = e.clientX / innerWidth - 0.5; mouseY = e.clientY / innerHeight - 0.5; });
  let nextBlink = 2, t0 = performance.now();
  wave = 2.0;                                       // wave hello when he appears
  function tick() {
    const t = (performance.now() - t0) / 1000;
    boy.position.y = Math.sin(t * 2) * 0.03;        // breathing
    head.rotation.y += ((mouseX * 0.8) - head.rotation.y) * 0.08;   // looks towards your mouse
    head.rotation.x += ((mouseY * 0.4) - head.rotation.x) * 0.08;
    // blink
    const blinking = t > nextBlink && t < nextBlink + 0.12;
    for (const e of eyes) e.scale.y = blinking ? 0.1 : (e === eyes[0] || e === eyes[3] ? 1.15 : 1);
    if (t > nextBlink + 0.12) nextBlink = t + 2 + Math.random() * 3;
    // talking: open and close the mouth
    const open = talking ? 0.35 + Math.abs(Math.sin(t * 14)) * 0.9 : 0.35;
    mouth.scale.y += (open - mouth.scale.y) * 0.4;
    // waving the right arm
    if (wave > 0) { wave -= 1 / 60; arms[1].rotation.z = -2.4 + Math.sin(t * 10) * 0.35; }
    else arms[1].rotation.z += (0.18 - arms[1].rotation.z) * 0.1;
    arms[0].rotation.x = Math.sin(t * 2) * 0.05;
    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  tick();
})();

add("him", GREETING);
</script></body></html>
"""


def hammy_widget(height=560):
    """Show Hammy 2.0 in the Streamlit page."""
    intents = [[name, keywords, answers] for name, keywords, answers in INTENTS]
    html = (HTML.replace("__INTENTS__", json.dumps(intents))
                .replace("__FALLBACK__", json.dumps(FALLBACK))
                .replace("__GREETING__", json.dumps(GREETING)))
    components.html(html, height=height)
