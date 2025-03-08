import streamlit as st
import chess
import chess.svg
import streamlit.components.v1 as components
import base64
import os
import subprocess
import time
import openai
import azure.cognitiveservices.speech as speechsdk
import platform

# ------------------------------------------------
#   LCZero & GPT Setup
# ------------------------------------------------
if platform.system() == "Windows":
    LCZERO_PATH = r"C:\LCZero\lc0.exe"  # Windows Path
else:
    LCZERO_PATH = "/usr/local/bin/lc0"  # Linux Path (adjust if needed)

# Securely fetch API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_VERSION = "2025-02-01-preview"
SPEECH_API_KEY = os.getenv("AZURE_SPEECH_API_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

if not OPENAI_API_KEY or not SPEECH_API_KEY or not AZURE_OPENAI_ENDPOINT or not SPEECH_REGION:
    st.error("Missing API keys! Please configure them in the environment settings.")

st.set_page_config(page_title="AI Chess Tutor with LCZero & GPT", layout="wide")

# ------------------------------------------------
#   LCZero Load Function
# ------------------------------------------------
def load_lczero():
    """Check if LCZero is available."""
    if not os.path.exists(LCZERO_PATH):
        st.error("LCZero executable not found! Check the path.")
        return None
    return LCZERO_PATH

# ------------------------------------------------
#   Azure Text-to-Speech Function
# ------------------------------------------------
def text_to_speech(text):
    """Convert text to speech using Azure's Speech API."""
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_API_KEY, region=SPEECH_REGION)
        speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesis successful!")
        elif result.reason == speechsdk.ResultReason.Canceled:
            print(f"Speech synthesis canceled: {result.cancellation_details.reason}")
    except Exception as e:
        print(f"Error during text-to-speech synthesis: {e}")

# ------------------------------------------------
#   Render Chess Board SVG
# ------------------------------------------------
def render_svg(svg_code):
    """Render SVG as an HTML component with a fixed width."""
    b64 = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}" width="450">'

# ------------------------------------------------
#   GPT Move Explanation Function
# ------------------------------------------------
def get_move_explanation(board, move_san):
    """Use GPT to explain why the move is recommended."""
    try:
        client = openai.AzureOpenAI(api_key=OPENAI_API_KEY, azure_endpoint=AZURE_OPENAI_ENDPOINT, api_version=AZURE_OPENAI_VERSION)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a chess coach."},
                {"role": "user", "content": f"In the position ({board.fen()}), why is {move_san} a good move? Also, what would be the best response?"}
            ],
            temperature=0.7,
            max_tokens=250
        )
        return response.choices[0].message.content
    except Exception:
        return "Error getting explanation."

# ------------------------------------------------
#   LCZero Best Move Function
# ------------------------------------------------
def get_best_move(board):
    """Get the best move from LCZero for the given board position."""
    try:
        process = subprocess.Popen([LCZERO_PATH], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.stdin.write("uci\n")
        process.stdin.flush()
        time.sleep(1)
        process.stdin.write("isready\n")
        process.stdin.flush()
        time.sleep(1)
        
        fen = board.fen()
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        process.stdin.write("go movetime 3000\n")
        process.stdin.flush()
        
        best_move = None
        for line in iter(process.stdout.readline, ""):
            if line.startswith("bestmove"):
                best_move = line.split()[1]
                break
        
        process.terminate()
        
        if best_move:
            best_move_obj = chess.Move.from_uci(best_move)
            if best_move_obj in board.legal_moves:
                return best_move
        return None
    except Exception as e:
        st.error(f"Error running LCZERO: {e}")
        return None
