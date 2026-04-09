// =====================
// GLOBAL STATE
// =====================

let currentPage = "welcomePage"
let selectedVoice = "EXAVITQu4vr4xnSDxMaL"

let orb, statusLine, langBtn, langDropdown

// 🌐 LANGUAGE MAP (IMPORTANT)
const LANG_MAP = {
    "1": "en-US",
    "2": "hi-IN",
    "3": "mr-IN",
    "4": "ta-IN",
    "5": "te-IN",
    "6": "gu-IN",
    "7": "bn-IN",
    "8": "kn-IN"
}

// =====================
// PAGE NAVIGATION
// =====================

function switchPage(next){
    document.getElementById(currentPage).classList.remove("active")
    document.getElementById(next).classList.add("active")
    currentPage = next
}

function goToLogin(){
    switchPage("loginPage")
}

// =====================
// LOAD VOICES
// =====================

async function loadVoices(){

    let select = document.getElementById("voiceSelect")

    try{
        let res = await fetch("http://localhost:5000/voices")
        let data = await res.json()

        select.innerHTML = ""

        data.voices.forEach(v=>{
            let option = document.createElement("option")
            option.value = v.id
            option.textContent = v.name
            select.appendChild(option)
        })

        selectedVoice = select.value

    }catch(e){
        select.innerHTML = "<option>Error loading voices</option>"
    }
}

// =====================
// LOGIN
// =====================

async function login(){

    let username = document.getElementById("username").value
    let password = document.getElementById("password").value
    selectedVoice = document.getElementById("voiceSelect").value

    let status = document.getElementById("loginStatus")

    if(!username || !password){
        status.innerText = "Enter credentials"
        return
    }

    try{

        let res = await fetch("http://localhost:5000/auth",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({username,password})
        })

        let data = await res.json()

        if(data.success){
            status.innerText = "Login Successful"
            setTimeout(()=>switchPage("appPage"),800)
        }else{
            status.innerText = "Login Failed"
        }

    }catch{
        status.innerText = "Server error"
    }
}

// =====================
// INIT
// =====================

window.onload = function(){

    loadVoices()

    orb = document.getElementById("orb")
    statusLine = document.getElementById("statusLine")
    langBtn = document.getElementById("langBtn")
    langDropdown = document.getElementById("language")

    langBtn.onclick = ()=>{
        langDropdown.classList.toggle("hidden")
    }

    // 🔥 CHANGE RECOGNITION LANGUAGE DYNAMICALLY
    langDropdown.onchange = ()=>{
        if(recognition){
            let selectedLang = langDropdown.value
            recognition.lang = LANG_MAP[selectedLang] || "en-US"
        }
    }

    orb.onclick = ()=>{
        if(recognition){
            recognition.start()
        }
    }
}

// =====================
// STATE CONTROL
// =====================

function setState(state){

    orb.className = "orb " + state
    statusLine.className = "status-line " + state

    if(state==="listening") statusLine.innerText="LISTENING..."
    else if(state==="processing") statusLine.innerText="PROCESSING..."
    else if(state==="speaking") statusLine.innerText="SPEAKING..."
    else statusLine.innerText="READY"
}

// =====================
// SPEECH RECOGNITION
// =====================

let recognition

if("webkitSpeechRecognition" in window){

    recognition = new webkitSpeechRecognition()

    recognition.lang = "en-US"
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = ()=> setState("listening")

    recognition.onend = ()=> setState("processing")

    recognition.onresult = (e)=>{
        let text = e.results[0][0].transcript
        console.log("User:", text)
        sendVoice(text)
    }

}else{
    alert("Speech recognition not supported")
}

// =====================
// SEND VOICE
// =====================

async function sendVoice(text){

    let lang = document.getElementById("language").value

    try{

        let res = await fetch("http://localhost:5000/voice",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                text:text,
                language:lang,
                voice:selectedVoice
            })
        })

        let data = await res.json()

        setTimeout(()=>{

            setState("speaking")

            let audio = new Audio(data.audio)
            audio.play()

            audio.onended = ()=> setState("ready")

        }, 800)

    }catch(e){
        console.log(e)
        setState("ready")
    }
}