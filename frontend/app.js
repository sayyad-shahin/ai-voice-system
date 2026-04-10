const BASE_URL = "https://ai-voice-system-j313.onrender.com"

// =====================
// GLOBAL STATE
// =====================
let currentPage = "welcomePage"
let selectedVoice = "EXAVITQu4vr4xnSDxMaL"

let orb, statusLine, langBtn, langDropdown

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
// LOAD VOICES
// =====================
async function loadVoices(){

    let select = document.getElementById("voiceSelect")

    try{
        let res = await fetch(`${BASE_URL}/voices`)
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
        console.log(e)
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
            status.innerText = "Login Failed"
        }

    }catch{
        status.innerText = "Server error"
    }
}

// =====================
// SEND VOICE
// =====================
async function sendVoice(text){

    let lang = document.getElementById("language").value

    try{
        let res = await fetch(`${BASE_URL}/voice`,{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                text:text,
                language:lang,
                voice:selectedVoice
            })
        })

        let data = await res.json()

        if(!data.audio){
            setState("ready")
            return
        }

        setTimeout(()=>{
            setState("speaking")
            let audio = new Audio(data.audio)
            audio.play()
            audio.onended = ()=> setState("ready")
        },800)

    }catch(e){
        console.log(e)
        setState("ready")
    }
}