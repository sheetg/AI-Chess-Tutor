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
import random

# ------------------------------------------------
#   LCZero & GPT Setup
# ------------------------------------------------
LCZERO_PATH = r"C:\LCZero\lc0.exe"  # Update this path if needed
OPENAI_API_KEY = "Update your key"
AZURE_OPENAI_ENDPOINT = "https://chesstutor.openai.azure.com/"
AZURE_OPENAI_VERSION = "2025-02-01-preview"

# Azure Speech API
SPEECH_ENDPOINT = "https://centralindia.api.cognitive.microsoft.com/"
SPEECH_API_KEY = "Update your key"
SPEECH_REGION = "centralindia"

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
        client = openai.AzureOpenAI(api_key=OPENAI_API_KEY,
                                      azure_endpoint=AZURE_OPENAI_ENDPOINT,
                                      api_version=AZURE_OPENAI_VERSION)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a chess coach."},
                {"role": "user", "content": f"White has just played {move_san}. Please explain in detail why this move is effective and suggest the best response for Black. Do not ask for additional details."}
            ],
            temperature=0.7,
            max_tokens=600
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
        process = subprocess.Popen([LCZERO_PATH], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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

# ------------------------------------------------
#   Streamlit UI
# ------------------------------------------------
st.title("AI Chess Tutor with LCZero & GPT-4")

if "board" not in st.session_state:
    st.session_state.board = chess.Board()
    st.session_state.lczero_path = load_lczero()

tts_enabled = st.checkbox("Speak explanations aloud")

# Create two columns (3,3) so there's enough width for each board
col1, col2 = st.columns([3,3])

with col1:
    st.write("Current Board Position:")
    svg_code = chess.svg.board(
        st.session_state.board,
        size=450,
        arrows=[],
        coordinates=True
    )
    components.html(render_svg(svg_code), height=500)

move_input = st.text_input("Enter your move (e.g., e4, Nf3, Bb5):")

if st.button("Play Move"):
    try:
        board_temp = st.session_state.board.copy(stack=False)
        try:
            white_move_obj = board_temp.parse_san(move_input)
        except ValueError:
            st.error(f"Invalid move '{move_input}'. Please enter a correct move in algebraic notation.")
            st.stop()
        
        # Get recommended move from LCZero for the current position
        recommended_white_uci = get_best_move(board_temp)
        if recommended_white_uci:
            recommended_white_obj = chess.Move.from_uci(recommended_white_uci)
            recommended_white_san = board_temp.san(recommended_white_obj)
            st.info(f"Recommended move: {recommended_white_san}")
            explanation = get_move_explanation(board_temp, recommended_white_san)
            st.write("Chess Coach AI:", explanation)
            if tts_enabled:
                text_to_speech(explanation)
        
        # Apply your move
        st.session_state.board.push(white_move_obj)
        st.success(f"Your move applied: {move_input}")
        
        # Automatically compute and apply Black's move
        black_move_uci = get_best_move(st.session_state.board)
        if not black_move_uci:
            st.info("No best move found for Black. Playing a random legal move as fallback.")
            legal_moves = list(st.session_state.board.legal_moves)
            if legal_moves:
                black_move_obj = random.choice(legal_moves)
                black_move_san = st.session_state.board.san(black_move_obj)
                st.session_state.board.push(black_move_obj)
                st.success(f"Black played (fallback): {black_move_san}")
        else:
            black_move_obj = chess.Move.from_uci(black_move_uci)
            if black_move_obj in st.session_state.board.legal_moves:
                board_copy = st.session_state.board.copy(stack=False)
                recommended_black_san = board_copy.san(black_move_obj)
                st.session_state.board.push(black_move_obj)
                st.success(f"Black played: {recommended_black_san}")
            else:
                st.warning("No legal move found for Black.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

with col2:
    st.write("Updated Board Position:")
    updated_svg = chess.svg.board(
        st.session_state.board,
        size=450,
        coordinates=True
    )
    components.html(render_svg(updated_svg), height=500)
