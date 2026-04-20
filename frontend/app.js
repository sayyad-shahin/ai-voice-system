const API = "https://ai-voice-system-j313.onrender.com";

/* ─── SESSION ────────────────────────────────────────────────
   Uses sessionStorage — clears when browser tab is closed.
   Survives F5 page refresh within same tab.
─────────────────────────────────────────────────────────────*/
const S = {
  set(username, name, voice) {
    sessionStorage.setItem("va_u",  username);
    sessionStorage.setItem("va_n",  name || username);
    sessionStorage.setItem("va_v",  voice || "EXAVITQu4vr4xnSDxMaL");
    sessionStorage.setItem("va_ok", "1");
  },
  clear() {
    ["va_u","va_n","va_v","va_ok"].forEach(k => sessionStorage.removeItem(k));
  },
  get username() { return sessionStorage.getItem("va_u") || ""; },
  get name()     { return sessionStorage.getItem("va_n") || ""; },
  get voice()    { return sessionStorage.getItem("va_v") || "EXAVITQu4vr4xnSDxMaL"; },
  get ok()       { return sessionStorage.getItem("va_ok") === "1"; }
};

/* ─── PAGE NAV ───────────────────────────────────────────────
   Auth guard: appPage is blocked unless logged in.
─────────────────────────────────────────────────────────────*/
function showPage(id) {
  if (id === "appPage" && !S.ok) {
    toast("Please sign in to continue.");
    id = "loginPage";
  }
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

/* ─── TOAST ──────────────────────────────────────────────────*/
let _tt;
function toast(msg, ms = 3400) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  clearTimeout(_tt);
  _tt = setTimeout(() => el.classList.add("hidden"), ms);
}

/* ─── INLINE MESSAGES ────────────────────────────────────────*/
function showMsg(id, text, type) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className   = "msg show " + type;
}
function clearMsg(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = "";
  el.className   = "msg";
}

/* ─── ORB / STATUS ───────────────────────────────────────────*/
function setStatus(state, label) {
  const orb   = document.getElementById("orb");
  const rings = document.getElementById("rings");
  const tag   = document.getElementById("statusTag");
  const icon  = document.getElementById("orbIcon");

  orb.className   = "orb "        + state;
  rings.className = "rings-wrap " + state;
  tag.className   = "status-tag " + state;
  tag.textContent = label;

  const icons = { listening:"", processing:"⏳", speaking:"", ready:"" };
  icon.textContent = icons[state] || "";
}

/* ─── PASSWORD TOGGLE ────────────────────────────────────────*/
function togglePw(id, btn) {
  const inp = document.getElementById(id);
  if (inp.type === "password") { inp.type = "text";     btn.textContent = "🙈"; }
  else                         { inp.type = "password"; btn.textContent = "👁"; }
}

/* ─── LANGUAGE SELECTOR ──────────────────────────────────────*/
let _langOpen = false;

function toggleLangMenu() {
  const menu = document.getElementById("langMenu");
  const btn  = document.getElementById("langBtn");
  _langOpen  = !_langOpen;
  menu.classList.toggle("hidden", !_langOpen);
  btn.classList.toggle("open",    _langOpen);
}

function selectLang(code, label, speechCode) {
  document.getElementById("selLang").value       = code;
  document.getElementById("selSpeech").value     = speechCode;
  document.getElementById("langLabel").textContent = label;
  document.querySelectorAll(".lang-opt").forEach(el =>
    el.classList.toggle("active", el.getAttribute("data-label") === label)
  );
  if (_langOpen) toggleLangMenu();
  toast("Language: " + label.replace(/^\S+\s*/, ""));
}

document.addEventListener("click", e => {
  const wrap = document.querySelector(".lang-wrap");
  if (wrap && !wrap.contains(e.target) && _langOpen) toggleLangMenu();
});

/* ─── LOAD VOICES ────────────────────────────────────────────*/
async function loadVoices() {
  const sel = document.getElementById("voiceSelect");
  try {
    const res  = await fetch(API + "/voices");
    const data = await res.json();
    sel.innerHTML = "";
    const list = (data.success && data.voices?.length) ? data.voices : [
      { id: "EXAVITQu4vr4xnSDxMaL", name: "Rachel" },
      { id: "21m00Tcm4TlvDq8ikWAM", name: "Bella"  },
      { id: "TxGEqnHWrfWFTfGW9XjX", name: "Josh"   },
      { id: "pNInz6obpgDQGcFmaJgB", name: "Adam"   },
    ];
    list.forEach(v => {
      const o = document.createElement("option");
      o.value = v.id; o.textContent = v.name;
      sel.appendChild(o);
    });
  } catch {
    sel.innerHTML = '<option value="EXAVITQu4vr4xnSDxMaL">Rachel (default)</option>';
  }
}

/* ─── LOGIN ──────────────────────────────────────────────────*/
async function login() {
  const username = document.getElementById("lUser").value.trim();
  const password = document.getElementById("lPass").value;
  const voice    = document.getElementById("voiceSelect").value;
  const btn      = document.getElementById("lBtn");

  clearMsg("lMsg");
  if (!username || !password) {
    showMsg("lMsg", "Please fill in all fields.", "err"); return;
  }

  btn.disabled = true; btn.textContent = "Signing in…";
  showMsg("lMsg", "Verifying your credentials…", "info");

  try {
    const res  = await fetch(API + "/auth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (data.success) {
      S.set(username, data.name, voice);
      showMsg("lMsg", "✓ Welcome back, " + (data.name || username) + "!", "ok");
      setTimeout(() => {
        btn.disabled = false; btn.textContent = "Sign In";
        showPage("appPage");
      }, 750);
    } else {
      showMsg("lMsg", data.error || "Login failed.", "err");
      btn.disabled = false; btn.textContent = "Sign In";
    }
  } catch {
    showMsg("lMsg", "Connection error. Check your internet.", "err");
    btn.disabled = false; btn.textContent = "Sign In";
  }
}

/* ─── REGISTER STEP 1 — send OTP ────────────────────────────*/
async function registerRequest() {
  const name     = document.getElementById("rName").value.trim();
  const email    = document.getElementById("rEmail").value.trim();
  const username = document.getElementById("rUser").value.trim();
  const password = document.getElementById("rPass").value;
  const confirm  = document.getElementById("rConf").value;
  const btn      = document.getElementById("rBtn1");

  clearMsg("rMsg1");

  if (!name || !email || !username || !password || !confirm) {
    showMsg("rMsg1", "Please fill in all fields.", "err"); return;
  }
  if (!email.includes("@") || !email.includes(".")) {
    showMsg("rMsg1", "Please enter a valid email address.", "err"); return;
  }
  if (password.length < 6) {
    showMsg("rMsg1", "Password must be at least 6 characters.", "err"); return;
  }
  if (password !== confirm) {
    showMsg("rMsg1", "Passwords do not match.", "err"); return;
  }

  btn.disabled = true; btn.textContent = "Sending code…";
  showMsg("rMsg1", "Sending verification code to your email…", "info");

  try {
    const res  = await fetch(API + "/register/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, username, password })
    });
    const data = await res.json();

    if (data.success) {
      // Move to Step 2
      document.getElementById("regStep1").style.display = "none";
      document.getElementById("regStep2").style.display = "block";
      showMsg("rMsg2", "✓ Code sent! Check your inbox (and spam folder).", "ok");
    } else {
      showMsg("rMsg1", data.error || "Failed to send code.", "err");
    }
  } catch {
    showMsg("rMsg1", "Connection error. Please try again.", "err");
  } finally {
    btn.disabled = false; btn.textContent = "Send Verification Code";
  }
}

/* ─── REGISTER STEP 2 — verify OTP ──────────────────────────*/
async function registerVerify() {
  const email = document.getElementById("rEmail").value.trim();
  const code  = document.getElementById("regOtp").value.trim().toUpperCase();
  const btn   = document.getElementById("rBtn2");

  clearMsg("rMsg2");

  if (!code || code.length < 4) {
    showMsg("rMsg2", "Please enter the verification code.", "err"); return;
  }

  btn.disabled = true; btn.textContent = "Verifying…";
  showMsg("rMsg2", "Verifying your code…", "info");

  try {
    const res  = await fetch(API + "/register/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code })
    });
    const data = await res.json();

    if (data.success) {
      showMsg("rMsg2", "✓ Account created! Redirecting to sign in…", "ok");
      setTimeout(() => {
        // Reset register form fully
        document.getElementById("regStep1").style.display = "block";
        document.getElementById("regStep2").style.display = "none";
        ["rName","rEmail","rUser","rPass","rConf","regOtp"].forEach(id => {
          const el = document.getElementById(id);
          if (el) el.value = "";
        });
        clearMsg("rMsg1"); clearMsg("rMsg2");
        btn.disabled = false; btn.textContent = "Verify & Create Account";
        showPage("loginPage");
      }, 1500);
    } else {
      showMsg("rMsg2", data.error || "Verification failed.", "err");
      btn.disabled = false; btn.textContent = "Verify & Create Account";
    }
  } catch {
    showMsg("rMsg2", "Connection error. Please try again.", "err");
    btn.disabled = false; btn.textContent = "Verify & Create Account";
  }
}

/* ─── REGISTER — RESEND OTP ──────────────────────────────────*/
async function resendOtp() {
  const name     = document.getElementById("rName").value.trim();
  const email    = document.getElementById("rEmail").value.trim();
  const username = document.getElementById("rUser").value.trim();
  const password = document.getElementById("rPass").value;

  showMsg("rMsg2", "Resending code…", "info");
  try {
    const res  = await fetch(API + "/register/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, username, password })
    });
    const data = await res.json();
    if (data.success) {
      showMsg("rMsg2", "✓ New code sent! Check your inbox.", "ok");
    } else {
      showMsg("rMsg2", data.error || "Failed to resend.", "err");
    }
  } catch {
    showMsg("rMsg2", "Connection error.", "err");
  }
}

/* ─── FORGOT PASSWORD — SEND CODE ────────────────────────────*/
async function sendResetCode() {
  const email = document.getElementById("fEmail").value.trim();
  clearMsg("fMsg1");

  if (!email || !email.includes("@")) {
    showMsg("fMsg1", "Please enter a valid email address.", "err"); return;
  }

  showMsg("fMsg1", "Sending reset code to your email…", "info");

  try {
    const res  = await fetch(API + "/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    const data = await res.json();

    if (data.success) {
      document.getElementById("fStep1").style.display = "none";
      document.getElementById("fStep2").style.display = "block";
      showMsg("fMsg2", "✓ Code sent! Check your inbox (and spam folder).", "ok");
    } else {
      showMsg("fMsg1", data.error || "Email not found.", "err");
    }
  } catch {
    showMsg("fMsg1", "Connection error. Please try again.", "err");
  }
}

/* ─── FORGOT PASSWORD — RESET ────────────────────────────────*/
async function resetPassword() {
  const email    = document.getElementById("fEmail").value.trim();
  const code     = document.getElementById("resetCode").value.trim().toUpperCase();
  const password = document.getElementById("newPw").value;
  const confirm  = document.getElementById("newPwConf").value;

  clearMsg("fMsg2");

  if (!code || code.length < 5) {
    showMsg("fMsg2", "Please enter the full reset code.", "err"); return;
  }
  if (!password || password.length < 6) {
    showMsg("fMsg2", "Password must be at least 6 characters.", "err"); return;
  }
  if (password !== confirm) {
    showMsg("fMsg2", "Passwords do not match.", "err"); return;
  }

  showMsg("fMsg2", "Verifying code…", "info");

  try {
    const res  = await fetch(API + "/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, password })
    });
    const data = await res.json();

    if (data.success) {
      showMsg("fMsg2", "✓ Password reset! Redirecting to sign in…", "ok");
      setTimeout(() => {
        document.getElementById("fStep1").style.display = "block";
        document.getElementById("fStep2").style.display = "none";
        document.getElementById("fEmail").value    = "";
        document.getElementById("resetCode").value = "";
        clearMsg("fMsg1"); clearMsg("fMsg2");
        showPage("loginPage");
      }, 1800);
    } else {
      showMsg("fMsg2", data.error || "Invalid code.", "err");
    }
  } catch {
    showMsg("fMsg2", "Connection error. Please try again.", "err");
  }
}

/* ─── LOGOUT ─────────────────────────────────────────────────*/
function logout() {
  S.clear();
  setStatus("ready", "TAP TO SPEAK");
  document.getElementById("transcriptBox").classList.add("hidden");
  document.getElementById("responseBox").classList.add("hidden");
  showPage("welcomePage");
  toast("Signed out successfully.");
}

/* ─── SPEECH RECOGNITION ─────────────────────────────────────*/
let recognition = null;
let _busy       = false;

(function initSR() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { console.warn("[SR] Not supported."); return; }

  recognition = new SR();
  recognition.continuous      = false;
  recognition.interimResults  = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => { _busy = true; setStatus("listening", "LISTENING…"); };

  recognition.onresult = event => {
    const text = event.results[0][0].transcript.trim();
    document.getElementById("transcriptText").textContent = text;
    document.getElementById("transcriptBox").classList.remove("hidden");
    document.getElementById("responseBox").classList.add("hidden");
    sendVoice(text);
  };

  recognition.onerror = e => {
    _busy = false;
    setStatus("ready", "TAP TO SPEAK");
    const map = {
      "no-speech":     "No speech detected. Please try again.",
      "audio-capture": "Microphone not found.",
      "not-allowed":   "Microphone access denied. Allow it in browser settings.",
      "network":       "Network error during recognition.",
    };
    toast(map[e.error] || "Speech error: " + e.error);
  };

  recognition.onend = () => {
    _busy = false;
    if (document.getElementById("orb").className.includes("listening"))
      setStatus("processing", "PROCESSING…");
  };
})();

function startListening() {
  if (_busy) return;
  const cls = document.getElementById("orb").className;
  if (cls.includes("listening") || cls.includes("processing") || cls.includes("speaking")) return;
  if (!recognition) {
    toast("Speech recognition not supported. Use Chrome or Edge."); return;
  }
  recognition.lang = document.getElementById("selSpeech").value || "en-US";
  try { recognition.start(); }
  catch(e) { setStatus("ready", "TAP TO SPEAK"); }
}

/* ─── SEND TO BACKEND ────────────────────────────────────────*/
async function sendVoice(text) {
  const lang     = document.getElementById("selLang").value;
  const voice    = S.voice;
  const username = S.username;

  setStatus("processing", "TRANSLATING…");

  try {
    const res = await fetch(API + "/voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language: lang, voice, username })
    });

    if (!res.ok) {
      let errMsg = "Server error (" + res.status + ").";
      try { const d = await res.json(); if (d.error) errMsg = d.error; } catch {}
      setStatus("ready", "TAP TO SPEAK"); toast(errMsg); return;
    }

    const data = await res.json();

    if (!data.success) {
      setStatus("ready", "TAP TO SPEAK");
      toast(data.error || "Something went wrong."); return;
    }

    document.getElementById("responseText").textContent = data.text;
    document.getElementById("responseMeta").textContent =
      "🔊 Speaking in " + (data.lang_name || "selected language");
    document.getElementById("responseBox").classList.remove("hidden");

    setStatus("speaking", "SPEAKING…");

    const audio = new Audio(data.audio);
    audio.onended = () => setStatus("ready", "TAP TO SPEAK");
    audio.onerror = () => {
      setStatus("ready", "TAP TO SPEAK");
      toast("Translation ready — audio playback failed.");
    };
    audio.play().catch(() => {
      setStatus("ready", "TAP TO SPEAK");
      toast("Translation done — tap to play (browser blocked autoplay).");
    });

  } catch(e) {
    console.error("[Voice]", e);
    setStatus("ready", "TAP TO SPEAK");
    toast("Connection error. Please check your internet.");
  }
}

/* ─── INIT ───────────────────────────────────────────────────*/
window.addEventListener("load", () => {
  loadVoices();
  // Restore session if returning to same tab after F5
  // New tab or closed browser → always welcome page (S.ok is false)
  showPage(S.ok ? "appPage" : "welcomePage");
});