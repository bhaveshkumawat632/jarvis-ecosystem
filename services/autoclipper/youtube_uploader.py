import os
import datetime
import json
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.llm_gateway import LLMGateway
import config
os.environ["OLLAMA_API_KEY"] = config.OLLAMA_API_KEY
os.environ["LLM_PROVIDER"] = "ollama"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Scopes needed to upload videos
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubeUploader:
    def __init__(self, secrets_file="client_secrets.json"):
        self.secrets_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), secrets_file)
        self.token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.json")
        self.youtube = self.authenticate()
        self.llm = LLMGateway()

    def authenticate(self):
        """Authenticates with YouTube API via OAuth2."""
        creds = None
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired token...")
                creds.refresh(Request())
            else:
                logger.info("Starting new OAuth flow. Please follow the link in your console!")
                if not os.path.exists(self.secrets_file):
                    raise FileNotFoundError(f"Missing {self.secrets_file}. Please download it from Google Cloud Console.")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
                
        return build('youtube', 'v3', credentials=creds)

    def generate_viral_metadata(self) -> dict:
        """Uses the LLMGateway to generate a clickbait title, description, and tags."""
        logger.info("Generating viral metadata via LLM...")
        system_prompt = "You are a top-tier YouTube Shorts strategist aiming for a GLOBAL audience. Generate a highly engaging title (max 60 chars) that transcends language barriers (use emojis, simple universally understood words like OMG, CRAZY, WOW). Provide a description with 3 hashtags, and 5 broad viral tags. Output ONLY strict JSON: {\"title\": \"...\", \"description\": \"...\", \"tags\": [\"...\"]}"
        user_prompt = "Generate metadata for a viral high-action MrBeast short clip. Make it appealing to non-English speakers too."
        
        try:
            response = self.llm.execute_with_retry(system_prompt, user_prompt, max_retries=2)
            if isinstance(response, dict) and "title" in response:
                return response
        except Exception as e:
            logger.error(f"LLM Metadata generation failed: {e}")
            
        # Fallback if LLM fails
        return {
            "title": "MrBeast CRAZIEST Challenge Ever! 😱 #shorts",
            "description": "You won't believe what happens next in this MrBeast challenge! Subscribe for more daily shorts! #mrbeast #challenge #shorts",
            "tags": ["mrbeast", "shorts", "challenge", "viral", "crazy"]
        }

    def upload_video(self, video_path: str):
        """Uploads a video to YouTube Shorts."""
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return
            
        metadata = self.generate_viral_metadata()
        
        logger.info(f"Uploading Video: {metadata['title']}")
        
        body = {
            'snippet': {
                'title': metadata['title'],
                'description': metadata['description'],
                'tags': metadata['tags'],
                'categoryId': '24' # Entertainment
            },
            'status': {
                'privacyStatus': 'public', # Will be public immediately upon upload
                'selfDeclaredMadeForKids': False
            }
        }

        # MediaFileUpload handles the actual file stream
        insert_request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )

        try:
            response = insert_request.execute()
            logger.info(f"[*] SUCCESS! Video uploaded to YouTube. Video ID: {response['id']}")
            logger.info(f"URL: https://youtube.com/shorts/{response['id']}")
            return response['id']
        except Exception as e:
            logger.error(f"An error occurred during upload: {e}")
            return None

if __name__ == "__main__":
    uploader = YouTubeUploader()
    # Replace with path to one of the generated short clips
    # uploader.upload_video("shorts_factory/example/short_clip_1.mp4")
    print("Authentication successful! The uploader is ready.")
