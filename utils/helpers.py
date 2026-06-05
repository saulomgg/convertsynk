import shutil
import subprocess
import os
import webbrowser
from utils.constants import *

def check_ffmpeg():
    """Verifica se FFmpeg está disponível"""
    return shutil.which('ffmpeg') is not None

def check_vp9_codec():
    """Verifica se libvpx-vp9 está disponível"""
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, encoding='utf-8')
        return 'libvpx-vp9' in result.stdout
    except Exception:
        return False

def detect_hw_codecs():
    """Detecta codecs de aceleração por hardware"""
    codecs = {}
    try:
        result = subprocess.run(['ffmpeg', '-codecs'], capture_output=True, text=True, encoding='utf-8')
        output = result.stdout
        
        mapping = {
            'h264_nvenc': HW_CODEC_NVIDIA_H264,
            'hevc_nvenc': HW_CODEC_NVIDIA_H265,
            'h264_qsv': HW_CODEC_INTEL_H264,
            'hevc_qsv': HW_CODEC_INTEL_H265,
            'h264_amf': HW_CODEC_AMD_H264,
            'hevc_amf': HW_CODEC_AMD_H265
        }
        
        for key, name in mapping.items():
            if key in output:
                codecs[key] = name
                
    except Exception as e:
        print(f"Could not detect hardware codecs: {e}")
    return codecs

def open_url(url):
    """Abre uma URL no navegador"""
    webbrowser.open(url)

def get_video_duration(filepath):
    """Obtém a duração do vídeo usando ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(filepath)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        return float(result.stdout)
    except Exception:
        return 0
