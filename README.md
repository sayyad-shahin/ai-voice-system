# AI Voice Conversation System

## Overview
The AI Voice Conversation System is a web-based application that enables real-time multilingual voice interaction. Users can speak in any language, and the system detects the input language, translates it into a selected output language, improves the text, and returns a spoken audio response.

## Features
- Multilingual voice input support
- Automatic language detection
- Translation to selected language
- AI-based text improvement
- Dynamic voice selection
- Audio response generation
- Login and registration system
- Conversation storage in database
- Interactive voice UI

## Technology Stack

Frontend:
- HTML
- CSS
- JavaScript (Web Speech API)

Backend:
- Python
- Flask
- Flask-CORS

Services:
- Deep Translator
- Langdetect
- ElevenLabs API

Database:
- SQLite

Deployment:
- GitHub
- Render (Backend)
- Netlify (Frontend)

## Project Structure

AI-Voice-Conversation-System/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── init_db.py
│   ├── requirements.txt
│   ├── Procfile
│   ├── routes/
│   │   ├── auth.py
│   │   ├── voice.py
│   ├── services/
│   │   ├── translator.py
│   │   ├── ai_engine.py
│   │   ├── tts.py
│   ├── audio/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│
├── database/
│   ├── database.db
│   ├── schema.sql

## Workflow

1. User logs in or registers
2. User selects language and voice
3. User speaks using the orb
4. Speech converts to text
5. Text is sent to backend
6. Language is detected
7. Text is translated
8. Text is improved
9. Audio is generated
10. Response is returned
11. Data is stored in database

## API Endpoints

POST /auth  
Handles login and registration  

POST /voice  
Processes text and returns audio  

GET /voices  
Fetch available voices  

GET /audio/<filename>  
Serve audio files  

## Setup Instructions

Clone repository:
git clone https://github.com/your-username/ai-voice-system.git
cd ai-voice-system

Backend:
cd backend
pip install -r requirements.txt
python init_db.py
python app.py

Frontend:
cd frontend
python -m http.server 5500

Open:
http://localhost:5500

## Deployment

Backend:
- Render (Gunicorn)

Frontend:
- Netlify

## Limitations

- Response delay due to multiple processing steps
- Translation may be slightly inaccurate for mixed languages
- Depends on external APIs

## Future Improvements

- Use PostgreSQL instead of SQLite
- Add real-time streaming voice
- Improve translation accuracy
- Add conversation history dashboard

## Conclusion

This system demonstrates a complete multilingual voice interaction pipeline with real-time processing, translation, and audio response generation. It follows a modular and scalable architecture suitable for modern AI-based applications.

## Developed by
Shahin Sayyad
