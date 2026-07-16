import os
import subprocess
import json

presets = {
    'do_mixi': 'ytsearch1:"độ mixi tâm sự không nhạc"',
    'amee': 'ytsearch1:"amee phỏng vấn không nhạc"',
    'tran_thanh': 'ytsearch1:"trấn thành chia sẻ không nhạc"',
    'barack_obama': 'ytsearch1:"barack obama clean speech no music"',
    'donald_trump': 'ytsearch1:"donald trump clean speech no music"'
}

os.makedirs('web_app/static/presets', exist_ok=True)

for name, search in presets.items():
    print(f'Downloading {name}...')
    try:
        cmd_info = ['python', '-m', 'yt_dlp', '--dump-json', '--no-warnings', search]
        result = subprocess.run(cmd_info, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout.strip().split('\n')[0])
        
        duration = info.get('duration', 120)
        start_time = min(max(duration // 2, 0), max(duration - 15, 0))
        
        out_full = f'{name}_full.m4a'
        cmd_dl = [
            'python', '-m', 'yt_dlp', '-f', 'bestaudio', 
            '-o', out_full, 
            info['webpage_url']
        ]
        subprocess.run(cmd_dl, check=True)
        
        out_wav = f'web_app/static/presets/{name}.wav'
        cmd_ffmpeg = [
            'ffmpeg', '-y', '-i', out_full,
            '-ss', str(start_time), '-t', '10',
            '-ar', '24000', '-ac', '1',
            '-acodec', 'pcm_s16le',
            out_wav
        ]
        subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(out_full):
            os.remove(out_full)
        print(f'Successfully generated {out_wav}')
    except Exception as e:
        print(f'Failed for {name}: {e}')
