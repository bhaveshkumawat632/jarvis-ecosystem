/* ==========================================================================
   Jarvis Universal Frontend Controller
   Logic: Navigation, API Requests, Polling, Gallery Rendering, and UX
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // --- BOOT SEQUENCE LOGIC ---
    const bootOverlay = document.getElementById("boot-sequence-overlay");
    const bootLog = document.getElementById("boot-log-text");
    const bootMessages = [
        "INITIALIZING KERNEL...",
        "LOADING NEURAL NETWORKS...",
        "CONNECTING TO GROQ CLUSTER...",
        "ESTABLISHING SATELLITE UPLINK...",
        "BYPASSING SECURITY PROTOCOLS...",
        "WELCOME, DIRECTOR."
    ];
    let bootIndex = 0;
    
    // Play sci-fi startup sound
    const audioCtxBoot = new (window.AudioContext || window.webkitAudioContext)();
    function playStartupSound() {
        if(audioCtxBoot.state === 'suspended') audioCtxBoot.resume();
        const osc = audioCtxBoot.createOscillator();
        const gain = audioCtxBoot.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(200, audioCtxBoot.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1000, audioCtxBoot.currentTime + 1.5);
        gain.gain.setValueAtTime(0, audioCtxBoot.currentTime);
        gain.gain.linearRampToValueAtTime(0.1, audioCtxBoot.currentTime + 0.5);
        gain.gain.linearRampToValueAtTime(0, audioCtxBoot.currentTime + 2.0);
        osc.connect(gain);
        gain.connect(audioCtxBoot.destination);
        osc.start();
        osc.stop(audioCtxBoot.currentTime + 2.0);
    }

    if(bootOverlay) {
        // We only play sound on click because of browser auto-play policies.
        // Wait, the user has to click to interact, but we can animate text anyway.
        const bootInterval = setInterval(() => {
            if (bootIndex < bootMessages.length) {
                bootLog.textContent = bootMessages[bootIndex];
                bootIndex++;
            } else {
                clearInterval(bootInterval);
                setTimeout(() => {
                    bootOverlay.style.opacity = '0';
                    setTimeout(() => bootOverlay.style.visibility = 'hidden', 1000);
                    jarvisSpeak("Welcome back, Director. The orchestration engine is ready.");
                }, 500);
            }
        }, 600); // 600ms per message
    }

    // --- CUSTOM CURSOR ---
    const cursor = document.querySelector('.custom-cursor');
    const follower = document.querySelector('.custom-cursor-follower');
    let mouseX = 0, mouseY = 0, followerX = 0, followerY = 0;
    
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        cursor.style.left = mouseX + 'px';
        cursor.style.top = mouseY + 'px';
    });
    
    function animateFollower() {
        followerX += (mouseX - followerX) * 0.15;
        followerY += (mouseY - followerY) * 0.15;
        follower.style.left = followerX + 'px';
        follower.style.top = followerY + 'px';
        requestAnimationFrame(animateFollower);
    }
    animateFollower();
    
    // --- UI SOUND EFFECTS (Web Audio API) ---
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    
    function playHoverSound() {
        if(audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1200, audioCtx.currentTime + 0.05);
        gainNode.gain.setValueAtTime(0.02, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);
        osc.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.05);
    }
    
    function playClickSound() {
        if(audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(150, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(40, audioCtx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.1);
        osc.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.1);
    }

    // --- JARVIS VOICE SYNTHESIS (Text-to-Speech) ---
    function jarvisSpeak(text) {
        if ('speechSynthesis' in window) {
            const synth = window.speechSynthesis;
            // Cancel any ongoing speech
            synth.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 0.9; // Slightly lower pitch for AI feel
            utterance.lang = 'en-US';
            
            // Try to find a good AI voice (like Microsoft Guy or Google UK English)
            const voices = synth.getVoices();
            let aiVoice = voices.find(v => v.name.includes('Google UK English Male') || v.name.includes('Microsoft Mark') || v.name.includes('Daniel'));
            if(aiVoice) utterance.voice = aiVoice;
            
            synth.speak(utterance);
        }
    }

    // --- WEBCAM UPLINK & AI FACE TRACKING ---
    const webcamFeed = document.getElementById("webcam-feed");
    const faceCanvas = document.getElementById("face-tracking-canvas");
    
    if (webcamFeed && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then((stream) => {
                webcamFeed.srcObject = stream;
                
                // Initialize Face Tracking once video starts playing
                webcamFeed.addEventListener('play', () => {
                    if(window.tracking && faceCanvas) {
                        faceCanvas.width = webcamFeed.offsetWidth;
                        faceCanvas.height = webcamFeed.offsetHeight;
                        const context = faceCanvas.getContext('2d');
                        
                        const tracker = new tracking.ObjectTracker('face');
                        tracker.setInitialScale(4);
                        tracker.setStepSize(2);
                        tracker.setEdgesDensity(0.1);
                        
                        tracking.track('#webcam-feed', tracker);
                        
                        tracker.on('track', function(event) {
                            context.clearRect(0, 0, faceCanvas.width, faceCanvas.height);
                            
                            // Draw cyan targeting box over faces
                            event.data.forEach(function(rect) {
                                context.strokeStyle = '#22d3ee';
                                context.lineWidth = 2;
                                context.strokeRect(rect.x, rect.y, rect.width, rect.height);
                                
                                // Draw targeting crosshairs
                                context.fillStyle = '#22d3ee';
                                context.font = '10px Fira Code';
                                context.fillText('TARGET ACQUIRED', rect.x, rect.y - 5);
                                
                                // Corners
                                const cL = 10; // corner length
                                context.beginPath();
                                context.moveTo(rect.x, rect.y + cL); context.lineTo(rect.x, rect.y); context.lineTo(rect.x + cL, rect.y);
                                context.moveTo(rect.x + rect.width - cL, rect.y); context.lineTo(rect.x + rect.width, rect.y); context.lineTo(rect.x + rect.width, rect.y + cL);
                                context.moveTo(rect.x, rect.y + rect.height - cL); context.lineTo(rect.x, rect.y + rect.height); context.lineTo(rect.x + cL, rect.y + rect.height);
                                context.moveTo(rect.x + rect.width - cL, rect.y + rect.height); context.lineTo(rect.x + rect.width, rect.y + rect.height); context.lineTo(rect.x + rect.width, rect.y + rect.height - cL);
                                context.stroke();
                            });
                        });
                    }
                });
            })
            .catch((err) => {
                console.log("Webcam uplink failed:", err);
                webcamFeed.parentElement.innerHTML += "<div style='position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:red; font-size:10px; text-align:center;'>NO SIGNAL</div>";
            });
    }

    // --- LIVE TELEMETRY GRAPH (CPU/RAM) ---
    const ctxTelemetry = document.getElementById('telemetryChart');
    if(ctxTelemetry) {
        const telemetryChart = new Chart(ctxTelemetry, {
            type: 'line',
            data: {
                labels: Array(20).fill(''),
                datasets: [
                    { label: 'CPU %', borderColor: '#22d3ee', backgroundColor: 'rgba(34,211,238,0.1)', borderWidth: 1, pointRadius: 0, fill: true, data: Array(20).fill(0) },
                    { label: 'RAM %', borderColor: '#a855f7', backgroundColor: 'rgba(168,85,247,0.1)', borderWidth: 1, pointRadius: 0, fill: true, data: Array(20).fill(0) }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: { min: 0, max: 100, display: false }
                }
            }
        });

        setInterval(async () => {
            try {
                const res = await fetch('/api/system/stats');
                if(!res.ok) return;
                const data = await res.json();
                
                telemetryChart.data.datasets[0].data.push(data.cpu);
                telemetryChart.data.datasets[0].data.shift();
                
                telemetryChart.data.datasets[1].data.push(data.ram);
                telemetryChart.data.datasets[1].data.shift();
                
                telemetryChart.update();
            } catch(e) {}
        }, 2000);
    }

    // --- GEO-SATELLITE UPLINK & CLIMATE ---
    const geoLocEl = document.getElementById("geo-location");
    const geoWeatherEl = document.getElementById("geo-weather");
    
    if (geoLocEl && geoWeatherEl) {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(async (pos) => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                geoLocEl.innerHTML = `LAT: ${lat.toFixed(4)}<br>LON: ${lon.toFixed(4)}`;
                
                // Fetch Weather from Open-Meteo API (No Auth required)
                try {
                    const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`);
                    const data = await res.json();
                    if(data.current_weather) {
                        const temp = data.current_weather.temperature;
                        const wind = data.current_weather.windspeed;
                        geoWeatherEl.innerHTML = `TEMP: ${temp}°C<br>WIND: ${wind} km/h`;
                    } else {
                        geoWeatherEl.textContent = "CLIMATE DATA UNAVAILABLE";
                    }
                } catch(e) {
                    geoWeatherEl.textContent = "UPLINK FAILED";
                }
            }, (err) => {
                geoLocEl.textContent = "LOC OBFUSCATED";
                geoWeatherEl.textContent = "RADAR JAMMED";
            });
        } else {
            geoLocEl.textContent = "GPS OFFLINE";
            geoWeatherEl.textContent = "NO SENSORS";
        }
    }

    // Hover effects for cursor and sounds
    const interactables = document.querySelectorAll('a, button, input, textarea, select, .nav-item');
    interactables.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.classList.add('hovering');
            follower.classList.add('hovering');
            playHoverSound();
        });
        el.addEventListener('mouseleave', () => {
            cursor.classList.remove('hovering');
            follower.classList.remove('hovering');
        });
        el.addEventListener('click', () => {
            playClickSound();
            // Pulse effect on cursor
            follower.style.transform = "translate(-50%, -50%) scale(1.5)";
            setTimeout(() => { follower.style.transform = "translate(-50%, -50%) scale(1)"; }, 150);
        });
    });

    // --- 3D TILT EFFECT ON CARDS ---
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -5;
            const rotateY = ((x - centerX) / centerX) * 5;
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
        });
    });

    // --- PARTICLE NETWORK CANVAS ---
    const canvas = document.getElementById('particle-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let width, height;
        let particles = [];
        
        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize);
        resize();
        
        class Particle {
            constructor() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.vx = (Math.random() - 0.5) * 0.5;
                this.vy = (Math.random() - 0.5) * 0.5;
                this.radius = Math.random() * 1.5 + 0.5;
            }
            update() {
                this.x += this.vx;
                this.y += this.vy;
                if (this.x < 0 || this.x > width) this.vx = -this.vx;
                if (this.y < 0 || this.y > height) this.vy = -this.vy;
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(34, 211, 238, 0.4)';
                ctx.fill();
            }
        }
        
        for(let i=0; i<80; i++) particles.push(new Particle());
        
        function animateParticles() {
            ctx.clearRect(0, 0, width, height);
            particles.forEach(p => {
                p.update();
                p.draw();
            });
            // Draw lines between close particles
            for(let i=0; i<particles.length; i++){
                for(let j=i+1; j<particles.length; j++){
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = dx*dx + dy*dy;
                    if(dist < 15000) {
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(168, 85, 247, ${1 - dist/15000})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }
            requestAnimationFrame(animateParticles);
        }
        animateParticles();
    }

    // --- VOICE RECOGNITION (Speech-to-Text) ---
    const dictationBtn = document.getElementById('voice-dictate-btn');
    const ideaInput = document.getElementById('idea-input');
    
    if (dictationBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        let isListening = false;
        
        dictationBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (!isListening) {
                recognition.start();
                isListening = true;
                dictationBtn.classList.add('listening-animation');
                playClickSound(); // High-tech blip
                if(!ideaInput.value.endsWith(' ')) ideaInput.value += ' ';
            } else {
                recognition.stop();
                isListening = false;
                dictationBtn.classList.remove('listening-animation');
                playClickSound();
            }
        });
        
        recognition.onresult = (event) => {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + ' ';
                }
            }
            if (finalTranscript) {
                ideaInput.value += finalTranscript;
            }
        };
        
        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            isListening = false;
            dictationBtn.classList.remove('listening-animation');
        };
    } else if(dictationBtn) {
        dictationBtn.style.display = 'none'; // Hide if not supported
    }

    // --- CONTINUOUS WAKE WORD UPLINK (HEY JARVIS) ---
    const uplinkToggle = document.getElementById("voice-uplink-toggle");
    const uplinkStatus = document.getElementById("uplink-status");
    let bgRecognition = null;
    let isUplinkActive = false;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        bgRecognition = new SpeechRecognition();
        bgRecognition.continuous = true;
        bgRecognition.interimResults = false;
        bgRecognition.lang = 'en-US';

        bgRecognition.onresult = (event) => {
            const last = event.results.length - 1;
            const transcript = event.results[last][0].transcript.toLowerCase().trim();
            console.log("Heard:", transcript);

            if (transcript.includes("jarvis")) {
                playHoverSound();
                
                // Voice Commands
                if (transcript.includes("protocol zero")) {
                    jarvisSpeak("Voice authorization accepted. Protocol Zero initiated.");
                    triggerProtocolZero();
                } 
                else if (transcript.includes("matrix")) {
                    jarvisSpeak("Voice authorization accepted. Entering the matrix.");
                    document.body.style.fontFamily = "'Fira Code', monospace";
                    document.body.style.color = "#00ff00";
                    document.querySelector('.grid-background').style.backgroundImage = "none";
                    document.querySelector('.grid-background').style.backgroundColor = "rgba(0,255,0,0.05)";
                }
                else if (transcript.includes("create a movie") || transcript.includes("make a movie")) {
                    jarvisSpeak("Right away, Director. Orchestrating your movie.");
                    ideaInput.value = transcript;
                    document.getElementById("movie-form").dispatchEvent(new Event('submit'));
                }
                else {
                    jarvisSpeak("At your service, Director.");
                    // Send to chat
                    chatWidget.classList.add("open");
                    chatToggleBtn.classList.add("hidden");
                    const actualQuery = transcript.replace("jarvis", "").trim();
                    if(actualQuery.length > 2) {
                        chatInput.value = actualQuery;
                        sendChatMessage();
                    }
                }
            }
        };

        bgRecognition.onerror = (e) => {
            if(isUplinkActive) setTimeout(() => { try{ bgRecognition.start(); }catch(e){} }, 1000);
        };
        bgRecognition.onend = () => {
            if(isUplinkActive) setTimeout(() => { try{ bgRecognition.start(); }catch(e){} }, 1000);
        };
    }

    if (uplinkToggle && bgRecognition) {
        uplinkToggle.addEventListener("click", () => {
            isUplinkActive = !isUplinkActive;
            if (isUplinkActive) {
                uplinkStatus.style.backgroundColor = "#34d399";
                uplinkStatus.style.boxShadow = "0 0 10px #34d399";
                jarvisSpeak("Voice Uplink established. I am listening, Director.");
                try{ bgRecognition.start(); }catch(e){}
            } else {
                uplinkStatus.style.backgroundColor = "#f87171";
                uplinkStatus.style.boxShadow = "0 0 8px #f87171";
                jarvisSpeak("Voice Uplink disconnected.");
                bgRecognition.stop();
            }
            playClickSound();
        });
    }

    // Navigation Tabs
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");

    // --- CHAT WIDGET LOGIC ---
    const chatToggleBtn = document.getElementById("chat-toggle-btn");
    const chatCloseBtn = document.getElementById("chat-close-btn");
    const chatWidget = document.getElementById("jarvis-chat-widget");
    const chatInput = document.getElementById("chat-input");
    const chatSendBtn = document.getElementById("chat-send-btn");
    const chatMessages = document.getElementById("chat-messages");

    function addChatMessage(text, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `chat-msg ${sender}`;
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        if(sender === 'jarvis') {
            jarvisSpeak(text);
        }
    }

    chatToggleBtn.addEventListener("click", () => {
        chatWidget.classList.add("open");
        chatToggleBtn.classList.add("hidden");
        playClickSound();
        chatInput.focus();
    });

    chatCloseBtn.addEventListener("click", () => {
        chatWidget.classList.remove("open");
        chatToggleBtn.classList.remove("hidden");
        playClickSound();
    });

    async function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text) return;
        addChatMessage(text, "user");
        chatInput.value = "";
        
        // EASTER EGG: Protocol Zero
        if (text.toLowerCase().includes("protocol zero")) {
            jarvisSpeak("Warning. Protocol Zero initiated. System override in progress.");
            addChatMessage("WARNING: SYSTEM OVERRIDE INITIATED.", "jarvis");
            triggerProtocolZero();
            return;
        }

        // EASTER EGG: Matrix Mode
        if (text.toLowerCase().includes("matrix")) {
            jarvisSpeak("Entering the Matrix, Director.");
            addChatMessage("Matrix mode enabled.", "jarvis");
            document.body.style.fontFamily = "'Fira Code', monospace";
            document.body.style.color = "#00ff00";
            document.querySelector('.grid-background').style.backgroundImage = "none";
            document.querySelector('.grid-background').style.backgroundColor = "rgba(0,255,0,0.05)";
            return;
        }

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            addChatMessage(data.reply, "jarvis");
        } catch (e) {
            addChatMessage("Error: Cannot reach communication array.", "jarvis");
        }
    }

    function triggerProtocolZero() {
        // Red Glitch Screen
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0'; overlay.style.left = '0';
        overlay.style.width = '100vw'; overlay.style.height = '100vh';
        overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.4)';
        overlay.style.zIndex = '99999';
        overlay.style.pointerEvents = 'none';
        overlay.style.animation = 'glitch-flash 0.5s infinite alternate';
        overlay.innerHTML = `<h1 style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:white; font-family:'Space Grotesk'; font-size:100px; text-shadow: 0 0 20px red;">SYSTEM OVERRIDE</h1>`;
        document.body.appendChild(overlay);

        // Siren Sound
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if(audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(400, audioCtx.currentTime);
        for(let i=0; i<10; i++){
            osc.frequency.linearRampToValueAtTime(800, audioCtx.currentTime + i + 0.5);
            osc.frequency.linearRampToValueAtTime(400, audioCtx.currentTime + i + 1);
        }
        gain.gain.value = 0.1;
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 10);

        setTimeout(() => {
            overlay.remove();
            jarvisSpeak("System restored. My apologies, Director.");
        }, 10000);
    }

    chatSendBtn.addEventListener("click", () => {
        playClickSound();
        sendChatMessage();
    });
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            playClickSound();
            sendChatMessage();
        }
    });
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");

            // Update Nav active state
            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");

            // Update Tab Panes visibility
            tabPanes.forEach(pane => pane.classList.remove("active"));
            document.getElementById(`tab-${tabId}`).classList.add("active");

            // Update Titles
            if (tabId === "create") {
                pageTitle.textContent = "Generate Masterpiece";
                pageSubtitle.textContent = "Orchestrate AI models to build a cinematic animated short movie.";
            } else if (tabId === "gallery") {
                pageTitle.textContent = "Studio Gallery";
                pageSubtitle.textContent = "Browse, preview, and download your compiled animated movies.";
                loadGallery();
            } else if (tabId === "settings") {
                pageTitle.textContent = "Engine Preferences";
                pageSubtitle.textContent = "Configure APIs, models, directories, and hardware options.";
            }
        });
    });

    // Form Elements & Submission
    const movieForm = document.getElementById("movie-form");
    const ideaInput = document.getElementById("idea-input");
    const youtubeInput = document.getElementById("youtube-input");
    const voiceSelect = document.getElementById("voice-select");
    const musicSelect = document.getElementById("music-select");
    const submitBtn = document.getElementById("submit-btn");

    // Monitor Panel Elements
    const monitorPanel = document.getElementById("monitor-panel");
    const creationLayout = document.querySelector(".creation-layout");
    const monitorStatus = document.getElementById("monitor-status");
    const progressCircle = document.querySelector(".progress-ring__circle");
    const progressVal = document.getElementById("progress-val");
    const logView = document.getElementById("log-view");
    
    // Steps
    const stepItems = {
        "script": document.getElementById("step-script"),
        "voiceover": document.getElementById("step-voiceover"),
        "visuals": document.getElementById("step-visuals"),
        "audio_mix": document.getElementById("step-audio_mix"),
        "compiling": document.getElementById("step-compiling")
    };

    let pollingInterval = null;
    let currentProjectId = null;
    let loggedLines = new Set();

    // Circular Progress Math
    const radius = progressCircle.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;
    progressCircle.style.strokeDasharray = `${circumference} ${circumference}`;
    progressCircle.style.strokeDashoffset = circumference;

    function setProgress(percent) {
        const offset = circumference - (percent / 100) * circumference;
        progressCircle.style.strokeDashoffset = offset;
        progressVal.textContent = `${Math.round(percent)}%`;
    }

    // Logger Utility
    function appendLog(message, type = "") {
        // Prevent duplicate logging
        if (loggedLines.has(message)) return;
        loggedLines.add(message);

        const line = document.createElement("div");
        line.className = "log-line";
        if (type) line.classList.add(`text-${type}`);
        line.textContent = `> ${message}`;
        logView.appendChild(line);
        logView.scrollTop = logView.scrollHeight;
    }

    // Start Generation Form Submit
    movieForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        jarvisSpeak("Orchestrating movie pipeline. Please hold.");

        const idea = ideaInput.value.trim();
        const youtubeUrl = youtubeInput.value.trim();
        const voice = voiceSelect.value;
        const musicMood = musicSelect.value;

        if (!idea) return;

        // Reset monitor states
        loggedLines.clear();
        logView.innerHTML = "";
        setProgress(0);
        Object.values(stepItems).forEach(item => {
            item.classList.remove("active", "completed");
        });
        
        appendLog("Initializing Jarvis Universal Pipeline...", "cyan");
        appendLog(`Idea: "${idea.substring(0, 60)}..."`);
        if (youtubeUrl) appendLog(`YouTube reference: ${youtubeUrl}`);
        appendLog(`Voice profile: ${voice} | Soundtrack: ${musicMood}`);

        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.querySelector("span").textContent = "hourglass_empty";
        submitBtn.querySelector("span").classList.add("spinner");

        // Display monitor panel
        monitorPanel.classList.remove("hidden");
        creationLayout.classList.add("creation-layout", "with-monitor");
        monitorStatus.textContent = "Orchestrating";
        monitorStatus.className = "badge badge-pulse";

        try {
            const response = await fetch("/api/projects", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    idea,
                    youtube_url: youtubeUrl,
                    voice,
                    music_mood: musicMood,
                    openrouter_key: localStorage.getItem("jarvis_openrouter_key") || "",
                    luma_key: localStorage.getItem("jarvis_luma_key") || "",
                    meshy_key: localStorage.getItem("jarvis_meshy_key") || "",
                    tripo3d_key: localStorage.getItem("jarvis_tripo3d_key") || "",
                    hf_token: localStorage.getItem("jarvis_hf_token") || ""
                })
            });

            let responseData = null;
            let parseSuccess = false;
            try {
                const text = await response.text();
                responseData = JSON.parse(text);
                parseSuccess = true;
            } catch (jsonErr) {
                console.error("Response is not JSON:", jsonErr);
            }

            if (!response.ok) {
                const errMsg = (responseData && responseData.error) || `HTTP Error ${response.status}: ${response.statusText}`;
                throw new Error(errMsg);
            }

            if (!parseSuccess || !responseData) {
                throw new Error("Invalid response received from server.");
            }

            currentProjectId = responseData.project_id;
            appendLog(`Job successfully queued. Project ID: ${currentProjectId}`, "green");

            // Start Polling progress
            startPollingProgress(currentProjectId);

        } catch (error) {
            appendLog(`Error: ${error.message}`, "red");
            showToast(error.message);
            resetSubmitBtn();
        }
    });

    function resetSubmitBtn() {
        submitBtn.disabled = false;
        submitBtn.querySelector("span").textContent = "movie_creation";
        submitBtn.querySelector("span").classList.remove("spinner");
    }

    function startPollingProgress(projectId) {
        if (pollingInterval) clearInterval(pollingInterval);
        
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/projects/${projectId}/progress`);
                if (!response.ok) return;

                const contentType = response.headers.get("content-type");
                if (!contentType || !contentType.includes("application/json")) {
                    console.warn("Expected JSON progress, got:", contentType);
                    return;
                }

                const progress = await response.json();
                
                // Update percentage and message
                setProgress(progress.percentage);
                appendLog(progress.message);

                // Update steps UI
                const currentStep = progress.step;
                const status = progress.status;

                // Mark previous steps as completed
                let foundCurrent = false;
                const stepOrder = ["script", "voiceover", "visuals", "audio_mix", "compiling"];
                
                stepOrder.forEach(step => {
                    const element = stepItems[step];
                    if (!element) return;

                    if (step === currentStep) {
                        foundCurrent = true;
                        if (status === "failed") {
                            element.classList.remove("active");
                            element.classList.add("failed");
                        } else if (status === "completed") {
                            element.classList.remove("active");
                            element.classList.add("completed");
                        } else {
                            element.classList.add("active");
                        }
                    } else if (!foundCurrent) {
                        element.classList.remove("active");
                        element.classList.add("completed");
                    } else {
                        element.classList.remove("active", "completed");
                    }
                });

                // Check terminal status
                if (status === "completed") {
                    clearInterval(pollingInterval);
                    appendLog("Pipeline Finished Successfully! Masterpiece generated.", "green");
                    showToast("Movie generated successfully!");
                    
                    // Transition back
                    setTimeout(() => {
                        resetSubmitBtn();
                        // Clear inputs
                        ideaInput.value = "";
                        youtubeInput.value = "";
                        monitorPanel.classList.add("hidden");
                        creationLayout.classList.remove("with-monitor");
                        
                        // Switch to gallery tab
                        const galleryTab = document.querySelector("[data-tab='gallery']");
                        if (galleryTab) {
                            galleryTab.click();
                            loadGallery(projectId); // Auto-play the new project
                        }
                    }, 2500);

                } else if (status === "failed") {
                    clearInterval(pollingInterval);
                    appendLog(`Pipeline crashed: ${progress.message}`, "red");
                    showToast("Movie generation failed!");
                    monitorStatus.textContent = "Crashed";
                    monitorStatus.className = "badge text-red";
                    resetSubmitBtn();
                }

            } catch (err) {
                console.error("Error polling progress:", err);
            }
        }, 1200);
    }

    // Gallery Elements
    const galleryGrid = document.getElementById("gallery-grid");
    const noProjectsMsg = document.getElementById("no-projects-msg");
    const activePlayerCard = document.getElementById("active-player-card");
    const galleryVideo = document.getElementById("gallery-video");
    const playerTitle = document.getElementById("player-title");
    const playerDuration = document.getElementById("player-duration");
    const playerDesc = document.getElementById("player-desc");
    const playerDownload = document.getElementById("player-download");
    const playerDeleteBtn = document.getElementById("player-delete-btn");
    const refreshGalleryBtn = document.getElementById("refresh-gallery-btn");

    let activeMovieId = null;

    async function loadGallery(autoPlayId = null) {
        try {
            const response = await fetch("/api/projects");
            if (!response.ok) throw new Error("Failed to fetch gallery.");
            
            const projects = await response.json();
            
            if (projects.length === 0) {
                galleryGrid.innerHTML = "";
                galleryGrid.appendChild(noProjectsMsg);
                noProjectsMsg.classList.remove("hidden");
                activePlayerCard.classList.add("hidden");
                return;
            }

            noProjectsMsg.classList.add("hidden");
            galleryGrid.innerHTML = "";

            projects.forEach(project => {
                const card = document.createElement("div");
                card.className = "movie-card";
                card.setAttribute("data-id", project.id);
                
                // Set poster thumbnail (frame_0 or fallback poster.jpg)
                const posterUrl = project.poster_file ? `${project.poster_file}?t=${Date.now()}` : "";
                
                card.innerHTML = `
                    <div class="movie-card-thumb" style="background-image: url('${posterUrl}')">
                        <div class="movie-card-play">
                            <span class="material-symbols-outlined">play_arrow</span>
                        </div>
                    </div>
                    <div class="movie-card-info">
                        <div class="movie-card-title">${project.title || "Untitled Project"}</div>
                        <div class="movie-card-meta">
                            <span>Voice: ${project.voice.split("-")[2] || "Standard"}</span>
                            <span class="movie-card-status ${project.status}">${project.status}</span>
                        </div>
                    </div>
                `;

                card.addEventListener("click", () => {
                    if (project.status === "completed") {
                        playMovie(project);
                    } else if (project.status === "processing") {
                        showToast("Movie is still rendering. Check 'Create Movie' for progress.");
                        // Switch to create tab to view progress
                        document.querySelector("[data-tab='create']").click();
                    } else {
                        showToast("Movie rendering failed.");
                    }
                });

                galleryGrid.appendChild(card);
            });

            // Automatically play new project if provided
            if (autoPlayId) {
                const targetProject = projects.find(p => p.id === autoPlayId);
                if (targetProject && targetProject.status === "completed") {
                    playMovie(targetProject);
                }
            } else if (projects.length > 0 && activePlayerCard.classList.contains("hidden")) {
                // Play the first completed project by default
                const firstCompleted = projects.find(p => p.status === "completed");
                if (firstCompleted) playMovie(firstCompleted);
            }

        } catch (error) {
            console.error("Gallery loading error:", error);
            showToast("Failed to load studio gallery.");
        }
    }

    function playMovie(project) {
        activeMovieId = project.id;
        
        // Setup Player elements
        galleryVideo.src = `${project.movie_file}?t=${Date.now()}`;
        galleryVideo.poster = project.poster_file ? `${project.poster_file}?t=${Date.now()}` : "";
        playerTitle.textContent = project.title;
        playerDesc.textContent = project.description || project.idea;
        
        // Format duration if available
        if (project.duration) {
            const mins = Math.floor(project.duration / 60);
            const secs = Math.floor(project.duration % 60).toString().padStart(2, "0");
            playerDuration.textContent = `${mins}:${secs}`;
        } else {
            playerDuration.textContent = "--:--";
        }

        playerDownload.href = project.movie_file;
        playerDownload.download = `${project.title.replace(/\s+/g, "_")}.mp4`;

        activePlayerCard.classList.remove("hidden");
        galleryVideo.load();
        
        // Smooth scroll to player card
        activePlayerCard.scrollIntoView({ behavior: "smooth", block: "start" });
        
        // Play the video
        galleryVideo.play().catch(e => console.log("Video auto-play blocked by browser policy"));
    }

    // Refresh Gallery click
    refreshGalleryBtn.addEventListener("click", () => {
        loadGallery();
        showToast("Studio gallery refreshed.");
    });

    // Delete project handler
    playerDeleteBtn.addEventListener("click", async () => {
        if (!activeMovieId) return;

        if (confirm("Are you sure you want to permanently delete this movie and all its generated frames?")) {
            try {
                const response = await fetch(`/api/projects/${activeMovieId}`, {
                    method: "DELETE"
                });

                if (!response.ok) throw new Error("Failed to delete project.");

                showToast("Movie deleted successfully.");
                activePlayerCard.classList.add("hidden");
                loadGallery();
            } catch (error) {
                showToast(error.message);
            }
        }
    });

    // Toast Notifications helper
    const toast = document.getElementById("notification-toast");
    const toastMsg = document.getElementById("toast-message");
    let toastTimeout = null;

    function showToast(message) {
        if (toastTimeout) clearTimeout(toastTimeout);
        toastMsg.textContent = message;
        toast.classList.remove("hidden");
        
        toastTimeout = setTimeout(() => {
            toast.classList.add("hidden");
        }, 4000);
    }

    // Settings elements & functionality
    const saveSettingsBtn = document.getElementById("save-settings-btn");
    const openrouterKeyInput = document.getElementById("settings-openrouter-key");
    const hfTokenInput = document.getElementById("settings-hf-token");
    const lumaKeyInput = document.getElementById("settings-luma-key");
    const meshyKeyInput = document.getElementById("settings-meshy-key");
    const tripo3dKeyInput = document.getElementById("settings-tripo3d-key");

    // Load saved settings on load
    const openrouterKey = localStorage.getItem("jarvis_openrouter_key") || "";
    const hfToken = localStorage.getItem("jarvis_hf_token") || "";
    const lumaKey = localStorage.getItem("jarvis_luma_key") || "";
    const meshyKey = localStorage.getItem("jarvis_meshy_key") || "";
    const tripo3dKey = localStorage.getItem("jarvis_tripo3d_key") || "";

    if (openrouterKey) openrouterKeyInput.value = openrouterKey;
    if (hfToken) hfTokenInput.value = hfToken;
    if (lumaKey) lumaKeyInput.value = lumaKey;
    if (meshyKey) meshyKeyInput.value = meshyKey;
    if (tripo3dKey) tripo3dKeyInput.value = tripo3dKey;

    async function loadSystemEnv() {
        try {
            const response = await fetch("/api/system/env");
            if (!response.ok) throw new Error("Failed to load env details.");
            const data = await response.json();
            
            const gpuVal = document.getElementById("env-gpu-val");
            const mixerVal = document.getElementById("env-mixer-val");
            const outputsVal = document.getElementById("env-outputs-val");
            const hostVal = document.getElementById("env-host-val");
            
            gpuVal.textContent = data.gpu_acceleration;
            if (data.gpu_acceleration.toLowerCase().includes("enabled")) {
                gpuVal.className = "detail-value text-green";
            } else {
                gpuVal.className = "detail-value text-red";
            }
            
            mixerVal.textContent = data.cpp_mixer;
            if (data.cpp_mixer.toLowerCase().includes("healthy")) {
                mixerVal.className = "detail-value text-green";
            } else {
                mixerVal.className = "detail-value text-red";
            }
            
            outputsVal.textContent = data.supported_outputs;
            hostVal.textContent = data.local_host;
        } catch (e) {
            console.error("Error loading system environment details:", e);
        }
    }

    saveSettingsBtn.addEventListener("click", () => {
        const orKey = openrouterKeyInput.value.trim();
        const hfTok = hfTokenInput.value.trim();
        const luKey = lumaKeyInput.value.trim();
        const meKey = meshyKeyInput.value.trim();
        const trKey = tripo3dKeyInput.value.trim();
        
        if (orKey) localStorage.setItem("jarvis_openrouter_key", orKey);
        else localStorage.removeItem("jarvis_openrouter_key");
        
        if (hfTok) localStorage.setItem("jarvis_hf_token", hfTok);
        else localStorage.removeItem("jarvis_hf_token");
        
        if (luKey) localStorage.setItem("jarvis_luma_key", luKey);
        else localStorage.removeItem("jarvis_luma_key");
        
        if (meKey) localStorage.setItem("jarvis_meshy_key", meKey);
        else localStorage.removeItem("jarvis_meshy_key");
        
        if (trKey) localStorage.setItem("jarvis_tripo3d_key", trKey);
        else localStorage.removeItem("jarvis_tripo3d_key");
        
        showToast("Preferences saved successfully.");
        loadSystemEnv();
    });

    // Initial load
    loadGallery();
    loadSystemEnv();
});
