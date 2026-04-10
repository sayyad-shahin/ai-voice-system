const BASE_URL = "https://ai-voice-system-j313.onrender.com"

// =====================
// GLOBAL STATE
// =====================
let currentPage = "welcomePage"
let selectedVoice = "EXAVITQu4vr4xnSDxMaL"

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
// PAGE SWITCHING (FIXED)
// =====================
function switchPage(pageId){
    document.querySelectorAll(".page").forEach(p => p.style.display = "none")
    document.getElementById(pageId).style.display = "block"
    currentPage = pageId
}

function goToLogin(){
    switchPage("loginPage")
}

// =====================
// STATE HANDLER
// =====================
function setState(state){
    console.log("STATE:", state)

    let status = document.getElementById("statusLine")
    if(!status) return

    if(state === "speaking"){
        status.innerText = "Speaking..."
    } else if(state === "listening"){
        status.innerText = "Listening..."
    } else {
        status.innerText = "Ready"
    }
}

// =====================
// WAKE RENDER SERVER (IMPORTANT)
// =====================
async function wakeServer(){
    try{
        await fetch(BASE_URL)
    }catch(e){
        console.log("Wake failed (normal on first try)")
    }
}

// =====================
// LOAD VOICES (FIXED)
// =====================
async function loadVoices(){

    let select = document.getElementById("voiceSelect")

    try{
        await wakeServer()  //  VERY IMPORTANT

        let res = await fetch(`${BASE_URL}/voices`)

        if(!res.ok){
            throw new Error("Server not responding")
        }

        let data = await res.json()
        console.log("Voices API:", data)

        select.innerHTML = ""

        if(!data.voices || data.voices.length === 0){
            select.innerHTML = "<option>No voices found</option>"
            return
        }

        data.voices.forEach(v=>{
            let option = document.createElement("option")
            option.value = v.id
            option.textContent = v.name
            select.appendChild(option)
        })

        selectedVoice = select.value

    }catch(e){
        console.log("VOICE ERROR:", e)
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

    try{
        await wakeServer()

        let res = await fetch(`${BASE_URL}/auth`,{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({username,password})
        })

        let data = await res.json()

        if(data.success){
            status.innerText = "Login Successful"
            setTimeout(()=>switchPage("appPage"),800)
        }else{
            status.innerText = data.error || "Login Failed"
        }

    }catch(e){
        console.log(e)
        status.innerText = "Server error"
    }
}

// =====================
// SEND VOICE (FULL FIX)
// =====================
async function sendVoice(text){

    let lang = document.getElementById("language").value

    try{
        setState("listening")

        await wakeServer()  // 👈 FIX RENDER DELAY

        let res = await fetch(`${BASE_URL}/voice`,{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                text: text,
                language: lang,
                voice: selectedVoice
            })
        })

        let data = await res.json()
        console.log("VOICE RESPONSE:", data)

        if(!data.success){
            console.log("API ERROR:", data.error)
            setState("ready")
            return
        }

        if(!data.audio){
            console.log("No audio received")
            setState("ready")
            return
        }

        setTimeout(()=>{
            setState("speaking")

            let audio = new Audio()

            // FIX: handle full URL or relative path
            audio.src = data.audio.startsWith("http")
                ? data.audio
                : `${BASE_URL}${data.audio}`

            audio.play().catch(err=>{
                console.log("Audio play error:", err)
                setState("ready")
            })

            audio.onended = ()=>{
                setState("ready")
            }

        },800)

    }catch(e){
        console.log("SEND VOICE ERROR:", e)
        setState("ready")
    }
}

// =====================
// AUTO LOAD VOICES ON START
// =====================
window.onload = ()=>{
    loadVoices()
}