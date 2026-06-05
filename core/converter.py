import subprocess
import os
import re
import time
from pathlib import Path

def build_ffmpeg_cmd(input_path, output_path, compression_profile, audio_codec_choice, available_hw_codecs):
    """Replicando exatamente a lógica de construção do comando do original"""
    ffmpeg_cmd = ['ffmpeg', '-i', str(input_path)]
    
    # Audio setup
    if audio_codec_choice == "opus":
        audio_codec = ['-c:a', 'libopus', '-b:a', '128k']
    else:
        audio_codec = ['-c:a', 'aac', '-b:a', '192k']
        
    # Video profile setup
    if compression_profile.startswith("h264_"):
        crf = {'h264_balanced': '23', 'h264_quality': '18', 'h264_fast': '28'}[compression_profile]
        ffmpeg_cmd.extend(['-c:v', 'libx264', '-crf', crf, '-preset', 'medium'])
    elif compression_profile.startswith("h265_"):
        crf = {'h265_balanced': '28', 'h265_quality': '23', 'h265_fast': '33'}[compression_profile]
        ffmpeg_cmd.extend(['-c:v', 'libx265', '-crf', crf, '-preset', 'medium'])
    elif compression_profile.startswith("vp9_"):
        crf = {'vp9_balanced': '30', 'vp9_quality': '20', 'vp9_fast': '40'}[compression_profile]
        ffmpeg_cmd.extend(['-c:v', 'libvpx-vp9', '-crf', crf, '-b:v', '0'])
    elif compression_profile.startswith("prores_"):
        profile = 'prores_ks'
        vprofile = {'prores_lt': 'lt', 'prores_standard': 'standard'}[compression_profile]
        ffmpeg_cmd.extend(['-c:v', profile, '-profile:v', vprofile])
        audio_codec = ['-c:a', 'pcm_s16le']
    elif compression_profile in available_hw_codecs:
        codec = compression_profile
        ffmpeg_cmd.extend(['-c:v', codec])
        if 'nvenc' in codec: ffmpeg_cmd.extend(['-preset', 'p5', '-cq', '23'])
        elif 'qsv' in codec: ffmpeg_cmd.extend(['-global_quality', '23'])
        elif 'amf' in codec: ffmpeg_cmd.extend(['-quality', 'balanced'])

    ffmpeg_cmd.extend(audio_codec)
    ffmpeg_cmd.extend(['-progress', 'pipe:1', '-y', str(output_path)])
    return ffmpeg_cmd

def execute_ffmpeg(ffmpeg_cmd, duration, progress_callback, stop_event):
    """Executa o processo FFmpeg com monitoramento de progresso idêntico ao original"""
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                             universal_newlines=True, bufsize=1, encoding='utf-8', 
                             errors='ignore', startupinfo=startupinfo)
    
    while process.poll() is None:
        if stop_event.is_set():
            process.terminate()
            time.sleep(0.5)
            if process.poll() is None: process.kill()
            return False
            
        line = process.stdout.readline()
        if not line: break
            
        time_match = re.search(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})', line)
        if time_match and duration > 0:
            time_str = time_match.group(1)
            h, m, s = map(float, time_str.split(':'))
            current_time = h * 3600 + m * 60 + s
            percent = (current_time / duration) * 100
            progress_callback(percent, current_time)
            
    process.wait()
    return process.returncode == 0
