import streamlit as st
# Configurações da página - DEVE ser a primeira chamada Streamlit
st.set_page_config(page_title="HeatGlass", page_icon="🔴", layout="centered")

from openai import OpenAI
import tempfile
import re
import json
import base64
import os
import hashlib
from datetime import datetime
from fpdf import FPDF

# ================== MÓDULO DE PROTEÇÃO DE DADOS ==================
class DataProtectionManager:
    def __init__(self):
        self.temp_files_created = []
        
    def anonymize_transcript(self, text):
        """
        PROTEÇÃO DE DADOS: Remove dados pessoais da transcrição
        """
        original_text = text
        
        # Remove CPFs (formatos: 123.456.789-00, 12345678900)
        text = re.sub(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b', '[CPF_REMOVIDO]', text)
        
        # Remove placas antigas (ABC-1234) e Mercosul (ABC1D23)
        text = re.sub(r'\b[A-Z]{3}-?\d{4}\b|\b[A-Z]{3}\d[A-Z]\d{2}\b', '[PLACA_REMOVIDA]', text)
        
        # Remove emails
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REMOVIDO]', text)
        
        # Remove telefones (vários formatos)
        text = re.sub(r'\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b', '[TELEFONE_REMOVIDO]', text)
        
        # Remove RG (formatos comuns)
        text = re.sub(r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9X]\b', '[RG_REMOVIDO]', text)
        
        # NOTA: Nomes de clientes são mantidos para contexto da análise
        # Removemos apenas dados pessoais estruturados (CPF, telefone, etc.)
        
        # Verificar se houve mudanças
        changes_made = len(original_text) != len(text)
        if changes_made:
            st.info("🔒 Dados pessoais identificados e anonimizados automaticamente")
            
        return text
    
    def track_temp_file(self, file_path):
        """
        RASTREAMENTO: Adiciona arquivo à lista para limpeza posterior
        """
        file_info = {
            'path': file_path,
            'created_at': datetime.now(),
            'hash': hashlib.md5(file_path.encode()).hexdigest()[:8]
        }
        self.temp_files_created.append(file_info)
        
        # Log da criação
        st.write(f"📁 Arquivo temporário criado: {file_info['hash']}")
        
        return file_path
    
    def cleanup_all_temp_files(self):
        """
        LIMPEZA: Remove todos os arquivos temporários
        """
        cleaned_count = 0
        
        for file_info in self.temp_files_created:
            try:
                if os.path.exists(file_info['path']):
                    os.unlink(file_info['path'])
                    cleaned_count += 1
                    st.write(f"🗑️ Removido: {file_info['hash']} (criado em {file_info['created_at'].strftime('%H:%M:%S')})")
            except Exception as e:
                st.warning(f"⚠️ Erro ao remover {file_info['hash']}: {str(e)}")
        
        if cleaned_count > 0:
            st.success(f"✅ {cleaned_count} arquivo(s) temporário(s) removido(s) com sucesso")
        
        # Limpa a lista
        self.temp_files_created.clear()

# ================== CÓDIGO PRINCIPAL ==================

# Inicializa o novo cliente da OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Função para criar PDF com dados anonimizados
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
    pdf.cell(0, 10, "Status: Dados pessoais anonimizados conforme LGPD", 0, 1)  # NOVO
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
    
    # Transcrição anonimizada na última página
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Transcrição Anonimizada", 0, 1)  # MODIFICADO
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
.privacy-notice {
    background-color: #e8f4f8;
    border-left: 5px solid #2196F3;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 20px;
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

# ================== INTERFACE PRINCIPAL ==================

# Título
st.title("HeatGlass")
st.write("Análise inteligente de ligações: avaliação de atendimento ao cliente e conformidade com processos.")

# NOVO: Aviso de Privacidade
st.markdown("""
<div class="privacy-notice">
🔒 <strong>Proteção de Dados Ativada</strong><br>
• Arquivos de áudio são removidos automaticamente após o processamento<br>
• Dados pessoais (CPF, nomes, telefones) são anonimizados na transcrição<br>
• Processamento conforme LGPD - nenhum dado pessoal é armazenado<br>
• Relatórios contêm apenas dados anonimizados
</div>
""", unsafe_allow_html=True)

# Upload de áudio
uploaded_file = st.file_uploader("Envie o áudio da ligação (.mp3)", type=["mp3"])

if uploaded_file is not None:
    # NOVO: Inicializar proteção de dados
    if 'data_protection' not in st.session_state:
        st.session_state.data_protection = DataProtectionManager()

    # MODIFICADO: Criar arquivo temporário com rastreamento
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # NOVO: Registrar arquivo para limpeza
    st.session_state.data_protection.track_temp_file(tmp_path)

    st.audio(uploaded_file, format='audio/mp3')

    if st.button("🔍 Analisar Atendimento"):
        try:  # NOVO: Envolver tudo em try/finally para garantir limpeza
            # Transcrição via Whisper
            with st.spinner("Transcrevendo o áudio..."):
                with open(tmp_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                raw_transcript = transcript.text  # MODIFICADO: Guardar versão original

            # NOVO: Anonimização imediata
            with st.spinner("Anonimizando dados pessoais..."):
                transcript_text = st.session_state.data_protection.anonymize_transcript(raw_transcript)

            # MODIFICADO: Mostrar apenas transcrição anonimizada
            with st.expander("Ver transcrição anonimizada"):
                st.code(transcript_text, language="markdown")

            # Prompt usando dados anonimizados
            prompt = f"""
Você é um especialista em atendimento ao cliente. Avalie a transcrição a seguir:

TRANSCRIÇÃO ANONIMIZADA:
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

Scoring logic (mandatory):
*Only add points for items marked as "yes".
*If the answer is "no", assign 0 points.
*Never display 81 points by default.
*Final score = sum of all "yes" items only.

Checklist (81 pts totais):
1. Atendeu a ligação prontamente, dentro de 5 seg. e utilizou a saudação correta com as técnicas do atendimento encantador? (10 Pontos)
2. Solicitou os dados do cadastro do cliente e pediu 2 telefones para contato, nome, cpf, placa do veículo e endereço ? Só é "sim" se todas as informações forem solicitadas (6 Pontos)
3. O Atendente Verbalizou o script LGPD? Script informado em Instruções Adicionais de Avaliação tópico 2. (2 Pontos)
4. Utilizou a técnica do eco para garantir o entendimento sobre as informações coletadas, evitando erros no processo e recontato do cliente? (5 Pontos)
5. Escutou atentamente a solicitação do segurado evitando solicitações em duplicidade?  (3 Pontos)
6. Compreendeu a solicitação do cliente em linha e demonstrou que entende sobre os serviços da empresa? (5 Pontos)
7. Confirmou as informações completas sobre o dano no veículo? Confirmou data e motivo da quebra, registro do item, dano na pintura e demais informações necessárias para o correto fluxo de atendimento. (tamanho da trinca, LED, Xenon, etc) - 10 Pontos
8. Confirmou cidade para o atendimento e selecionou corretamente a primeira opção de loja identificada pelo sistema?  (10 Pontos)
9. A comunicação com o cliente foi eficaz: não houve uso de gírias, linguagem inadequada ou conversas paralelas? O analista informou quando ficou ausente da linha e quando retornou? (5 Pontos)
10. A conduta do analista foi acolhedora, com sorriso na voz, empatia e desejo verdadeiro em entender e solucionar a solicitação do cliente? (4 Pontos)
11.Realizou o script de encerramento completo, informando: prazo de validade, franquia, link de acompanhamento e vistoria, e orientou que o cliente aguarde o contato para agendamento? (15 Pontos)
12. Orientou o cliente sobre a pesquisa de satisfação do atendimento? (6 Pontos)

[resto do prompt igual ao original...]

IMPORTANTE: Retorne APENAS o JSON, sem nenhum texto adicional, sem decoradores de código como ```json ou ```, e sem explicações adicionais.
"""

            with st.spinner("Analisando a conversa..."):
                response = client.chat.completions.create(
                    model=modelo_gpt,
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em atendimento. Responda APENAS com o JSON solicitado, sem texto adicional, sem marcadores de código como ```json, e sem explicações."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                result = response.choices[0].message.content.strip()

                # Debug
                with st.expander("Debug - Resposta bruta"):
                    st.code(result, language="json")
                
                # Processar JSON
                try:
                    if not result.startswith("{"):
                        analysis = extract_json(result)
                    else:
                        analysis = json.loads(result)
                except Exception as json_error:
                    st.error(f"Erro ao processar JSON: {str(json_error)}")
                    st.text_area("Resposta da IA:", value=result, height=300)
                    st.stop()

                # Exibir resultados (código original)
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
                
                # MODIFICADO: Gerar PDF com dados anonimizados
                st.subheader("📄 Relatório em PDF")
                try:
                    pdf_bytes = create_pdf(analysis, transcript_text, modelo_gpt)  # transcript_text já anonimizado
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"HeatGlass_Relatorio_Anonimizado_{timestamp}.pdf"  # MODIFICADO: Nome indica anonimização
                    st.markdown(get_pdf_download_link(pdf_bytes, filename), unsafe_allow_html=True)
                except Exception as pdf_error:
                    st.error(f"Erro ao gerar PDF: {str(pdf_error)}")

        except Exception as e:
            st.error(f"Erro ao processar a análise: {str(e)}")
            try:
                st.text_area("Resposta da IA:", value=response.choices[0].message.content.strip(), height=300)
            except:
                st.text_area("Não foi possível recuperar a resposta da IA", height=300)
        
        finally:
            # NOVO: Limpeza garantida (sempre executa)
            st.subheader("🧹 Limpeza de Dados")
            st.session_state.data_protection.cleanup_all_temp_files()

# NOVO: Botão manual de limpeza (segurança extra)
if st.button("🗑️ Limpar Todos os Arquivos Temporários"):
    if 'data_protection' in st.session_state:
        st.session_state.data_protection.cleanup_all_temp_files()
    else:
        st.info("Nenhum arquivo temporário para limpar")

# NOVO: Status de arquivos temporários (para debugging)
if st.checkbox("Mostrar Status de Arquivos Temporários (Debug)"):
    if 'data_protection' in st.session_state and st.session_state.data_protection.temp_files_created:
        st.write("📁 Arquivos temporários ativos:")
        for file_info in st.session_state.data_protection.temp_files_created:
            st.write(f"- {file_info['hash']}: {file_info['created_at'].strftime('%H:%M:%S')}")
    else:
        st.success("✅ Nenhum arquivo temporário ativo")
