import asyncio
from ruaccent import RUAccent
import numpy as np
import re
from silero import silero_tts
import soundfile as sf
from io import BytesIO
import torch
import json
import requests

# Класс для расстановки ударений
class Accent_Maker():
    # Скачивание модельки для ударений, omograph_model_size - размер модели
    def __init__(self, omograph_model_size='turbo3.1'):
        self.accentizer = RUAccent()
        self.accentizer.load(omograph_model_size=omograph_model_size, use_dictionary=True, tiny_mode=False)
    
    # функция котороая принимает строку и возращает уже размеченную строку 
    def put_accent(self, text: str):
        accent_text = self.accentizer.process_all(text)
        return accent_text

# Класс для модели Silero  
class Silero_TTS():
    # Скачивание модельки, можны выбрать язык и какие спикеры скачиваются 
    def __init__(self, language='ru', speaker='v5_ru'):
        self.model, _ = silero_tts(language=language,
                      speaker=speaker)
        
    # Возращает возможные голоса
    def get_voice(self):
        return self.model.speakers
    
    # Подготовка текста для озвучки
    # - Разбивает текст по предложениям до 1000 символов в противном случае дробит строку на строки до 1000 символов
    # - Добавляет паузы и приводит текст в ssml разметку
    def text_prepare(self, text):
        # Разбиваем текст на предложения
        list_of_sentence = re.split(r'[.!?]', text)
        # Здесь буду хранить список предложений
        text_prep = []
        for sentence in list_of_sentence:
            # Если строка не пустая и < 1000 символов то я просто привожу её к ssml и добавляю паузы
            if sentence != "" and len(sentence) < 1000:  
                sentence = sentence.replace(',', ',<break strength="medium" />')
                sentence = '<speak>\n' + sentence.strip() + '.\n<break strength="strong" /></speak>'
                text_prep.append(sentence)
            # Если строка >1000, то я делю её на 
            # chunks - целое кол-во чанков примерно чуть больше 500
            # step - с каким шагом мне нужно идти
            elif len(sentence) > 1000:
                chunks = len(sentence) // 500
                step = len(sentence) // chunks
                prev_index = 0
                # Тут я хожу по чанкам
                for chunk in range(1, chunks + 1):
                    # Начинаю идти по строке с шага до первого пробела или конца строки
                    for j in range(step * chunk, len(sentence)):
                        if sentence[j] == ' ' or j == len(sentence) - 1:
                            # Создаю временную строку и скалдываю в неё нужный кусочек
                            temp_sentence = sentence[prev_index:j + 1] 
                            temp_sentence = temp_sentence.replace(',', ',<break strength="medium" />')
                            temp_sentence = '<speak>\n' + temp_sentence.strip() + '</speak>'
                            text_prep.append(temp_sentence)
                            prev_index = j
                            break
        return text_prep
    
    # Функция для преобразования ssml текста в аудио
    def get_audio_from_ssml_text(self, text: str, format_audio='WAV', sample_rate = 48000, speaker = 'baya', put_accent=True, put_yo=True, put_stress_homo=True, put_yo_homo=True):
        self.sample_rate = sample_rate
        if len(text) <= 1000:
            tensor = self.model.apply_tts(ssml_text = text,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo,
                                    put_stress_homo=put_stress_homo,
                                    put_yo_homo=put_yo_homo
                                    )
        else:
            raise Exception("Текст превышает длинну в 1000 символов, восмпользуйтесь text_to_voice()")
        return tensor
    
    # Функция для преобразования текста в аудио
    def get_audio_from_text(self, text: str, format_audio='WAV', sample_rate = 48000, speaker = 'baya', put_accent=True, put_yo=True, put_stress_homo=True, put_yo_homo=True):
        self.sample_rate = sample_rate
        if len(text) <= 1000:
            tensor = self.model.apply_tts(text = text,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo,
                                    put_stress_homo=put_stress_homo,
                                    put_yo_homo=put_yo_homo
                                    )
        else:
            raise Exception("Текст превышает длинну в 1000 символов, восмпользуйтесь text_to_voice()")
        return tensor
        

    # Функция которая принимает список строк в ssml формате и возвращает numpy тензор
    def text_to_voice(self, prepared_ssml_text_list, sample_rate = 48000, speaker = 'baya', put_accent=True, put_yo=True, put_stress_homo=True, put_yo_homo=True):
        audios = []
        for text in prepared_ssml_text_list:
            audio = self.get_audio_from_ssml_text(text = text,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo,
                                    put_stress_homo=put_stress_homo,
                                    put_yo_homo=put_yo_homo
                                    )
            audios.append(audio)
        tensor = torch.cat(audios)
        return tensor

    # Преобразовывает numpy tensor в байты
    def numpy_to_bytes(self, audio: np.array , format_audio='WAV'):
        # т.к silero возвращает NumPy array тут я кодирую его в байты в нужном формате и частоте дискретизации
        audio_bytes_io = BytesIO()
        sf.write(audio_bytes_io, audio, samplerate=self.sample_rate, format=format_audio)
        return audio_bytes_io.getvalue()
    

class Sber_Salut():
    def __init__(self, apikey):
        self.apikey = apikey

    # Получаю токен который действителен 30 мин
    def get_access_token(cert, apikey):
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        payload={
        'scope': 'SALUTE_SPEECH_PERS'
        }
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': '7afd6a33-e0fd-4c80-aa1b-2ba8b583a113',
        'Authorization': 'Basic ' + apikey
        }
        return requests.request("POST", url, headers=headers, data=payload, verify=cert)

    # Получаю озвученный текст
    def get_audio(voice, text, cert, access_token):
        url = f"https://smartspeech.sber.ru/rest/v1/text:synthesize?voice={voice}"
        payload = text
        headers = {
        'Content-Type': 'application/text',
        'Accept': 'audio/x-wav',
        'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.request("POST", url, headers=headers, data=payload, verify=cert)
        return response
    
    def get_audio_from_text(self, text, voice, cert='./russiantrustedca.pem'):
            # Тут нужен:
            # apikey - ключ апи
            # cert - сертификат минцифры
            # voice - голос
            # text - текст
            # Тут я получю access_token на основе apikey он живёт 30 минут, но ничего лучше чем каждый раз получать его cнова я не придумал 
            response = self.get_access_token(cert, self.apikey)
            access_token = json.loads(response.text)["access_token"]
            # Здесь уже аудидоржка в байтах в нужном формате
            response = self.get_audio(voice, text, cert, access_token)
            return response.content
    

# Оставил на всякий случай
class TTS:
    def __init__(self):
        pass

    async def generate_voice_message(self, text: str):
        await asyncio.sleep(1)
        return 'temp/voice_message.mp3'