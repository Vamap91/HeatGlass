import streamlit as st
from openai import OpenAI
import tempfile
import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configurações da página
st.set_page_config(page_title="HeatGlass", page_icon="🔍", layout="wide")

# Estilo visual corporativo
st.markdown("""
<style>
    /* Estilos gerais */
    .main {
        background-color: #f8f9fa;
    }
    h1, h2, h3 {
        color: #343a40 !important;
    }
    
    /* Cartões de resultados */
    .card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Estilos para temperatura emocional */
    .emotion-calma {
        color: #28a745;
        font-weight: bold;
    }
    .emotion-neutra {
        color: #17a2b8;
        font-weight: bold;
    }
    .emotion-tensa {
        color: #ffc107;
        font-weight: bold;
    }
    .emotion-muito-tensa {
        color: #dc3545;
        font-weight: bold;
    }
    
    /* Barras de progresso */
    .stProgress > div > div {
        height: 20px;
        border-radius: 10px;
    }
    
    /* Checklist */
    .checklist-item {
        margin-bottom: 10px;
        padding: 10px;
        border-radius: 5px;
        background-color: #f8f9fa;
    }
    .yes-item {
        border-left: 5px solid #28a745;
    }
    .no-item {
        border-left: 5px solid #dc3545;
    }
    
    /* Status */
    .status-box {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .status-resolvido {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .status-pendente {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
    }
    .status-insatisfatorio {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }
    
    /* Botões de ação */
    .stButton>button {
        background-color: #007bff;
        color: white;
        font-weight: 500;
        border-radius: 6px;
        padding: 0.4em 1em;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0069d9;
    }
</style>
""", unsafe_allow_html=True)

# Inicializa o cliente OpenAI
# Verifica se estamos no ambiente Streamlit Cloud (que usa st.secrets)
# ou em desenvolvimento local (que usa variáveis de ambiente)
if 'OPENAI_API_KEY' in st.secrets:
    openai_api_key = st.secrets['OPENAI_API_KEY']
else:
    openai_api_key = os.environ.get('OPENAI_API_KEY')

client = OpenAI(api_key=openai_api_key)

# Função para gerar um gráfico de barras para o checklist
def generate_checklist_chart(checklist_items):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Preparar dados
    items = [f"Item {item['item']}" for item in checklist_items]
    points = [item['pontos'] if item['resposta'] == 'Sim' else 0 for item in checklist_items]
    max_points = [item['pontos'] for item in checklist_items]
    
    # Criar barras
    y_pos = np.arange(len(items))
    ax.barh(y_pos, max_points, color='lightgray', height=0.6)
    ax.barh(y_pos, points, color='#4CAF50', height=0.6)
    
    # Ajustar eixos
    ax.set_yticks(y_pos)
    ax.set_yticklabels(items)
    ax.invert_yaxis()  # Para que o item 1 fique no topo
    ax.set_xlabel('Pontos')
    ax.set_title('Checklist Técnico de Atendimento')
    
    # Adicionar anotações de pontuação
    for i, v in enumerate(points):
        if v > 0:
            ax.text(v + 0.5, i, f'{v}/{max_points[i]}', va='center')
        else:
            ax.text(1, i, f'0/{max_points[i]}', va='center')
    
    plt.tight_layout()
    return fig

# Sidebar
st.sidebar.image("https://via.placeholder.com/200x100.png?text=HeatGlass", width=200)
st.sidebar.title("HeatGlass")
st.sidebar.markdown("### Análise Inteligente de Atendimento")

# Opções de navegação
page = st.sidebar.radio("Navegação", ["Análise de Áudio", "Histórico", "Configurações"])

# Conteúdo principal
if page == "Análise de Áudio":
    st.title("🎙️ HeatGlass - Análise de Atendimento")
    st.write("Carregue o áudio de uma ligação para análise automática de qualidade e impacto emocional.")
    
    # Upload do áudio
    uploaded_file = st.file_uploader("Envie o áudio da ligação (.mp3)", type=["mp3"])
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
    
        # Player de áudio
        st.audio(uploaded_file, format='audio/mp3')
        
        # Botão para analisar
        analyze_button = st.button("🔍 Analisar Atendimento")
        
        if analyze_button:
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
            
            # Prompt estruturado conforme o documento de requisitos
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
            {
                "temperatura": {
                    "classificacao": "classificação aqui",
                    "justificativa": "justificativa aqui"
                },
                "impacto_comercial": {
                    "percentual": número aqui,
                    "faixa": "faixa aqui com emoji",
                    "justificativa": "justificativa aqui"
                },
                "status_final": {
                    "satisfacao": "satisfeito/não satisfeito",
                    "risco": "descrição do risco",
                    "desfecho": "resolvido/pendente/insatisfatório"
                },
                "checklist": [
                    {
                        "item": 1,
                        "criterio": "Saudação inicial adequada",
                        "pontos": 10,
                        "resposta": "Sim/Não",
                        "justificativa": "justificativa aqui"
                    },
                    ...continuar para todos os 18 itens
                ],
                "pontuacao_total": número aqui,
                "resumo_geral": "resumo textual da análise completa"
            }
            """

            # Análise com GPT-4
            with st.spinner("Analisando a conversa..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Você é um analista especializado em avaliar atendimentos telefônicos."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                analysis_text = response.choices[0].message.content
                
                try:
                    # Converter para JSON
                    analysis = json.loads(analysis_text)
                    
                    # Exibir resultados
                    st.header("📊 Resultados da Análise")
                    
                    # Layout em colunas
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Temperatura Emocional
                        st.subheader("🌡️ Temperatura Emocional")
                        temp_class = analysis['temperatura']['classificacao']
                        temp_emoji = {
                            'Calma': '😌',
                            'Neutra': '😐',
                            'Tensa': '😟',
                            'Muito Tensa': '😡'
                        }.get(temp_class, '❓')
                        
                        st.markdown(f"<div class='card'><h3 class='emotion-{temp_class.lower()}'>{temp_class} {temp_emoji}</h3><p>{analysis['temperatura']['justificativa']}</p></div>", unsafe_allow_html=True)
                        
                        # Status Final
                        st.subheader("📋 Status Final do Atendimento")
                        satisfacao = analysis['status_final']['satisfacao']
                        desfecho = analysis['status_final']['desfecho']
                        risco = analysis['status_final']['risco']
                        
                        satisfacao_emoji = '😊' if 'satisfeito' in satisfacao.lower() else '☹️'
                        desfecho_class = {
                            'resolvido': 'status-resolvido',
                            'pendente': 'status-pendente',
                            'insatisfatório': 'status-insatisfatorio'
                        }.get(desfecho.lower(), '')
                        
                        st.markdown(f"""
                        <div class='card'>
                            <div class='status-box {desfecho_class}'>
                                <h3>Desfecho: {desfecho}</h3>
                                <p><strong>Cliente:</strong> {satisfacao} {satisfacao_emoji}</p>
                                <p><strong>Risco:</strong> {risco}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Resumo Geral
                        st.subheader("📝 Resumo Geral")
                        st.markdown(f"<div class='card'>{analysis['resumo_geral']}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        # Impacto Comercial
                        st.subheader("💼 Impacto Comercial")
                        impact_pct = analysis['impacto_comercial']['percentual']
                        impact_range = analysis['impacto_comercial']['faixa']
                        
                        # Remover possíveis caracteres não numéricos
                        if isinstance(impact_pct, str):
                            impact_pct = float(re.sub(r'[^\d.]', '', impact_pct))
                        
                        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                        st.progress(int(impact_pct) / 100)
                        st.markdown(f"<h3>{int(impact_pct)}% - {impact_range}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p>{analysis['impacto_comercial']['justificativa']}</p></div>", unsafe_allow_html=True)
                        
                        # Pontuação Total do Checklist
                        st.subheader("🏆 Pontuação Total")
                        total_pts = analysis['pontuacao_total']
                        if isinstance(total_pts, str):
                            total_pts = float(re.sub(r'[^\d.]', '', total_pts))
                            
                        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                        st.progress(int(total_pts) / 100)
                        st.markdown(f"<h3>{int(total_pts)} pontos de 100</h3>", unsafe_allow_html=True)
                        
                        # Gerar classificação com base na pontuação
                        if total_pts >= 90:
                            st.success("Excelente Atendimento ⭐⭐⭐⭐⭐")
                        elif total_pts >= 80:
                            st.success("Ótimo Atendimento ⭐⭐⭐⭐")
                        elif total_pts >= 70:
                            st.warning("Bom Atendimento ⭐⭐⭐")
                        elif total_pts >= 60:
                            st.warning("Atendimento Regular ⭐⭐")
                        else:
                            st.error("Atendimento Abaixo do Esperado ⭐")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Checklist Técnico detalhado
                    st.header("📋 Checklist Técnico Detalhado")
                    
                    # Gerar e exibir o gráfico do checklist
                    checklist_chart = generate_checklist_chart(analysis['checklist'])
                    st.pyplot(checklist_chart)
                    
                    # Exibir itens do checklist em forma de lista expandível
                    with st.expander("Ver detalhes do checklist"):
                        for item in analysis['checklist']:
                            item_num = item['item']
                            criterio = item['criterio']
                            pontos = item['pontos']
                            resposta = item['resposta']
                            justificativa = item['justificativa']
                            
                            # Estilo condicional baseado na resposta
                            if resposta == 'Sim':
                                st.markdown(f"""
                                <div class="checklist-item yes-item">
                                    <strong>{item_num}. {criterio}</strong> ({pontos} pts) - ✅ {resposta}
                                    <br/><small>{justificativa}</small>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class="checklist-item no-item">
                                    <strong>{item_num}. {criterio}</strong> ({pontos} pts) - ❌ {resposta}
                                    <br/><small>{justificativa}</small>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Botões de ação
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("📥 Exportar Relatório (PDF)"):
                            st.info("Função de exportação para PDF será implementada aqui")
                    with col2:
                        if st.button("📊 Salvar no Histórico"):
                            st.success("Análise salva no histórico com sucesso!")
                    with col3:
                        if st.button("✉️ Enviar por E-mail"):
                            st.info("Função de envio por e-mail será implementada aqui")
                
                except Exception as e:
                    st.error(f"Erro ao processar a análise: {e}")
                    st.code(analysis_text)

elif page == "Histórico":
    st.title("📚 Histórico de Análises")
    st.info("O módulo de histórico está em desenvolvimento. Aqui serão exibidas todas as análises já realizadas, com filtros por data, temperatura emocional e impacto comercial.")
    
    # Mockup de tabela de histórico
    data = {
        'Data': ['15/04/2025', '14/04/2025', '12/04/2025', '10/04/2025'],
        'Atendente': ['Juliana', 'Carlos', 'Márcia', 'Roberto'],
        'Temperatura': ['Calma 😌', 'Tensa 😟', 'Neutra 😐', 'Muito Tensa 😡'],
        'Impacto': ['85% 🟢', '45% 🟠', '67% 🟡', '15% 🔴'],
        'Status': ['Resolvido', 'Pendente', 'Resolvido', 'Insatisfatório']
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

elif page == "Configurações":
    st.title("⚙️ Configurações")
    st.info("O módulo de configurações está em desenvolvimento. Aqui serão disponibilizadas opções para personalizar a análise, definir parâmetros de IA, e gerenciar integrações com outros sistemas.")
    
    # Mockup de configurações
    with st.form("config_form"):
        st.subheader("Configurações de IA")
        api_key = st.text_input("OpenAI API Key", value="••••••••••••••••••••••••", type="password")
        model = st.selectbox("Modelo de IA", ["GPT-4", "GPT-3.5 Turbo"])
        temperature = st.slider("Temperatura da IA", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
        
        st.subheader("Configurações de E-mail")
        email_notify = st.checkbox("Enviar notificações por e-mail")
        email_dest = st.text_input("E-mail para relatórios")
        
        st.subheader("Configurações de Integração")
        integrate_xcontact = st.checkbox("Integrar com XContact")
        auto_analysis = st.checkbox("Análise automática de novas ligações")
        
        submit = st.form_submit_button("Salvar Configurações")
        if submit:
            st.success("Configurações salvas com sucesso!")

# Rodapé
st.markdown("---")
st.markdown("HeatGlass v1.0 | Análise Inteligente de Atendimentos")
