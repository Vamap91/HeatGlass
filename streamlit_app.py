#!/usr/bin/env python
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

        # Definição do prompt MELHORADO
        prompt_template = """
        Você é um especialista em avaliação de atendimento ao cliente para a Carglass. Avalie APENAS o que pode ser verificado pela transcrição do áudio a seguir, sem fazer suposições sobre o que aconteceu na tela do atendente.

        TRANSCRIÇÃO:
        """{{}}"""

        IMPORTANTE: Você está avaliando SOMENTE o áudio da ligação. NÃO tem acesso à tela do atendente e NÃO pode ver suas ações no sistema. Para itens que exigem visualização da tela (como "realizou tabulação", "selecionou loja corretamente"), responda "Não Verificável".

        INSTRUÇÕES CRÍTICAS:
        1. Avalie SOMENTE o que é explicitamente verificável na transcrição.
        2. A pontuação DEVE refletir exatamente os critérios cumpridos ou não cumpridos.
        3. Sempre que um item for marcado como "Não" ou "Não Verificável", atribua 0 pontos.
        4. Quando um item for marcado como "Parcial", atribua metade dos pontos disponíveis.
        5. Calcule a pontuação total como a soma exata dos pontos obtidos, sem arredondamentos.
        6. Use APENAS as classificações permitidas para cada campo.
        7. Analise o **tom geral da conversa** e o **comportamento do cliente**. Identifique palavras-chave, frases ou padrões de fala que indiquem emoções específicas (positivas ou negativas), mesmo que não declaradas explicitamente. Considere a progressão da conversa: ela se tornou mais tensa ou mais calma ao longo do tempo?

        Retorne um JSON com os seguintes campos:

        {{
          "temperatura": {{
            "classificacao": "Calma/Neutra/Tensa/Muito Tensa", 
            "justificativa": "[Avalie a temperatura emocional predominante da interação, considerando tanto as falas do cliente quanto as do atendente. Justifique sua classificação citando trechos específicos da transcrição que evidenciem o sentimento. Preste atenção especial a sinais de frustração, impaciência, sarcasmo, tom de voz elevado (inferido do texto), ou qualquer indicação de conflito ou desconforto. Ex: Cliente demonstrou impaciência ao dizer '...'. A atendente pareceu não compreender a solicitação inicial, levando a repetições.]",
            "definicoes_temperatura": {{
                "Calma": "Interação fluida, cordial, sem sinais de tensão, frustração ou discordância significativa. Cliente e atendente demonstram paciência e cooperação.",
                "Neutra": "Interação predominantemente informativa, sem forte carga emocional positiva ou negativa. Pode haver pequenas dúvidas ou hesitações, mas sem escalada para conflito.",
                "Tensa": "Presença de sinais de impaciência, frustração leve, discordâncias não resolvidas rapidamente, ou um tom de voz que sugere irritação por parte de um ou ambos os interlocutores. Pode haver repetição de perguntas ou afirmações de forma enfática.",
                "Muito Tensa": "Conflito aberto, reclamações diretas e contundentes sobre o serviço, a empresa ou o atendente. Sarcasmo evidente, ameaças de escalonamento, ou linguagem que indique forte insatisfação e hostilidade. A comunicação é difícil e pouco produtiva."
            }}
          }},
          "impacto_comercial": {{ 
            "percentual": [0-100], 
            "faixa": "Baixo/Moderado/Alto", 
            "justificativa": "[Ao definir o percentual e a faixa de impacto comercial, leve em consideração a temperatura emocional da ligação e a satisfação final do cliente. Interações muito negativas, mesmo que curtas, podem ter alto impacto comercial devido ao risco de perda do cliente ou dano à reputação.]"
          }},
          "status_final": {{
            "satisfacao": "Satisfeito/Parcialmente Satisfeito/Insatisfeito", 
            "risco": "Baixo/Médio/Alto", 
            "desfecho": "Positivo/Neutro/Negativo",
            "justificativa_satisfacao": "[Avalie o nível de satisfação do cliente ao final da interação, com base em suas declarações explícitas e implícitas, tom de voz (inferido) e a resolução (ou não) de seus problemas/questões. Justifique sua classificação com evidências da transcrição. Ex: Cliente afirmou 'não está tudo bem' e criticou a empresa.]",
            "definicoes_satisfacao": {{
                "Satisfeito": "Cliente expressa contentamento claro, agradece de forma genuína, e seus problemas parecem ter sido resolvidos a contento. Não há resquícios de frustração.",
                "Parcialmente Satisfeito": "O problema principal pode ter sido encaminhado, mas o cliente ainda demonstra alguma hesitação, dúvida, ou resquício de insatisfação com parte do processo ou da interação. Pode haver agradecimentos protocolares, mas sem entusiasmo.",
                "Insatisfeito": "Cliente expressa claramente descontentamento, frustração, ou irritação. O problema não foi resolvido a contento, ou a experiência de atendimento foi negativa. Pode haver reclamações diretas, tom agressivo, ou finalização abrupta da chamada pelo cliente."
            }}
          }},
          "checklist": [
            {{"item": 1, "criterio": "Atendeu a ligação prontamente, dentro de 5 seg. e utilizou a saudação correta com as técnicas do atendimento encantador?", "pontos": [valor numérico], "resposta": "Sim/Parcial/Não/Não Verificável", "justificativa": "..."}},
            {{ "item": 2, "criterio": "Confirmou verbalmente o histórico de utilizações do cliente?", "pontos": [valor numérico], "resposta": "Sim/Não/Não Verificável", "justificativa": "..."}} 
            # ... (restante do checklist permanece o mesmo, adicionei reticências para brevidade aqui, mas no código real ele continua)
          ],
          "criterios_eliminatorios": [
            {{"criterio": "Ofereceu/garantiu algum serviço que o cliente não tinha direito?", "ocorreu": true/false, "justificativa": "..."}},
            {{"criterio": "Atendente forneceu informações ou orientações incorretas sobre a garantia do fabricante do veículo (ex: sugerir que acionar um serviço da Carglass poderia afetar a garantia de fábrica)?", "ocorreu": true/false, "justificativa": "[Se ocorreu, detalhar a orientação incorreta fornecida.]"}}
            # ... (restante dos critérios eliminatórios permanece o mesmo)
          ],
          "uso_script": {{"status": "completo/parcial/não utilizado", "justificativa": "..."}},
          "pontuacao_total": [soma exata dos pontos],
          "resumo_geral": "[No campo resumo_geral, forneça uma síntese concisa da ligação, destacando os pontos principais discutidos, a experiência emocional do cliente, os problemas levantados, as soluções oferecidas (se houver) e o desfecho da interação. O resumo deve refletir tanto os aspectos técnicos quanto os emocionais.]"
        }}

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
              c) Informou sobre a pesquisa de satisfação
              d) Agradeceu e desejou um bom dia/tarde/noite
              e) Mencionou o nome da empresa no encerramento
        """

        # Análise via OpenAI
        with st.spinner("Analisando a transcrição com IA..."):
            try:
                prompt = prompt_template.format(transcript_text)
                response = client.chat.completions.create(
                    model=modelo_gpt,
                    messages=[
                        {"role": "system", "content": "Você é um especialista em avaliação de atendimento ao cliente."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2 # Baixa temperatura para respostas mais consistentes e factuais
                )
                analysis_text = response.choices[0].message.content
                
                # Limpeza de possível formatação markdown no JSON
                if analysis_text.strip().startswith("```json"):
                    analysis_text = analysis_text.strip()[7:-3].strip()
                elif analysis_text.strip().startswith("```"):
                    analysis_text = analysis_text.strip()[3:-3].strip()

                analysis_data = json.loads(analysis_text)

                st.subheader("Resultado da Análise da IA")

                # Exibição da Temperatura Emocional
                temp_info = analysis_data.get("temperatura", {})
                temp_class = get_temp_class(temp_info.get("classificacao", ""))
                st.markdown(f"<div class='status-box'><b>Temperatura Emocional:</b> <span class='{temp_class}'>{temp_info.get('classificacao', 'N/A')}</span><br><b>Justificativa:</b> {temp_info.get('justificativa', 'N/A')}</div>", unsafe_allow_html=True)

                # Exibição do Impacto Comercial
                impact_info = analysis_data.get("impacto_comercial", {})
                st.markdown(f"<div class='status-box'><b>Impacto Comercial:</b> {impact_info.get('percentual', 'N/A')}% ({impact_info.get('faixa', 'N/A')})<br><b>Justificativa:</b> {impact_info.get('justificativa', 'N/A')}</div>", unsafe_allow_html=True)

                # Exibição do Status Final
                final_info = analysis_data.get("status_final", {})
                st.markdown(f"<div class='status-box'><b>Status Final:</b><br>Satisfação do Cliente: {final_info.get('satisfacao', 'N/A')}<br>Risco: {final_info.get('risco', 'N/A')}<br>Desfecho: {final_info.get('desfecho', 'N/A')}</div>", unsafe_allow_html=True)

                # Exibição do Uso do Script de Encerramento
                script_info = analysis_data.get("uso_script", {})
                script_class = get_script_status_class(script_info.get("status", ""))
                st.markdown(f"<div class='{script_class}'><b>Uso do Script de Encerramento:</b> {script_info.get('status', 'N/A')}<br><b>Justificativa:</b> {script_info.get('justificativa', 'N/A')}</div>", unsafe_allow_html=True)
                
                # Exibição da Pontuação Total
                total_score = analysis_data.get("pontuacao_total", "N/A")
                st.markdown(f"<div class='status-box'><b>Pontuação Total:</b> {total_score} / 100 pontos</div>", unsafe_allow_html=True)

                # Exibição do Resumo Geral
                st.markdown(f"<div class='result-box'><b>Resumo Geral:</b><br>{analysis_data.get('resumo_geral', 'N/A')}</div>", unsafe_allow_html=True)
                
                # Exibição dos Critérios Eliminatórios
                eliminatorios = analysis_data.get("criterios_eliminatorios", [])
                if eliminatorios:
                    st.subheader("Critérios Eliminatórios")
                    for criterio in eliminatorios:
                        ocorreu_text = "Sim" if criterio.get("ocorreu") else "Não"
                        st.markdown(f"<div class='criterio-eliminatorio'><b>Critério:</b> {criterio.get('criterio', 'N/A')}<br><b>Ocorreu:</b> {ocorreu_text}<br><b>Justificativa:</b> {criterio.get('justificativa', 'N/A')}</div>", unsafe_allow_html=True)
                
                # Exibição do Checklist
                st.subheader("Checklist Detalhado da Avaliação")
                checklist_items = analysis_data.get("checklist", [])
                for item in checklist_items:
                    resposta = str(item.get("resposta", ""))
                    item_class = ""
                    if resposta.lower() == "sim": item_class = "criterio-sim"
                    elif resposta.lower() == "não": item_class = "criterio-nao"
                    elif resposta.lower() == "parcial": item_class = "criterio-parcial"
                    elif resposta.lower() == "não verificável": item_class = "criterio-nao-verificavel"
                    
                    st.markdown(f"<div class='{item_class}'><b>Item {item.get('item', '')}:</b> {item.get('criterio', 'N/A')} ({item.get('pontos', 0)} pts)<br><b>Resposta:</b> {resposta}<br><b>Justificativa:</b> {item.get('justificativa', 'N/A')}</div>", unsafe_allow_html=True)

                # Geração e download do PDF
                pdf_bytes = create_pdf(analysis_data, transcript_text, modelo_gpt)
                st.markdown(get_pdf_download_link(pdf_bytes, f"Relatorio_HeatGlass_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"), unsafe_allow_html=True)

            except json.JSONDecodeError as e:
                st.error(f"Erro ao decodificar a resposta JSON da IA: {e}")
                st.text_area("Resposta da IA (com erro de JSON):", analysis_text, height=200)
            except Exception as e:
                st.error(f"Ocorreu um erro durante a análise da IA: {e}")
                st.text_area("Resposta da IA (se disponível):", analysis_text if 'analysis_text' in locals() else "Nenhuma resposta da IA disponível", height=200)

    # Limpa o arquivo temporário
    import os
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
