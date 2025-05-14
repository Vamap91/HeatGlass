import streamlit as st
from openai import OpenAI
import tempfile
import re
import json

# Inicializa o novo cliente da OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Configurações da página
st.set_page_config(page_title="HeatGlass", page_icon="🔴", layout="centered")

# Estilo visual
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
.script-usado {
    background-color: #e6ffe6;
    padding: 10px;
    border-left: 5px solid #00C100;
    border-radius: 6px;
    margin-bottom: 10px;
}
.script-parcial {
    background-color: #ffffcc;
    padding: 10px;
    border-left: 5px solid #FFD700;
    border-radius: 6px;
    margin-bottom: 10px;
}
.script-nao-usado {
    background-color: #ffcccc;
    padding: 10px;
    border-left: 5px solid #FF0000;
    border-radius: 6px;
    margin-bottom: 10px;
}
.criterio-sim {
    background-color: #e6ffe6;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 5px;
    border-left: 5px solid #00C100;
}
.criterio-nao {
    background-color: #ffcccc;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 5px;
    border-left: 5px solid #FF0000;
}
.criterio-parcial {
    background-color: #ffffcc;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 5px;
    border-left: 5px solid #FFD700;
}
.temperature-calm {
    color: #00C100;
    font-size: 1.5em;
}
.temperature-neutral {
    color: #FFD700;
    font-size: 1.5em;
}
.temperature-tense {
    color: #FFA500;
    font-size: 1.5em;
}
.temperature-very-tense {
    color: #FF0000;
    font-size: 1.5em;
}
.progress-high {
    color: #00C100;
}
.progress-medium {
    color: #FFD700;
}
.progress-low {
    color: #FF0000;
}
.criterio-eliminatorio {
    background-color: #ffcccc;
    padding: 10px;
    border-radius: 6px;
    margin-top: 20px;
    border: 2px solid #FF0000;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Função para determinar classe de temperatura
def get_temp_class(temp):
    if temp == "Calma":
        return "temperature-calm"
    elif temp == "Neutra":
        return "temperature-neutral"
    elif temp == "Tensa":
        return "temperature-tense"
    elif temp == "Muito Tensa":
        return "temperature-very-tense"
    else:
        return ""

# Função para determinar classe de progresso
def get_progress_class(value):
    if value >= 70:
        return "progress-high"
    elif value >= 50:
        return "progress-medium"
    else:
        return "progress-low"

# Função para verificar status do script
def get_script_status_class(status):
    if status.lower() == "completo" or status.lower() == "sim":
        return "script-usado"
    elif "parcial" in status.lower():
        return "script-parcial"
    else:
        return "script-nao-usado"

# Título
st.title("HeatGlass")
st.write("Análise inteligente de ligações: temperatura emocional, impacto no negócio e status do atendimento.")

# Upload de áudio
uploaded_file = st.file_uploader("Envie o áudio da ligação (.mp3)", type=["mp3"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.audio(uploaded_file, format='audio/mp3')

    if st.button("🔍 Analisar Atendimento"):
        # Transcrição via Whisper
        with st.spinner("Transcrevendo o áudio..."):
            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            transcript_text = transcript.text

        with st.expander("Ver transcrição completa"):
            st.code(transcript_text, language="markdown")

        # Prompt
        prompt = f"""
Você é um especialista em atendimento ao cliente. Avalie a transcrição a seguir:

TRANSCRIÇÃO:
\"\"\"{transcript_text}\"\"\"

Retorne um JSON com os seguintes campos:

{{
  "temperatura": {{"classificacao": "...", "justificativa": "..."}},
  "impacto_comercial": {{"percentual": ..., "faixa": "...", "justificativa": "..."}},
  "status_final": {{"satisfacao": "...", "risco": "...", "desfecho": "..."}},
  "checklist": [
    {{"item": 1, "criterio": "Atendeu a ligação prontamente, dentro de 5 seg. e utilizou a saudação correta com as técnicas do atendimento encantador?", "pontos": 10, "resposta": "...", "justificativa": "..."}},
    ...
  ],
  "criterios_eliminatorios": [
    {{"criterio": "Ofereceu/garantiu algum serviço que o cliente não tinha direito?", "ocorreu": true/false, "justificativa": "..."}},
    ...
  ],
  "uso_script": {{"status": "completo/parcial/não utilizado", "justificativa": "..."}},
  "pontuacao_total": ...,
  "resumo_geral": "..."
}}

Checklist (100 pts totais):
1. Atendeu a ligação prontamente, dentro de 5 seg. e utilizou a saudação correta com as técnicas do atendimento encantador? (10 pts)
2. Confirmou o histórico de utilizações do cliente, garantindo que seu atendimento será prestado conforme sua solicitação? (7 pts)
3. Confirmou os dados do cadastro e pediu 2 telefones para contato? (Nome, CPF, Placa, e-mail, Veículo, Endereço, etc) (6 pts)
4. Verbalizou o script da LGPD? (2 pts)
5. Utilizou a técnica do eco para garantir o entendimento sobre as informações coletadas, evitando erros no processo e recontato do cliente? (5 pts)
6. Escutou atentamente a solicitação do segurado evitando solicitações em duplicidade? (3 pts)
7. Compreendeu a solicitação do cliente em linha e demonstrou domínio sobre o produto/serviço? (5 pts)
8. Antes de solicitar ajuda, consultou o manual de procedimento para localizar a informação desejada? (caso não tenha solicitado/precisado de ajuda, selecionar sim para a resposta) (2 pts)
9. Confirmou as informações completas sobre o dano no veículo? (10 pts)
10. Confirmou data e motivo da quebra, registro do item, dano na pintura e demais informações necessárias para o correto fluxo de atendimento. (tamanho da trinca, LED, Xenon, etc) (10 pts)
11. Confirmou cidade para o atendimento e selecionou corretamente a primeira opção de loja identificada pelo sistema? Porto/Sura/Bradesco (Seguiu o procedimento de lojas em verde/livre escolha?) (10 pts)
12. A comunicação com o cliente foi eficaz: não houve uso de gírias, linguagem inadequada ou conversas paralelas? O analista informou quando ficou ausente da linha e quando retornou? (5 pts)
13. Realizou o registro da ligação corretamente e garantiu ter sanado as dúvidas do cliente evitando o recontato? (6 pts)
14. Realizou o script de encerramento completo, informando: prazo de validade, franquia, link de acompanhamento e vistoria, e orientou que o cliente aguarde o contato para agendamento? (15 pts)
15. Orientou o cliente sobre a pesquisa de satisfação do atendimento? (6 pts)
16. Realizou a tabulação de forma correta? (4 pts)
17. A conduta do analista foi acolhedora, com sorriso na voz, empatia e desejo verdadeiro em entender e solucionar a solicitação do cliente? (4 pts)

Critérios Eliminatórios (0 pontos em cada caso):
- Ofereceu/garantiu algum serviço que o cliente não tinha direito?
- Preencheu ou selecionou o Veículo/peça incorretos?
- Agiu de forma rude, grosseira, não deixando o cliente falar e/ou se alterou na ligação?
- Encerrou a chamada ou transferiu o cliente sem o seu conhecimento?
- Difamou a imagem da Carglass, de afiliados, seguradoras ou colegas de trabalho, ou falou negativamente sobre algum serviço prestado por nós ou por afiliados?
- Comentou sobre serviços de terceiros (como oficinas, seguradoras, garatias ou parceiros), mesmo que sem difamação, quebrando o padrão de orientação ao cliente?** (Esse item deve ser considerado eliminatório e justificado se ocorrer.)

O script correto para a pergunta 14 é:
"*obrigada por me aguardar! O seu atendimento foi gerado, e em breve receberá dois links no whatsapp informado, para acompanhar o pedido e realizar a vistoria.*
*Lembrando que o seu atendimento tem uma franquia de XXX que deverá ser paga no ato do atendimento. (****acessórios/RRSM ****- tem uma franquia que será confirmada após a vistoria).*
*Te ajudo com algo mais?*
*Ao final do atendimento terá uma pesquisa de Satisfação, a nota 5 é a máxima, tudo bem?*
*Agradeço o seu contato, tenha um excelente dia!"*

Avalie se o script acima foi utilizado completamente, parcialmente ou não foi utilizado.

Responda apenas com o JSON e nada mais.
"""

        with st.spinner("Analisando a conversa..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em atendimento."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                result = response.choices[0].message.content.strip()

                if not result.startswith("{"):
                    raise ValueError("Formato de resposta inválido")

                analysis = json.loads(result)

                # Temperatura
                st.subheader("🌡️ Temperatura Emocional")
                temp = analysis.get("temperatura", {})
                temp_class = temp.get("classificacao", "Desconhecida")
                emoji = {'Calma': '😌', 'Neutra': '😐', 'Tensa': '😟', 'Muito Tensa': '😡'}.get(temp_class, '❓')
                temp_class_style = get_temp_class(temp_class)
                st.markdown(f"<h3 class='{temp_class_style}'>{temp_class} {emoji}</h3>", unsafe_allow_html=True)
                st.markdown(f"**Justificativa:** {temp.get('justificativa')}")

                # Impacto
                st.subheader("💼 Impacto Comercial")
                impact = analysis.get("impacto_comercial", {})
                pct = float(re.sub(r"[^\d.]", "", str(impact.get("percentual", "0"))))
                progress_class = get_progress_class(pct)
                st.progress(min(pct / 100, 1.0))
                st.markdown(f"<h3 class='{progress_class}'>{int(pct)}% - {impact.get('faixa')}</h3>", unsafe_allow_html=True)
                st.markdown(f"**Justificativa:** {impact.get('justificativa')}")

                # Status Final
                st.subheader("📋 Status Final")
                final = analysis.get("status_final", {})
                st.markdown(f"""
                <div class="status-box">
                <strong>Cliente:</strong> {final.get("satisfacao")}<br>
                <strong>Desfecho:</strong> {final.get("desfecho")}<br>
                <strong>Risco:</strong> {final.get("risco")}
                </div>
                """, unsafe_allow_html=True)

                # Script de Encerramento
                st.subheader("📝 Script de Encerramento")
                script_info = analysis.get("uso_script", {})
                script_status = script_info.get("status", "Não avaliado")
                script_class = get_script_status_class(script_status)
                
                st.markdown(f"""
                <div class="{script_class}">
                <strong>Status:</strong> {script_status}<br>
                <strong>Justificativa:</strong> {script_info.get("justificativa", "Não informado")}
                </div>
                """, unsafe_allow_html=True)

                # Critérios Eliminatórios
                st.subheader("⚠️ Critérios Eliminatórios")
                criterios_elim = analysis.get("criterios_eliminatorios", [])
                criterios_violados = False
                
                for criterio in criterios_elim:
                    if criterio.get("ocorreu", False):
                        criterios_violados = True
                        st.markdown(f"""
                        <div class="criterio-eliminatorio">
                        <strong>{criterio.get('criterio')}</strong><br>
                        {criterio.get('justificativa', '')}
                        </div>
                        """, unsafe_allow_html=True)
                
                if not criterios_violados:
                    st.success("Nenhum critério eliminatório foi violado.")

                # Checklist
                st.subheader("✅ Checklist Técnico")
                checklist = analysis.get("checklist", [])
                total = float(re.sub(r"[^\d.]", "", str(analysis.get("pontuacao_total", "0"))))
                progress_class = get_progress_class(total)
                st.progress(min(total / 100, 1.0))
                st.markdown(f"<h3 class='{progress_class}'>{int(total)} pontos de 100</h3>", unsafe_allow_html=True)

                with st.expander("Ver Detalhes do Checklist"):
                    for item in checklist:
                        resposta = item.get("resposta", "").lower()
                        if resposta == "sim":
                            classe = "criterio-sim"
                            icone = "✅"
                        elif "parcial" in resposta:
                            classe = "criterio-parcial"
                            icone = "⚠️"
                        else:
                            classe = "criterio-nao"
                            icone = "❌"
                        
                        st.markdown(f"""
                        <div class="{classe}">
                        {icone} <strong>{item['item']}. {item['criterio']}</strong> ({item['pontos']} pts)<br>
                        <em>{item['justificativa']}</em>
                        </div>
                        """, unsafe_allow_html=True)

                # Resumo
                st.subheader("📝 Resumo Geral")
                st.markdown(f"<div class='result-box'>{analysis.get('resumo_geral')}</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erro ao processar a análise: {str(e)}")
                try:
                    st.text_area("Resposta da IA:", value=response.choices[0].message.content.strip(), height=300)
                except:
                    st.text_area("Não foi possível recuperar a resposta da IA", height=300)
