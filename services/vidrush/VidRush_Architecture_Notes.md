# VidRush Architecture & Module Guide 🚀

Ye document aapko VidRush ke har ek component ka deep breakdown dega. Isse aapko samajh aayega ki konsi file **kya karti hai**, **kaise karti hai**, aur aap use future mein **kaise advance bana sakte hain**.

---

## 🧠 1. AGENTS (AI Brains)
Ye agents Groq LLM (`llama-3.3-70b-versatile`) ka use karke video ka content aur metadata banate hain.

### `app/agents/director_agent.py`
* **Kaam kya hai:** Video ka overall "Direction" (Vibe) decide karna.
* **Kaise karta hai:** User se Topic leta hai aur JSON format mein output deta hai ki video ki Emotion (fear/tension), Pace (fast/slow), aur Music style kaisa hona chahiye.
* **Advance Kaise Karein:** Isme alag-alag YouTube niches (e.g., Gaming, Horror, Facts) ke mutabiq pre-defined templates feed kar sakte hain taaki direction aur accurate ho.

### `app/agents/hook_agent.py`
* **Kaam kya hai:** Viewer ko pehle 5 second mein rokne ke liye "Hook" likhna.
* **Kaise karta hai:** Maximum retention engineering ka use karke ek 20-word ki aisi line likhta hai jo curiosity, shock, ya tension create kare.
* **Advance Kaise Karein:** A/B testing ke liye ek sath 5 hooks generate kara sakte hain aur Memory System se pucha jaa sakta hai ki konsa hook sabse best perform karega.

### `app/agents/script_agent.py`
* **Kaam kya hai:** Pure video ki script likhna (approx 800 words).
* **Kaise karta hai:** MrBeast aur Reddit Story formats ko follow karte hue `Hook → Buildup → Conflict → Reveal → Ending → CTA` ke sequence mein bolne wali lines (narration) likhta hai.
* **Advance Kaise Karein:** Ise kisi external API (jaise Reddit Praw API) se connect kar sakte hain taaki ye real viral stories utha kar unhe rewrite kare, bajaye apni taraf se fake kahani banane ke.

### `app/agents/emotion_agent.py`
* **Kaam kya hai:** Script ki emotion detect karna taaki visuals ko change kiya ja sake.
* **Kaise karta hai:** Script ka segment padhta hai aur `fear, tension, sadness, excitement, neutral` mein se koi ek emotion chunta hai. Uske basis par subtitles ka color (e.g., red for fear) aur zoom effect bataata hai.
* **Advance Kaise Karein:** Ise frame-by-frame analysis ke liye upgrade kiya ja sakta hai jahan ye har line ke baad alag background music ya sound effect (jaise heart beat, swoosh) trigger kare.

### `app/agents/seo_agent.py`
* **Kaam kya hai:** YouTube upload ke liye metadata banana.
* **Kaise karta hai:** Viral CTR-optimized Title, 500-word description, 30 hashtags, 20 tags aur best upload time generate karta hai.
* **Advance Kaise Karein:** YouTube Data API se connect karke competitors ke tags ko real-time analyze karke best keywords nikalne ki capability add ki ja sakti hai.

### `app/agents/thumbnail_agent.py`
* **Kaam kya hai:** Video ke liye Thumbnail image create karna.
* **Kaise karta hai:** Python ki `Pillow (PIL)` library ka use karke dark background par emotion-based color scheme aur bold text ke sath ek basic image banata hai.
* **Advance Kaise Karein:** Ise `Midjourney` ya `Flux` image generation API se connect karke high-quality hyper-realistic 3D thumbnails banwa sakte hain.

---

## 🎬 2. VISUALS & SUBTITLES (Video Formatting)

### `app/visuals/visual_selector.py`
* **Kaam kya hai:** Background gameplay loops select aur download karna.
* **Kaise karta hai:** Emotion Agent se detect kiye gaye mood ke hisaab se (e.g., Tension = GTA, Excitement = Subway Surfers, Neutral = Minecraft) Archive.org ya Pexels se free videos download karta hai.
* **Advance Kaise Karein:** Local folder mein hazaron loops download karke rakh sakte hain, aur database se randomly pick kara sakte hain taaki API par depend na rehna pade.

### `app/visuals/loop_engine.py`
* **Kaam kya hai:** Raw video ko YouTube Shorts (9:16) format mein fit karna.
* **Kaise karta hai:** FFmpeg filters ka use karke video ko crop karta hai, loop karta hai, thoda blur karta hai aur dark karta hai taaki white text achhe se padha ja sake.
* **Advance Kaise Karein:** Dynamic zooming (video dheere-dheere zoom ho) aur motion blur effects add kiye ja sakte hain.

### `app/subtitles/subtitle_engine.py`
* **Kaam kya hai:** Audio sun kar MrBeast style subtitles banana.
* **Kaise karta hai:** `faster-whisper` AI model se audio transcribe karta hai aur ek `.ass` (Advanced SubStation Alpha) file banata hai. Is file mein word-by-word pop-up (bounce) animations, emojis, aur emotion-based colors code kiye hote hain.
* **Advance Kaise Karein:** Har word par sound effect (pop sound) add karne ke timestamps generate karwa sakte hain.

---

## 🖥️ 3. CORE ENGINES (Main Processing)

### `app/rendering/ffmpeg_renderer.py`
* **Kaam kya hai:** Sab kuch mila kar final `.mp4` video export karna.
* **Kaise karta hai:** Background video, Narration Audio, Background Music, aur `.ass` subtitles ko ek single FFmpeg command mein combine karta hai. Ye MoviePy se 10x fast hai kyunki ye direct GPU/CPU level par render karta hai.
* **Advance Kaise Karein:** Transition effects (crossfade, glitch) aur multi-track audio ducking (jab voice aaye toh music dheema ho jaye) ko aur refine kar sakte hain.

### `app/core/orchestrator.py`
* **Kaam kya hai:** Manager ki tarah sabse kaam karwana.
* **Kaise karta hai:** Phase 1 se lekar 10 tak ke saare agents aur engines ko ek order mein call karta hai (Director -> Hook -> Script -> Visuals -> Subtitles -> Render).
* **Advance Kaise Karein:** Isme error handling itni tagdi kar sakte hain ki agar bich mein internet chala jaye toh system wahi ruk jaye aur baad mein wahi se resume kare.

---

## 🧠 4. MEMORY & ANALYTICS (AI Learning)

### `app/core/memory_system.py`
* **Kaam kya hai:** AI ka dimaag (Database).
* **Kaise karta hai:** `ChromaDB` (Vector database) ka use karke jo bhi Hook ya Script generate hoti hai, use save kar leta hai.
* **Advance Kaise Karein:** Jab YouTube se real analytics aayenge, toh AI khud pichle "failed" hooks ko delete karke sirf "viral" hooks ke pattern par nayi scripts likhna shuru kar dega.

### `app/core/analytics_engine.py`
* **Kaam kya hai:** YouTube videos ki performance track karna.
* **Kaise karta hai:** CTR (Click Through Rate) aur Retention log karta hai.
* **Advance Kaise Karein:** Ise YouTube API Dashboard se sync kar sakte hain, jisse ye auto-pilot par har video ki report card banaye.

---

## ⚙️ 5. AUTOMATION & DEPLOYMENT

### `workers/scheduler.py`
* **Kaam kya hai:** Auto-pilot par video banane ka schedule.
* **Kaise karta hai:** `APScheduler` library se background mein cron-jobs run karta hai (e.g., Har din subah 4 baje naya video generate karo).
* **Advance Kaise Karein:** "Trend Alert" feature add karein jo Twitter/Reddit par trends detect hote hi khud video banana shuru kar de.

### `app/main.py` & `workers/celery_worker.py`
* **Kaam kya hai:** Web Dashboard aur Task Queue.
* **Kaise karta hai:** `FastAPI` aur `WebSockets` se aapko phone par ek dashboard deta hai. Jab aap "Generate" dabate hain, toh kaam `Celery` + `Redis` queue mein chala jata hai, taaki agar aap browser band bhi kar dein, toh background mein render hota rahe.
* **Advance Kaise Karein:** Dashboard mein User Authentication (Login ID/Password) lagayein taaki koi aur aapka system use na kar sake.
