# AI Chess Tutor with LCZero & GPT-4

## Overview

This project is an AI-powered chess tutor that uses **LCZero (Leela Chess Zero)** for move evaluation and **GPT-4** for move explanations. It also includes **text-to-speech (TTS)** capabilities using **Azure Cognitive Services Speech API** to provide verbal move analysis.

## Features

- **Chess Move Evaluation**: Uses LCZero to suggest the best move.
- **AI-Powered Explanation**: GPT-4 provides insights into each move.
- **Text-to-Speech**: Azure Speech API reads move explanations aloud.
- **Interactive UI**: Built with **Streamlit** for a simple and intuitive experience.

## Installation

### **1. Clone the Repository**

```sh
git clone https://github.com/your-username/AI-Chess-Tutor.git
cd AI-Chess-Tutor
```

### **2. Install Dependencies**

```sh
pip install -r requirements.txt
```

### **3. Run the Application**

```sh
streamlit run app1.py
```

## Deployment

This project can be deployed to **Azure Web Apps** using **Windows Containers**. The key steps include:

1. **Build a Docker Image**
2. **Push the Image to a Docker Registry**
3. **Deploy to Azure Web App (Windows Container)**

### **Startup Command for Azure**

```sh
streamlit run app1.py --server.port 8000 --server.address 0.0.0.0
```

## Configuration

Before deploying, set the following **environment variables**:

- `OPENAI_API_KEY`
- `AZURE_SPEECH_API_KEY`

## Next Steps

- Improve UI with more interactive features
- Add **Stockfish** as an alternative chess engine
- Enhance move explanations with **visual annotations**

---

**Author**: Sheetal Gudigar
License : MIT


