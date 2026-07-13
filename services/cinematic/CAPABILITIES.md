# VidRush - JARVIS Universal: Capability Report

Yeh ek detailed report hai aapke `movie_generator.py` aur `app.py` software ki current capabilities aur features ki. Software ko completely overhaul kiya gaya hai latest "Reddit Story" YouTube format ke liye!

---

## 1. WHAT THIS SOFTWARE CAN DO
Yeh software ek fully automated "Text-to-Video" pipeline hai jo automatically ek topic ko highly engaging YouTube video mein convert karta hai.

**Features Implemented:**
- **Reddit Story Generation:** Groq LLM ka use karke fake aur highly realistic Reddit stories generate karta hai (e.g. r/TrueOffMyChest style).
- **Background Gameplay Loops:** Archive.org se copyright-free Minecraft/GTA gameplay loops download karke automatically video ke duration ke hisaab se loop karta hai.
- **MrBeast Style Subtitles:** Voiceover ko sunkar exactly word-by-word subtitles screen ke center mein flash hote hain (Whisper AI ki madad se).
- **Automated Web Server:** Aap seedha apne PC par server run karke phone browser se videos generate kar sakte hain.
- **Automated Batching:** Aap script likh kar raat bhar multiple videos automatically queue karke render kar sakte hain.

**Example:**
Agar aap topic dete hain "I Found My Wife's Secret Life", toh AI ek 8-minute lambi story likhega, uski voiceover banayega, background mein Minecraft chalayega, video darken karega, aur bade white fonts mein har ek word screen par animate karega!

---

## 2. VIDEO GENERATION CAPABILITIES
- **Formats Supported:** Vertical ya Horizontal MP4.
- **Quality Options:** 
  - `720p` (1280x720)
  - `1080p` (1920x1080)
  - `4K` (3840x2160)
- **Duration Limits:** Koi strict limit nahi hai. Aap `1` minute (YouTube Shorts) se lekar `8` minutes ya usse zyada (Long-form videos) tak render kar sakte hain. Background video automatically utni der ke liye loop ho jayega.
- **Styles Available:** Currently, poore system ko **"Reddit Story"** format ke liye overhaul kar diya gaya hai. Purane styles (Cinematic Documentary, News Report) CLI options mein hain, par internally execution ab Reddit format mein hi hota hai.

---

## 3. AI INTEGRATIONS
Backend mein kaafi powerful APIs aur libraries connected hain:

| AI Service | Use Case / Role | Working Status |
| :--- | :--- | :--- |
| **Groq (LLaMA-3 70B)** | Fake realistic stories aur YouTube scripts likhne ke liye. | ✅ 100% Working |
| **OpenAI Whisper** | Audio ko transcribe karke exact millisecond word timestamps nikalne ke liye (for subtitles). | ✅ Working locally |
| **Pexels API** | Agar Archive.org down ho, toh gaming ya stock footage nikalne ke liye fallback. | ✅ Working |
| **Replicate (minimax)** | AI cinematic video clips generate karne ke liye (purani pipeline mein). | ⚠️ Hits Rate Limits (Free tier restrictions) |
| **Coqui TTS** | Ultra-realistic human voice generation. | ❌ Broken on Python 3.13 |

---

## 4. AUDIO CAPABILITIES
- **Voice Types:** 
  - Default fallback is `edge-tts` (Voice: "en-US-GuyNeural" - energetic and fast).
  - Framework mein `Coqui TTS (Tacotron2-DDC)` ka code bhi integrated hai (agar purana Python version use karein).
- **Languages Supported:** Edge-TTS ke zariye practically duniya ki koi bhi bhasha (Hindi, English, Spanish) support ki ja sakti hai if configured.
- **Music Options:** Background ke liye Cinematic, Ambient, aur Dramatic music. Background music ko automatically `0.08` volume par duck (kam) kar diya jata hai taaki aawaz double/echo na kare.

---

## 5. VIDEO EFFECTS
- **Subtitles:** Har shabd (word) exact time par center screen mein bada aur bold ho kar aata hai. Font: `DejaVuSans-Bold` (White color, black outline/stroke).
- **Color Grades & Filters:** Background gameplay ko `vfx.MultiplyColor(0.4)` se darken (shade) kiya gaya hai taaki saamne aane wale white words brilliantly pop out karein.
- **Transitions:** Purane documentary style mein `CrossFadeIn` aur `CrossFadeOut` (1.5 seconds) available hain.
- **Zoom Effects:** Image placeholders par "Ken Burns" pan/zoom effect automatically lagta hai.

---

## 6. OUTPUT FORMATS
- **Resolution:** Center-cropped aspect ratio mein output milta hai (perfect for maintaining visual focus).
- **File Format:** High-compatibility `.mp4` file.
- **Encoding Codecs:** `libx264` (Video) aur `aac` (Audio). 
- **File Sizes:** 8-minute ki 1080p video lagbhag 150MB se 300MB ki hoti hai, jisse render aur upload dono kaafi fast hote hain.

---

## 7. CURRENT LIMITATIONS
Yeh kuch known issues hain jo abhi system mein exist karte hain:
1. **Coqui TTS Python Error:** Coqui (`TTS`) package maintainers ne isey abandon kar diya hai. Aapke system par Python 3.13 installed hai, aur Coqui sirf Python 3.11 tak chalta hai. Isliye code mein error aata hai (jisko abhi gracefully catch karke `edge-tts` fallback laga diya gaya hai).
2. **Whisper Rendering Time:** Kyunki aap local CPU par `openai-whisper` run kar rahe hain exact timestamps nikalne ke liye, ek lambi 8-minute ki video ki text alignment process thoda time leti hai.
3. **Style Override:** Complete overhaul ke baad, pipeline by default Reddit format hi output kar rahi hai (chahe aap CLI mein `--style Documentary` pass karein).

---

## 8. COMMANDS TO USE IT
Software ko control karne ke liye aap terminal mein yeh commands use kar sakte hain:

**1. Create a Reddit Story Video (CLI):**
```bash
python3 app.py --topic "I Found My Wife's Secret Life" --duration 8 --quality 1080p
```

**2. Create a Short-Form Video:**
```bash
python3 app.py --topic "A creepy ghost encounter" --duration 1 --quality 720p
```

**3. Run Web Dashboard for Phone/PC Browser:**
```bash
python3 app.py --server
```
*(Yeh command local server start kar degi. Fir aap apne phone mein `http://[PC_IP]:5000` dal kar UI access kar sakte hain!)*
