# ==============================
# 🔧 IMPORTAÇÕES
# ==============================
import streamlit as st
import openai
import tempfile

# ==============================
# ⚙️ CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="🔥 HeatGlass - Análise de Ligações",
    page_icon="🔴",
    layout="centered"
)

# ==============================
# 🎨 ESTILO VISUAL - TEMA VERMELHO CARGALASS
# ==============================
st.markdown("""
<style>
/* Cabeçalhos vermelhos */
h1, h2, h3 {
    color: #C10000 !important;
}

/* Caixa de resultado destacada */
.result-box {
    background-color: #ffecec;
    padding: 1.5em;
    border-left: 6px solid #C10000;
    border-radius: 10px;
    font-size: 1.1em;
    line-height: 1.6em;
    white-space: pre-wrap;
}

/* Botão estilizado */
.stButton>button {
    background-color: #C10000;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 0.5em 1em;
    border: none;
}

/* Spinner com cor vermelha */
.stSpinner {
    color: #C10000 !important;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# 🔐 CHAVE DA OPENAI (via secrets)
# ==============================
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ==============================
# 🟥 TÍTULO DO APLICATIVO
# ==============================
st.markdown("## 🔴 HeatGlass")
st.markdown("""
Bem-vindo ao **HeatGlass**, o sistema inteligente que transforma gravações de atendimento em dados valiosos.

> Envie um áudio `.mp3` de uma ligação e descubra:
> - A **temperatura emocional** da conversa (calma ou tensa)
> - Um **resumo claro e estruturado** do atendimento
""")

# ==============================
# 📤 UPLOAD DE ÁUDIO
# ==============================
uploaded_file = st.file_uploader("📤 Faça upload do áudio da ligação (.mp3)", type=["mp3"])

if uploaded_file is not None:
    # ✅ Salva o áudio temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # ▶️ Exibe o player de áudio
    st.audio(uploaded_file, format='audio/mp3')
    st.success("🎧 Áudio carregado com sucesso!")

    # ==============================
    # 🧠 TRANSCRIÇÃO COM WHISPER
    # ==============================
    with st.spinner("📝 Transcrevendo a ligação com IA..."):
        audio_file = open(tmp_path, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcript_text = transcript["text"]

    # ==============================
    # 📝 EXIBIÇÃO DA TRANSCRIÇÃO
    # ==============================
    st.subheader("📝 Transcrição da Ligação")
    st.code(transcript_text, language='markdown')

    # ==============================
    # 💬 PROMPT PARA ANÁLISE EMOCIONAL + RESUMO
    # ==============================
    prompt = f"""
Você é um analista de qualidade de atendimentos por voz. Com base na transcrição abaixo, responda com:

1. **Temperatura emocional da ligação**: Calma, Neutra, Tensa ou Muito Tensa. Justifique com base nas frases do cliente.
2. **Resumo estruturado**:

• Cliente relatou:  
• Atendente respondeu:  
• Status final do atendimento:

Transcrição da ligação:
\"\"\"{transcript_text}\"\"\"
"""

    # ==============================
    # 🔍 CHAMADA AO GPT-4
    # ==============================
    with st.spinner("🔍 Analisando com inteligência emocional..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        resultado = response.choices[0].message.content

    # ==============================
    # 📊 EXIBIÇÃO DOS RESULTADOS
    # ==============================
    st.subheader("🌡️ Temperatura emocional + Resumo")
    st.markdown(f"<div class='result-box'>{resultado}</div>", unsafe_allow_html=True)
