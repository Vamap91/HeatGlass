import streamlit as st
from openai import OpenAI
import tempfile
import re
import json
import base64
from datetime import datetime
from fpdf import FPDF

# Inicializa o novo cliente da OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Configurações da página
st.set_page_config(page_title="HeatGlass", page_icon="🔴", layout="centered")

# Função para criar PDF
def create_pdf(analysis, transcript_text, model_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Configurações de fonte
    pdf.set_font("Arial", "B", 16)
    
    # Cabeçalho
    pdf.set_fill_color(193, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "HeatGlass - Relatório de Atendimento", 1, 1, "C", True)
    pdf.ln(5)
    
    # Informações gerais
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1)
    pdf.cell(0, 10, f"Modelo utilizado: {model_name}", 0, 1)
    pdf.ln(5)
    
    # Temperatura Emocional
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Temperatura Emocional", 0, 1)
    pdf.set_font("Arial", "", 12)
    temp = analysis.get("temperatura", {})
    pdf.cell(0, 10, f"Classificação: {temp.get('classificacao', 'N/A')}", 0, 1)
    pdf.multi_cell(0, 10, f"Justificativa: {temp.get('justificativa', 'N/A')}")
    pdf.ln(5)
    
    # Impacto Comercial
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Impacto Comercial", 0, 1)
    pdf.set_font("Arial", "", 12)
    impact = analysis.get("impacto_comercial", {})
    pdf.cell(0, 10, f"Percentual: {impact.get('percentual', 'N/A')}% - {impact.get('faixa', 'N/A')}", 0, 1)
    pdf.multi_cell(0, 10, f"Justificativa: {impact.get('justificativa', 'N/A')}")
    pdf.ln(5)
    
    # Status Final
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Status Final", 0, 1)
    pdf.set_font("Arial", "", 12)
    final = analysis.get("status_final", {})
    pdf.cell(0, 10, f"Cliente: {final.get('satisfacao', 'N/A')}", 0, 1)
    pdf.cell(0, 10, f"Desfecho: {final.get('desfecho', 'N/A')}", 0, 1)
    pdf.cell(0, 10, f"Risco: {final.get('risco', 'N/A')}", 0, 1)
    pdf.ln(5)
    
    # Script de Encerramento
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Script de Encerramento", 0, 1)
    pdf.set_font("Arial", "", 12)
    script_info = analysis.get("uso_script", {})
    pdf.cell(0, 10, f"Status: {script_info.get('status', 'N/A')}", 0, 1)
    pdf.multi_cell(0, 10, f"Justificativa: {script_info.get('justificativa', 'N/A')}")
    pdf.ln(5)
    
    # Pontuação Total
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Pontuação Total", 0, 1)
    pdf.set_font("Arial", "B", 12)
    total = analysis.get("pontuacao_total", "N/A")
    pdf.cell(0, 10, f"{total} pontos de 100", 0, 1)
    pdf.ln(5)
    
    # Resumo Geral
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Resumo Geral", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, analysis.get("resumo_geral", "N/A"))
    pdf.ln(5)
    
    # Checklist (nova página)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Checklist Técnico", 0, 1)
    pdf.ln(5)
    
    # Itens do checklist
    checklist = analysis.get("checklist", [])
    for item in checklist:
        item_num = item.get('item', '')
        criterio = item.get('criterio', '')
        pontos = item.get('pontos', 0)
        resposta = str(item.get('resposta', ''))
        justificativa = item.get('justificativa', '')
        
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 10, f"{item_num}. {criterio} ({pontos} pts)")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Resposta: {resposta}", 0, 1)
        pdf.multi_cell(0, 10, f"Justificativa: {justificativa}")
        pdf.ln(5)
    
    # Transcrição na última página
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Transcrição da Ligação", 0, 1)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 10, transcript_text)
    
    return pdf.output(dest="S").encode("latin1")

# Função para criar link de download do PDF
def get_pdf_download_link(pdf_bytes, filename):
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Baixar Relatório em PDF</a>'
    return href

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
.criterio-nao-verificavel {
    background-color: #f0f0f0;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 5px;
    border-left: 5px solid #808080;
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

# Seleção do modelo GPT
col1, col2 = st.columns(2)
with col1:
    modelo_gpt = st.selectbox(
        "Selecione o modelo de IA:",
        ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0
    )
    
with col2:
    st.write("")  # Espaço em branco para alinhar com o campo acima
    st.write("O modelo selecionado afeta a qualidade da análise.")

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
```
Você é um especialista em avaliação de atendimento ao cliente para a Carglass. Avalie APENAS o que pode ser verificado pela transcrição do áudio a seguir, sem fazer suposições sobre o que aconteceu na tela do atendente:

TRANSCRIÇÃO:
\"\"\"{transcript_text}\"\"\"

IMPORTANTE: Você está avaliando SOMENTE o áudio da ligação. NÃO tem acesso à tela do atendente e NÃO pode ver suas ações no sistema. Para itens que exigem visualização da tela (como "realizou tabulação", "selecionou loja corretamente"), responda "Não Verificável".

INSTRUÇÕES CRÍTICAS:
1. Avalie SOMENTE o que é explicitamente verificável na transcrição.
2. A pontuação DEVE refletir exatamente os critérios cumpridos ou não cumpridos.
3. Sempre que um item for marcado como "Não" ou "Não Verificável", atribua 0 pontos.
4. Quando um item for marcado como "Parcial", atribua metade dos pontos disponíveis.
5. Calcule a pontuação total como a soma exata dos pontos obtidos, sem arredondamentos.
6. Use APENAS as classificações permitidas para cada campo.

Retorne um JSON com os seguintes campos:

{
  "temperatura": {"classificacao": "Calma/Neutra/Tensa/Muito Tensa", "justificativa": "..."},
  "impacto_comercial": {"percentual": [0-100], "faixa": "Baixo/Moderado/Alto", "justificativa": "..."},
  "status_final": {"satisfacao": "Satisfeito/Parcialmente Satisfeito/Insatisfeito", "risco": "Baixo/Médio/Alto", "desfecho": "Positivo/Neutro/Negativo"},
  "checklist": [
    {"item": 1, "criterio": "Atendeu a ligação prontamente, dentro de 5 seg. e utilizou a saudação correta com as técnicas do atendimento encantador?", "pontos": [valor numérico], "resposta": "Sim/Parcial/Não/Não Verificável", "justificativa": "..."},
    ...
  ],
  "criterios_eliminatorios": [
    {"criterio": "Ofereceu/garantiu algum serviço que o cliente não tinha direito?", "ocorreu": true/false, "justificativa": "..."},
    ...
  ],
  "uso_script": {"status": "completo/parcial/não utilizado", "justificativa": "..."},
  "pontuacao_total": [soma exata dos pontos],
  "resumo_geral": "..."
}

CHECKLIST DETALHADO (Total: 100 pontos):
1. Atendeu a ligação prontamente e utilizou a saudação correta? (10 pts)
   - "Sim" (10 pts): Saudação completa com nome e empresa, seguida de oferta de ajuda
   - "Parcial" (5 pts): Saudação incompleta 
   - "Não" (0 pts): Sem saudação adequada

2. Confirmou verbalmente o histórico de utilizações do cliente? (7 pts)
   - "Sim" (7 pts): Mencionou ou perguntou diretamente sobre histórico de utilizações
   - "Não" (0 pts): Não mencionou histórico de utilização

3. Solicitou verbalmente 2 telefones para contato e confirmou outros dados? (6 pts)
   - "Sim" (6 pts): Solicitou explicitamente dois números de telefone diferentes
   - "Parcial" (3 pts): Solicitou apenas um telefone ou não confirmou segundo número
   - "Não" (0 pts): Não solicitou número de telefone

4. Verbalizou COMPLETAMENTE o script da LGPD? (2 pts)
   - "Sim" (2 pts): Mencionou tratamento de dados pessoais conforme LGPD e compartilhamento
   - "Não" (0 pts): Não mencionou LGPD ou mencionou apenas parcialmente
   - Script LGPD referência: "Informo que seus dados pessoais serão tratados para a finalidade específica de prestação dos serviços contratados, incluindo os dados sensíveis, se necessário, conforme a Lei Geral de Proteção de Dados. Podemos compartilhar seus dados com parceiros comerciais envolvidos na prestação dos nossos serviços."

5. Utilizou a técnica do eco para confirmar informações coletadas? (5 pts)
   - "Sim" (5 pts): Repetiu informações fornecidas pelo cliente para confirmar
   - "Parcial" (2.5 pts): Usou a técnica parcialmente, apenas com algumas informações
   - "Não" (0 pts): Não repetiu informações para confirmar

6. Escutou atentamente, evitando solicitações em duplicidade? (3 pts)
   - "Sim" (3 pts): Não pediu a mesma informação mais de uma vez sem justificativa
   - "Não" (0 pts): Solicitou a mesma informação repetidamente

7. Demonstrou verbalmente domínio sobre o produto/serviço? (5 pts)
   - "Sim" (5 pts): Explicou procedimentos com segurança e conhecimento
   - "Parcial" (2.5 pts): Demonstrou conhecimento limitado ou insegurança
   - "Não" (0 pts): Demonstrou falta de conhecimento ou forneceu informações incorretas

8. Se precisou de ajuda, mencionou consulta ao manual? (2 pts)
   - "Sim" (2 pts): Mencionou consulta ao manual OU não precisou de ajuda
   - "Não" (0 pts): Precisou de ajuda e não mencionou consulta ao manual
   - "Não Verificável" (0 pts): Não é possível determinar se precisou de ajuda

9. Confirmou verbalmente informações completas sobre o dano no veículo? (10 pts)
   - "Sim" (10 pts): Perguntou sobre detalhes específicos do dano (localização, tamanho, etc.)
   - "Parcial" (5 pts): Perguntou apenas informações básicas sobre o dano
   - "Não" (0 pts): Não perguntou detalhes sobre o dano

10. Confirmou verbalmente data e motivo da quebra e demais detalhes do dano? (10 pts)
    - "Sim" (10 pts): Perguntou especificamente sobre quando e como ocorreu o dano
    - "Parcial" (5 pts): Perguntou apenas data OU motivo, mas não ambos
    - "Não" (0 pts): Não perguntou sobre data e motivo

11. Confirmou verbalmente cidade para atendimento e discutiu opções de loja? (10 pts)
    - "Sim" (10 pts): Confirmou a cidade E discutiu opções de lojas
    - "Parcial" (5 pts): Confirmou apenas a cidade sem discutir opções
    - "Não" (0 pts): Não confirmou cidade nem discutiu opções

12. Comunicação eficaz, sem gírias, informando ausências na linha? (5 pts)
    - "Sim" (5 pts): Comunicação clara, profissional e informou ausências
    - "Parcial" (2.5 pts): Comunicação geralmente boa, mas com falhas pontuais
    - "Não" (0 pts): Uso de gírias ou não informou ausências na linha

13. Verificou verbalmente se dúvidas foram sanadas? (6 pts)
    - "Sim" (6 pts): Perguntou explicitamente se havia mais dúvidas/questões
    - "Não" (0 pts): Não verificou se o cliente tinha mais dúvidas

14. Realizou o script de encerramento completo? (15 pts)
    - "Sim" (15 pts): Utilizou TODOS os elementos do script
    - "Parcial" (7.5 pts): Utilizou parte do script (pelo menos 3 elementos)
    - "Não" (0 pts): Utilizou menos de 3 elementos do script
    - Elementos do script:
      a) Informou sobre o envio de links no WhatsApp
      b) Mencionou sobre a franquia a ser paga
      c) Perguntou se poderia ajudar com mais alguma coisa
      d) Mencionou a pesquisa de satisfação
      e) Agradeceu e desejou bom dia/tarde/noite

15. Orientou verbalmente sobre a pesquisa de satisfação? (6 pts)
    - "Sim" (6 pts): Mencionou explicitamente a pesquisa e a nota máxima
    - "Parcial" (3 pts): Mencionou a pesquisa sem explicar a nota máxima
    - "Não" (0 pts): Não mencionou a pesquisa de satisfação

16. Mencionou verbalmente que estava realizando o registro/tabulação? (4 pts)
    - "Sim" (4 pts): Mencionou explicitamente que estava registrando/tabulando
    - "Não" (0 pts): Não mencionou registro/tabulação
    - "Não Verificável" (0 pts): Impossível determinar apenas pelo áudio

17. Demonstrou conduta acolhedora, com empatia e desejo de ajudar? (4 pts)
    - "Sim" (4 pts): Tom acolhedor, expressões de cortesia, sem interrupções
    - "Parcial" (2 pts): Comportamento misto, com momentos de empatia e outros de frieza
    - "Não" (0 pts): Tom frio, interruptions frequentes, falta de empatia

SCRIPT DE ENCERRAMENTO COMPLETO (referência para item 14):
"*obrigada por me aguardar! O seu atendimento foi gerado, e em breve receberá dois links no whatsapp informado, para acompanhar o pedido e realizar a vistoria.*
*Lembrando que o seu atendimento tem uma franquia de XXX que deverá ser paga no ato do atendimento. (****acessórios/RRSM ****- tem uma franquia que será confirmada após a vistoria).*
*Te ajudo com algo mais?*
*Ao final do atendimento terá uma pesquisa de Satisfação, a nota 5 é a máxima, tudo bem?*
*Agradeço o seu contato, tenha um excelente dia!"*

CRITÉRIOS ELIMINATÓRIOS (cada um resulta em 0 pontos se ocorrer):
- Ofereceu/garantiu verbalmente algum serviço que o cliente não tinha direito?
- Mencionou verbalmente informações incorretas sobre veículo/peça?
- Agiu de forma rude, grosseira, não deixando o cliente falar?
- Encerrou a chamada ou transferiu o cliente sem o seu conhecimento?
- Falou negativamente sobre a Carglass, afiliados, seguradoras ou colegas?

DIRETRIZES FINAIS:
1. Para itens que NÃO podem ser verificados somente pelo áudio (ações no sistema), classifique como "Não Verificável" e atribua 0 pontos.
2. Avalie o script LGPD com rigor - ele deve ser mencionado COMPLETAMENTE para pontuar.
3. Na avaliação do script de encerramento, verifique se todos os elementos foram mencionados.
4. CALCULE a pontuação total somando exatamente os pontos atribuídos, sem arredondamentos.
5. Responda APENAS com o JSON, sem texto adicional antes ou depois.
"""

        with st.spinner(f"Analisando a conversa com {modelo_gpt}..."):
            try:
                response = client.chat.completions.create(
                    model=modelo_gpt,
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em atendimento."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                result = response.choices[0].message.content.strip()

                # Debugar o resultado para identificar problemas
                with st.expander("Debug - Resposta JSON (expandir em caso de erro)"):
                    st.code(result, language="json")
                
                # Limpar o resultado para ter certeza que começa com {
                if not result.startswith("{"):
                    # Tenta encontrar o JSON na resposta
                    json_start = result.find("{")
                    json_end = result.rfind("}")
                    if json_start >= 0 and json_end >= 0:
                        result = result[json_start:json_end+1]
                    else:
                        raise ValueError("Formato de resposta inválido")

                analysis = json.loads(result)

                # Temperatura
                st.subheader("🌡️ Temperatura Emocional")
                temp = analysis.get("temperatura", {})
                temp_class = temp.get("classificacao", "Desconhecida")
                
                # Mapeamento expandido de temperaturas emocionais
                emoji_map = {
                    'Calma': '😌', 
                    'Neutra': '😐', 
                    'Tensa': '😟', 
                    'Muito Tensa': '😡',
                    'Quente': '🔥',  # Adicionado novo status
                    'Fria': '❄️'     # Adicionado novo status
                }
                emoji = emoji_map.get(temp_class, '❓')
                
                # Mapeamento para cores de temperatura
                if temp_class == "Calma" or temp_class == "Fria":
                    temp_class_style = "temperature-calm"
                elif temp_class == "Neutra":
                    temp_class_style = "temperature-neutral"
                elif temp_class == "Tensa" or temp_class == "Quente":
                    temp_class_style = "temperature-tense"
                elif temp_class == "Muito Tensa":
                    temp_class_style = "temperature-very-tense"
                else:
                    temp_class_style = ""
                    
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
                    # Mostra apenas os primeiros itens se a lista for muito longa
                    for item in checklist:
                        try:
                            # Garantir que todos os campos existam, mesmo que vazios
                            item_num = item.get('item', '')
                            criterio = item.get('criterio', '')
                            pontos = item.get('pontos', 0)
                            resposta = str(item.get('resposta', '')).lower()
                            justificativa = item.get('justificativa', '')
                            
                            if resposta == "sim":
                                classe = "criterio-sim"
                                icone = "✅"
                            elif "parcial" in resposta:
                                classe = "criterio-parcial"
                                icone = "⚠️"
                            elif "não verificável" in resposta:
                                classe = "criterio-nao-verificavel"
                                icone = "❔"
                            else:
                                classe = "criterio-nao"
                                icone = "❌"
                            
                            st.markdown(f"""
                            <div class="{classe}">
                            {icone} <strong>{item_num}. {criterio}</strong> ({pontos} pts)<br>
                            <em>{justificativa}</em>
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as item_error:
                            st.warning(f"Não foi possível exibir um item do checklist: {str(item_error)}")
                            st.write(item)

                # Resumo
                st.subheader("📝 Resumo Geral")
                st.markdown(f"<div class='result-box'>{analysis.get('resumo_geral')}</div>", unsafe_allow_html=True)
                
                # Gerar PDF
                st.subheader("📄 Relatório em PDF")
                try:
                    pdf_bytes = create_pdf(analysis, transcript_text, modelo_gpt)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"HeatGlass_Relatorio_{timestamp}.pdf"
                    st.markdown(get_pdf_download_link(pdf_bytes, filename), unsafe_allow_html=True)
                except Exception as pdf_error:
                    st.error(f"Erro ao gerar PDF: {str(pdf_error)}")

            except Exception as e:
                st.error(f"Erro ao processar a análise: {str(e)}")
                try:
                    st.text_area("Resposta da IA:", value=response.choices[0].message.content.strip(), height=300)
                except:
                    st.text_area("Não foi possível recuperar a resposta da IA", height=300)
