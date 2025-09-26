import os
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

def generate_and_play_audio(narration: str, voice_id="pNInz6obpgDQGcFmaJgB"):
    elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    audio = elevenlabs.text_to_speech.convert(
        text=narration,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    play(audio)
