from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, ConfigYesNo, getConfigListEntry
from enigma import eConsoleAppContainer, eTimer
import os
import io
import hashlib

# API Key file paths in /etc/enigma2/aisubtitles/
API_KEY_FILES = {
    "groq": "/etc/enigma2/aisubtitles/groq.key",
    "gemini": "/etc/enigma2/aisubtitles/gemini.key",
    "openai": "/etc/enigma2/aisubtitles/openai.key",
    "deepgram": "/etc/enigma2/aisubtitles/deepgram.key",
    "assemblyai": "/etc/enigma2/aisubtitles/assemblyai.key"
}

config.plugins.AISubtitles = ConfigSubsection()
config.plugins.AISubtitles.enabled = ConfigSelection(default="false", choices=[("false", "Disabled"), ("true", "Enabled")])
config.plugins.AISubtitles.provider = ConfigSelection(default="auto", choices=[("auto", "Auto (All Enabled)"), ("groq", "Groq Only"), ("deepgram", "Deepgram Only"), ("assemblyai", "AssemblyAI Only"), ("gemini", "Gemini Only"), ("openai", "OpenAI Only")])
config.plugins.AISubtitles.api_key = ConfigText(default="", visible_width=50, fixed_size=False)
config.plugins.AISubtitles.api_key_gemini = ConfigText(default="", visible_width=50, fixed_size=False)
config.plugins.AISubtitles.api_key_openai = ConfigText(default="", visible_width=50, fixed_size=False)
config.plugins.AISubtitles.api_key_deepgram = ConfigText(default="", visible_width=50, fixed_size=False)
config.plugins.AISubtitles.api_key_assemblyai = ConfigText(default="", visible_width=50, fixed_size=False)
# Provider enable/disable toggles - use ConfigYesNo for independent boolean toggles
config.plugins.AISubtitles.enable_groq = ConfigYesNo(default=True)
config.plugins.AISubtitles.enable_deepgram = ConfigYesNo(default=False)
config.plugins.AISubtitles.enable_assemblyai = ConfigYesNo(default=False)
config.plugins.AISubtitles.enable_gemini = ConfigYesNo(default=False)
config.plugins.AISubtitles.enable_openai = ConfigYesNo(default=False)
# Dummy configs for display
config.plugins.AISubtitles.hidden_key = ConfigSelection(default="****", choices=[("****", "****")])
config.plugins.AISubtitles.section_header = ConfigSelection(default="", choices=[("", "")])
# New appearance settings
config.plugins.AISubtitles.background_style = ConfigSelection(default="semi_transparent", choices=[("transparent", "Transparent"), ("semi_transparent", "Semi-Transparent"), ("solid", "Solid Black")])
config.plugins.AISubtitles.text_color = ConfigSelection(default="white", choices=[("white", "White"), ("yellow", "Yellow"), ("green", "Green"), ("cyan", "Cyan"), ("orange", "Orange")])
config.plugins.AISubtitles.text_size = ConfigSelection(default="medium", choices=[("small", "Small (28)"), ("medium", "Medium (34)"), ("large", "Large (42)"), ("xlarge", "X-Large (52)"), ("mega", "Mega (62)")])
config.plugins.AISubtitles.font_type = ConfigSelection(default="Regular", choices=[("Regular", "Regular")])

# Function to get available fonts - uses known Enigma2 font aliases
def scanAvailableFonts():
    """Get fonts available in Enigma2 - these are registered font aliases"""
    # These are common font aliases registered in Enigma2 skins
    # Font aliases are defined in skin.xml with <font> or addFont()
    fonts = [
        ("Regular", "Regular"),
        ("Bold", "Bold"),
        ("Italic", "Italic"),
        ("LCD", "LCD"),
        ("Console", "Console"),
        ("Replacement", "Replacement"),
        # Common skin fonts
        ("Body", "Body"),
        ("Title", "Title"),
        ("Button", "Button"),
        ("HandelGotDBol", "Handel Gothic Bold"),
        ("LiberationSans", "Liberation Sans"),
        ("OpenSans", "Open Sans"),
        ("Roboto", "Roboto"),
        ("Ubuntu", "Ubuntu"),
        ("DejaVuSans", "DejaVu Sans"),
        ("NotoSans", "Noto Sans"),
        ("DroidSans", "Droid Sans"),
        ("arial", "Arial"),
        ("times", "Times"),
        ("verdana", "Verdana")
    ]
    return fonts
config.plugins.AISubtitles.show_keys = ConfigSelection(default="false", choices=[("false", "Hidden (****)"), ("true", "Show Keys")])
# Target language for translation
config.plugins.AISubtitles.target_language = ConfigSelection(default="ar", choices=[
    ("ar", "Arabic"),
    ("en", "English"),
    ("tr", "Turkish"),
    ("fa", "Persian"),
    ("de", "German"),
    ("fr", "French"),
    ("it", "Italian"),
    ("ro", "Romanian"),
    ("es", "Spanish"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("hi", "Hindi"),
    ("ur", "Urdu"),
    ("id", "Indonesian"),
    ("nl", "Dutch"),
    ("pl", "Polish"),
    ("el", "Greek"),
    ("uk", "Ukrainian"),
    ("cs", "Czech"),
    ("sv", "Swedish"),
    ("hu", "Hungarian"),
    ("th", "Thai"),
    ("vi", "Vietnamese"),
    ("bn", "Bengali"),
    ("ms", "Malay"),
    ("ku", "Kurdish"),
    # New languages - Scandinavian
    ("no", "Norwegian"),
    ("da", "Danish"),
    ("fi", "Finnish"),
    # Eastern European languages
    ("hr", "Croatian"),
    ("sr", "Serbian"),
    ("bg", "Bulgarian"),
    ("sk", "Slovak"),
    ("sl", "Slovenian"),
    ("mk", "Macedonian"),
    ("sq", "Albanian"),
    ("bs", "Bosnian"),
    ("lt", "Lithuanian"),
    ("lv", "Latvian"),
    ("et", "Estonian"),
    # Additional languages
    ("he", "Hebrew"),
    ("az", "Azerbaijani"),
    ("ka", "Georgian"),
    ("hy", "Armenian"),
    ("be", "Belarusian"),
    ("mt", "Maltese"),
    ("is", "Icelandic"),
    ("ga", "Irish"),
    ("cy", "Welsh"),
    ("af", "Afrikaans"),
    ("sw", "Swahili"),
    ("tl", "Filipino"),
    ("pa", "Punjabi"),
    ("ta", "Tamil"),
    ("te", "Telugu"),
    ("mr", "Marathi"),
    ("gu", "Gujarati"),
    ("ne", "Nepali"),
    ("si", "Sinhala"),
    ("my", "Myanmar"),
    ("km", "Khmer"),
    ("lo", "Lao"),
    ("am", "Amharic")
])

# Language code to full name mapping for prompts
LANGUAGE_NAMES = {
    "ar": "Arabic", "en": "English", "tr": "Turkish", "fa": "Persian",
    "de": "German", "fr": "French", "it": "Italian", "ro": "Romanian",
    "es": "Spanish", "pt": "Portuguese", "ru": "Russian", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean", "hi": "Hindi", "ur": "Urdu",
    "id": "Indonesian", "nl": "Dutch", "pl": "Polish", "el": "Greek",
    "uk": "Ukrainian", "cs": "Czech", "sv": "Swedish", "hu": "Hungarian",
    "th": "Thai", "vi": "Vietnamese", "bn": "Bengali",
    "ms": "Malay", "ku": "Kurdish",
    # Scandinavian
    "no": "Norwegian", "da": "Danish", "fi": "Finnish",
    # Eastern European
    "hr": "Croatian", "sr": "Serbian", "bg": "Bulgarian", "sk": "Slovak",
    "sl": "Slovenian", "mk": "Macedonian", "sq": "Albanian", "bs": "Bosnian",
    "lt": "Lithuanian", "lv": "Latvian", "et": "Estonian",
    # Additional
    "he": "Hebrew", "az": "Azerbaijani", "ka": "Georgian", "hy": "Armenian",
    "be": "Belarusian", "mt": "Maltese", "is": "Icelandic", "ga": "Irish",
    "cy": "Welsh", "af": "Afrikaans", "sw": "Swahili", "tl": "Filipino",
    "pa": "Punjabi", "ta": "Tamil", "te": "Telugu", "mr": "Marathi",
    "gu": "Gujarati", "ne": "Nepali", "si": "Sinhala", "my": "Myanmar",
    "km": "Khmer", "lo": "Lao", "am": "Amharic"
}

class AISubtitlesOverlay(Screen):
    # Default skin will be overridden in __init__
    skin = """
    <screen name="AISubtitlesOverlay" position="0,0" size="1920,1080" flags="wfNoBorder" backgroundColor="transparent" zPosition="10">
        <widget name="subtitles" position="50,850" size="1820,200" font="Regular;28" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#80000000" />
        <widget name="status" position="5,5" size="200,35" font="Regular;18" foregroundColor="#00ff00" backgroundColor="#80000000" />
    </screen>
    """

    STAGE_IDLE = 0
    STAGE_DOWNLOAD = 1
    STAGE_TRANSCRIBE = 3
    STAGE_TRANSLATE = 4
    STAGE_GEMINI = 5
    
    # Color mapping
    COLOR_MAP = {
        "white": "#ffffff",
        "yellow": "#ffff00",
        "green": "#00ff00",
        "cyan": "#00ffff",
        "orange": "#ff8800"
    }
    
    # Font size mapping
    SIZE_MAP = {
        "small": 28,
        "medium": 34,
        "large": 42,
        "xlarge": 52,
        "mega": 62
    }

    def __init__(self, session):
        # Build dynamic skin based on settings
        bg_style = config.plugins.AISubtitles.background_style.value
        text_color = config.plugins.AISubtitles.text_color.value
        text_size = config.plugins.AISubtitles.text_size.value
        font_type = config.plugins.AISubtitles.font_type.value
        
        # Get actual values
        fg_color = self.COLOR_MAP.get(text_color, "#ffffff")
        font_size = self.SIZE_MAP.get(text_size, 28)
        # Background: transparent, semi_transparent, solid black
        if bg_style == "solid":
            bg_color = "#000000"  # Solid black (no transparency)
        elif bg_style == "semi_transparent":
            bg_color = "#80000000"  # 50% transparent black
        else:
            bg_color = "transparent"
        
        # Build skin dynamically with selected font
        self.skin = """
        <screen name="AISubtitlesOverlay" position="0,0" size="1920,1080" flags="wfNoBorder" backgroundColor="transparent" zPosition="10">
            <widget name="subtitles" position="50,850" size="1820,200" font="{font_type};{font_size}" halign="center" valign="center" foregroundColor="{fg_color}" backgroundColor="{bg_color}" />
            <widget name="status" position="5,5" size="200,35" font="Regular;18" foregroundColor="#00ff00" backgroundColor="#80000000" />
        </screen>
        """.format(font_type=font_type, font_size=font_size, fg_color=fg_color, bg_color=bg_color)
        
        Screen.__init__(self, session)
        self.session = session
        
        self["subtitles"] = Label("")
        self["status"] = Label("Initializing...")
        
        self.console = eConsoleAppContainer()
        self.console.appClosed.append(self.onProcessFinished)
        
        self.stage = self.STAGE_IDLE
        self.api_key_groq = config.plugins.AISubtitles.api_key.value
        self.api_key_gemini = config.plugins.AISubtitles.api_key_gemini.value
        self.api_key_openai = config.plugins.AISubtitles.api_key_openai.value
        self.api_key_deepgram = config.plugins.AISubtitles.api_key_deepgram.value
        self.api_key_assemblyai = config.plugins.AISubtitles.api_key_assemblyai.value
        self.provider_mode = config.plugins.AISubtitles.provider.value
        self.current_provider = "groq"
        self.target_lang_code = config.plugins.AISubtitles.target_language.value
        self.target_lang_name = LANGUAGE_NAMES.get(self.target_lang_code, "Arabic")
        
        # Read provider enable/disable settings (ConfigYesNo returns True/False)
        self.enable_groq = config.plugins.AISubtitles.enable_groq.value
        self.enable_deepgram = config.plugins.AISubtitles.enable_deepgram.value
        self.enable_assemblyai = config.plugins.AISubtitles.enable_assemblyai.value
        self.enable_gemini = config.plugins.AISubtitles.enable_gemini.value
        self.enable_openai = config.plugins.AISubtitles.enable_openai.value
        
        self.wav_path = "/tmp/ai_capture.wav"
        self.raw_path = "/tmp/ai_raw.pcm"
        
        # Performance: Audio hash cache to skip duplicate processing
        self._last_audio_hash = ""
        self._consecutive_empty = 0
        self._retry_delay = 300  # Start with fast retry, increase on empty
        
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "cancel": self.close, "exit": self.close, "red": self.close
        }, -2)
        
        self.onLayoutFinish.append(self.startCycle)

    def getFirstEnabledProvider(self):
        """Get first enabled provider for Auto mode"""
        if self.enable_groq:
            return "groq"
        elif self.enable_deepgram:
            return "deepgram"
        elif self.enable_assemblyai:
            return "assemblyai"
        elif self.enable_gemini:
            return "gemini"
        elif self.enable_openai:
            return "openai"
        return None  # No providers enabled

    def getNextEnabledProvider(self, current):
        """Get next enabled provider after current one"""
        providers = ["groq", "deepgram", "assemblyai", "gemini", "openai"]
        enables = [self.enable_groq, self.enable_deepgram, self.enable_assemblyai, self.enable_gemini, self.enable_openai]
        
        try:
            current_idx = providers.index(current)
            for i in range(current_idx + 1, len(providers)):
                if enables[i]:
                    return providers[i]
        except:
            pass
        return None  # No more enabled providers

    def startCycle(self):
        if self.provider_mode == "auto":
            self.current_provider = self.getFirstEnabledProvider()
        else:
            self.current_provider = self.provider_mode
        
        # Check if any provider is enabled
        if not self.current_provider:
            self["status"].setText("No Provider!")
            self["subtitles"].setText("Enable a provider in settings")
            return
        
        self["status"].setText("Live ({})".format(self.current_provider.upper()))
        self.startCapture()

    def extractIptvUrl(self, sref_str):
        try:
            parts = sref_str.split(':')
            if len(parts) >= 10:
                url_part = ':'.join(parts[10:])
                if url_part:
                    try:
                        import urllib
                        stream_url = urllib.unquote(url_part)
                    except:
                        from urllib.parse import unquote
                        stream_url = unquote(url_part)
                    
                    stream_url = stream_url.strip()
                    
                    # Fix 0.0.0.0 address - replace with 127.0.0.1
                    if '0.0.0.0' in stream_url:
                        stream_url = stream_url.replace('0.0.0.0', '127.0.0.1')
                    
                    # Handle StreamRelay URLs (e.g., /abertis/pid8002)
                    # These don't have file extensions, so don't strip them
                    is_streamrelay = '/abertis/' in stream_url or ':9999/' in stream_url
                    
                    if not is_streamrelay:
                        # Remove channel name after .ts, .m3u8, etc. for regular IPTV
                        for ext in ['.ts', '.m3u8', '.flv', '.mp4', '.mkv']:
                            if ext in stream_url:
                                idx = stream_url.find(ext) + len(ext)
                                stream_url = stream_url[:idx]
                                break
                    
                    if ' ' in stream_url:
                        stream_url = stream_url.split(' ')[0]
                    
                    if stream_url.startswith('http'):
                        return stream_url
        except:
            pass
        return None

    def startCapture(self):
        self.stage = self.STAGE_DOWNLOAD
        
        sref = self.session.nav.getCurrentlyPlayingServiceReference()
        if not sref:
            self["status"].setText("No Service")
            return

        sref_str = sref.toString()
        is_iptv = sref_str.startswith('4097:') or sref_str.startswith('5001:') or sref_str.startswith('5002:') or sref_str.startswith('8193:')
        
        # Check for StreamRelay channels - DVB style sref with embedded URL
        # Pattern: contains 0.0.0.0 or abertis or :9999/
        is_streamrelay = '0.0.0.0' in sref_str or '/abertis/' in sref_str or ':9999/' in sref_str or '%3a9999' in sref_str
        
        # Always log for debugging
        try:
            with open("/tmp/ai_debug.log", "w") as f:
                f.write("sref={}\n".format(sref_str[:200]))
                f.write("is_iptv={}\n".format(is_iptv))
                f.write("is_streamrelay={}\n".format(is_streamrelay))
        except: pass
        
        try:
            if os.path.exists(self.wav_path): os.remove(self.wav_path)
            if os.path.exists(self.raw_path): os.remove(self.raw_path)
        except: pass

        if is_iptv:
            stream_url = self.extractIptvUrl(sref_str)
            if stream_url:
                # Detect StreamRelay by URL pattern
                is_relay = '/abertis/' in stream_url or ':9999/' in stream_url
                
                if is_relay:
                    self["status"].setText("Rec (Relay)...")
                else:
                    self["status"].setText("Rec (IPTV)...")
                # Use uridecodebin for all IPTV - better compatibility
                cmd = "sh -c \"timeout 3 gst-launch-1.0 -q uridecodebin uri='{}' ! audioconvert ! audioresample ! audio/x-raw,rate=16000,channels=1,format=S16LE ! filesink location='{}'\"".format(stream_url, self.raw_path)
                capture_time = 4000
                
                with open("/tmp/ai_iptv_url.log", "w") as f:
                    f.write("relay={} url={}".format(is_relay, stream_url))
            else:
                self["status"].setText("Err: No URL")
                self.scheduleRetry(1000)
                return
        elif is_streamrelay:
            self["status"].setText("Rec (Relay)...")
            # Extract URL from DVB-style sref with embedded URL
            # Format: 1:0:1:...:http%3a//0.0.0.0%3a9999/abertis/pid8001:name
            stream_url = None
            try:
                # URL is after the 10th colon, URL-encoded
                parts = sref_str.split(':')
                if len(parts) >= 11:
                    url_part = parts[10]
                    try:
                        import urllib
                        stream_url = urllib.unquote(url_part)
                    except:
                        from urllib.parse import unquote
                        stream_url = unquote(url_part)
                    # Fix 0.0.0.0 to 127.0.0.1
                    if stream_url and '0.0.0.0' in stream_url:
                        stream_url = stream_url.replace('0.0.0.0', '127.0.0.1')
            except:
                pass
            
            if stream_url and stream_url.startswith('http'):
                with open("/tmp/ai_iptv_url.log", "w") as f:
                    f.write("streamrelay url={}".format(stream_url))
                cmd = "sh -c \"timeout 4 gst-launch-1.0 -q uridecodebin uri='{}' ! audioconvert ! audioresample ! audio/x-raw,rate=16000,channels=1,format=S16LE ! filesink location='{}'\"".format(stream_url, self.raw_path)
                capture_time = 5000
            else:
                self["status"].setText("Err: Relay URL")
                self.scheduleRetry(1000)
                return
        else:
            # DVB channel - use gstreamer souphttpsrc
            url = "http://127.0.0.1:8001/" + sref_str
            self["status"].setText("Rec (DVB)...")
            cmd = "sh -c \"timeout 4 gst-launch-1.0 -q souphttpsrc location='{}' ! decodebin ! audioconvert ! audioresample ! audio/x-raw,rate=16000,channels=1,format=S16LE ! filesink location='{}'\"".format(url, self.raw_path)
            capture_time = 4500
        
        self.console.execute(cmd)
        
        self.capture_timer = eTimer()
        self.capture_timer.callback.append(self.stopCapturePipe)
        self.capture_timer.start(capture_time, True)

    def stopCapturePipe(self):
        self.console.sendCtrlC() 
        self.kill_timer = eTimer()
        self.kill_timer.callback.append(self.forceFinish)
        self.kill_timer.start(1500, True)

    def forceFinish(self):
        self.console.kill()
        self.onProcessFinished(0)

    def writeWavHeader(self, raw_path, wav_path):
        """Convert raw PCM to WAV - optimized with in-memory buffer"""
        try:
            with open(raw_path, "rb") as inp:
                audio_data = inp.read()
            
            data_size = len(audio_data)
            
            # Build WAV in memory first (faster than sequential disk writes)
            buf = io.BytesIO()
            buf.write(b"RIFF")
            buf.write((data_size + 36).to_bytes(4, 'little'))
            buf.write(b"WAVE")
            buf.write(b"fmt ")
            buf.write((16).to_bytes(4, 'little'))
            buf.write((1).to_bytes(2, 'little'))  # PCM format
            buf.write((1).to_bytes(2, 'little'))  # 1 channel
            buf.write((16000).to_bytes(4, 'little'))  # Sample rate
            buf.write((32000).to_bytes(4, 'little'))  # Byte rate
            buf.write((2).to_bytes(2, 'little'))  # Block align
            buf.write((16).to_bytes(2, 'little'))  # Bits per sample
            buf.write(b"data")
            buf.write(data_size.to_bytes(4, 'little'))
            buf.write(audio_data)
            
            # Single write to disk
            with open(wav_path, "wb") as out:
                out.write(buf.getvalue())
            
            return True
        except:
            return False

    def onProcessFinished(self, retval):
        if hasattr(self, 'capture_timer'): self.capture_timer.stop()
        if hasattr(self, 'kill_timer'): self.kill_timer.stop()

        if self.stage == self.STAGE_DOWNLOAD:
            # Check for WAV file first (from ffmpeg/StreamRelay)
            wav_exists = os.path.exists(self.wav_path) and os.path.getsize(self.wav_path) > 5000
            raw_exists = os.path.exists(self.raw_path) and os.path.getsize(self.raw_path) > 5000
            
            if wav_exists:
                # WAV file already created by ffmpeg, proceed directly
                pass
            elif raw_exists:
                # RAW file from gstreamer, need to add WAV header
                if not self.writeWavHeader(self.raw_path, self.wav_path):
                    self["status"].setText("Err: WAV")
                    self.scheduleRetry(1000)
                    return
                try:
                    if os.path.exists(self.raw_path): os.remove(self.raw_path)
                except: pass
            else:
                # Capture failed, retry quickly
                self["status"].setText("Retry...")
                self.scheduleRetry(self._retry_delay)
                return

            # Performance: Audio hash check DISABLED to prevent skipping sentences
            # The hash check was causing some sentences to be skipped
            # TODO: Re-enable with smarter logic if needed
            # try:
            #     with open(self.wav_path, "rb") as f:
            #         audio_hash = hashlib.md5(f.read()).hexdigest()
            #     if audio_hash == self._last_audio_hash:
            #         self._consecutive_empty += 1
            #         if self._consecutive_empty > 3:
            #             self._retry_delay = min(1500, self._retry_delay + 200)
            #         self.restartLoop()
            #         return
            #     self._last_audio_hash = audio_hash
            #     self._consecutive_empty = 0
            #     self._retry_delay = 300
            # except:
            #     pass

            self.stage = self.STAGE_TRANSCRIBE
            if self.current_provider == "gemini":
                self.doGeminiProcess()
            elif self.current_provider == "openai":
                self.doOpenAIProcess()
            elif self.current_provider == "deepgram":
                self.doDeepgramProcess()
            elif self.current_provider == "assemblyai":
                self.doAssemblyAIProcess()
            else:
                self.doGroqTranscribe()
                
        elif self.stage == self.STAGE_TRANSCRIBE:
            if self.current_provider == "groq":
                self.doGroqTranslate()
            elif self.current_provider == "openai":
                self.doOpenAITranslate()
            elif self.current_provider == "deepgram":
                self.showResultDeepgram()
            elif self.current_provider == "assemblyai":
                self.showResultAssemblyAI()
            else:
                self.showResultGemini()

        elif self.stage == self.STAGE_TRANSLATE:
            if self.current_provider == "openai":
                self.showResultOpenAI()
            elif self.current_provider == "assemblyai":
                self.showResultAssemblyAIPoll()
            else:
                self.showResult()

        elif self.stage == self.STAGE_GEMINI:
            self.showResultGemini()

    def doGroqTranscribe(self):
        self.stage = self.STAGE_TRANSCRIBE
        self["status"].setText("Transcribing...")

        if not self.api_key_groq.startswith("gsk_"):
             self.handleFail("Invalid Groq Key")
             return

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        cmd = 'curl -k -s --max-time 15 -X POST "{}" -H "Authorization: Bearer {}" -F "file=@{}" -F "model=whisper-large-v3" -F "response_format=json" > /tmp/groq_transcribe.json'.format(url, self.api_key_groq.strip(), self.wav_path)
        self.console.execute(cmd)

    def doGeminiProcess(self):
        self.stage = self.STAGE_GEMINI
        self["status"].setText("Gemini...")
        
        if not self.api_key_gemini:
            self["status"].setText("No Gemini Key!")
            return

        import base64, json
        try:
            with open(self.wav_path, "rb") as wav_file:
                b64_audio = base64.b64encode(wav_file.read()).decode('utf-8')
        except:
             self.handleFail("Read WAV Fail")
             return

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=" + self.api_key_gemini.strip()
        
        prompt_text = "Listen to this audio, transcribe it, and translate it to {}. Return ONLY the {} text. If no speech, return nothing.".format(self.target_lang_name, self.target_lang_name)
        payload = {"contents": [{"parts": [{"text": prompt_text}, {"inline_data": {"mime_type": "audio/wav", "data": b64_audio}}]}]}
        
        with open("/tmp/gemini_payload.json", "w") as f:
            json.dump(payload, f)
            
        cmd = "curl -k -s --max-time 20 -X POST '{}' -H 'Content-Type: application/json' -d @/tmp/gemini_payload.json > /tmp/gemini_result.json".format(url)
        self.console.execute(cmd)

    def doDeepgramProcess(self):
        """Deepgram Speech-to-Text"""
        self.stage = self.STAGE_TRANSCRIBE
        self["status"].setText("Deepgram...")
        
        if not self.api_key_deepgram:
            self["status"].setText("No Deepgram Key!")
            self.scheduleRetry(1000)
            return
        
        # Check if wav file exists
        if not os.path.exists(self.wav_path) or os.path.getsize(self.wav_path) < 1000:
            self["status"].setText("DG: No Audio")
            self.scheduleRetry(1000)
            return
        
        # Deepgram API - transcription only, translation done by Groq later
        url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&punctuate=true"
        
        cmd = 'curl -k -s --max-time 20 -X POST "{}" -H "Authorization: Token {}" -H "Content-Type: audio/wav" --data-binary @{} > /tmp/deepgram_result.json'.format(url, self.api_key_deepgram.strip(), self.wav_path)
        self.console.execute(cmd)

    def showResultDeepgram(self):
        """Show Deepgram transcription result and translate if needed"""
        self.stage = self.STAGE_IDLE
        import json
        try:
            if os.path.exists("/tmp/deepgram_result.json"):
                with open("/tmp/deepgram_result.json", "r") as f:
                    response = json.load(f)
                
                # Check for error
                if 'error' in response or 'err_code' in response:
                    err_msg = response.get('error', response.get('err_msg', 'API Error'))
                    self["status"].setText("DG: " + str(err_msg)[:20])
                    self.restartLoop()
                    return
                
                # Extract transcript
                if 'results' in response and 'channels' in response['results']:
                    channels = response['results']['channels']
                    if channels and len(channels) > 0:
                        alternatives = channels[0].get('alternatives', [])
                        if alternatives and len(alternatives) > 0:
                            transcript = alternatives[0].get('transcript', '').strip()
                            
                            if transcript and len(transcript) > 1:
                                # If target is not English, translate using Groq
                                if self.target_lang_code != "en":
                                    self.deepgram_transcript = transcript
                                    self.doDeepgramTranslate()
                                    return
                                else:
                                    formatted = self.formatSubtitle(transcript)
                                    self["subtitles"].setText(formatted)
                                    self["status"].setText("")
                            else:
                                self["status"].setText("DG: No Speech")
                        else:
                            self["status"].setText("DG: Empty")
                    else:
                        self["status"].setText("DG: No Channels")
                else:
                    self["status"].setText("DG: Bad Response")
        except Exception as e:
            self["status"].setText("DG Parse Err")
        self.restartLoop()

    def doDeepgramTranslate(self):
        """Translate Deepgram transcript using Groq LLM"""
        import json
        self.stage = self.STAGE_TRANSLATE
        self["status"].setText("Translating...")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        prompt = "Translate this text to {}. Return ONLY the translation: ".format(self.target_lang_name) + self.deepgram_transcript
        json_payload = '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":' + json.dumps(prompt) + '}]}'
        
        with open("/tmp/groq_payload.json", "w") as f:
            f.write(json_payload)
            
        cmd = "curl -k -s --max-time 10 -X POST '{}' -H 'Authorization: Bearer {}' -H 'Content-Type: application/json' -d @/tmp/groq_payload.json > /tmp/groq_translate.json".format(url, self.api_key_groq)
        self.console.execute(cmd)

    def doAssemblyAIProcess(self):
        """AssemblyAI Speech-to-Text - uses upload then transcribe flow"""
        self.stage = self.STAGE_TRANSCRIBE
        self["status"].setText("AssemblyAI...")
        
        if not self.api_key_assemblyai:
            self["status"].setText("No AAI Key!")
            self.scheduleRetry(1000)
            return
        
        # Check if wav file exists
        if not os.path.exists(self.wav_path) or os.path.getsize(self.wav_path) < 1000:
            self["status"].setText("AAI: No Audio")
            self.scheduleRetry(1000)
            return
        
        # AssemblyAI requires: 1) Upload audio, 2) Create transcription, 3) Poll for result
        # For simplicity, we'll use their synchronous endpoint in one step
        # First upload the file and get upload_url
        upload_url = "https://api.assemblyai.com/v2/upload"
        
        cmd = 'curl -k -s --max-time 15 -X POST "{}" -H "authorization: {}" -H "content-type: application/octet-stream" --data-binary @{} > /tmp/assemblyai_upload.json'.format(upload_url, self.api_key_assemblyai.strip(), self.wav_path)
        self.console.execute(cmd)

    def showResultAssemblyAI(self):
        """Process AssemblyAI upload result and start transcription"""
        import json
        
        # Check upload result
        try:
            if os.path.exists("/tmp/assemblyai_upload.json"):
                with open("/tmp/assemblyai_upload.json", "r") as f:
                    upload_data = json.load(f)
                
                if 'error' in upload_data:
                    self["status"].setText("AAI: " + str(upload_data['error'])[:20])
                    self.stage = self.STAGE_IDLE
                    self.restartLoop()
                    return
                
                audio_url = upload_data.get('upload_url', '')
                if not audio_url:
                    self["status"].setText("AAI: No Upload URL")
                    self.stage = self.STAGE_IDLE
                    self.restartLoop()
                    return
                
                # Now create transcription request
                self["status"].setText("AAI Transcribing...")
                self.assemblyai_audio_url = audio_url
                self.doAssemblyAITranscribe()
                return
        except Exception as e:
            self["status"].setText("AAI Err")
        
        self.stage = self.STAGE_IDLE
        self.restartLoop()

    def doAssemblyAITranscribe(self):
        """Start AssemblyAI transcription job"""
        import json
        
        transcribe_url = "https://api.assemblyai.com/v2/transcript"
        payload = {
            "audio_url": self.assemblyai_audio_url,
            "language_detection": True
        }
        
        with open("/tmp/assemblyai_req.json", "w") as f:
            json.dump(payload, f)
        
        cmd = "curl -k -s --max-time 15 -X POST '{}' -H 'authorization: {}' -H 'content-type: application/json' -d @/tmp/assemblyai_req.json > /tmp/assemblyai_transcript.json".format(transcribe_url, self.api_key_assemblyai)
        self.console.execute(cmd)
        
        # After this completes, we need to poll for results
        self.stage = self.STAGE_TRANSLATE  # Reuse for polling step

    def showResultAssemblyAIPoll(self):
        """Poll AssemblyAI for transcription result"""
        import json
        
        try:
            if os.path.exists("/tmp/assemblyai_transcript.json"):
                with open("/tmp/assemblyai_transcript.json", "r") as f:
                    data = json.load(f)
                
                transcript_id = data.get('id', '')
                status = data.get('status', '')
                
                if status == 'completed':
                    text = data.get('text', '').strip()
                    if text and len(text) > 1:
                        if self.target_lang_code != "en":
                            self.assemblyai_transcript = text
                            self.doAssemblyAITranslate()
                            return
                        else:
                            formatted = self.formatSubtitle(text)
                            self["subtitles"].setText(formatted)
                            self["status"].setText("")
                    else:
                        self["status"].setText("AAI: No Speech")
                elif status == 'queued' or status == 'processing':
                    # Need to poll again
                    self["status"].setText("AAI: " + status)
                    poll_url = "https://api.assemblyai.com/v2/transcript/" + transcript_id
                    cmd = "curl -k -s --max-time 10 -X GET '{}' -H 'authorization: {}' > /tmp/assemblyai_transcript.json".format(poll_url, self.api_key_assemblyai)
                    self.console.execute(cmd)
                    return
                elif status == 'error':
                    self["status"].setText("AAI: Error")
                else:
                    # Initial response - need to poll
                    if transcript_id:
                        poll_url = "https://api.assemblyai.com/v2/transcript/" + transcript_id
                        cmd = "curl -k -s --max-time 10 -X GET '{}' -H 'authorization: {}' > /tmp/assemblyai_transcript.json".format(poll_url, self.api_key_assemblyai)
                        self.console.execute(cmd)
                        return
        except Exception as e:
            self["status"].setText("AAI Parse Err")
        
        self.stage = self.STAGE_IDLE
        self.restartLoop()

    def doAssemblyAITranslate(self):
        """Translate AssemblyAI transcript using Groq LLM"""
        import json
        self.stage = self.STAGE_TRANSLATE
        self["status"].setText("Translating...")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        prompt = "Translate this text to {}. Return ONLY the translation: ".format(self.target_lang_name) + self.assemblyai_transcript
        json_payload = '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":' + json.dumps(prompt) + '}]}'
        
        with open("/tmp/groq_payload.json", "w") as f:
            f.write(json_payload)
            
        cmd = "curl -k -s --max-time 10 -X POST '{}' -H 'Authorization: Bearer {}' -H 'Content-Type: application/json' -d @/tmp/groq_payload.json > /tmp/groq_translate.json".format(url, self.api_key_groq)
        self.console.execute(cmd)

    def doGroqTranslate(self):
        import json
        text = ""
        try:
            if os.path.exists("/tmp/groq_transcribe.json"):
                with open("/tmp/groq_transcribe.json", "r") as f:
                    data = json.load(f)
                    if 'text' in data:
                        text = data['text'].strip()
        except: pass
        
        if not text or len(text) < 2:
            if self.provider_mode == "auto":
                # Try next enabled provider
                next_provider = self.getNextEnabledProvider(self.current_provider)
                if next_provider:
                    self.current_provider = next_provider
                    self["status"].setText("-> " + next_provider.upper())
                    if next_provider == "deepgram":
                        self.doDeepgramProcess()
                    elif next_provider == "assemblyai":
                        self.doAssemblyAIProcess()
                    elif next_provider == "gemini":
                        self.doGeminiProcess()
                    elif next_provider == "openai":
                        self.doOpenAIProcess()
                    return

            self["status"].setText("No Speech")
            self.restartLoop()
            return

        self.stage = self.STAGE_TRANSLATE
        self["status"].setText("Translating...")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        prompt = "Translate this text to {}. Return ONLY the translation: ".format(self.target_lang_name) + text
        json_payload = '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":' + json.dumps(prompt) + '}]}'
        
        with open("/tmp/groq_payload.json", "w") as f:
            f.write(json_payload)
            
        cmd = "curl -k -s --max-time 10 -X POST '{}' -H 'Authorization: Bearer {}' -H 'Content-Type: application/json' -d @/tmp/groq_payload.json > /tmp/groq_translate.json".format(url, self.api_key_groq)
        self.console.execute(cmd)

    def formatSubtitle(self, text, max_chars_per_line=50, max_lines=2):
        """Format subtitle to max 2 lines, 50 chars each"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = ' '.join(text.split())
        
        # If text is short enough, return as is
        if len(text) <= max_chars_per_line:
            return text
        
        # Split into words
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars_per_line:
                current_line = (current_line + " " + word).strip()
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                if len(lines) >= max_lines:
                    break
        
        # Add last line if within limit
        if current_line and len(lines) < max_lines:
            lines.append(current_line)
        
        return "\n".join(lines)

    def showResultGemini(self):
        self.stage = self.STAGE_IDLE
        import json
        try:
            if os.path.exists("/tmp/gemini_result.json"):
                with open("/tmp/gemini_result.json", "r") as f:
                    response = json.load(f)
                if 'candidates' in response and len(response['candidates']) > 0:
                    parts = response['candidates'][0]['content']['parts']
                    content = parts[0]['text'].strip()
                    formatted = self.formatSubtitle(content)
                    self["subtitles"].setText(formatted)
                    self["status"].setText("")
                else:
                    self["status"].setText("Gemini Empty")
        except:
             self["status"].setText("Gemini Err")
        self.restartLoop()

    def showResult(self):
        self.stage = self.STAGE_IDLE
        import json
        try:
            if os.path.exists("/tmp/groq_translate.json"):
                with open("/tmp/groq_translate.json", "r") as f:
                    response = json.load(f)
                if 'choices' in response:
                    content = response['choices'][0]['message']['content']
                    formatted = self.formatSubtitle(content)
                    self["subtitles"].setText(formatted)
                    self["status"].setText("")
        except:
             pass
        self.restartLoop()
             
    def scheduleRetry(self, delay):
        self.retry_timer = eTimer() 
        self.retry_timer.callback.append(self.startCycle) 
        self.retry_timer.start(delay, True)

    def restartLoop(self):
        self.loop_timer = eTimer()
        self.loop_timer.callback.append(self.startCycle)
        self.loop_timer.start(500, True)

    def handleFail(self, msg):
        self["status"].setText(msg)
        if self.provider_mode == "auto":
            if self.current_provider == "groq":
                self["status"].setText(msg + " -> Gem")
                self.current_provider = "gemini"
                self.doGeminiProcess()
                return
            elif self.current_provider == "gemini" and self.api_key_openai:
                self["status"].setText(msg + " -> OAI")
                self.current_provider = "openai"
                self.doOpenAIProcess()
                return
        self.scheduleRetry(1000)

    def doOpenAIProcess(self):
        self.stage = self.STAGE_TRANSCRIBE
        self["status"].setText("OAI Whisper...")
        
        if not self.api_key_openai or not self.api_key_openai.startswith("sk-"):
            self["status"].setText("No OpenAI Key!")
            self.scheduleRetry(1000)
            return
        
        # Check if wav file exists and has content
        if not os.path.exists(self.wav_path) or os.path.getsize(self.wav_path) < 1000:
            self["status"].setText("OAI: No Audio")
            self.scheduleRetry(1000)
            return
        
        # Remove old response file
        try:
            if os.path.exists("/tmp/openai_transcribe.json"):
                os.remove("/tmp/openai_transcribe.json")
        except: pass
        
        # Use OpenAI Whisper API - simpler curl command
        url = "https://api.openai.com/v1/audio/transcriptions"
        cmd = 'curl -k -s --connect-timeout 10 --max-time 30 -X POST "{}" -H "Authorization: Bearer {}" -H "Content-Type: multipart/form-data" -F "file=@{}" -F "model=whisper-1" -o /tmp/openai_transcribe.json'.format(url, self.api_key_openai.strip(), self.wav_path)
        self.console.execute(cmd)

    def doOpenAITranslate(self):
        import json
        text = ""
        
        # Check if response file exists
        if not os.path.exists("/tmp/openai_transcribe.json"):
            self["status"].setText("OAI: No Response")
            self.restartLoop()
            return
        
        # Check file size
        fsize = os.path.getsize("/tmp/openai_transcribe.json")
        if fsize < 5:
            self["status"].setText("OAI: Empty File")
            self.restartLoop()
            return
        
        try:
            with open("/tmp/openai_transcribe.json", "r") as f:
                raw_content = f.read()
            
            # Try to parse as JSON
            data = json.loads(raw_content)
            
            # Check for error in response
            if 'error' in data:
                err_msg = data['error'].get('message', 'API Error')[:25]
                self["status"].setText("OAI: " + err_msg)
                self.restartLoop()
                return
            
            if 'text' in data:
                text = data['text'].strip()
                
        except json.JSONDecodeError:
            # Not JSON - might be curl error or HTML
            self["status"].setText("OAI: Not JSON")
            self.restartLoop()
            return
        except Exception as e:
            self["status"].setText("OAI Parse Err")
            self.restartLoop()
            return
        
        if not text or len(text) < 2:
            self["status"].setText("OAI: No Text")
            self.restartLoop()
            return

        self.stage = self.STAGE_TRANSLATE
        self["status"].setText("OAI Translate...")
        
        url = "https://api.openai.com/v1/chat/completions"
        prompt = "Translate this text to {}. Return ONLY the translation: ".format(self.target_lang_name) + text
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
        
        with open("/tmp/openai_payload.json", "w") as f:
            json.dump(payload, f)
        
        cmd = "curl -k -s --max-time 15 -X POST '{}' -H 'Authorization: Bearer {}' -H 'Content-Type: application/json' -d @/tmp/openai_payload.json > /tmp/openai_result.json".format(url, self.api_key_openai)
        self.console.execute(cmd)

    def showResultOpenAI(self):
        self.stage = self.STAGE_IDLE
        import json
        try:
            if os.path.exists("/tmp/openai_result.json"):
                with open("/tmp/openai_result.json", "r") as f:
                    response = json.load(f)
                if 'choices' in response and len(response['choices']) > 0:
                    content = response['choices'][0]['message']['content'].strip()
                    formatted = self.formatSubtitle(content)
                    self["subtitles"].setText(formatted)
                    self["status"].setText("")
                else:
                    self["status"].setText("OpenAI Empty")
        except:
            self["status"].setText("OpenAI Err")
        self.restartLoop()

    def close(self):
        try: self.console.sendCtrlC() 
        except: pass
        Screen.close(self)


class AISubtitlesSettings(ConfigListScreen, Screen):
    skin = """
    <screen name="AISubtitlesSettings" position="center,center" size="800,500" title="AI Subtitles Settings" flags="wfNoBorder" backgroundColor="#99000000">
        <!-- Version label top right -->
        <widget name="version" position="450,10" size="330,40" font="Regular;30" halign="right" valign="center" foregroundColor="#00ddff" backgroundColor="transparent" />
        
        <!-- Config list full width with more height -->
        <widget name="config" position="20,60" size="760,300" scrollbarMode="showOnDemand" backgroundColor="#40000000" itemHeight="38" />
        
        <!-- Credits -->
        <widget name="credits" position="20,370" size="760,35" font="Regular;20" halign="center" valign="center" foregroundColor="#ffff00" backgroundColor="transparent" />
        
        <!-- Buttons: Red=Close, Green=Save, Yellow=Start Live, Blue=Visual Test -->
        <widget name="key_red" position="20,420" size="185,55" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#cc0000" foregroundColor="white" />
        <widget name="key_green" position="215,420" size="185,55" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#00aa00" foregroundColor="white" />
        <widget name="key_yellow" position="410,420" size="185,55" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#ccaa00" foregroundColor="white" />
        <widget name="key_blue" position="605,420" size="185,55" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#0066cc" foregroundColor="white" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.list = []
        ConfigListScreen.__init__(self, self.list)
        self["key_red"] = Label("Close")
        self["key_green"] = Label("Save")
        self["key_yellow"] = Label("Start Live")
        self["key_blue"] = Label("Visual Test")
        self["version"] = Label("AISubtitles v1.8")
        self["credits"] = Label("Developed by ammarbary")
        
        # Update font choices dynamically
        self.updateFontChoices()
        
        self.createConfigList()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "save": self.save, "cancel": self.close, "ok": self.handleOk, "yellow": self.startOverlay, "red": self.close, "blue": self.visualTest
        }, -2)
        
        # Track which config we're editing
        self.editing_config = None
        self.editing_provider = None
    
    def updateFontChoices(self):
        """Update font choices by scanning /usr/share/fonts"""
        fonts = scanAvailableFonts()
        # Update the config choices
        config.plugins.AISubtitles.font_type.setChoices(fonts, default="Regular")

    def createConfigList(self):
        self.list = []
        self.list.append(getConfigListEntry("Provider", config.plugins.AISubtitles.provider))
        self.list.append(getConfigListEntry("Target Language", config.plugins.AISubtitles.target_language))
        self.list.append(getConfigListEntry("Show API Keys", config.plugins.AISubtitles.show_keys))
        
        # Show API keys or masked version
        if config.plugins.AISubtitles.show_keys.value == "true":
            self.list.append(getConfigListEntry("Groq API Key", config.plugins.AISubtitles.api_key))
            self.list.append(getConfigListEntry("Deepgram API Key", config.plugins.AISubtitles.api_key_deepgram))
            self.list.append(getConfigListEntry("AssemblyAI API Key", config.plugins.AISubtitles.api_key_assemblyai))
            self.list.append(getConfigListEntry("Gemini API Key", config.plugins.AISubtitles.api_key_gemini))
            self.list.append(getConfigListEntry("OpenAI API Key", config.plugins.AISubtitles.api_key_openai))
        else:
            # Just show that keys are set (masked with ****)
            self.list.append(getConfigListEntry("Groq API Key", config.plugins.AISubtitles.hidden_key))
            self.list.append(getConfigListEntry("Deepgram API Key", config.plugins.AISubtitles.hidden_key))
            self.list.append(getConfigListEntry("AssemblyAI API Key", config.plugins.AISubtitles.hidden_key))
            self.list.append(getConfigListEntry("Gemini API Key", config.plugins.AISubtitles.hidden_key))
            self.list.append(getConfigListEntry("OpenAI API Key", config.plugins.AISubtitles.hidden_key))
        
        self.list.append(getConfigListEntry("======== PROVIDERS ========", config.plugins.AISubtitles.section_header))
        self.list.append(getConfigListEntry("Groq", config.plugins.AISubtitles.enable_groq))
        self.list.append(getConfigListEntry("Deepgram", config.plugins.AISubtitles.enable_deepgram))
        self.list.append(getConfigListEntry("AssemblyAI", config.plugins.AISubtitles.enable_assemblyai))
        self.list.append(getConfigListEntry("Gemini", config.plugins.AISubtitles.enable_gemini))
        self.list.append(getConfigListEntry("OpenAI", config.plugins.AISubtitles.enable_openai))
        
        self.list.append(getConfigListEntry("======= APPEARANCE =======", config.plugins.AISubtitles.section_header))
        self.list.append(getConfigListEntry("Background Style", config.plugins.AISubtitles.background_style))
        self.list.append(getConfigListEntry("Text Color", config.plugins.AISubtitles.text_color))
        self.list.append(getConfigListEntry("Text Size", config.plugins.AISubtitles.text_size))
        self.list.append(getConfigListEntry("Font Type", config.plugins.AISubtitles.font_type))
        self["config"].setList(self.list)

    def handleOk(self):
        """Handle OK button - show choice dialog for API keys or ConfigSelection items"""
        current = self["config"].getCurrent()
        if current:
            label = current[0]
            config_item = current[1]
            
            # Check if it's an API key field
            api_key_map = {
                config.plugins.AISubtitles.api_key: "groq",
                config.plugins.AISubtitles.api_key_gemini: "gemini",
                config.plugins.AISubtitles.api_key_openai: "openai",
                config.plugins.AISubtitles.api_key_deepgram: "deepgram",
                config.plugins.AISubtitles.api_key_assemblyai: "assemblyai"
            }
            
            if config_item in api_key_map:
                self.showKeyInputChoice(api_key_map[config_item], config_item)
                return
            
            # Check if it's a hidden API key field (hidden_key with ****)
            if config_item == config.plugins.AISubtitles.hidden_key:
                # Determine which provider based on label
                label_to_provider = {
                    "Groq API Key": ("groq", config.plugins.AISubtitles.api_key),
                    "Gemini API Key": ("gemini", config.plugins.AISubtitles.api_key_gemini),
                    "OpenAI API Key": ("openai", config.plugins.AISubtitles.api_key_openai),
                    "Deepgram API Key": ("deepgram", config.plugins.AISubtitles.api_key_deepgram),
                    "AssemblyAI API Key": ("assemblyai", config.plugins.AISubtitles.api_key_assemblyai)
                }
                if label in label_to_provider:
                    provider, actual_config = label_to_provider[label]
                    self.showKeyInputChoice(provider, actual_config)
                    return
            
            # Skip section headers
            if config_item == config.plugins.AISubtitles.section_header:
                return
            
            # Check if it's a ConfigSelection item - show dropdown
            if hasattr(config_item, 'choices') and config_item.choices:
                self.showSelectionChoice(label, config_item)
                return
        
        # For other items, just save
        self.save()

    def showSelectionChoice(self, label, config_item):
        """Show ChoiceBox for ConfigSelection items"""
        self.editing_config = config_item
        
        # Build choices list from config choices
        choices = []
        for choice in config_item.choices.choices:
            # choice is (value, display_text)
            choices.append((choice[1], choice[0]))
        
        self.session.openWithCallback(
            self.selectionChoiceCallback,
            ChoiceBox,
            title=label,
            list=choices
        )

    def selectionChoiceCallback(self, choice):
        """Handle ConfigSelection choice"""
        if choice and self.editing_config:
            self.editing_config.value = choice[1]
            self.createConfigList()

    def showKeyInputChoice(self, provider, config_item):
        """Show choice dialog: Import from file or Manual entry"""
        self.editing_config = config_item
        self.editing_provider = provider
        
        choices = [
            ("Import from File (/etc/)", "import"),
            ("Manual Entry (Keyboard)", "keyboard")
        ]
        
        self.session.openWithCallback(
            self.keyInputChoiceCallback,
            ChoiceBox,
            title="Enter {} API Key".format(provider.upper()),
            list=choices
        )

    def keyInputChoiceCallback(self, choice):
        """Handle choice selection"""
        if choice:
            if choice[1] == "import":
                self.importFromFile()
            elif choice[1] == "keyboard":
                self.openKeyboard()

    def importFromFile(self):
        """Import API key from file in /etc/"""
        if not self.editing_provider:
            return
        
        filepath = API_KEY_FILES.get(self.editing_provider, "")
        if not filepath:
            self.session.open(MessageBox, "No file path defined for {}".format(self.editing_provider), MessageBox.TYPE_ERROR, timeout=3)
            return
        
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    key = f.read().strip()
                    if key:
                        self.editing_config.value = key
                        self.createConfigList()
                        self.session.open(MessageBox, "Key imported from:\n{}".format(filepath), MessageBox.TYPE_INFO, timeout=3)
                    else:
                        self.session.open(MessageBox, "File is empty:\n{}".format(filepath), MessageBox.TYPE_WARNING, timeout=3)
            except Exception as e:
                self.session.open(MessageBox, "Error reading file:\n{}".format(str(e)), MessageBox.TYPE_ERROR, timeout=3)
        else:
            self.session.open(MessageBox, "File not found:\n{}\\n\\nCreate this file with your API key.".format(filepath), MessageBox.TYPE_ERROR, timeout=5)

    def openKeyboard(self):
        """Open virtual keyboard for manual entry"""
        if not self.editing_config:
            return
        
        current_value = self.editing_config.value if self.editing_config.value else ""
        self.session.openWithCallback(
            self.keyboardCallback,
            VirtualKeyBoard,
            title="Enter {} API Key".format(self.editing_provider.upper() if self.editing_provider else "API"),
            text=current_value
        )

    def keyboardCallback(self, text):
        """Handle keyboard input"""
        if text is not None and self.editing_config:
            self.editing_config.value = text
            self.createConfigList()

    def save(self):
        for x in self["config"].list:
            x[1].save()
        config.plugins.AISubtitles.save()

    def startOverlay(self):
        self.session.open(AISubtitlesOverlay)

    def visualTest(self):
        self.session.open(AISubtitlesPreview)


class AISubtitlesPreview(Screen):
    def __init__(self, session):
        # Build dynamic skin based on settings
        bg_style = config.plugins.AISubtitles.background_style.value
        text_color = config.plugins.AISubtitles.text_color.value
        text_size = config.plugins.AISubtitles.text_size.value
        font_type = config.plugins.AISubtitles.font_type.value
        
        COLOR_MAP = {"white": "#ffffff", "yellow": "#ffff00", "green": "#00ff00", "cyan": "#00ffff", "orange": "#ff8800"}
        SIZE_MAP = {"small": 28, "medium": 34, "large": 42, "xlarge": 52, "mega": 62}
        
        fg_color = COLOR_MAP.get(text_color, "#ffffff")
        font_size = SIZE_MAP.get(text_size, 28)
        # Background: transparent, semi_transparent, solid black
        if bg_style == "solid":
            bg_color = "#000000"  # Solid black (no transparency)
        elif bg_style == "semi_transparent":
            bg_color = "#80000000"  # 50% transparent black
        else:
            bg_color = "transparent"
        
        self.skin = """
        <screen name="AISubtitlesPreview" position="0,0" size="1920,1080" flags="wfNoBorder" backgroundColor="transparent" zPosition="10">
            <widget name="preview" position="50,850" size="1820,200" font="{font_type};{font_size}" halign="center" valign="center" foregroundColor="{fg_color}" backgroundColor="{bg_color}" />
            <widget name="info" position="50,50" size="500,40" font="{font_type};20" foregroundColor="#00aaff" backgroundColor="#80000000" />
        </screen>
        """.format(font_type=font_type, font_size=font_size, fg_color=fg_color, bg_color=bg_color)
        
        Screen.__init__(self, session)
        self["preview"] = Label("Sample Subtitle Preview Text")
        self["info"] = Label("Font: {} - Press EXIT".format(font_type))
        
        self["actions"] = ActionMap(["SetupActions"], {
            "cancel": self.close, "ok": self.close
        }, -2)


def main(session, **kwargs):
    session.open(AISubtitlesSettings)

def startSubtitles(session, **kwargs):
    """Direct start of subtitles overlay - for Red button"""
    session.open(AISubtitlesOverlay)

def autostart(reason, **kwargs):
    """Extend InfoBar with Red button handler"""
    if reason == 0:
        try:
            from Screens.InfoBar import InfoBar
            
            # Save original __init__
            original_init = InfoBar.__init__
            
            def new_init(self, session):
                original_init(self, session)
                # Add our action after InfoBar is fully initialized
                from Components.ActionMap import ActionMap
                self["AISubtitlesRedAction"] = ActionMap(["ColorActions"], {
                    "red": lambda: session.open(AISubtitlesOverlay)
                }, 0)  # Priority 0
            
            InfoBar.__init__ = new_init
        except Exception as e:
            print("[AISubtitles] Autostart error: {}".format(str(e)))

def Plugins(**kwargs):
    return [
        PluginDescriptor(name="AI Live Subtitles", description="Real-time Translation & Subtitles", where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
        PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
        PluginDescriptor(name="AI Subtitles", description="Start AI Subtitles", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=startSubtitles)
    ]

