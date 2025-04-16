import streamlit as st
import openai
import tempfile

# --- Configuração da Página ---
st.set_page_config(
    page_title="🔥 HeatGlass - Análise de Ligações",
    page_icon="🔴",
    layout="centered"
)

# --- Estilo Customizado (vermelho Carglass) ---
st.markdown("""
<style>
h1, h2, h3 {
    color: #C10000 !important;
}
.result-box {
    background-color: #ffecec;
    padding: 1.5em;
    border-left: 6px solid #C10000;
    border-radius: 10px;
    font-size: 1.1em;
    line-height: 1.6em;
}
.stButton>button {
    background-color: #C10000;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 0.5em 1em;
    border: none;
}
.stSpinner {
    color: #C10000 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Chave da OpenAI ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Título e Instrução ---
st.markdown("## 🔴 HeatGlass")
st.markdown("Envie uma gravação de ligação em `.mp3` para analisar a **temperatura emocional** da conversa e obter um **resumo automático** do atendimento.")

# --- Upload de Áudio ---
uploaded_file = st.file_uploader("📤 Faça upload do áudio da ligação", type=["mp3"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.audio(uploaded_file, format='audio/mp3')
    st.success("🎧 Áudio carregado com sucesso!")

    with st.spinner("📝 Transcrevendo com IA..."):
        audio_file = open(tmp_path, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcript_text = transcript["text"]

    st.subheader("📝 Transcrição")
    st.code(transcript_text, language='markdown')

    # --- Prompt de Análise ---
    prompt = f"""
Você é um analista de qualidade. Com base na transcrição da ligação abaixo:

1. Classifique a temperatura emocional da conversa como: **Calma**, **Neutra**, **Tensa** ou **Muito Tensa**. Justifique com base nas frases do cliente.
2. Gere um resumo estruturado no formato:

• Cliente relatou:  
• Atendente respondeu:  
• Status final do atendimento:

Transcrição:
\"\"\"{transcript_text}\"\"\"
"""

    with st.spinner("🔍 Analisando com inteligência emocional..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        resultado = response.choices[0].message.content

    st.subheader("🌡️ Resultado")
    st.markdown(f"<div class='result-box'>{resultado}</div>", unsafe_allow_html=True)
