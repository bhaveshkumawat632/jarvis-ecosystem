import os
import uuid
import shutil
import json
import time
import sys

# Setup python path to allow importing VidRush and movie_generator
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)

if current_dir not in sys.path:
    sys.path.append(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if grandparent_dir not in sys.path:
    sys.path.append(grandparent_dir)

# Map VidRush import to services.vidrush or vidrush in sys.modules so the bytecode's VidRush imports succeed
try:
    import vidrush
    sys.modules['VidRush'] = vidrush
    import vidrush.workers as workers
    sys.modules['VidRush.workers'] = workers
    import vidrush.workers.celery_worker as celery_worker
    sys.modules['VidRush.workers.celery_worker'] = celery_worker
except ImportError:
    try:
        import services.vidrush as vidrush
        sys.modules['VidRush'] = vidrush
        import services.vidrush.workers as workers
        sys.modules['VidRush.workers'] = workers
        import services.vidrush.workers.celery_worker as celery_worker
        sys.modules['VidRush.workers.celery_worker'] = celery_worker
    except ImportError:
        pass

from celery.result import AsyncResult
from VidRush.workers.celery_worker import celery_app, generate_video_task
from flask import Flask, jsonify, request, send_from_directory
from movie_generator import PROJECTS_DIR, generate_movie_pipeline

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/projects/<path:path>')
def serve_project_files(path):
    return send_from_directory(PROJECTS_DIR, path)

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """Lists all projects by scanning meta.json in each project folder."""
    projects = []
    if not os.path.exists(PROJECTS_DIR):
        return jsonify(projects)
    
    for item in os.listdir(PROJECTS_DIR):
        item_path = os.path.join(PROJECTS_DIR, item)
        if not os.path.isdir(item_path):
            continue
        meta_file = os.path.join(item_path, 'meta.json')
        if not os.path.exists(meta_file):
            continue
        try:
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)
            
            if meta_data.get('status') == 'processing':
                progress_file = os.path.join(item_path, 'progress.json')
                if os.path.exists(progress_file):
                    with open(progress_file, 'r') as pf:
                        meta_data['progress'] = json.load(pf)
            projects.append(meta_data)
        except Exception as e:
            print(f"Error reading meta for project {item}: {e}")
            
    projects.sort(key=lambda x: x.get('created_at', 0), reverse=True)
    return jsonify(projects)

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    if not data or 'idea' not in data:
        return jsonify({'error': "Missing 'idea' in payload"}), 400
    
    project_id = data.get('project_id', f"proj_{uuid.uuid4().hex[:8]}")
    idea = data.get('idea')
    voice = data.get('voice', 'en-US-GuyNeural')
    music_mood = data.get('music_mood', 'cinematic')
    
    try:
        task = generate_video_task.delay(
            project_id=project_id,
            idea=idea,
            voice=voice,
            music_mood=music_mood
        )
        return jsonify({
            'message': 'Project queued successfully.',
            'project_id': project_id,
            'task_id': task.id
        }), 202
    except Exception as e:
        return jsonify({'error': f"Failed to queue task: {str(e)}"}), 500

@app.route('/api/projects/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = AsyncResult(task_id, app=celery_app)
    meta_info = ''
    if isinstance(task.info, dict):
        meta_info = task.info.get('status', '')
    elif task.info:
        meta_info = str(task.info)
        
    response = {
        'task_id': task_id,
        'state': task.state,
        'details': meta_info
    }
    return jsonify(response), 200

@app.route('/api/projects/<project_id>/progress', methods=['GET'])
def get_progress(project_id):
    """Returns the current progress state of a project."""
    project_path = os.path.join(PROJECTS_DIR, project_id)
    if not os.path.exists(project_path):
        return jsonify({'error': 'Project not found.'}), 404
        
    progress_file = os.path.join(project_path, 'progress.json')
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            return jsonify(progress_data)
        except Exception as e:
            return jsonify({'error': f"Failed to read progress: {e}"}), 500
    else:
        return jsonify({
            'step': 'initialize',
            'status': 'processing',
            'percentage': 0,
            'message': 'Starting project generation...',
            'timestamp': time.time()
        })

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Deletes a project folder and all its files."""
    project_path = os.path.join(PROJECTS_DIR, project_id)
    if not os.path.exists(project_path):
        return jsonify({'error': 'Project not found.'}), 404
        
    try:
        shutil.rmtree(project_path)
        return jsonify({'message': f"Project {project_id} deleted successfully."})
    except Exception as e:
        return jsonify({'error': f"Failed to delete project: {e}"}), 500

def get_gpu_status():
    """Detects graphics card and hardware acceleration capability."""
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            return f"Enabled ({device_name})"
    except ImportError:
        pass

    import subprocess
    import shutil
    if shutil.which('nvidia-smi'):
        try:
            res = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True, text=True, check=True
            )
            gpu_name = res.stdout.strip()
            if gpu_name:
                return f"Enabled ({gpu_name})"
        except Exception:
            pass

    if shutil.which('lspci'):
        try:
            res = subprocess.run(
                ['lspci'],
                capture_output=True, text=True, check=True
            )
            lines = res.stdout.splitlines()
            discrete_gpus = []
            integrated_gpus = []
            for line in lines:
                if 'VGA compatible controller' in line or '3D controller' in line:
                    clean_name = line.split('controller:')[1].strip() if 'controller:' in line else line
                    clean_name = (clean_name
                                  .replace('Intel Corporation ', '')
                                  .replace('NVIDIA Corporation ', '')
                                  .replace('Advanced Micro Devices, Inc. ', ''))
                    if any(x in line for x in ('NVIDIA', 'Radeon', 'AMD', 'Arc', 'GeForce')):
                        discrete_gpus.append(clean_name)
                    else:
                        integrated_gpus.append(clean_name)
            if discrete_gpus:
                return f"Enabled ({discrete_gpus[0]})"
            elif integrated_gpus:
                return f"Disabled ({integrated_gpus[0]} Integrated)"
        except Exception:
            pass

    return 'Disabled (Intel HD Integrated)'

@app.route('/api/system/env', methods=['GET'])
def system_env():
    """Returns dynamic details about the running hardware/software environment."""
    gpu_status = get_gpu_status()
    mixer_path = os.path.join(os.path.dirname(__file__), 'mixer')
    if os.path.exists(mixer_path) and os.access(mixer_path, os.X_OK):
        mixer_status = 'Compiled & Healthy'
    else:
        mixer_status = 'Missing or Unusable'
        
    return jsonify({
        'gpu_acceleration': gpu_status,
        'cpp_mixer': mixer_status,
        'supported_outputs': 'MP4 (H.264/AAC, 1024x576)',
        'local_host': request.host_url
    })

@app.route('/outputs/<path:filename>')
def custom_outputs(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'outputs'), filename)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handles chat requests for the Jarvis AI Assistant."""
    data = request.json
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'reply': "I didn't hear anything, Director."})
        
    groq_key = 'GROQ_API_KEY_HERE'
    import requests
    headers = {
        'Authorization': f"Bearer {groq_key}",
        'Content-Type': 'application/json'
    }
    payload = {
        'model': 'llama3-8b-8192',
        'messages': [
            {
                'role': 'system',
                'content': "You are JARVIS, a highly advanced AI movie director assistant in a cyberpunk sci-fi web application. Keep responses short, professional, and slightly snarky like Iron Man's Jarvis."
            },
            {
                'role': 'user',
                'content': user_message
            }
        ],
        'max_tokens': 150
    }
    
    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            return jsonify({'reply': reply})
        else:
            return jsonify({'reply': f"Systems offline. Groq Error: {response.status_code}"})
    except Exception as e:
        return jsonify({'reply': f"Communication array error: {str(e)}"})

@app.route('/api/system/stats', methods=['GET'])
def system_stats():
    """Returns live CPU and RAM usage by reading /proc"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        mem_total = int(lines[0].split()[1])
        mem_available = int(lines[2].split()[1])
        ram_usage = (mem_total - mem_available) / mem_total * 100
        
        with open('/proc/loadavg', 'r') as f:
            load = float(f.read().split()[0])
        cpu_usage = min(load / os.cpu_count() * 100, 100)
        
        return jsonify({
            'cpu': round(cpu_usage, 1),
            'ram': round(ram_usage, 1)
        })
    except Exception as e:
        return jsonify({
            'cpu': 0,
            'ram': 0
        })

if __name__ == '__main__':
    import argparse
    if len(sys.argv) > 1:
        from movie_generator import generate_cinematic_movie
        
        parser = argparse.ArgumentParser(description='VidRush Cinematic Movie Generator')
        parser.add_argument('--topic', help='Video topic (required for CLI generation)')
        parser.add_argument('--duration', type=int, default=3, help='Duration in minutes')
        parser.add_argument('--style', default='Cinematic Documentary', choices=[
            'Cinematic Documentary', 'YouTube Educational', 'Motivational',
            'Horror Documentary', 'News Report', 'Short Film'
        ])
        parser.add_argument('--quality', default='1080p', choices=['720p', '1080p', '4K'])
        parser.add_argument('--ai-video', action='store_true', help='Use Replicate AI video')
        parser.add_argument('--no-subtitles', action='store_true')
        parser.add_argument('--voice', default='narrator', choices=['narrator', 'deep_male', 'female', 'news'])
        parser.add_argument('--server', action='store_true', help='Run the web UI server')
        
        args = parser.parse_args()
        
        if args.server:
            app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        elif args.topic:
            generate_cinematic_movie(
                topic=args.topic,
                duration_minutes=args.duration,
                style=args.style,
                voice_type=args.voice,
                quality=args.quality,
                use_ai_video=args.ai_video,
                subtitles=not args.no_subtitles
            )
        else:
            print('You must specify either --topic to generate a video or --server to run the web UI.')
    else:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
