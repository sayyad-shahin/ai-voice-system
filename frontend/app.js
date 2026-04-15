const API = "https://ai-voice-system-j313.onrender.com"

let currentPage = "welcomePage"
let selectedVoice = "EXAVITQu4vr4xnSDxMaL"

let orb, statusLine, langBtn, langDropdown
let recognition

function switchPage(next){
document.getElementById(currentPage).classList.remove("active")
document.getElementById(next).classList.add("active")
currentPage = next
}

function goToLogin(){
switchPage("loginPage")
}

async function loadVoices(){

let select = document.getElementById("voiceSelect")

try{

// STEP 1: show loading immediately
select.innerHTML = "<option>Loading voices...</option>"

// STEP 2: check cache first
let cached = localStorage.getItem("voices")

if(cached){

let data = JSON.parse(cached)

select.innerHTML = ""

data.voices.forEach(v=>{
let option = document.createElement("option")
option.value = v.id
option.textContent = v.name
select.appendChild(option)
})

selectedVoice = select.value

}

// STEP 3: fetch fresh voices in background
let res = await fetch(API + "/voices")
let data = await res.json()

if(data.success && data.voices){

// update dropdown
select.innerHTML = ""

data.voices.forEach(v=>{
let option = document.createElement("option")
option.value = v.id
option.textContent = v.name
select.appendChild(option)
})

selectedVoice = select.value

// update cache
localStorage.setItem("voices", JSON.stringify(data))

}

}catch(e){

console.log("Voice loading error:", e)
select.innerHTML = "<option>Error loading voices</option>"

}

}

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

let res = await fetch(API + "/auth",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({username,password})
})

let data = await res.json()

if(data.success){

status.innerText = "Login successful"

setTimeout(()=>{
switchPage("appPage")
},800)

}else{

status.innerText = data.error || "Login failed"

}

}catch(e){

console.log("Login error:", e)
status.innerText = "Server error"

}

}

function goToLogin(){
switchPage("loginPage")
loadVoices()


orb = document.getElementById("orb")
statusLine = document.getElementById("statusLine")
langBtn = document.getElementById("langBtn")
langDropdown = document.getElementById("language")

langBtn.onclick = ()=>{
langDropdown.classList.toggle("hidden")
}

orb.onclick = ()=>{

console.log("Orb clicked")

let lang = document.getElementById("language").value

if(recognition){
recognition.lang = getSpeechLang(lang)
recognition.start()
}

}

}

/* STATE CHANGE */

function setState(state){

orb.className = "orb " + state
statusLine.className = "status-line " + state

if(state === "listening") statusLine.innerText = "LISTENING"
else if(state === "processing") statusLine.innerText = "PROCESSING"
else if(state === "speaking") statusLine.innerText = "SPEAKING"
else statusLine.innerText = "READY"

}

/* LANGUAGE MAP */

function getSpeechLang(code){

if(code=="1") return "en-US"
if(code=="2") return "hi-IN"
if(code=="3") return "mr-IN"
if(code=="4") return "ta-IN"
if(code=="5") return "te-IN"
if(code=="6") return "gu-IN"
if(code=="7") return "bn-IN"
if(code=="8") return "kn-IN"

return "en-US"

}

/* SPEECH RECOGNITION */

if("webkitSpeechRecognition" in window){

recognition = new webkitSpeechRecognition()

recognition.continuous = false
recognition.interimResults = false

recognition.onstart = ()=>{
console.log("Listening started")
setState("listening")
}

recognition.onresult = (event)=>{

let text = event.results[0][0].transcript

console.log("User said:", text)

sendVoice(text)

}

recognition.onerror = (event)=>{
console.log("Speech recognition error:", event.error)
setState("ready")
}

recognition.onend = ()=>{
console.log("Listening ended")
setState("processing")
}

}else{

alert("Speech recognition not supported")

}

/* SEND TEXT TO BACKEND */

async function sendVoice(text){

let lang = document.getElementById("language").value

try{

let res = await fetch(API + "/voice",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
text:text,
language:lang,
voice:selectedVoice
})
})

let data = await res.json()

if(!data.success){

console.log("API error:", data.error)
setState("ready")
return

}


setState("speaking")

if(!data.audio){

console.log("Audio missing")
setState("ready")
return

}

let audio = new Audio(data.audio)

audio.play()

audio.onended = ()=>{
setState("ready")
}

audio.onerror = ()=>{
console.log("Audio failed")
setState("ready")
}


}catch(e){

console.log("Voice request failed:", e)
setState("ready")

}

}