import pvporcupine
import pyaudio
import struct

class WakeWord:
    def __init__(self, keyword="jarvis"):
        # Get free access key from https://console.picovoice.ai/
        # For personal use only. If no key, fallback to keyword in audio.
        try:
            self.porcupine = pvporcupine.create(keywords=[keyword])
            self.use_porcupine = True
        except:
            print("Porcupine key missing. Using simple keyword detection.")
            self.use_porcupine = False
            return

        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

    def listen(self):
        if not self.use_porcupine:
            # Fallback: wait for "hey jarvis" from voice.listen()
            return False
        try:
            pcm = self.stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            return self.porcupine.process(pcm) >= 0
        except:
            return False

    def __del__(self):
        if hasattr(self, 'stream'):
            self.stream.close()
        if hasattr(self, 'pa'):
            self.pa.terminate()
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()