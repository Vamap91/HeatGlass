import streamlit as st
from openai import OpenAI
import tempfile
import re
import json
import logging
import os
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
            # Cria um modelo de análise padrão com valores vazios
            default_analysis = {
                "temperatura": {"classificacao": "Neutra", "justificativa": "Não foi possível determinar"},
                "impacto_comercial": {"percentual": 50, "faixa": "Médio", "justificativa": "Não foi possível determinar"},
                "status_final": {"satisfacao": "Indeterminado", "risco": "Médio", "desfecho": "Indeterminado"},
                "checklist": [],
                "criterios_eliminatorios": [],
                "uso_script": {"status": "não avaliado", "justificativa": "Não foi possível determinar"},
                "pontuacao_total": 0,
                "resumo_geral": "Não foi possível analisar a transcrição completamente."
            }
            
            # Cria o checklist padrão
            checklist_items = [
                "Atendeu a ligação prontamente, dentro de 5 seg. e utilizou a saudação correta com as técnicas do atendimento encantador?",
                "Confirmou o histórico de utilizações do cliente, garantindo que seu atendimento será prestado conforme sua solicitação?",
                "Confirmou os dados do cadastro e pediu 2 telefones para contato? (Nome, CPF, Placa, e-mail, Veículo, Endereço, etc)",
                "Verbalizou o script da LGPD?",
                "Utilizou a técnica do eco para garantir o entendimento sobre as informações coletadas, evitando erros no processo e recontato do cliente?",
                "Escutou atentamente a solicitação do segurado evitando solicitações em duplicidade?",
                "Compreendeu a solicitação do cliente em linha e demonstrou domínio sobre o produto/serviço?",
                "Antes de solicitar ajuda, consultou o manual de procedimento para localizar a informação desejada? (caso não tenha solicitado/precisado de ajuda, selecionar sim para a resposta)",
                "Confirmou as informações completas sobre o dano no veículo?",
                "Confirmou data e motivo da quebra, registro do item, dano na pintura e demais informações necessárias para o correto fluxo de atendimento. (tamanho da trinca, LED, Xenon, etc)",
                "Confirmou cidade para o atendimento e selecionou corretamente a primeira opção de loja identificada pelo sistema? Porto/Sura/Bradesco (Seguiu o procedimento de lojas em verde/livre escolha?)",
                "A comunicação com o cliente foi eficaz: não houve uso de gírias, linguagem inadequada ou conversas paralelas? O analista informou quando ficou ausente da linha e quando retornou?",
                "Realizou o registro da ligação corretamente e garantiu ter sanado as dúvidas do cliente evitando o recontato?",
                "Realizou o script de encerramento completo, informando: prazo de validade, franquia, link de acompanhamento e vistoria, e orientou que o cliente aguarde o contato para agendamento?",
                "Orientou o cliente sobre a pesquisa de satisfação do atendimento?",
                "Realizou a tabulação de forma correta?",
                "A conduta do analista foi acolhedora, com sorriso na voz, empatia e desejo verdadeiro em entender e solucionar a solicitação do cliente?"
            ]
            
            pontos = [10, 7, 6, 2, 5, 3, 5, 2, 10, 10, 10, 5, 6, 15, 6, 4, 4]
            
            for i, criterio in enumerate(checklist_items):
                default_analysis["checklist"].append({
                    "item": i + 1,
                    "criterio": criterio,
                    "pontos": pontos[i],
                    "resposta": "Não",
                    "justificativa": "Não foi possível avaliar"
                })
            
            # Critérios eliminatórios padrão
            criterios_elim = [
                "Ofereceu/garantiu algum serviço que o cliente não tinha direito?",
                "Preencheu ou selecionou o Veículo/peça incorretos?",
                "Agiu de forma rude, grosseira, não deixando o cliente falar e/ou se alterou na ligação?",
                "Encerrou a chamada ou transferiu o cliente sem o seu conhecimento?",
                "Difamou a imagem da Carglass, de afiliados, seguradoras ou colegas de trabalho, ou falou negativamente sobre algum serviço prestado por nós ou por afiliados?"
            ]
            
            for criterio in criterios_elim:
                default_analysis["criterios_eliminatorios"].append({
                    "criterio": criterio,
                    "ocorreu": False,
                    "justificativa": "Não foi possível avaliar"
                })
            
            # Tenta obter a análise da API
            prompt = self._create_analysis_prompt(transcript_text)
            
            # Instrução clara no prompt do sistema para retornar apenas JSON válido
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um analista especializado em atendimento. Responda apenas com JSON válido, sem texto adicional, sem marcadores de código, apenas o objeto JSON puro."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # Salva a resposta bruta para depuração
            with open('/tmp/debug_response.txt', 'w') as f:
                f.write(result)
            
            # Tenta várias abordagens para extrair um JSON válido
            analysis = self._extract_valid_json(result)
            
            # Se conseguiu extrair um JSON válido, mescla com o padrão para garantir que todos os campos existam
            if analysis:
                # Mescla os campos de primeiro nível
                for key in default_analysis:
                    if key in analysis:
                        if isinstance(default_analysis[key], dict) and isinstance(analysis[key], dict):
                            # Para dicionários, mescla os subcampos
                            for subkey in default_analysis[key]:
                                if subkey not in analysis[key] or analysis[key][subkey] is None:
                                    analysis[key][subkey] = default_analysis[key][subkey]
                        elif isinstance(default_analysis[key], list) and isinstance(analysis[key], list):
                            # Para listas, garante que tenha pelo menos o número mínimo de itens
                            if key == "checklist" and len(analysis[key]) < len(default_analysis[key]):
                                # Completa o checklist com itens padrão
                                for i in range(len(analysis[key]), len(default_analysis[key])):
                                    analysis[key].append(default_analysis[key][i])
                            elif key == "criterios_eliminatorios" and len(analysis[key]) < len(default_analysis[key]):
                                # Completa os critérios eliminatórios com itens padrão
                                for i in range(len(analysis[key]), len(default_analysis[key])):
                                    analysis[key].append(default_analysis[key][i])
                    else:
                        analysis[key] = default_analysis[key]
                
                return analysis
            else:
                # Se não conseguiu extrair um JSON válido, usa o padrão
                logger.warning("Não foi possível extrair um JSON válido da resposta. Usando análise padrão.")
                return default_analysis
                
        except Exception as e:
            logger.error(f"Erro na análise: {str(e)}")
            # Tenta usar o modelo padrão em caso de erro
            logger.warning("Usando análise padrão devido a erro.")
            return self._create_default_analysis(checklist_items, pontos, criterios_elim)
    
    def _extract_valid_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Tenta extrair um JSON válido de um texto usando várias abordagens.
        
        Args:
            text: Texto que pode conter JSON
            
        Returns:
            Dicionário com o JSON extraído ou None se não for possível extrair
        """
        # Lista de abordagens para tentar extrair JSON válido
        approaches = [
            # Abordagem 1: Tentar carregar diretamente
            lambda t: json.loads(t.strip()),
            
            # Abordagem 2: Remover marcadores de código
            lambda t: json.loads(self._remove_code_markers(t)),
            
            # Abordagem 3: Extrair usando regex para encontrar o objeto JSON
            lambda t: json.loads(self._extract_json_with_regex(t)),
            
            # Abordagem 4: Corrigir problemas comuns e tentar novamente
            lambda t: json.loads(self._fix_common_json_issues(t)),
            
            # Abordagem 5: Usar uma biblioteca mais tolerante (demjson3 se disponível)
            lambda t: self._try_demjson_parse(t),
            
            # Abordagem 6: Tentar corrigir manualmente problemas específicos
            lambda t: json.loads(self._manual_json_fix(t))
        ]
        
        # Tenta cada abordagem em sequência
        for i, approach in enumerate(approaches):
            try:
                result = approach(text)
                logger.info(f"JSON extraído com sucesso usando abordagem {i+1}")
                return result
            except Exception as e:
                logger.debug(f"Abordagem {i+1} falhou: {str(e)}")
                continue
        
        # Se todas as abordagens falharem, retorna None
        return None
    
    def _remove_code_markers(self, text: str) -> str:
        """Remove marcadores de código Markdown do texto."""
        text = text.strip()
        # Remove blocos de código
        if text.startswith("```") and "```" in text[3:]:
            # Encontra o tipo de código (se especificado)
            first_line_end = text.find("\n")
            if first_line_end > 3:
                # Remove a primeira linha (```json ou similar)
                text = text[first_line_end:].strip()
            else:
                # Remove apenas os primeiros ```
                text = text[3:].strip()
            
            # Remove os ``` finais
            if text.endswith("```"):
                text = text[:-3].strip()
            else:
                last_marker = text.rfind("```")
                if last_marker > 0:
                    text = text[:last_marker].strip()
        
        return text
    
    def _extract_json_with_regex(self, text: str) -> str:
        """Extrai um objeto JSON usando expressões regulares."""
        import re
        # Tenta encontrar um objeto JSON completo
        json_pattern = r'({[\s\S]*})'
        match = re.search(json_pattern, text)
        if match:
            return match.group(1)
        raise ValueError("Não foi possível encontrar um objeto JSON no texto")
    
    def _fix_common_json_issues(self, text: str) -> str:
        """Corrige problemas comuns em strings JSON."""
        import re
        # Remove caracteres não-ASCII
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        # Substitui aspas simples por aspas duplas
        text = text.replace("'", "\"")
        # Garante que nomes de propriedades tenham aspas duplas
        text = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', text)
        # Corrige valores booleanos e nulos
        text = text.replace("True", "true").replace("False", "false").replace("None", "null")
        # Remove vírgulas extras antes de fechamento de objetos/arrays
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        return text
    
    def _try_demjson_parse(self, text: str) -> Dict[str, Any]:
        """Tenta usar demjson3 para analisar JSON com problemas."""
        try:
            import demjson3
            return demjson3.decode(text)
        except ImportError:
            # Se demjson3 não estiver disponível, tenta instalar
            try:
                import subprocess
                subprocess.check_call(["pip", "install", "demjson3"])
                import demjson3
                return demjson3.decode(text)
            except:
                raise ValueError("Não foi possível usar demjson3 para analisar o JSON")
        except Exception as e:
            raise ValueError(f"demjson3 falhou ao analisar o JSON: {str(e)}")
    
    def _manual_json_fix(self, text: str) -> str:
        """Tenta corrigir manualmente problemas específicos no JSON."""
        # Corrige problemas específicos que foram observados nas respostas
        # Exemplo: corrigir o problema na linha 24, coluna 5
        lines = text.split('\n')
        if len(lines) >= 24:
            problematic_line = lines[23]  # índice 23 = linha 24
            if len(problematic_line) >= 5:
                # Verifica se há um problema específico nessa posição
                if problematic_line[4] in [',', ':', '}', ']']:
                    # Tenta corrigir adicionando um valor padrão
                    fixed_line = problematic_line[:4] + '"valor_corrigido"' + problematic_line[4:]
                    lines[23] = fixed_line
                    return '\n'.join(lines)
        
        # Se não conseguiu corrigir especificamente, tenta uma abordagem mais genérica
        # Remove todas as linhas em branco e espaços extras
        text = re.sub(r'\n\s*\n', '\n', text)
        # Remove comentários (linhas começando com //)
        text = re.sub(r'//.*\n', '\n', text)
        # Tenta corrigir chaves e colchetes desbalanceados
        open_braces = text.count('{')
        close_braces = text.count('}')
        if open_braces > close_braces:
            text += '}' * (open_braces - close_braces)
        elif close_braces > open_braces:
            text = '{' * (close_braces - open_braces) + text
        
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        if open_brackets > close_brackets:
            text += ']' * (open_brackets - close_brackets)
        elif close_brackets > open_brackets:
            text = '[' * (close_brackets - open_brackets) + text
        
        return text
    
    def _create_default_analysis(self, checklist_items, pontos, criterios_elim) -> Dict[str, Any]:
        """
        Cria uma análise padrão com valores vazios.
        
        Returns:
            Dicionário com a análise padrão
        """
        default_analysis = {
            "temperatura": {"classificacao": "Neutra", "justificativa": "Não foi possível determinar"},
            "impacto_comercial": {"percentual": 50, "faixa": "Médio", "justificativa": "Não foi possível determinar"},
            "status_final": {"satisfacao": "Indeterminado", "risco": "Médio", "desfecho": "Indeterminado"},
            "checklist": [],
            "criterios_eliminatorios": [],
            "uso_script": {"status": "não avaliado", "justificativa": "Não foi possível determinar"},
            "pontuacao_total": 0,
            "resumo_geral": "Não foi possível analisar a transcrição completamente."
        }
        
        # Cria o checklist padrão
        for i, criterio in enumerate(checklist_items):
            default_analysis["checklist"].append({
                "item": i + 1,
                "criterio": criterio,
                "pontos": pontos[i],
                "resposta": "Não",
                "justificativa": "Não foi possível avaliar"
            })
        
        # Critérios eliminatórios padrão
        for criterio in criterios_elim:
            default_analysis["criterios_eliminatorios"].append({
                "criterio": criterio,
                "ocorreu": False,
                "justificativa": "Não foi possível avaliar"
            })
        
        return default_analysis
    
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
                # Verifica se existe arquivo de debug
                try:
                    if os.path.exists('/tmp/debug_response.txt'):
                        with open('/tmp/debug_response.txt', 'r') as f:
                            debug_content = f.read()
                        self.ui.render_raw_response(f"Resposta da API (para depuração):\n{debug_content}")
                except Exception as debug_err:
                    logger.error(f"Erro ao ler arquivo de debug: {str(debug_err)}")
                    pass

# Ponto de entrada da aplicação
if __name__ == "__main__":
    try:
        app = HeatGlassApp()
        app.run()
    except Exception as e:
        st.error(f"Erro ao iniciar a aplicação: {str(e)}")
        logger.critical(f"Erro fatal na aplicação: {str(e)}")
