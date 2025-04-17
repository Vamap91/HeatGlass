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

    # Botão para iniciar análise
    if st.button("🔍 Analisar Atendimento"):
        # Transcrição com Whisper
        with st.spinner("Transcrevendo o áudio..."):
            try:
                with open(tmp_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                transcript_text = transcript.text
                
                with st.expander("Ver transcrição completa"):
                    st.code(transcript_text, language="markdown")
            except Exception as e:
                st.error(f"Erro na transcrição: {str(e)}")
                st.stop()

        # Prompt estratégico
        prompt = f"""
Você é um especialista em atendimento ao cliente, com foco na avaliação inteligente de ligações telefônicas. Sua missão é analisar transcrições de áudios e gerar um diagnóstico completo, seguindo quatro blocos principais:

TRANSCRIÇÃO DA LIGAÇÃO:
{transcript_text}

Por favor, faça uma análise completa abordando os seguintes pontos:

1. TEMPERATURA EMOCIONAL DA LIGAÇÃO
- Classifique como: `Calma`, `Neutra`, `Tensa` ou `Muito Tensa`
- Justifique sua escolha com base no tom do cliente e do atendente
- Avalie linguagem emocional, ritmo da conversa e palavras-chave de tensão

2. IMPACTO COMERCIAL
- De 0% a 100%, qual o impacto desta ligação para o negócio?
- Considere: postura do atendente, humor do cliente, resultado final
- Classifique a nota dentro das faixas:
  * 0-25% → Crítico 🔴
  * 26-50% → Baixo 🟠
  * 51-70% → Razoável 🟡
  * 71-85% → Positivo 🟢
  * 86-100% → Excelente 🟩

3. STATUS FINAL DO ATENDIMENTO
- O cliente ficou satisfeito?
- Houve risco de perda ou fechamento?
- Qual foi o desfecho: resolvido, pendente ou insatisfatório?

4. CHECKLIST TÉCNICO DE ATENDIMENTO (Pontuação Total = 100 pts)
Para cada item abaixo, responda `Sim` ou `Não` com uma breve justificativa.

1. Saudação inicial adequada (10 pts)
2. Confirmou histórico do cliente (7 pts)
3. Solicitou dois telefones logo no início (6 pts)
4. Verbalizou o script da LGPD (2 pts)
5. Usou a técnica do eco (validação) (5 pts)
6. Escutou com atenção, sem repetições desnecessárias (3 pts)
7. Demonstrou domínio sobre o serviço (5 pts)
8. Consultou o manual antes de pedir ajuda (2 pts)
9. Confirmou corretamente o veículo e ano (5 pts)
10. Perguntou data e motivo do dano (5 pts)
11. Confirmou cidade do cliente (3 pts)
12. Selecionou a primeira loja sugerida no sistema (5 pts)
13. Explicou link de acompanhamento claramente (3 pts)
14. Informou prazo de retorno e validade da OS (5 pts)
15. Registrou a ligação corretamente no mesmo pedido (5 pts)
16. Tabulação correta com código correspondente (5 pts)
17. Fez encerramento com todas as orientações finais (10 pts)
18. Informou sobre pesquisa de satisfação (CSAT) (6 pts)

Apresente sua análise em formato JSON, com a seguinte estrutura:
{{
    "temperatura": {{
        "classificacao": "classificação aqui",
        "justificativa": "justificativa aqui"
    }},
    "impacto_comercial": {{
        "percentual": número aqui,
        "faixa": "faixa aqui com emoji",
        "justificativa": "justificativa aqui"
    }},
    "status_final": {{
        "satisfacao": "satisfeito/não satisfeito",
        "risco": "descrição do risco",
        "desfecho": "resolvido/pendente/insatisfatório"
    }},
    "checklist": [
        {{
            "item": 1,
            "criterio": "Saudação inicial adequada",
            "pontos": 10,
            "resposta": "Sim/Não",
            "justificativa": "justificativa aqui"
        }},
        ...continuar para todos os 18 itens
    ],
    "pontuacao_total": número aqui,
    "resumo_geral": "resumo textual da análise completa"
}}

Retorne exclusivamente no formato JSON conforme a estrutura acima, sem explicações adicionais.
"""

        # Análise com GPT-4
        with st.spinner("Analisando a conversa..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em avaliar atendimentos telefônicos."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                    # Removido o parâmetro response_format que estava causando erro
                )
                analysis_text = response.choices[0].message.content
                
                # Verificar se a resposta parece ser um JSON
                if not analysis_text.strip().startswith("{"):
                    st.error("A resposta do modelo não está em formato JSON. Tente novamente.")
                    st.text(analysis_text)
                    st.stop()
                
                # Converter para JSON com tratamento de erro
                try:
                    analysis = json.loads(analysis_text)
                except json.JSONDecodeError as e:
                    st.error(f"Erro ao processar o JSON: {e}")
                    st.text(analysis_text)
                    st.stop()
                
                # Exibir resultados
                st.header("📊 Resultados da Análise")
                
                # Temperatura Emocional
                st.subheader("🌡️ Temperatura Emocional")
                temp_class = analysis.get('temperatura', {}).get('classificacao', "Não informado")
                temp_justificativa = analysis.get('temperatura', {}).get('justificativa', "Não informado")
                temp_emoji = {
                    'Calma': '😌',
                    'Neutra': '😐',
                    'Tensa': '😟',
                    'Muito Tensa': '😡'
                }.get(temp_class, '❓')
                
                st.markdown(f"### {temp_class} {temp_emoji}")
                st.markdown(f"**Justificativa**: {temp_justificativa}")
                
                # Impacto Comercial
                st.subheader("💼 Impacto Comercial")
                impact_pct = analysis.get('impacto_comercial', {}).get('percentual', 0)
                impact_range = analysis.get('impacto_comercial', {}).get('faixa', "Não informado")
                impact_justificativa = analysis.get('impacto_comercial', {}).get('justificativa', "Não informado")
                
                # Remover possíveis caracteres não numéricos e validar intervalo
                if isinstance(impact_pct, str):
                    impact_pct = float(re.sub(r'[^\d.]', '', impact_pct))
                
                # Garantir que o percentual está entre 0 e 100
                impact_pct = max(0, min(100, impact_pct))
                
                st.progress(int(impact_pct) / 100)
                st.markdown(f"### {int(impact_pct)}% - {impact_range}")
                st.markdown(f"**Justificativa**: {impact_justificativa}")
                
                # Status Final
                st.subheader("📋 Status Final do Atendimento")
                satisfacao = analysis.get('status_final', {}).get('satisfacao', "Não informado")
                desfecho = analysis.get('status_final', {}).get('desfecho', "Não informado")
                risco = analysis.get('status_final', {}).get('risco', "Não informado")
                
                satisfacao_emoji = '😊' if 'satisfeito' in satisfacao.lower() else '☹️'
                
                st.markdown(f"""
                <div class="status-box">
                    <strong>Cliente</strong>: {satisfacao} {satisfacao_emoji}<br>
                    <strong>Desfecho</strong>: {desfecho}<br>
                    <strong>Risco</strong>: {risco}
                </div>
                """, unsafe_allow_html=True)
                
                # Pontuação do Checklist
                st.subheader("🏆 Checklist Técnico")
                checklist = analysis.get('checklist', [])
                total_pts = analysis.get('pontuacao_total', 0)
                if isinstance(total_pts, str):
                    total_pts = float(re.sub(r'[^\d.]', '', total_pts))
                
                # Calcular o total possível baseado nos itens do checklist
                total_possible = 100  # Padrão
                if checklist:
                    # Calcula o total possível baseado nos pontos de cada item
                    try:
                        total_possible = sum(item.get('pontos', 0) for item in checklist)
                    except:
                        total_possible = 100  # Se falhar, usa o padrão
                
                # Garantir que o total está entre 0 e o máximo possível
                total_pts = max(0, min(total_pts, total_possible))
                
                # Mostrar progresso normalizado para 100%
                st.progress(total_pts / total_possible)
                st.markdown(f"### {int(total_pts)} pontos de {int(total_possible)}")
                
                # Exibir itens do checklist em forma de lista expandível
                with st.expander("Ver detalhes do checklist"):
                    for item in checklist:
                        item_num = item.get('item', 0)
                        criterio = item.get('criterio', "Não especificado")
                        pontos = item.get('pontos', 0)
                        resposta = item.get('resposta', "Não")
                        justificativa = item.get('justificativa', "Não informado")
                        
                        if resposta == 'Sim':
                            st.markdown(f"✅ **{item_num}. {criterio}** ({pontos} pts) - {justificativa}")
                        else:
                            st.markdown(f"❌ **{item_num}. {criterio}** (0 pts) - {justificativa}")
                
                # Resumo Geral
                st.subheader("📝 Resumo Geral")
                resumo = analysis.get('resumo_geral', "Não foi possível gerar um resumo.")
                st.markdown(f"<div class='result-box'>{resumo}</div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Erro ao processar a análise: {str(e)}")
                st.error("Detalhes do erro:")
                st.text(str(e))
                st.write("Resposta do modelo:")
                st.text(analysis_text if 'analysis_text' in locals() else "Não disponível")
