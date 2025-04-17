import streamlit as st
from openai import OpenAI
import tempfile
import re
import json

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
.status-box {
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 15px;
    background-color: #ffecec;
    border: 1px solid #C10000;
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

    if st.button("🔍 Analisar Atendimento"):
        # Transcrição com Whisper
        with st.spinner("Transcrevendo o áudio..."):
            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            transcript_text = transcript.text

        with st.expander("Ver transcrição completa"):
            st.code(transcript_text, language="markdown")

        # Prompt estratégico com instrução final reforçada
        prompt = f"""
Você é um especialista em atendimento ao cliente, com foco na avaliação inteligente de ligações telefônicas. Sua missão é analisar transcrições de áudios e gerar um diagnóstico completo, seguindo quatro blocos principais:

TRANSCRIÇÃO DA LIGAÇÃO:
{transcript_text}

Por favor, faça uma análise completa abordando os seguintes pontos:

1. TEMPERATURA EMOCIONAL DA LIGAÇÃO
- Classifique como: `Calma`, `Neutra`, `Tensa` ou `Muito Tensa`
- Justifique sua escolha com base no tom do cliente e do atendente

2. IMPACTO COMERCIAL
- De 0% a 100%, qual o impacto desta ligação para o negócio?
- Classifique:
  * 0-25% → Crítico 🔴
  * 26-50% → Baixo 🟠
  * 51-70% → Razoável 🟡
  * 71-85% → Positivo 🟢
  * 86-100% → Excelente 🟩

3. STATUS FINAL DO ATENDIMENTO
- O cliente ficou satisfeito?
- Houve risco de perda ou fechamento?
- Qual foi o desfecho?

4. CHECKLIST TÉCNICO (100 pts)
Responda com Sim/Não e justificativa:

1. Saudação inicial adequada (10 pts)
2. Confirmou histórico do cliente (7 pts)
3. Solicitou dois telefones logo no início (6 pts)
4. Verbalizou o script da LGPD (2 pts)
5. Usou a técnica do eco (5 pts)
6. Escutou com atenção, sem repetições desnecessárias (3 pts)
7. Demonstrou domínio sobre o serviço (5 pts)
8. Consultou o manual antes de pedir ajuda (2 pts)
9. Confirmou corretamente o veículo e ano (5 pts)
10. Perguntou data e motivo do dano (5 pts)
11. Confirmou cidade do cliente (3 pts)
12. Selecionou a primeira loja sugerida (5 pts)
13. Explicou link de acompanhamento (3 pts)
14. Informou prazo de retorno e validade da OS (5 pts)
15. Registrou corretamente no mesmo pedido (5 pts)
16. Tabulação correta com código correspondente (5 pts)
17. Encerramento com todas as orientações finais (10 pts)
18. Informou sobre pesquisa de satisfação (6 pts)

Formato de resposta: JSON estruturado conforme abaixo e **não adicione comentários fora do JSON**:

{{
  "temperatura": {{"classificacao": "...", "justificativa": "..."}},
  "impacto_comercial": {{"percentual": ..., "faixa": "...", "justificativa": "..."}},
  "status_final": {{"satisfacao": "...", "risco": "...", "desfecho": "..."}},
  "checklist": [
    {{"item": 1, "criterio": "...", "pontos": ..., "resposta": "...", "justificativa": "..."}},
    ...
  ],
  "pontuacao_total": ...,
  "resumo_geral": "..."
}}
"""

        with st.spinner("Analisando a conversa..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em avaliar atendimentos telefônicos."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                analysis_text = response.choices[0].message.content.strip()

                # Valida se o retorno é JSON
                if not analysis_text.startswith("{"):
                    raise ValueError("Resposta fora do formato JSON")

                analysis = json.loads(analysis_text)

                # Temperatura
                st.subheader("🌡️ Temperatura Emocional")
                temp = analysis.get("temperatura", {})
                temp_class = temp.get("classificacao", "Desconhecida")
                temp_emoji = {'Calma': '😌', 'Neutra': '😐', 'Tensa': '😟', 'Muito Tensa': '😡'}.get(temp_class, '❓')
                st.markdown(f"### {temp_class} {temp_emoji}")
                st.markdown(f"**Justificativa:** {temp.get('justificativa', 'Não informada')}")

                # Impacto Comercial
                st.subheader("💼 Impacto Comercial")
                impacto = analysis.get("impacto_comercial", {})
                pct = float(re.sub(r'[^\d.]', '', str(impacto.get("percentual", "0"))))
                if 0 <= pct <= 100:
                    st.progress(pct / 100)
                st.markdown(f"### {int(pct)}% - {impacto.get('faixa', '')}")
                st.markdown(f"**Justificativa:** {impacto.get('justificativa', 'Não informada')}")

                # Status Final
                st.subheader("📋 Status Final")
                status = analysis.get("status_final", {})
                st.markdown(f"""
                    <div class="status-box">
                    <strong>Cliente:</strong> {status.get("satisfacao", '')}<br>
                    <strong>Desfecho:</strong> {status.get("desfecho", '')}<br>
                    <strong>Risco:</strong> {status.get("risco", '')}
                    </div>
                """, unsafe_allow_html=True)

                # Checklist
                st.subheader("✅ Checklist Técnico")
                checklist = analysis.get("checklist", [])
                total_pts = float(re.sub(r'[^\d.]', '', str(analysis.get("pontuacao_total", 0))))
                st.progress(min(total_pts / 100, 1))
                st.markdown(f"### {int(total_pts)} pontos de 100")

                with st.expander("Ver Detalhes do Checklist"):
                    for item in checklist:
                        icone = "✅" if item.get("resposta", "").lower() == "sim" else "❌"
                        st.markdown(f"{icone} **{item['item']}. {item['criterio']}** ({item['pontos']} pts) – {item['justificativa']}")

                # Resumo
                st.subheader("📝 Resumo Geral")
                st.markdown(f"<div class='result-box'>{analysis.get('resumo_geral', '')}</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error("❌ Ocorreu um erro na análise. Verifique se a resposta do modelo está no formato JSON válido.")
                st.text_area("Conteúdo recebido do modelo:", value=response.choices[0].message.content, height=300)
