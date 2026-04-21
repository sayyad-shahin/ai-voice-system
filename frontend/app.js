/* ═══════════════════════════════════════════════════════
   VoiceAI  app.js  v6.0  DUAL-LANG FIXED
   ─────────────────────────────────────────────────────
   TWO selectors:
     FROM (#fromBtn) → language YOU ARE SPEAKING
                       → sets recognition.lang on the mic
     TO   (#toBtn)   → language TO TRANSLATE INTO
                       → sent to backend as target

   These are 100% independent of each other.
   Example: FROM=Hindi (mic hears Hindi script)
            TO=Marathi  (backend outputs Marathi)
            Result: "कैसे हो?" → "कसे आहात?" ✅
═══════════════════════════════════════════════════════ */

const API = "https://ai-voice-system-j313.onrender.com";

/* ── LANGUAGE TABLE ──────────────────────────────────── */
const LANGS = [
  { code:"1", lang:"en", sr:"en-US", label:"🇺🇸 English"  },
  { code:"2", lang:"hi", sr:"hi-IN", label:"🇮🇳 Hindi"    },
  { code:"3", lang:"mr", sr:"mr-IN", label:"🇮🇳 Marathi"  },
  { code:"4", lang:"ta", sr:"ta-IN", label:"🇮🇳 Tamil"    },
  { code:"5", lang:"te", sr:"te-IN", label:"🇮🇳 Telugu"   },
  { code:"6", lang:"gu", sr:"gu-IN", label:"🇮🇳 Gujarati" },
  { code:"7", lang:"bn", sr:"bn-IN", label:"🇧🇩 Bengali"  },
  { code:"8", lang:"kn", sr:"kn-IN", label:"🇮🇳 Kannada"  },
];
let _fromCode = "2";  // default: speak Hindi
let _toCode   = "1";  // default: translate to English

function getLang(code){ return LANGS.find(l=>l.code===code)||LANGS[0]; }

/* SESSION */
const S = {
  set(u,n,v){sessionStorage.setItem("va_u",u);sessionStorage.setItem("va_n",n||u);sessionStorage.setItem("va_v",v||"EXAVITQu4vr4xnSDxMaL");sessionStorage.setItem("va_ok","1");},
  clear(){["va_u","va_n","va_v","va_ok"].forEach(k=>sessionStorage.removeItem(k));},
  get username(){return sessionStorage.getItem("va_u")||"";},
  get name(){return sessionStorage.getItem("va_n")||"";},
  get voice(){return sessionStorage.getItem("va_v")||"EXAVITQu4vr4xnSDxMaL";},
  get ok(){return sessionStorage.getItem("va_ok")==="1";}
};

/* PAGE NAV */
function showPage(id){
  if(id==="appPage"&&!S.ok){toast("Please sign in to continue.");id="loginPage";}
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

/* TOAST */
let _tt;
function toast(msg,ms=3400){
  const el=document.getElementById("toast");
  el.textContent=msg;el.classList.remove("hidden");
  clearTimeout(_tt);_tt=setTimeout(()=>el.classList.add("hidden"),ms);
}

/* STATUS MESSAGES */
function showMsg(id,text,type){
  const el=document.getElementById(id);if(!el)return;
  el.textContent=text;el.className="msg show "+type;
}
function clearMsg(id){
  const el=document.getElementById(id);if(!el)return;
  el.textContent="";el.className="msg";
}

/* ORB STATUS */
function setStatus(state,label){
  const orb=document.getElementById("orb");
  const rings=document.getElementById("rings");
  const tag=document.getElementById("statusTag");
  const icon=document.getElementById("orbIcon");
  if(!orb)return;
  orb.className="orb "+state;
  rings.className="rings-wrap "+state;
  tag.className="status-tag "+state;
  tag.textContent=label;
  const icons={listening:"🎤",processing:"⏳",speaking:"🔊",ready:"🎙️"};
  icon.textContent=icons[state]||"🎙️";
}

/* PASSWORD TOGGLE */
function togglePw(id,btn){
  const inp=document.getElementById(id);
  if(inp.type==="password"){inp.type="text";btn.textContent="🙈";}
  else{inp.type="password";btn.textContent="👁";}
}

/* ── DUAL LANGUAGE DROPDOWNS ─────────────────────────────
   Each dropdown is built dynamically from LANGS[].
   FROM menu updates recognition.lang on selection.
   TO   menu updates _toCode which is sent to backend.
─────────────────────────────────────────────────────── */
let _fromOpen=false, _toOpen=false;

function _buildMenu(menuId, activeCode, onSelect){
  const menu=document.getElementById(menuId);
  if(!menu)return;
  menu.innerHTML="";
  LANGS.forEach(l=>{
    const div=document.createElement("div");
    div.className="lang-opt"+(l.code===activeCode?" active":"");
    div.textContent=l.label;
    div.onclick=()=>onSelect(l);
    menu.appendChild(div);
  });
}

function toggleFromMenu(){
  // Close TO menu first
  _toOpen=false;
  document.getElementById("toMenu").classList.add("hidden");
  document.getElementById("toBtn").classList.remove("open");

  _fromOpen=!_fromOpen;
  const menu=document.getElementById("fromMenu");
  const btn=document.getElementById("fromBtn");
  if(_fromOpen){
    _buildMenu("fromMenu",_fromCode,l=>{
      _fromCode=l.code;
      document.getElementById("fromLabel").textContent=l.label;
      // ← KEY: update speech recognition language to what user speaks
      if(recognition) recognition.lang=l.sr;
      _fromOpen=false;
      menu.classList.add("hidden");
      btn.classList.remove("open");
      toast("Speaking in: "+l.label.replace(/^\S+\s*/,""));
    });
    menu.classList.remove("hidden");
    btn.classList.add("open");
  } else {
    menu.classList.add("hidden");
    btn.classList.remove("open");
  }
}

function toggleToMenu(){
  // Close FROM menu first
  _fromOpen=false;
  document.getElementById("fromMenu").classList.add("hidden");
  document.getElementById("fromBtn").classList.remove("open");

  _toOpen=!_toOpen;
  const menu=document.getElementById("toMenu");
  const btn=document.getElementById("toBtn");
  if(_toOpen){
    _buildMenu("toMenu",_toCode,l=>{
      _toCode=l.code;
      document.getElementById("toLabel").textContent=l.label;
      _toOpen=false;
      menu.classList.add("hidden");
      btn.classList.remove("open");
      toast("Translating to: "+l.label.replace(/^\S+\s*/,""));
    });
    menu.classList.remove("hidden");
    btn.classList.add("open");
  } else {
    menu.classList.add("hidden");
    btn.classList.remove("open");
  }
}

// Close menus on outside click
document.addEventListener("click",e=>{
  const fw=document.getElementById("fromWrap");
  const tw=document.getElementById("toWrap");
  if(fw&&!fw.contains(e.target)&&_fromOpen){
    _fromOpen=false;
    document.getElementById("fromMenu").classList.add("hidden");
    document.getElementById("fromBtn").classList.remove("open");
  }
  if(tw&&!tw.contains(e.target)&&_toOpen){
    _toOpen=false;
    document.getElementById("toMenu").classList.add("hidden");
    document.getElementById("toBtn").classList.remove("open");
  }
});

/* LOAD VOICES */
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
  }catch{if(sel)sel.innerHTML='<option value="EXAVITQu4vr4xnSDxMaL">Rachel (default)</option>';}
}

/* LOGIN */
async function login(){
  const username=document.getElementById("lUser").value.trim();
  const password=document.getElementById("lPass").value;
  const voice=document.getElementById("voiceSelect").value;
  const btn=document.getElementById("lBtn");
  clearMsg("lMsg");
  if(!username||!password){showMsg("lMsg","Please fill in all fields.","err");return;}
  btn.disabled=true;btn.textContent="Signing in…";
  showMsg("lMsg","Verifying your credentials…","info");
  try{
    const res=await fetch(API+"/auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username,password})});
    const data=await res.json();
    if(data.success){
      S.set(username,data.name,voice);
      showMsg("lMsg","✓ Welcome back, "+(data.name||username)+"!","ok");
      setTimeout(()=>{btn.disabled=false;btn.textContent="Sign In";showPage("appPage");},750);
    }else{
      showMsg("lMsg",data.error||"Login failed.","err");
      btn.disabled=false;btn.textContent="Sign In";
    }
  }catch{
    showMsg("lMsg","Connection error. Check your internet.","err");
    btn.disabled=false;btn.textContent="Sign In";
  }
}

/* REGISTER STEP 1 */
async function registerRequest(){
  const name=document.getElementById("rName").value.trim();
  const email=document.getElementById("rEmail").value.trim();
  const username=document.getElementById("rUser").value.trim();
  const password=document.getElementById("rPass").value;
  const confirm=document.getElementById("rConf").value;
  const btn=document.getElementById("rBtn1");
  clearMsg("rMsg1");
  if(!name||!email||!username||!password||!confirm){showMsg("rMsg1","Please fill in all fields.","err");return;}
  if(!email.includes("@")||!email.includes(".")){showMsg("rMsg1","Please enter a valid email.","err");return;}
  if(password.length<6){showMsg("rMsg1","Password must be at least 6 characters.","err");return;}
  if(password!==confirm){showMsg("rMsg1","Passwords do not match.","err");return;}
  btn.disabled=true;btn.textContent="Sending code…";
  showMsg("rMsg1","Sending verification code to your email…","info");
  try{
    const res=await fetch(API+"/register/request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,email,username,password})});
    const data=await res.json();
    if(data.success){
      document.getElementById("regStep1").style.display="none";
      document.getElementById("regStep2").style.display="block";
      showMsg("rMsg2","✓ Code sent! Check your inbox (and spam folder).","ok");
    }else{showMsg("rMsg1",data.error||"Failed to send code.","err");}
  }catch{showMsg("rMsg1","Connection error. Please try again.","err");}
  finally{btn.disabled=false;btn.textContent="Send Verification Code";}
}

/* REGISTER STEP 2 */
async function registerVerify(){
  const email=document.getElementById("rEmail").value.trim();
  const code=document.getElementById("regOtp").value.trim().toUpperCase();
  const btn=document.getElementById("rBtn2");
  clearMsg("rMsg2");
  if(!code||code.length<4){showMsg("rMsg2","Please enter the verification code.","err");return;}
  btn.disabled=true;btn.textContent="Verifying…";
  showMsg("rMsg2","Verifying your code…","info");
  try{
    const res=await fetch(API+"/register/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,code})});
    const data=await res.json();
    if(data.success){
      showMsg("rMsg2","✓ Account created! Redirecting to sign in…","ok");
      setTimeout(()=>{
        document.getElementById("regStep1").style.display="block";
        document.getElementById("regStep2").style.display="none";
        ["rName","rEmail","rUser","rPass","rConf","regOtp"].forEach(id=>{const el=document.getElementById(id);if(el)el.value="";});
        clearMsg("rMsg1");clearMsg("rMsg2");
        btn.disabled=false;btn.textContent="Verify & Create Account";
        showPage("loginPage");
      },1500);
    }else{showMsg("rMsg2",data.error||"Verification failed.","err");btn.disabled=false;btn.textContent="Verify & Create Account";}
  }catch{showMsg("rMsg2","Connection error. Please try again.","err");btn.disabled=false;btn.textContent="Verify & Create Account";}
}

/* RESEND OTP */
async function resendOtp(){
  const name=document.getElementById("rName").value.trim();
  const email=document.getElementById("rEmail").value.trim();
  const username=document.getElementById("rUser").value.trim();
  const password=document.getElementById("rPass").value;
  showMsg("rMsg2","Resending code…","info");
  try{
    const res=await fetch(API+"/register/request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,email,username,password})});
    const data=await res.json();
    showMsg("rMsg2",data.success?"✓ New code sent! Check your inbox.":(data.error||"Failed."),data.success?"ok":"err");
  }catch{showMsg("rMsg2","Connection error.","err");}
}

/* FORGOT PASSWORD */
async function sendResetCode(){
  const email=document.getElementById("fEmail").value.trim();
  clearMsg("fMsg1");
  if(!email||!email.includes("@")){showMsg("fMsg1","Please enter a valid email.","err");return;}
  showMsg("fMsg1","Sending reset code to your email…","info");
  try{
    const res=await fetch(API+"/forgot-password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email})});
    const data=await res.json();
    if(data.success){
      document.getElementById("fStep1").style.display="none";
      document.getElementById("fStep2").style.display="block";
      showMsg("fMsg2","✓ Code sent! Check your inbox (and spam folder).","ok");
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
      showMsg("fMsg2","✓ Password reset! Redirecting…","ok");
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

/* LOGOUT */
function logout(){
  S.clear();setStatus("ready","TAP TO SPEAK");
  const tb=document.getElementById("transcriptBox");
  const rb=document.getElementById("responseBox");
  if(tb)tb.classList.add("hidden");if(rb)rb.classList.add("hidden");
  showPage("welcomePage");toast("Signed out successfully.");
}

/* ── SPEECH RECOGNITION ──────────────────────────────────
   recognition.lang always tracks _fromCode.
   It is updated at init and every time FROM dropdown changes.
   The TO language (_toCode) never touches recognition.lang.
─────────────────────────────────────────────────────── */
let recognition=null, _busy=false;

(function initSR(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){console.warn("[SR] Not supported.");return;}
  recognition=new SR();
  recognition.continuous=false;
  recognition.interimResults=false;
  recognition.maxAlternatives=1;
  recognition.lang=getLang(_fromCode).sr;   // ← driven by FROM, not TO

  recognition.onstart=()=>{_busy=true;setStatus("listening","LISTENING…");};

  recognition.onresult=event=>{
    const text=event.results[0][0].transcript.trim();
    console.log("[SR] Heard:",text,
      "| FROM lang:",getLang(_fromCode).label,
      "| TO lang:",getLang(_toCode).label);
    document.getElementById("transcriptText").textContent=text;
    document.getElementById("transcriptBox").classList.remove("hidden");
    document.getElementById("responseBox").classList.add("hidden");
    sendVoice(text);
  };

  recognition.onerror=e=>{
    _busy=false;setStatus("ready","TAP TO SPEAK");
    const map={
      "no-speech":"No speech detected. Try again.",
      "audio-capture":"Microphone not found.",
      "not-allowed":"Microphone denied. Allow in browser settings.",
      "network":"Network error."
    };
    toast(map[e.error]||"Speech error: "+e.error);
  };

  recognition.onend=()=>{
    _busy=false;
    const orb=document.getElementById("orb");
    if(orb&&orb.className.includes("listening"))setStatus("processing","PROCESSING…");
  };
})();

function startListening(){
  if(_busy)return;
  const orb=document.getElementById("orb");if(!orb)return;
  if(orb.className.includes("listening")||
     orb.className.includes("processing")||
     orb.className.includes("speaking"))return;
  if(!recognition){toast("Speech recognition not supported. Use Chrome or Edge.");return;}

  // Sync recognition.lang to current FROM selection before every listen
  recognition.lang=getLang(_fromCode).sr;
  console.log("[SR] Listening | mic lang:",recognition.lang,"→ translate to code:",_toCode);
  try{recognition.start();}catch(e){setStatus("ready","TAP TO SPEAK");}
}

/* ── SEND TO BACKEND ─────────────────────────────────────
   Sends transcribed text + _toCode as the translation target.
   The backend auto-detects the source language from the text
   and translates to the target language.
─────────────────────────────────────────────────────── */
async function sendVoice(text){
  setStatus("processing","TRANSLATING…");
  const voice=S.voice;
  const username=S.username;
  const toL=getLang(_toCode);

  try{
    const res=await fetch(API+"/voice",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({text, language:_toCode, voice, username})
    });

    if(!res.ok){
      let errMsg="Server error ("+res.status+").";
      try{const d=await res.json();if(d.error)errMsg=d.error;}catch{}
      setStatus("ready","TAP TO SPEAK");toast(errMsg);return;
    }

    const data=await res.json();
    if(!data.success){
      setStatus("ready","TAP TO SPEAK");
      toast(data.error||"Something went wrong.");
      return;
    }

    document.getElementById("responseText").textContent=data.text;
    document.getElementById("responseMeta").textContent=
      "🔊 Speaking in "+(data.lang_name||toL.label.replace(/^\S+\s*/,""));
    document.getElementById("responseBox").classList.remove("hidden");
    setStatus("speaking","SPEAKING…");

    const audio=new Audio(data.audio);
    audio.onended=()=>setStatus("ready","TAP TO SPEAK");
    audio.onerror=()=>{setStatus("ready","TAP TO SPEAK");toast("Audio playback failed.");};
    audio.play().catch(()=>{
      setStatus("ready","TAP TO SPEAK");
      toast("Translation done — tap play (browser blocked autoplay).");
    });

  }catch(e){
    console.error("[Voice]",e);
    setStatus("ready","TAP TO SPEAK");
    toast("Connection error. Check your internet.");
  }
}

/* INIT */
window.addEventListener("load",()=>{
  loadVoices();
  document.getElementById("fromLabel").textContent=getLang(_fromCode).label;
  document.getElementById("toLabel").textContent=getLang(_toCode).label;
  showPage(S.ok?"appPage":"welcomePage");
});