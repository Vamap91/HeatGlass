import streamlit as st
# Configurações da página - DEVE ser a primeira chamada Streamlit
st.set_page_config(page_title="HeatGlass", page_icon="🔴", layout="centered")

from openai import OpenAI
import tempfile
import re
import json
import base64
from datetime import datetime
from fpdf import FPDF

# Inicializa o novo cliente da OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
    pdf.cell(0, 10, f"{total} pontos de 81", 0, 1)
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

# Função para extrair JSON válido da resposta
def extract_json(text):
    # Procura pelo primeiro '{' e último '}'
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = text[start_idx:end_idx+1]
        try:
            # Verifica se é um JSON válido
            return json.loads(json_str)
        except:
            # Se não for, tenta encontrar o JSON de outras formas
            pass
    
    # Tenta usar expressão regular para encontrar um bloco JSON
    import re
    json_pattern = r'\{(?:[^{}]|(?R))*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    if matches:
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
    
    # Se tudo falhar, lança um erro detalhado
    raise ValueError(f"Não foi possível extrair JSON válido da resposta: {text[:100]}...")

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
    else:
        return "script-nao-usado"

# Modelo fixo: GPT-4 Turbo
modelo_gpt = "gpt-4-turbo"

# Título
st.title("HeatGlass")
st.write("Análise inteligente de ligações: avaliação de atendimento ao cliente e conformidade com processos.")

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

        # Prompt - Usando o checklist e instruções originais, mas removendo temperatura/impacto
        prompt = f"""
Você é um especialista em atendimento ao cliente. Avalie a transcrição a seguir:

TRANSCRIÇÃO:
\"\"\"{transcript_text}\"\"\"

Retorne APENAS um JSON com os seguintes campos, sem texto adicional antes ou depois:

{{
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

You are a specialized customer service analyst. Analyze the Portuguese transcript with ABSOLUTE RIGOR.
MANDATORY SCORING LOGIC:

Default assumption: All items start as "NO" until explicitly proven in transcript
Scoring rule: Only add points for items marked as "yes"
Zero tolerance: If the answer is "no", assign 0 points
Never display 81 points by default
Final score = sum of all "yes" items only

VALIDATION PROCESS:

Read transcript completely first
For each checklist item: Find explicit evidence before marking "yes"
Cross-validation: Re-check items 2 and 6 using specific criteria below
Final verification: Ensure total score reflects only "yes" items


TRANSCRIPT TO ANALYZE:
{transcript_text}

CHECKLIST (Portuguese content - 81 pts totais):

Atendeu a ligação prontamente, dentro de 5 seg. e utilizou a saudação correta com as técnicas do atendimento encantador? (10 Pontos)
Confirmou os dados do cadastro e pediu 2 telefones para contato? (Nome, CPF, Placa, e-mail, Veículo, Endereço, etc) (6 Pontos)
Verbalizou o script da LGPD? (2 Pontos)
Utilizou a técnica do eco para garantir o entendimento sobre as informações coletadas, evitando erros no processo e recontato do cliente? (5 Pontos)
Escutou atentamente a solicitação do segurado evitando solicitações em duplicidade? (3 Pontos)
Compreendeu a solicitação do cliente em linha e demonstrou domínio sobre o produto/serviço? (5 Pontos)
Confirmou as informações completas sobre o dano no veículo? Confirmou data e motivo da quebra, registro do item, dano na pintura e demais informações necessárias para o correto fluxo de atendimento. (tamanho da trinca, LED, Xenon, etc) - 10 Pontos
Confirmou cidade para o atendimento e selecionou corretamente a primeira opção de loja identificada pelo sistema? (10 Pontos)
A comunicação com o cliente foi eficaz: não houve uso de gírias, linguagem inadequada ou conversas paralelas? O analista informou quando ficou ausente da linha e quando retornou? (5 Pontos)
A conduta do analista foi acolhedora, com sorriso na voz, empatia e desejo verdadeiro em entender e solucionar a solicitação do cliente? (4 Pontos)
Realizou o script de encerramento completo, informando: prazo de validade, franquia, link de acompanhamento e vistoria, e orientou que o cliente aguarde o contato para agendamento? (15 Pontos)
Orientou o cliente sobre a pesquisa de satisfação do atendimento? (6 Pontos)


CRITICAL VALIDATION RULES (English for accuracy):
IMPORTANT: Final score must be automatically recalculated based on points effectively assigned to each item. Even if the evaluation structure provides for a maximum of 81 points, no report should display 81 points if any item is evaluated as "no". The value displayed as "Total Score" must faithfully reflect the sum of points obtained.

INSTRUÇÕES ADICIONAIS DE AVALIAÇÃO (Portuguese content):

Técnica do eco: Marque como "sim" somente se o atendente repetir verbalmente informações essenciais como telefones, placa ou CPF após coletá-las. O eco deve ser claro, objetivo e demonstrar validação do entendimento. Caso contrário, marque como "não".
Script LGPD: O atendente deve mencionar explicitamente que o telefone será compartilhado com o prestador de serviço, com ênfase em privacidade ou consentimento. As seguintes variações são válidas:

Você permite que a nossa empresa compartilhe o seu telefone com o prestador que irá lhe atender?
Podemos compartilhar seu telefone com o prestador que irá realizar o serviço?
Seu telefone pode ser informado ao prestador que irá realizar o serviço?
O prestador pode ter acesso ao seu número para realizar o agendamento do serviço?
Podemos compartilhar seu telefone com o prestador que irá te atender?
Você autoriza o compartilhamento do telefone informado com o prestador que irá te atender?


Confirmação de histórico: Verifique se há menção explícita ao histórico de utilização do serviço pelo cliente. A simples localização do cliente no sistema NÃO constitui confirmação de histórico.
Pontuação: Cada item não realizado deve impactar estritamente a pontuação final. Os pontos máximos de cada item estão indicados entre parênteses - se marcado como "não", zero pontos devem ser atribuídos.
Critérios eliminatórios: Avalie com alto rigor - qualquer ocorrência, mesmo que sutil, deve ser marcada.
Script de encerramento: Compare literalmente com o modelo fornecido - só marque como "completo" se TODOS os elementos estiverem presentes (validade, franquia, link, pesquisa de satisfação e despedida).

ENHANCED VALIDATION (English for precision):

Checklist Item 2 - Data Confirmation: Mark "yes" ONLY if ALL the following are present: complete name confirmed, CPF/CNPJ requested, plate confirmed, email requested, address confirmed, exactly 2 phones collected. If ANY item is missing, mark "no".
Checklist Item 6 - Service Comprehension: Mark "yes" only if the agent correctly identified the requested service/part from the beginning, without confusion. Any misunderstanding about the service type results in "no".


CRITÉRIOS ELIMINATÓRIOS (Portuguese content):
Cada um resulta em 0 pontos se ocorrer:

Ofereceu/garantiu algum serviço que o cliente não tinha direito?
Preencheu ou selecionou o Veículo/peça incorretos?
Agiu de forma rude, grosseira, não deixando o cliente falar e/ou se alterou na ligação?
Encerrou a chamada ou transferiu o cliente sem o seu conhecimento?
Falou negativamente sobre a Carglass, afiliados, seguradoras ou colegas de trabalho?
Forneceu informações incorretas ou fez suposições infundadas sobre garantias, serviços ou procedimentos?
Comentou sobre serviços de terceiros ou orientou o cliente para serviços externos sem autorização?

ATENÇÃO: Avalie com rigor frases como "Não teria problema em mexer na lataria e o senhor perder a garantia?" ou "provavelmente a sua garantia é motor e câmbio".

SCRIPT DE ENCERRAMENTO CORRETO:
"obrigada por me aguardar! O seu atendimento foi gerado, e em breve receberá dois links no whatsapp informado, para acompanhar o pedido e realizar a vistoria.
Lembrando que o seu atendimento tem uma franquia de XXX que deverá ser paga no ato do atendimento. (acessórios/RRSM - tem uma franquia que será confirmada após a vistoria).
Te ajudo com algo mais?
Ao final do atendimento terá uma pesquisa de Satisfação, a nota 5 é a máxima, tudo bem?
Agradeço o seu contato, tenha um excelente dia!"
Avalie se o script acima foi utilizado completamente ou não foi utilizado.

OUTPUT FORMAT (English for precision):
CRITICAL: Return ONLY JSON, no additional text, no code decorators like ```json, and no additional explanations."""

        with st.spinner("Analisando a conversa..."):
            try:
                response = client.chat.completions.create(
                    model=modelo_gpt,
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em atendimento. Responda APENAS com o JSON solicitado, sem texto adicional, sem marcadores de código como ```json, e sem explicações."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}  # Força resposta em formato JSON
                )
                result = response.choices[0].message.content.strip()

                # Mostrar resultado bruto para depuração
                with st.expander("Debug - Resposta bruta"):
                    st.code(result, language="json")
                
                # Tentar extrair e validar o JSON com a função melhorada
                try:
                    if not result.startswith("{"):
                        analysis = extract_json(result)
                    else:
                        analysis = json.loads(result)
                except Exception as json_error:
                    st.error(f"Erro ao processar JSON: {str(json_error)}")
                    st.text_area("Resposta da IA:", value=result, height=300)
                    st.stop()

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
                st.markdown(f"<h3 class='{progress_class}'>{int(total)} pontos de 81</h3>", unsafe_allow_html=True)

                with st.expander("Ver Detalhes do Checklist"):
                    for item in checklist:
                        resposta = item.get("resposta", "").lower()
                        if resposta == "sim":
                            classe = "criterio-sim"
                            icone = "✅"
                        else:
                            classe = "criterio-nao"
                            icone = "❌"
                        
                        st.markdown(f"""
                        <div class="{classe}">
                        {icone} <strong>{item.get('item')}. {item.get('criterio')}</strong> ({item.get('pontos')} pts)<br>
                        <em>{item.get('justificativa')}</em>
                        </div>
                        """, unsafe_allow_html=True)

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
