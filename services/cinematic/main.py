import os
import sys
import time
import socket
import threading
import webbrowser

# Check if port is already in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

# Start Flask Web Server in a background thread
def start_flask_server():
    from app import app
    print("Starting Flask Web Server on http://127.0.0.1:5000...")
    # Disable automatic reload to prevent thread double-spawning
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

def run_desktop_mode():
    """Starts Flask server and opens the system web browser."""
    if not is_port_in_use(5000):
        server_thread = threading.Thread(target=start_flask_server)
        server_thread.daemon = True
        server_thread.start()
        # Give Flask half a second to initialize
        time.sleep(0.5)
    else:
        print("Jarvis server port 5000 already active. Connecting to running instance.")

    url = "http://127.0.0.1:5000"
    print(f"\n=======================================================")
    print(f"JARVIS UNIVERSAL STUDIO ACTIVE")
    print(f"Opening browser at: {url}")
    print(f"=======================================================\n")
    
    webbrowser.open(url)
    
    # Keep the main thread alive for the command line runner
    print("Press Ctrl+C to terminate the Jarvis Universal Studio server.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Jarvis Universal Studio...")

# Kivy Mobile Mode Loader for Android
def run_android_mode():
    """Initializes Kivy app and wraps a native Android Webview."""
    # Start Flask Server in background
    server_thread = threading.Thread(target=start_flask_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Import Kivy components
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.clock import Clock
    from jnius import autoclass
    
    class AndroidWebView(Widget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.url = "http://127.0.0.1:5000"
            Clock.schedule_once(self.create_webview, 0)
            
        def create_webview(self, *args):
            # Fetch native Android activity
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            # Fetch native Android WebView classes
            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            
            # Setup WebView on Android UI Thread
            self.webview = WebView(activity)
            self.webview.getSettings().setJavaScriptEnabled(True)
            self.webview.getSettings().setDomStorageEnabled(True)
            self.webview.getSettings().setAllowFileAccess(True)
            self.webview.getSettings().setMediaPlaybackRequiresUserGesture(False)
            self.webview.setWebViewClient(WebViewClient())
            self.webview.loadUrl(self.url)
            
            # Set WebView as screen content
            activity.setContentView(self.webview)
            
    class JarvisUniversalApp(App):
        def build(self):
            return AndroidWebView()
            
        def on_pause(self):
            return True
            
        def on_resume(self):
            pass

    # Launch Kivy App
    JarvisUniversalApp().run()

if __name__ == "__main__":
    # Check if running on Android (kivy android environment defines ANDROID_ARGUMENT or ANDROID_APP_PATH)
    is_android = 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_APP_PATH' in os.environ
    
    if is_android:
        run_android_mode()
    else:
        # Fallback to Desktop mode
        run_desktop_mode()
