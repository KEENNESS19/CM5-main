import pyaudio,wave,random
import wave
import numpy as np
from scipy import fftpack
import os,time
from datetime import datetime
import os,sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from auto_platform import AudiostreamSource, play_command, default_libpath
from libnyumaya import AudioRecognition, FeatureExtractor
from uiutils import Button,mic_logo,mic_purple,splash_theme_color,clear_top,draw,splash,display,la,lcd_draw_string,get_font
font1=get_font(17)
button=Button()
# 录音参数
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 600  # 最大录音时长
SAVE_FILE = "recorded_audio.wav"
SAVE_KEYWORD="keyword_audio.wav"
START_THRESHOLD = 100000  # 开始录音的音量阈值
END_THRESHOLD = 40000  # 停止录音的音量阈值
ENDLAST = 30
start_threshold = 60000
end_threshold = 40000
endlast = 10


# 关键词检测参数
KEYWORD_MODEL_PATH = "./demos/src/lulu_v3.1.907.premium"
KEYWORD_THRESHOLD = 0.7
PLAY_COMMAND = "aplay"  # Linux 播放命令，Windows 可改为 "start"

def calculate_volume(data):

    rt_data = np.frombuffer(data, dtype=np.int16)
    fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
    fft_data = np.abs(fft_temp_data)[0: fft_temp_data.size // 2 + 1]
    return sum(fft_data) // len(fft_data)

def start_recording():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("wait recording...")
    clear_top()
    frames = []
    start_recording_flag = False
    end_data_list = [0] * ENDLAST
    pre_record_frames = []  # 预录音缓冲区
    pre_record_length = int(RATE / CHUNK * 1)  # 预录音 1 秒
    silence_duration = 0  # 静音持续时间
    max_silence_duration = int(RATE / CHUNK * 4)  # 最大允许静音时长（4 秒）
    recording_start_time = None  # 录音开始时间
    no_sound_timeout = int(RATE / CHUNK * 6)  # 无声音超时（6秒）
    no_sound_counter = 0  # 无声音计数器
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        volume = calculate_volume(data)
        
        if not start_recording_flag:
            pre_record_frames.append(data)  # 保存到预录音缓冲区
            if len(pre_record_frames) > pre_record_length:
                pre_record_frames.pop(0)  # 保持缓冲区大小
            if volume > START_THRESHOLD:
                print("detected voice, start recording...")
                start_recording_flag = True
                recording_start_time = time.time()  # 记录录音开始时间
                frames.extend(pre_record_frames)  # 将预录音数据加入正式录音
                frames.append(data)
                no_sound_counter = 0  # 重置无声音计数器
            else:
                no_sound_counter += 1
                # 如果6秒内没有检测到声音，结束录音
                if no_sound_counter >= no_sound_timeout:
                    print("No sound detected for 6 seconds, ending recording")
                    break
        else:
            end_data_list.pop(0)
            end_data_list.append(volume)
            frames.append(data)

            # 检测静音
            if volume < END_THRESHOLD:
                silence_duration += 1
            else:
                silence_duration = 0

            # 如果录音时间超过 2 秒且没有检测到有效声音，结束录音
            if recording_start_time and (time.time() - recording_start_time) >= 2:
                if max(end_data_list) < START_THRESHOLD:
                    print("No valid sound detected within 2 seconds, end recording")
                    break

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(SAVE_FILE, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"The recording has been saved as: {SAVE_FILE}")


def draw_wave(ch):
    ch = min(ch, 10)
    clear_top()
    draw.bitmap((145, 40), mic_logo, mic_purple)
    
    wave_params = [
        {"start_x": 40, "start_y": 32, "width": 80, "height": 50},
        {"start_x": 210, "start_y": 32, "width": 80, "height": 50}
    ]
    
    for params in wave_params:
        draw_single_wave(
            params["start_x"], 
            params["start_y"], 
            params["width"], 
            params["height"], 
            ch
        )

def draw_single_wave(start_x, start_y, width, height, ch):
    y_center = height // 2
    current_y = y_center
    previous_point = (start_x, y_center + start_y)
    
    if start_x > 200: 
        draw.rectangle(
            [(start_x - 1, start_y), (start_x + width, start_y + height)],
            fill=splash_theme_color,
        )
    
    x = 0
    while x < width:
        seg_len = random.randint(7, 25)
        gap_len = random.randint(4, 20)
        
        for _ in range(seg_len):
            if x >= width: break
            current_y = max(0, min(height - 1, current_y + random.randint(-ch, ch)))
            current_point = (x + start_x, current_y + start_y)
            draw.line([previous_point, current_point], fill=mic_purple)
            previous_point, x = current_point, x + 1
        
        for _ in range(gap_len):
            if x >= width: break
            current_point = (x + start_x, y_center + start_y)
            draw.line([previous_point, current_point], fill=mic_purple, width=2)
            previous_point, x = current_point, x + 1

def detect_keyword():
    # 初始化关键词检测
    audio_stream = AudiostreamSource()
    libpath = "./demos/src/libnyumaya_premium.so.3.1.0"
    extractor = FeatureExtractor(libpath)
    detector = AudioRecognition(libpath)
    extractor_gain = 1.0
    keyword_id = detector.addModel(KEYWORD_MODEL_PATH, KEYWORD_THRESHOLD)
    bufsize = detector.getInputDataSize()
    audio_stream.start()
 
    print("Waiting for keyword...")
    while True:
        # 读取音频数据
        frame = audio_stream.read(bufsize * 2, bufsize * 2)
        if not frame:
            continue

        # 绘制波形（直接使用当前帧）
        rt_data = np.frombuffer(frame, dtype=np.int16)
        fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
        fft_data = np.abs(fft_temp_data)[0:fft_temp_data.size // 2 + 1]
        vol = sum(fft_data) // len(fft_data)
        draw_wave(int(vol / 10000))  # 调整除数使波形显示合适
        display.ShowImage(splash)

        # 关键词检测
        features = extractor.signalToMel(frame, extractor_gain)
        prediction = detector.runDetection(features)

        if prediction == keyword_id:
            now = datetime.now().strftime("%d.%b %Y %H:%M:%S")
            print(f"Keyword detected: {now}")
            os.system(f"{PLAY_COMMAND} ./demos/src/ding.wav")
            return True

    