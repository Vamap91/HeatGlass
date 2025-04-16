import streamlit as st
from openai import OpenAI
import tempfile

# Configuração da página
st.set_page_config(
    page_title="HeatGlass",
    page_icon="🔴",
    layout="centered"
)

# Estilo visual discreto com tema vermelho
st.markdown("""
<style>
h1, h2, h3 {
    color: #C10000 !important;
}
.result-box {
    background-color: #ffecec;
    padding: 1.2em;
    border-left: 5px solid #C10000;
    border-radius: 6px;
    font-size: 1rem;
    line-height: 1.5em;
    white-space: pre-wrap;
}
.stButton>button {
    background-color: #C10000;
    color: white;
    font-weight: 500;
    border-radius: 6px;
    padding: 0.4em 1em;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# Inicializa OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Cabeçalho
st.title("HeatGlass")
st.write("Ferramenta para análise de ligações com transcrição automática, detecção de temperatura emocional e resumo da conversa.")

# Upload de áudio
uploaded_file = st.file_uploader("Envie o áudio da ligação (.mp3)", type=["mp3"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.audio(uploaded_file, format='audio/mp3')

    with st.spinner("Transcrevendo o áudio..."):
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcript_text = transcript.text

    st.subheader("Transcrição")
    st.code(transcript_text, language='markdown')

    prompt = f"""
Você é um analista de qualidade. Com base na transcrição abaixo, responda com:

1. Temperatura emocional da ligação: Calma, Neutra, Tensa ou Muito Tensa. Justifique.
2. Resumo da conversa:

• Cliente relatou:  
• Atendente respondeu:  
• Status final do atendimento:

Transcrição:
\"\"\"{transcript_text}\"\"\"
"""

    with st.spinner("Analisando a conversa..."):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        resultado = response.choices[0].message.content

    st.subheader("Análise")
    st.markdown(f"<div class='result-box'>{resultado}</div>", unsafe_allow_html=True)

