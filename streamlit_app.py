import streamlit as st
from openai import OpenAI
import tempfile
import re

# Configurações da página
st.set_page_config(page_title="HeatGlass", page_icon="🔴", layout="centered")

# Estilo visual simples e vermelho discreto
st.markdown("""
<style>
h1, h2, h3 {
    color: #C10000 !important;
}
.result-box {
    background-color: #ffecec;
    padding: 1em;
    border-left: 5px solid #C10000;
    border-radius: 6px;
    font-size: 1rem;
    white-space: pre-wrap;
    line-height: 1.5;
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

# Inicializa o cliente OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Título
st.title("HeatGlass")
st.write("Análise inteligente de ligações: temperatura emocional, impacto no negócio e status do atendimento.")

# Upload do áudio
uploaded_file = st.file_uploader("Envie o áudio da ligação (.mp3)", type=["mp3"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.audio(uploaded_file, format='audio/mp3')

    # Transcrição com Whisper
    with st.spinner("Transcrevendo o áudio..."):
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcript_text = transcript.text

    st.subheader("Transcrição")
    st.code(transcript_text, language="markdown")

    # Prompt estratégico
    prompt = f"""
Você é um especialista em atendimento ao cliente. Com base na transcrição abaixo, responda:

1. Temperatura emocional da conversa: Calma, Neutra, Tensa ou Muito Tensa. Justifique brevemente.
2. Impacto comercial da conversa: De 0% a 100%, quanto essa ligação favoreceu o negócio? Leve em conta o humor do cliente, a postura do atendente e o desfecho.
3. Status final do atendimento:
• O cliente ficou satisfeito?
• Houve risco de perda ou fechamento?
• Qual foi o resultado final?

Ao final, classifique o impacto em:
- Crítico (0–25%)
- Baixo (26–50%)
- Razoável (51–70%)
- Positivo (71–85%)
- Excelente (86–100%)

Transcrição:
\"\"\"{transcript_text}\"\"\"
"""

    with st.spinner("Analisando a conversa..."):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        output = response.choices[0].message.content

    # Extrai o percentual do texto
    match = re.search(r"Impacto.*?(\d{1,3})\%", output)
    impacto = int(match.group(1)) if match else None

    # Exibe barra de progresso e status
    if impacto is not None:
        st.subheader("Impacto no negócio")
        st.progress(impacto / 100)
        if impacto <= 25:
            status = "🔴 Crítico"
        elif impacto <= 50:
            status = "🟠 Baixo"
        elif impacto <= 70:
            status = "🟡 Razoável"
        elif impacto <= 85:
            status = "🟢 Positivo"
        else:
            status = "🟩 Excelente"
        st.write(f"Resultado: **{status}** ({impacto}%)")

    # Exibe texto final da análise
    st.subheader("Análise da Ligação")
    st.markdown(f"<div class='result-box'>{output}</div>", unsafe_allow_html=True)
