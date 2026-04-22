const API = "https://ai-voice-system-j313.onrender.com";

/* ── LANGUAGE TABLE ──────────────────────────────────── */
const LANGS = [
  { code:"1", lang:"en", sr:"en-US", name:"English",  native:"English"  },
  { code:"2", lang:"hi", sr:"hi-IN", name:"Hindi",    native:"हिंदी"    },
  { code:"3", lang:"mr", sr:"mr-IN", name:"Marathi",  native:"मराठी"    },
  { code:"4", lang:"ta", sr:"ta-IN", name:"Tamil",    native:"தமிழ்"   },
  { code:"5", lang:"te", sr:"te-IN", name:"Telugu",   native:"తెలుగు"  },
  { code:"6", lang:"gu", sr:"gu-IN", name:"Gujarati", native:"ગુજરાતી" },
  { code:"7", lang:"bn", sr:"bn-IN", name:"Bengali",  native:"বাংলা"   },
  { code:"8", lang:"kn", sr:"kn-IN", name:"Kannada",  native:"ಕನ್ನಡ"  },
];

// Default: speak Hindi → translate to English
let _fromCode = "2";
let _toCode   = "1";

function getLang(code){ return LANGS.find(l => l.code === code) || LANGS[0]; }

/* ── SESSION ─────────────────────────────────────────── */
const S = {
  set(u,n,v){
    sessionStorage.setItem("va_u",u);
    sessionStorage.setItem("va_n",n||u);
    sessionStorage.setItem("va_v",v||"EXAVITQu4vr4xnSDxMaL");
    sessionStorage.setItem("va_ok","1");
  },
  clear(){["va_u","va_n","va_v","va_ok"].forEach(k=>sessionStorage.removeItem(k));},
  get username(){return sessionStorage.getItem("va_u")||"";},
  get name()   {return sessionStorage.getItem("va_n")||"";},
  get voice()  {return sessionStorage.getItem("va_v")||"EXAVITQu4vr4xnSDxMaL";},
  get ok()     {return sessionStorage.getItem("va_ok")==="1";}
};

/* ── AUTH GUARD ──────────────────────────────────────── */
function showPage(id){
  if(id==="appPage"&&!S.ok){notify("Please sign in to continue.");id="loginPage";}
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

/* ── TOAST ───────────────────────────────────────────── */
let _tt;
function notify(msg,ms=3400){
  const el=document.getElementById("toast");
  el.textContent=msg;el.classList.remove("hidden");
  clearTimeout(_tt);_tt=setTimeout(()=>el.classList.add("hidden"),ms);
}

/* ── INLINE MESSAGES ─────────────────────────────────── */
function showMsg(id,text,type){
  const el=document.getElementById(id);if(!el)return;
  el.textContent=text;el.className="msg show "+type;
}
function clearMsg(id){
  const el=document.getElementById(id);if(!el)return;
  el.textContent="";el.className="msg";
}

/* ── ORB STATE ───────────────────────────────────────── */
function setStatus(state,label){
  const orb  = document.getElementById("orb");
  const rings= document.getElementById("rings");
  const tag  = document.getElementById("statusTag");
  const mic  = document.getElementById("orbSvg");
  const spin = document.getElementById("orbSpinner");
  const wave = document.getElementById("orbWave");
  if(!orb)return;
  orb.className   = "orb "+state;
  rings.className = "rings-wrap "+state;
  tag.className   = "status-tag "+state;
  tag.textContent = label;
  mic.classList.add("hidden");
  spin.classList.add("hidden");
  wave.classList.add("hidden");
  if(state==="processing")     spin.classList.remove("hidden");
  else if(state==="speaking")  wave.classList.remove("hidden");
  else                          mic.classList.remove("hidden");
}

/* ── PASSWORD TOGGLE ─────────────────────────────────── */
function togglePw(id,btn){
  const inp=document.getElementById(id);
  if(inp.type==="password"){
    inp.type="text";
    btn.innerHTML=`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;
  }else{
    inp.type="password";
    btn.innerHTML=`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
  }
}

/* ── DUAL LANGUAGE DROPDOWNS ───────────────────────────── */
let _fromOpen = false, _toOpen = false;

function _buildMenu(menuId, activeCode, onSelect){
  const menu = document.getElementById(menuId);
  if(!menu) return;
  menu.innerHTML = "";
  LANGS.forEach(l => {
    const div = document.createElement("div");
    div.className = "lang-opt" + (l.code === activeCode ? " active" : "");
    div.innerHTML = `<span class="lo-name">${l.name}</span><span class="lo-native">${l.native}</span>`;
    div.onclick = () => onSelect(l);
    menu.appendChild(div);
  });
}

function _closeAll(){
  _fromOpen = false; _toOpen = false;
  ["fromMenu","toMenu"].forEach(id=>{
    const m=document.getElementById(id); if(m) m.classList.add("hidden");
  });
  ["fromBtn","toBtn"].forEach(id=>{
    const b=document.getElementById(id); if(b) b.classList.remove("open");
  });
}

function toggleFromMenu(){
  if(_toOpen){ _toOpen=false; document.getElementById("toMenu").classList.add("hidden"); document.getElementById("toBtn").classList.remove("open"); }
  _fromOpen = !_fromOpen;
  const menu = document.getElementById("fromMenu");
  const btn  = document.getElementById("fromBtn");
  if(_fromOpen){
    _buildMenu("fromMenu", _fromCode, l => {
      _fromCode = l.code;
      // ← KEY: update mic recognition language to what user speaks
      if(recognition) recognition.lang = l.sr;
      document.getElementById("fromName").textContent = l.name;
      _updateBadge();
      _closeAll();
      notify("Speaking in: " + l.name + " — " + l.native);
    });
    menu.classList.remove("hidden"); btn.classList.add("open");
  } else {
    menu.classList.add("hidden"); btn.classList.remove("open");
  }
}

function toggleToMenu(){
  if(_fromOpen){ _fromOpen=false; document.getElementById("fromMenu").classList.add("hidden"); document.getElementById("fromBtn").classList.remove("open"); }
  _toOpen = !_toOpen;
  const menu = document.getElementById("toMenu");
  const btn  = document.getElementById("toBtn");
  if(_toOpen){
    _buildMenu("toMenu", _toCode, l => {
      _toCode = l.code;
      document.getElementById("toName").textContent = l.name;
      _updateBadge();
      _closeAll();
      notify("Translating to: " + l.name + " — " + l.native);
    });
    menu.classList.remove("hidden"); btn.classList.add("open");
  } else {
    menu.classList.add("hidden"); btn.classList.remove("open");
  }
}

function _updateBadge(){
  const el = document.getElementById("langBadge");
  if(!el) return;
  const f = getLang(_fromCode), t = getLang(_toCode);
  el.innerHTML = `Speak <strong>${f.name}</strong> &rarr; hear <strong>${t.name}</strong>`;
}

// Close menus on outside click
document.addEventListener("click", e => {
  const fw = document.getElementById("fromWrap");
  const tw = document.getElementById("toWrap");
  if(fw && !fw.contains(e.target) && _fromOpen){ _fromOpen=false; document.getElementById("fromMenu").classList.add("hidden"); document.getElementById("fromBtn").classList.remove("open"); }
  if(tw && !tw.contains(e.target) && _toOpen)  { _toOpen=false;  document.getElementById("toMenu").classList.add("hidden");   document.getElementById("toBtn").classList.remove("open"); }
});

/* ── LOAD VOICES ─────────────────────────────────────── */
async function loadVoices(){
  const sel=document.getElementById("voiceSelect");if(!sel)return;
  try{
    const res=await fetch(API+"/voices");
    const data=await res.json();
    sel.innerHTML="";
    const list=(data.success&&data.voices?.length)?data.voices:[
      {id:"EXAVITQu4vr4xnSDxMaL",name:"Rachel"},
      {id:"21m00Tcm4TlvDq8ikWAM",name:"Bella"},
      {id:"TxGEqnHWrfWFTfGW9XjX",name:"Josh"},
      {id:"pNInz6obpgDQGcFmaJgB",name:"Adam"},
    ];
    list.forEach(v=>{const o=document.createElement("option");o.value=v.id;o.textContent=v.name;sel.appendChild(o);});
  }catch{
    if(sel)sel.innerHTML='<option value="EXAVITQu4vr4xnSDxMaL">Rachel</option>';
  }
}

/* ── LOGIN ───────────────────────────────────────────── */
async function login(){
  const username=document.getElementById("lUser").value.trim();
  const password=document.getElementById("lPass").value;
  const voice=document.getElementById("voiceSelect").value;
  const btn=document.getElementById("lBtn");
  clearMsg("lMsg");
  if(!username||!password){showMsg("lMsg","Please fill in all fields.","err");return;}
  btn.disabled=true;btn.textContent="Signing in…";
  showMsg("lMsg","Verifying credentials…","info");
  try{
    const res=await fetch(API+"/auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username,password})});
    const data=await res.json();
    if(data.success){
      S.set(username,data.name,voice);
      showMsg("lMsg","Welcome back, "+(data.name||username)+"!","ok");
      setTimeout(()=>{btn.disabled=false;btn.textContent="Sign In";showPage("appPage");},700);
    }else{
      showMsg("lMsg",data.error||"Login failed.","err");
      btn.disabled=false;btn.textContent="Sign In";
    }
  }catch{
    showMsg("lMsg","Connection error. Please check your internet.","err");
    btn.disabled=false;btn.textContent="Sign In";
  }
}

/* ── REGISTER STEP 1 ─────────────────────────────────── */
async function registerRequest(){
  const name=document.getElementById("rName").value.trim();
  const email=document.getElementById("rEmail").value.trim();
  const username=document.getElementById("rUser").value.trim();
  const password=document.getElementById("rPass").value;
  const confirm=document.getElementById("rConf").value;
  const btn=document.getElementById("rBtn1");
  clearMsg("rMsg1");
  if(!name||!email||!username||!password||!confirm){showMsg("rMsg1","Please fill in all fields.","err");return;}
  if(!email.includes("@")||!email.includes(".")){showMsg("rMsg1","Please enter a valid email address.","err");return;}
  if(password.length<6){showMsg("rMsg1","Password must be at least 6 characters.","err");return;}
  if(password!==confirm){showMsg("rMsg1","Passwords do not match.","err");return;}
  btn.disabled=true;btn.textContent="Sending…";
  showMsg("rMsg1","Sending verification code to your email…","info");
  try{
    const res=await fetch(API+"/register/request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,email,username,password})});
    const data=await res.json();
    if(data.success){
      document.getElementById("regStep1").style.display="none";
      document.getElementById("regStep2").style.display="block";
      showMsg("rMsg2","Code sent. Check your inbox and spam folder.","ok");
    }else{showMsg("rMsg1",data.error||"Failed to send code.","err");}
  }catch{showMsg("rMsg1","Connection error. Please try again.","err");}
  finally{btn.disabled=false;btn.textContent="Send Verification Code";}
}

/* ── REGISTER STEP 2 ─────────────────────────────────── */
async function registerVerify(){
  const email=document.getElementById("rEmail").value.trim();
  const code=document.getElementById("regOtp").value.trim().toUpperCase();
  const btn=document.getElementById("rBtn2");
  clearMsg("rMsg2");
  if(!code||code.length<4){showMsg("rMsg2","Please enter the verification code.","err");return;}
  btn.disabled=true;btn.textContent="Verifying…";
  showMsg("rMsg2","Verifying code…","info");
  try{
    const res=await fetch(API+"/register/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,code})});
    const data=await res.json();
    if(data.success){
      showMsg("rMsg2","Account created. Redirecting to sign in…","ok");
      setTimeout(()=>{
        document.getElementById("regStep1").style.display="block";
        document.getElementById("regStep2").style.display="none";
        ["rName","rEmail","rUser","rPass","rConf","regOtp"].forEach(id=>{const el=document.getElementById(id);if(el)el.value="";});
        clearMsg("rMsg1");clearMsg("rMsg2");
        btn.disabled=false;btn.textContent="Verify & Create Account";
        showPage("loginPage");
      },1400);
    }else{showMsg("rMsg2",data.error||"Verification failed.","err");btn.disabled=false;btn.textContent="Verify & Create Account";}
  }catch{showMsg("rMsg2","Connection error. Please try again.","err");btn.disabled=false;btn.textContent="Verify & Create Account";}
}

/* ── RESEND OTP ──────────────────────────────────────── */
async function resendOtp(){
  const name=document.getElementById("rName").value.trim();
  const email=document.getElementById("rEmail").value.trim();
  const username=document.getElementById("rUser").value.trim();
  const password=document.getElementById("rPass").value;
  showMsg("rMsg2","Resending code…","info");
  try{
    const res=await fetch(API+"/register/request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,email,username,password})});
    const data=await res.json();
    showMsg("rMsg2",data.success?"New code sent. Check your inbox.":(data.error||"Failed."),data.success?"ok":"err");
  }catch{showMsg("rMsg2","Connection error.","err");}
}

/* ── FORGOT / RESET PASSWORD ─────────────────────────── */
async function sendResetCode(){
  const email=document.getElementById("fEmail").value.trim();
  clearMsg("fMsg1");
  if(!email||!email.includes("@")){showMsg("fMsg1","Please enter a valid email address.","err");return;}
  showMsg("fMsg1","Sending reset code…","info");
  try{
    const res=await fetch(API+"/forgot-password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email})});
    const data=await res.json();
    if(data.success){
      document.getElementById("fStep1").style.display="none";
      document.getElementById("fStep2").style.display="block";
      showMsg("fMsg2","Code sent. Check your inbox and spam folder.","ok");
    }else{showMsg("fMsg1",data.error||"Email not found.","err");}
  }catch{showMsg("fMsg1","Connection error. Please try again.","err");}
}

async function resetPassword(){
  const email=document.getElementById("fEmail").value.trim();
  const code=document.getElementById("resetCode").value.trim().toUpperCase();
  const password=document.getElementById("newPw").value;
  const confirm=document.getElementById("newPwConf").value;
  clearMsg("fMsg2");
  if(!code||code.length<5){showMsg("fMsg2","Please enter the full reset code.","err");return;}
  if(!password||password.length<6){showMsg("fMsg2","Password must be at least 6 characters.","err");return;}
  if(password!==confirm){showMsg("fMsg2","Passwords do not match.","err");return;}
  showMsg("fMsg2","Verifying code…","info");
  try{
    const res=await fetch(API+"/reset-password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,code,password})});
    const data=await res.json();
    if(data.success){
      showMsg("fMsg2","Password reset. Redirecting to sign in…","ok");
      setTimeout(()=>{
        document.getElementById("fStep1").style.display="block";
        document.getElementById("fStep2").style.display="none";
        document.getElementById("fEmail").value="";
        document.getElementById("resetCode").value="";
        clearMsg("fMsg1");clearMsg("fMsg2");
        showPage("loginPage");
      },1800);
    }else{showMsg("fMsg2",data.error||"Invalid code.","err");}
  }catch{showMsg("fMsg2","Connection error. Please try again.","err");}
}

/* ── LOGOUT ──────────────────────────────────────────── */
function logout(){
  S.clear();setStatus("ready","TAP TO SPEAK");
  ["transcriptBox","responseBox"].forEach(id=>{
    const el=document.getElementById(id);if(el)el.classList.add("hidden");
  });
  showPage("welcomePage");notify("Signed out successfully.");
}

/* ── SPEECH RECOGNITION ────────────────────────────────── */
let recognition = null, _busy = false;

(function initSR(){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){ console.warn("[SR] Not supported."); return; }
  recognition = new SR();
  recognition.continuous     = false;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.lang = getLang(_fromCode).sr;  // ← FROM lang, not TO

  recognition.onstart = () => { _busy=true; setStatus("listening","LISTENING"); };

  recognition.onresult = event => {
    const text = event.results[0][0].transcript.trim();
    console.log("[SR] Heard:", text,
      "| FROM:", getLang(_fromCode).name,
      "→ TO:", getLang(_toCode).name);
    document.getElementById("transcriptText").textContent = text;
    document.getElementById("transcriptBox").classList.remove("hidden");
    document.getElementById("responseBox").classList.add("hidden");
    sendVoice(text);
  };

  recognition.onerror = e => {
    _busy=false; setStatus("ready","TAP TO SPEAK");
    const map = {
      "no-speech":      "No speech detected. Please try again.",
      "audio-capture":  "Microphone not found. Check your device.",
      "not-allowed":    "Microphone access denied. Allow it in browser settings.",
      "network":        "Network error during speech recognition.",
    };
    notify(map[e.error] || "Speech error: "+e.error);
  };

  recognition.onend = () => {
    _busy = false;
    const orb = document.getElementById("orb");
    if(orb && orb.className.includes("listening"))
      setStatus("processing","PROCESSING");
  };
})();

function startListening(){
  if(_busy) return;
  const orb = document.getElementById("orb"); if(!orb) return;
  if(orb.className.includes("listening") ||
     orb.className.includes("processing") ||
     orb.className.includes("speaking")) return;
  if(!recognition){ notify("Speech recognition not supported. Use Chrome or Edge."); return; }

  // Always re-sync FROM lang before starting — ensures any dropdown change is applied
  recognition.lang = getLang(_fromCode).sr;
  console.log("[SR] Start | mic lang:", recognition.lang, "| translate to code:", _toCode);
  try{ recognition.start(); }catch(e){ setStatus("ready","TAP TO SPEAK"); }
}

/* ── SEND TO BACKEND ───────────────────────────────────── */
async function sendVoice(text){
  setStatus("processing","TRANSLATING");
  const voice    = S.voice;
  const username = S.username;
  const toL      = getLang(_toCode);

  try{
    const res = await fetch(API+"/voice",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({ text, language: _toCode, voice, username })
    });

    if(!res.ok){
      let err = "Server error ("+res.status+").";
      try{ const d=await res.json(); if(d.error)err=d.error; }catch{}
      setStatus("ready","TAP TO SPEAK"); notify(err); return;
    }

    const data = await res.json();
    if(!data.success){
      setStatus("ready","TAP TO SPEAK");
      notify(data.error||"Something went wrong."); return;
    }

    document.getElementById("responseText").textContent = data.text;
    document.getElementById("responseMeta").textContent =
      "Speaking in " + (data.lang_name || toL.name);
    document.getElementById("responseBox").classList.remove("hidden");
    setStatus("speaking","SPEAKING");

    const audio = new Audio(data.audio);
    audio.oncanplaythrough = () => audio.play().catch(()=>{
      setStatus("ready","TAP TO SPEAK");
      notify("Translation complete. Tap play — browser blocked autoplay.");
    });
    audio.onended = () => setStatus("ready","TAP TO SPEAK");
    audio.onerror = () => { setStatus("ready","TAP TO SPEAK"); notify("Audio playback failed."); };
    audio.load();

  }catch(e){
    console.error("[Voice]",e);
    setStatus("ready","TAP TO SPEAK");
    notify("Connection error. Please check your internet connection.");
  }
}

/* ── INIT ────────────────────────────────────────────── */
window.addEventListener("load", () => {
  loadVoices();
  // Set initial button labels
  document.getElementById("fromName").textContent = getLang(_fromCode).name;
  document.getElementById("toName").textContent   = getLang(_toCode).name;
  _updateBadge();
  showPage(S.ok ? "appPage" : "welcomePage");
});