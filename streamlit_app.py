import streamlit as st
from openai import OpenAI
import tempfile
import re
import json
import logging
from typing import Dict, List, Any, Tuple, Optional, Union

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('heatglass')

# Classe para gerenciar a API da OpenAI
class OpenAIManager:
    def __init__(self, api_key: str):
        """
        Inicializa o gerenciador da API OpenAI.
        
        Args:
            api_key: Chave de API da OpenAI
        """
        self.client = OpenAI(api_key=api_key)
        logger.info("Cliente OpenAI inicializado")
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcreve um arquivo de áudio usando o modelo Whisper.
        
        Args:
            audio_file_path: Caminho para o arquivo de áudio
            
        Returns:
            Texto transcrito
            
        Raises:
            Exception: Se ocorrer um erro durante a transcrição
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            logger.error(f"Erro na transcrição: {str(e)}")
            raise Exception(f"Falha ao transcrever o áudio: {str(e)}")
    
    def analyze_transcript(self, transcript_text: str) -> Dict[str, Any]:
        """
        Analisa a transcrição usando o modelo GPT-4.
        
        Args:
            transcript_text: Texto transcrito para análise
            
        Returns:
            Dicionário com os resultados da análise
            
        Raises:
            Exception: Se ocorrer um erro durante a análise
        """
        try:
            prompt = self._create_analysis_prompt(transcript_text)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um analista especializado em atendimento."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            if not result.startswith("{"):
                raise ValueError("Formato de resposta inválido")
                
            return json.loads(result)
        except Exception as e:
            logger.error(f"Erro na análise: {str(e)}")
            raise Exception(f"Falha ao analisar a transcrição: {str(e)}")
    
    def _create_analysis_prompt(self, transcript_text: str) -> str:
        """
        Cria o prompt para análise da transcrição.
        
        Args:
            transcript_text: Texto transcrito
            
        Returns:
            Prompt formatado para análise
        """
        return f"""
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

O script correto para a pergunta 14 é:
"*obrigada por me aguardar! O seu atendimento foi gerado, e em breve receberá dois links no whatsapp informado, para acompanhar o pedido e realizar a vistoria.*
*Lembrando que o seu atendimento tem uma franquia de XXX que deverá ser paga no ato do atendimento. (****acessórios/RRSM ****- tem uma franquia que será confirmada após a vistoria).*
*Te ajudo com algo mais?*
*Ao final do atendimento terá uma pesquisa de Satisfação, a nota 5 é a máxima, tudo bem?*
*Agradeço o seu contato, tenha um excelente dia!"*

Avalie se o script acima foi utilizado completamente, parcialmente ou não foi utilizado.

Responda apenas com o JSON e nada mais.
"""

# Classe para gerenciar a interface do usuário
class UIManager:
    def __init__(self):
        """
        Inicializa o gerenciador de interface do usuário.
        """
        self._setup_page_config()
        self._apply_custom_styles()
    
    def _setup_page_config(self):
        """
        Configura as definições da página Streamlit.
        """
        st.set_page_config(
            page_title="HeatGlass",
            page_icon="🔴",
            layout="centered"
        )
    
    def _apply_custom_styles(self):
        """
        Aplica estilos CSS personalizados à interface.
        """
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
        .app-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .app-description {
            margin-bottom: 2rem;
            text-align: center;
            font-size: 1.1rem;
        }
        .file-uploader {
            margin-bottom: 1.5rem;
        }
        .analysis-button {
            margin: 1rem 0;
        }
        .section-header {
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        .loading-spinner {
            text-align: center;
            margin: 2rem 0;
        }
        .error-message {
            background-color: #ffecec;
            padding: 1rem;
            border-radius: 6px;
            border-left: 5px solid #C10000;
            margin: 1rem 0;
        }
        .success-message {
            background-color: #e6ffe6;
            padding: 1rem;
            border-radius: 6px;
            border-left: 5px solid #00C100;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """
        Renderiza o cabeçalho da aplicação.
        """
        st.markdown('<div class="app-header">', unsafe_allow_html=True)
        st.title("HeatGlass")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="app-description">', unsafe_allow_html=True)
        st.write("Análise inteligente de ligações: temperatura emocional, impacto no negócio e status do atendimento.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_file_uploader(self) -> Optional[tempfile._TemporaryFileWrapper]:
        """
        Renderiza o componente de upload de arquivo.
        
        Returns:
            Arquivo temporário com o áudio carregado ou None
        """
        st.markdown('<div class="file-uploader">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Envie o áudio da ligação (.mp3)", type=["mp3"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            
            st.audio(uploaded_file, format='audio/mp3')
            return tmp_path
        
        return None
    
    def render_analysis_button(self) -> bool:
        """
        Renderiza o botão de análise.
        
        Returns:
            True se o botão foi clicado, False caso contrário
        """
        st.markdown('<div class="analysis-button">', unsafe_allow_html=True)
        button_clicked = st.button("🔍 Analisar Atendimento")
        st.markdown('</div>', unsafe_allow_html=True)
        return button_clicked
    
    def render_transcript(self, transcript_text: str):
        """
        Renderiza a transcrição do áudio.
        
        Args:
            transcript_text: Texto transcrito
        """
        with st.expander("Ver transcrição completa"):
            st.code(transcript_text, language="markdown")
    
    def render_analysis_results(self, analysis: Dict[str, Any]):
        """
        Renderiza os resultados da análise.
        
        Args:
            analysis: Dicionário com os resultados da análise
        """
        self._render_temperatura(analysis)
        self._render_impacto_comercial(analysis)
        self._render_status_final(analysis)
        self._render_script_encerramento(analysis)
        self._render_criterios_eliminatorios(analysis)
        self._render_checklist(analysis)
        self._render_resumo(analysis)
    
    def _render_temperatura(self, analysis: Dict[str, Any]):
        """
        Renderiza a seção de temperatura emocional.
        
        Args:
            analysis: Dicionário com os resultados da análise
        """
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader("🌡️ Temperatura Emocional")
        st.markdown('</div>', unsafe_allow_html=True)
        
        temp = analysis.get("temperatura", {})
        temp_class = temp.get("classificacao", "Desconhecida")
        emoji = {'Calma': '😌', 'Neutra': '😐', 'Tensa': '😟', 'Muito Tensa': '😡', 'Quente': '😡'}.get(temp_class, '❓')
        temp_class_style = self._get_temp_class(temp_class)
        
        st.markdown(f"<h3 class='{temp_class_style}'>{temp_class} {emoji}</h3>", unsafe_allow_html=True)
        st.markdown(f"**Justificativa:** {temp.get('justificativa')}")
    
    def _render_impacto_comercial(self, analysis: Dict[str, Any]):
        """
        Renderiza a seção de impacto comercial.
        
        Args:
            analysis: Dicionário com os resultados da análise
        """
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader("💼 Impacto Comercial")
        st.markdown('</div>', unsafe_allow_html=True)
        
        impact = analysis.get("impacto_comercial", {})
        pct = self._extract_percentage(impact.get("percentual", "0"))
        progress_class = self._get_progress_class(pct)
        
        st.progress(min(pct / 100, 1.0))
        st.markdown(f"<h3 class='{progress_class}'>{int(pct)}% - {impact.get('faixa')}</h3>", unsafe_allow_html=True)
        st.markdown(f"**Justificativa:** {impact.get('justificativa')}")
    
    def _render_status_final(self, analysis: Dict[str, Any]):
        """
        Renderiza a seção de status final.
        
        Args:
            analysis: Dicionário com os resultados da análise
        """
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader("📋 Status Final")
        st.markdown('</div>', unsafe_allow_html=True)
        
        final = analysis.get("status_final", {})
        
        st.markdown(f"""
        <div class="status-box">
        <strong>Cliente:</strong> {final.get("satisfacao", "Não informado")}<br>
        <strong>Desfecho:</strong> {final.get("desfecho", "Não informado")}<br>
        <strong>Risco:</strong> {final.get("risco", "Não informado")}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_script_encerramento(self, analysis: Dict[str, Any]):
        """
        Renderiza a seção de script de encerramento.
        
        Args:
            analysis: Dicionário com os resultados da análise
        """
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader("📝 Script de Encerramento")
        st.markdown('</div>', unsafe_allow_html=True)
        
        script_info = analysis.get("uso_script", {})
        script_status = script_info.get("status", "Não avaliado")
        script_class = self._get_script_status_class(script_status)
        
        st.markdown(f"""
        <div class="{script_class}">
        <strong>Status:</strong> {script_status}<br>
        <strong>Justificativa:</strong> {script_info.get("justificativa", "Não informado")}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_criterios_eliminatorios(self, analysis: Dict[str, Any]):
        """
        Renderiza a seção de critérios eliminatórios.
        
        Args:
            analysis: Dicionário com os resultados da análise
        """
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader("⚠️ Critérios Eliminatórios")
        st.markdown('</div>', unsafe_allow_html=True)
        
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
            st.markdown('<div class="success-message">', unsafe_allow_html=True)
            st.success("Nenhum critério eliminatório foi violado.")
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_checklist(self, analysis: Dict[str, Any]):
        """
        Renderiza a seção de checklist técnico.
        
        Args:
            analysis: Dicionário com os resultados da análise
        """
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader("✅ Checklist Técnico")
        st.markdown('</div>', unsafe_allow_html=True)
        
        checklist = analysis.get("checklist", [])
        total = self._extract_percentage(analysis.get("pontuacao_total", "0"))
        progress_class = self._get_progress_class(total)
        
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
                {icone} <strong>{item.get('item', '')}. {item.get('criterio', '')}</strong> ({item.get('pontos', 0)} pts)<br>
                <em>{item.get('justificativa', '')}</em>
                </div>
                """, unsafe_allow_html=True)
    
    def _render_resumo(self, analysis: Dict[str, Any]):
        """
        Renderiza a seção de resumo geral.
        
        Args:
            analysis: Dicionário com os resultados da análise
        """
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader("📝 Resumo Geral")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f"<div class='result-box'>{analysis.get('resumo_geral', '')}</div>", unsafe_allow_html=True)
    
    def render_error(self, error_message: str):
        """
        Renderiza uma mensagem de erro.
        
        Args:
            error_message: Mensagem de erro
        """
        st.markdown('<div class="error-message">', unsafe_allow_html=True)
        st.error(f"Erro ao processar a análise: {error_message}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_raw_response(self, response_text: str):
        """
        Renderiza a resposta bruta da API.
        
        Args:
            response_text: Texto da resposta
        """
        st.text_area("Resposta da IA:", value=response_text, height=300)
    
    def _get_temp_class(self, temp: str) -> str:
        """
        Determina a classe CSS para a temperatura.
        
        Args:
            temp: Classificação de temperatura
            
        Returns:
            Nome da classe CSS
        """
        temp_lower = temp.lower()
        if temp_lower == "calma":
            return "temperature-calm"
        elif temp_lower == "neutra":
            return "temperature-neutral"
        elif temp_lower == "tensa":
            return "temperature-tense"
        elif temp_lower in ["muito tensa", "quente"]:
            return "temperature-very-tense"
        else:
            return ""
    
    def _get_progress_class(self, value: float) -> str:
        """
        Determina a classe CSS para o progresso.
        
        Args:
            value: Valor numérico
            
        Returns:
            Nome da classe CSS
        """
        if value >= 70:
            return "progress-high"
        elif value >= 50:
            return "progress-medium"
        else:
            return "progress-low"
    
    def _get_script_status_class(self, status: str) -> str:
        """
        Determina a classe CSS para o status do script.
        
        Args:
            status: Status do script
            
        Returns:
            Nome da classe CSS
        """
        status_lower = status.lower()
        if status_lower == "completo" or status_lower == "sim":
            return "script-usado"
        elif "parcial" in status_lower:
            return "script-parcial"
        else:
            return "script-nao-usado"
    
    def _extract_percentage(self, value: Union[str, int, float]) -> float:
        """
        Extrai um valor percentual de diferentes tipos de entrada.
        
        Args:
            value: Valor a ser convertido
            
        Returns:
            Valor numérico
        """
        if isinstance(value, (int, float)):
            return float(value)
        return float(re.sub(r"[^\d.]", "", str(value)) or "0")

# Classe principal da aplicação
class HeatGlassApp:
    def __init__(self):
        """
        Inicializa a aplicação HeatGlass.
        """
        self.ui = UIManager()
        
        # Inicializa o cliente OpenAI com a chave da API
        try:
            self.openai_manager = OpenAIManager(api_key=st.secrets["OPENAI_API_KEY"])
        except Exception as e:
            logger.error(f"Erro ao inicializar o cliente OpenAI: {str(e)}")
            st.error(f"Erro ao inicializar o cliente OpenAI: {str(e)}")
            st.stop()
    
    def run(self):
        """
        Executa a aplicação principal.
        """
        # Renderiza o cabeçalho
        self.ui.render_header()
        
        # Renderiza o uploader de arquivo
        audio_file_path = self.ui.render_file_uploader()
        
        if audio_file_path is not None:
            # Renderiza o botão de análise
            if self.ui.render_analysis_button():
                self._process_audio(audio_file_path)
    
    def _process_audio(self, audio_file_path: str):
        """
        Processa o arquivo de áudio.
        
        Args:
            audio_file_path: Caminho para o arquivo de áudio
        """
        try:
            # Transcrição via Whisper
            with st.spinner("Transcrevendo o áudio..."):
                transcript_text = self.openai_manager.transcribe_audio(audio_file_path)
            
            # Exibe a transcrição
            self.ui.render_transcript(transcript_text)
            
            # Análise via GPT-4
            with st.spinner("Analisando a conversa..."):
                analysis = self.openai_manager.analyze_transcript(transcript_text)
            
            # Renderiza os resultados
            self.ui.render_analysis_results(analysis)
            
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            self.ui.render_error(str(e))
            
            # Tenta recuperar a resposta bruta em caso de erro
            try:
                if 'response' in locals():
                    self.ui.render_raw_response(response.choices[0].message.content.strip())
            except:
                pass

# Ponto de entrada da aplicação
if __name__ == "__main__":
    try:
        app = HeatGlassApp()
        app.run()
    except Exception as e:
        st.error(f"Erro ao iniciar a aplicação: {str(e)}")
        logger.critical(f"Erro fatal na aplicação: {str(e)}")
