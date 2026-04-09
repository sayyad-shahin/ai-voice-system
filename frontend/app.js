// =====================
// GLOBAL STATE
// =====================

const API_URL = "https://ai-voice-system-j313.onrender.com"

let currentPage = "welcomePage"
let selectedVoice = ""

let orb, statusLine, langBtn, langDropdown

// LANGUAGE MAP
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
// LOAD VOICES (FIXED)
// =====================

async function loadVoices(){

    let select = document.getElementById("voiceSelect")

    try{

        let res = await fetch(API_URL + "/voices")

        if(!res.ok) throw new Error("Server error")

        let data = await res.json()

        select.innerHTML = ""

        // SUPPORT BOTH FORMATS
        let voices = data.voices || data

        voices.forEach(v=>{
            let option = document.createElement("option")
            option.value = v.id
            option.textContent = v.name
            select.appendChild(option)
        })

        selectedVoice = select.value

    }catch(e){
        console.log(e)
        select.innerHTML = "<option>No voices available</option>"
    }
}

// =====================
// LOGIN (FIXED)
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

        status.innerText = "Connecting to server..."

        let res = await fetch(API_URL + "/auth",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({username,password})
        })

        if(!res.ok) throw new Error("Server down")

        let data = await res.json()

        if(data.success){
            status.innerText = "Login Successful"
            setTimeout(()=>switchPage("appPage"),800)
        }else{
            status.innerText = "Login Failed"
        }

    }catch(e){
        console.log(e)
        status.innerText = "Server waking up... try again"
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
    alert("Speech recognition not supported on this device")
}

// =====================
// SEND VOICE (FIXED)
// =====================

async function sendVoice(text){

    let lang = document.getElementById("language").value

    try{

        let res = await fetch(API_URL + "/voice",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                text:text,
                language:lang,
                voice:selectedVoice
            })
        })

        if(!res.ok) throw new Error("Voice API error")

        let data = await res.json()

        setTimeout(()=>{

            setState("speaking")

            if(data.audio){
                let audio = new Audio(data.audio)
                audio.play()
                audio.onended = ()=> setState("ready")
            }else{
                setState("ready")
            }

        }, 600)

    }catch(e){
        console.log(e)
        setState("ready")
    }
}