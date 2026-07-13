import os

# Ollama API Configuration
OLLAMA_API_KEY=os.getenv("OLLAMA_API_KEY", "a80332ae19134785a7ec377ccf23d938.OTAtrLFk_mu-U34M_pIBI2H1")
OLLAMA_BASE_URL="https://ollama.com/api"

# OpenAI Configuration
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL=os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Luma Configuration
LUMA_API_KEY=os.getenv("LUMA_API_KEY", "")

# NVIDIA Configuration
NIM_API_KEY=os.getenv("NIM_API_KEY", "NVIDIA_API_KEY_HERE")
NIM_MODEL="meta/llama-3.1-70b-instruct"

# ElevenLabs Configuration
ELEVENLABS_API_KEY=os.getenv("ELEVENLABS_API_KEY", "")

# LLM Provider (e.g., openai, ollama)
LLM_PROVIDER=os.getenv("LLM_PROVIDER", "ollama")

# Video Provider (e.g., luma, mock)
VIDEO_PROVIDER=os.getenv("VIDEO_PROVIDER", "mock")

# Audio Provider (e.g., openai, mock)
AUDIO_PROVIDER=os.getenv("AUDIO_PROVIDER", "mock")
