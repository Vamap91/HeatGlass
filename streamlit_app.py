import streamlit as st
from openai import OpenAI
import tempfile
import re
import json

# Inicializa o cliente OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Configurações da página (deve ser a primeira chamada Streamlit)
st.set_page_config(page_title="HeatGlass", page_icon="🔴", layout="centered")

# Estilos visuais customizados
st.markdown("""
<style>
h1, h2, h3 { color: #C10000 !important; }
.result-box { background-color: #ffecec; padding: 1em; border-left: 5px solid #C10000; border-radius: 6px; font-size: 1rem; white-space: pre-wrap; line-height: 1.5; }
.status-box { padding: 15px; border-radius: 8px; margin-bottom: 15px; background-color: #ffecec; border: 1px solid #C10000; }
.script-usado { background-color: #e6ffe6; padding: 10px; border-left: 5px solid #00C100; border-radius: 6px; margin-bottom: 10px; }
.script-parcial { background-color: #ffffcc; padding: 10px; border-left: 5px solid #FFD700; border-radius: 6px; margin-bottom: 10px; }
.script-nao-usado { background-color: #ffcccc; padding: 10px; border-left: 5px solid #FF0000; border-radius: 6px; margin-bottom: 10px; }
.criterio-sim { background-color: #e6ffe6; padding: 10px; border-radius: 6px; margin-bottom: 5px; border-left: 5px solid #00C100; }
.criterio-nao { background-color: #ffcccc; padding: 10px; border-radius: 6px; margin-bottom: 5px; border-left: 5px solid #FF0000; }
.criterio-parcial { background-color: #ffffcc; padding: 10px; border-radius: 6px; margin-bottom: 5px; border-left: 5px solid #FFD700; }
.criterio-eliminatorio { background-color: #ffcccc; padding: 10px; border-radius: 6px; margin-top: 20px; border: 2px solid #FF0000; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares para classes CSS
def get_temp_class(temp):
    classes = {"Calma": "temperature-calm", "Neutra": "temperature-neutral", "Tensa": "temperature-tense", "Muito Tensa": "temperature-very-tense"}
    return classes.get(temp, "")

def get_script_status_class(status):
    status = status.lower()
    if "completo" in status or status == "sim": return "script-usado"
    elif "parcial" in status: return "script-parcial"
    else: return "script-nao-usado"

def get_progress_class(value):
    if value >= 70: return "progress-high"
    elif value >= 50: return "progress-medium"
    else: return "progress-low"

# Título da página
st.title("HeatGlass")
st.write("Análise inteligente de ligações: temperatura emocional, impacto no negócio e status do atendimento.")

# Upload do áudio
uploaded_file = st.file_uploader("Envie o áudio da ligação (.mp3)", type=["mp3"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.audio(uploaded_file, format='audio/mp3')

    if st.button("🔍 Analisar Atendimento"):
        with st.spinner("Transcrevendo o áudio..."):
            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            transcript_text = transcript.text

        with st.expander("Ver transcrição completa"):
            st.code(transcript_text, language="markdown")

        prompt = f"""
Você é um especialista em atendimento ao cliente. Avalie a transcrição a seguir:

TRANSCRIÇÃO:
"""
{transcript_text}
"""

Retorne um JSON com os seguintes campos:
- temperatura emocional (classificacao + justificativa)
- impacto comercial (percentual + faixa + justificativa)
- status final do atendimento
- checklist com os 16 critérios técnicos completos
- script de encerramento (status e justificativa)
- critérios eliminatórios (criterio, ocorreu, justificativa)
- pontuação total e resumo geral

Responda apenas com o JSON completo e válido.
"""

        with st.spinner("Analisando a conversa..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em atendimento."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                result = response.choices[0].message.content.strip()

                if not result.startswith("{"):
                    raise ValueError("Resposta fora do formato JSON")

                analysis = json.loads(result)

                st.subheader("🌡️ Temperatura Emocional")
                temp = analysis.get("temperatura", {})
                temp_class = get_temp_class(temp.get("classificacao", ""))
                st.markdown(f"<h3 class='{temp_class}'>{temp.get('classificacao', '')}</h3>", unsafe_allow_html=True)
                st.markdown(f"**Justificativa:** {temp.get('justificativa', '')}")

                st.subheader("💼 Impacto Comercial")
                impact = analysis.get("impacto_comercial", {})
                pct = float(re.sub(r"[^\d.]", "", str(impact.get("percentual", "0"))))
                st.progress(min(pct / 100, 1.0))
                st.markdown(f"**{int(pct)}% - {impact.get('faixa', '')}**")
                st.markdown(f"**Justificativa:** {impact.get('justificativa', '')}")

                st.subheader("📋 Status Final")
                final = analysis.get("status_final", {})
                st.markdown(f"""
                <div class="status-box">
                <strong>Cliente:</strong> {final.get("satisfacao")}<br>
                <strong>Desfecho:</strong> {final.get("desfecho")}<br>
                <strong>Risco:</strong> {final.get("risco")}
                </div>
                """, unsafe_allow_html=True)

                st.subheader("📝 Script de Encerramento")
                script_info = analysis.get("uso_script", {})
                script_status = script_info.get("status", "Não informado")
                script_class = get_script_status_class(script_status)
                st.markdown(f"""
                <div class="{script_class}">
                <strong>Status:</strong> {script_status}<br>
                <strong>Justificativa:</strong> {script_info.get("justificativa", "Não informado")}
                </div>
                """, unsafe_allow_html=True)

                st.subheader("⚠️ Critérios Eliminatórios")
                eliminatorios = analysis.get("criterios_eliminatorios", [])
                for item in eliminatorios:
                    if item.get("ocorreu", False):
                        st.markdown(f"""
                        <div class="criterio-eliminatorio">
                        <strong>{item.get('criterio')}</strong><br>
                        {item.get('justificativa', '')}
                        </div>
                        """, unsafe_allow_html=True)

                st.subheader("✅ Checklist Técnico")
                checklist = analysis.get("checklist", [])
                total = float(re.sub(r"[^\d.]", "", str(analysis.get("pontuacao_total", "0"))))
                st.progress(min(total / 100, 1.0))
                st.markdown(f"**Pontuação total: {int(total)} de 100**")

                with st.expander("Ver Detalhes do Checklist"):
                    for item in checklist:
                        resposta = item.get("resposta", "").lower()
                        if resposta == "sim": classe = "criterio-sim"; icone = "✅"
                        elif "parcial" in resposta: classe = "criterio-parcial"; icone = "⚠️"
                        else: classe = "criterio-nao"; icone = "❌"
                        st.markdown(f"""
                        <div class="{classe}">
                        {icone} <strong>{item['item']}. {item['criterio']}</strong> ({item['pontos']} pts)<br>
                        <em>{item['justificativa']}</em>
                        </div>
                        """, unsafe_allow_html=True)

                st.subheader("📌 Resumo Geral")
                st.markdown(f"<div class='result-box'>{analysis.get('resumo_geral')}</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erro ao processar a análise: {str(e)}")
                try:
                    st.text_area("Resposta da IA:", value=response.choices[0].message.content.strip(), height=300)
                except:
                    st.text_area("Não foi possível recuperar a resposta da IA", height=300)
