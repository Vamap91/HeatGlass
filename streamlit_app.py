# Corrigindo erro de string quebrada no código da linha 100
codigo_corrigido = [
    "import streamlit as st",
    "from openai import OpenAI",
    "import tempfile",
    "import re",
    "",
    "st.set_page_config(page_title=\"HeatGlass\", page_icon=\"🔴\", layout=\"centered\")",
    "",
    "st.markdown(\"\"\"",
    "<style>",
    "h1, h2, h3 { color: #C10000 !important; }",
    ".result-box { background-color: #ffecec; padding: 1em; border-left: 5px solid #C10000; border-radius: 6px; font-size: 1rem; white-space: pre-wrap; line-height: 1.5; }",
    ".stButton>button { background-color: #C10000; color: white; font-weight: 500; border-radius: 6px; padding: 0.4em 1em; border: none; }",
    "</style>",
    "\"\"\", unsafe_allow_html=True)",
    "",
    "client = OpenAI(api_key=st.secrets[\"OPENAI_API_KEY\"])",
    "",
    "st.title(\"HeatGlass\")",
    "st.write(\"Análise de ligações com transcrição, impacto comercial, temperatura emocional e checklist técnico.\")",
    "",
    "uploaded_file = st.file_uploader(\"Envie o áudio da ligação (.mp3)\", type=[\"mp3\"])",
    "",
    "if uploaded_file is not None:",
    "    with tempfile.NamedTemporaryFile(delete=False, suffix=\".mp3\") as tmp:",
    "        tmp.write(uploaded_file.read())",
    "        tmp_path = tmp.name",
    "",
    "    st.audio(uploaded_file, format='audio/mp3')",
    "",
    "    with st.spinner(\"Transcrevendo o áudio...\"):",
    "        with open(tmp_path, \"rb\") as audio_file:",
    "            transcript = client.audio.transcriptions.create(",
    "                model=\"whisper-1\",",
    "                file=audio_file",
    "            )",
    "        transcript_text = transcript.text",
    "",
    "    st.subheader(\"Transcrição da Ligação\")",
    "    st.code(transcript_text, language=\"markdown\")",
    "",
    "    prompt = f'''",
    "Você é um especialista em atendimento ao cliente e auditor de qualidade. Com base na transcrição de uma ligação, realize duas análises:",
    "",
    "1. Análise emocional e comercial:",
    "- Temperatura emocional: Calma, Neutra, Tensa ou Muito Tensa.",
    "- Justifique com base no humor do cliente e na condução do atendente.",
    "- Impacto no negócio (0 a 100%): Quanto a ligação favoreceu a empresa?",
    "",
    "Avalie o impacto no negócio com base nos critérios abaixo:",
    "• Se o cliente demonstrou insatisfação, frustração ou ameaça de cancelamento → o impacto deve ser inferior a 50%.",
    "• Se o cliente mencionou problemas anteriores com a empresa → penalize o percentual.",
    "• Se o cliente finalizou satisfeito, confiante e com boa expectativa → o impacto pode ser maior.",
    "• Só atribua 100% se houver clareza de satisfação total por parte do cliente ao final da ligação.",
    "",
    "- Situação final: O cliente ficou satisfeito? Houve fechamento, cancelamento ou risco?",
    "",
    "2. Avaliação técnica do atendimento com base no checklist abaixo. Para cada item, responda \"Sim\" ou \"Não\" com justificativa. Some os pontos dos itens marcados como \"Sim\" e exiba ao final:",
    "",
    "Checklist de Qualidade (com pontuação):",
    "1. Saudação correta e atendimento imediato – 10 pts",
    "2. Confirmação do histórico do cliente – 7 pts",
    "3. Confirmação dos dados e dois telefones – 6 pts",
    "4. Verbalização do script da LGPD – 2 pts",
    "5. Técnica do eco para garantir entendimento – 5 pts",
    "6. Escuta ativa e atenção à solicitação – 3 pts",
    "7. Domínio do serviço – 5 pts",
    "8. Consulta ao manual antes de pedir ajuda – 2 pts",
    "9. Confirmação de dados sobre o dano – 10 pts",
    "10. Registro técnico detalhado (LED, Xenon etc) – 10 pts",
    "11. Seleção correta da loja – 10 pts",
    "12. Comunicação adequada, sem gírias – 5 pts",
    "13. Registro correto e resolução completa – 6 pts",
    "14. Script de encerramento completo – 15 pts",
    "15. Informação sobre pesquisa de satisfação – 6 pts",
    "16. Tabulação correta – 4 pts",
    "",
    "Apresente o resultado assim:",
    "- Checklist = X pontos de 100",
    "- Itens não atendidos: liste os números e sugestões de melhoria.",
    "",
    f"Transcrição:\\n\"\"\"{transcript_text}\"\"\"",
    "'''",
    "",
    "    with st.spinner(\"Analisando a conversa...\"):",
    "        response = client.chat.completions.create(",
    "            model=\"gpt-4\",",
    "            messages=[{\"role\": \"user\", \"content\": prompt}],",
    "            temperature=0.4",
    "        )",
    "        output = response.choices[0].message.content",
    "",
    "    match_impacto = re.search(r\"Impacto.*?(\\d{1,3})%\", output)",
    "    impacto = int(match_impacto.group(1)) if match_impacto else None",
    "",
    "    match_pontos = re.search(r\"Checklist\\s*=\\s*(\\d{1,3})\\s*pontos\", output, re.IGNORECASE)",
    "    checklist_pontos = int(match_pontos.group(1)) if match_pontos else None",
    "",
    "    if impacto is not None:",
    "        st.subheader(\"Impacto no negócio\")",
    "        st.progress(impacto / 100)",
    "        if impacto <= 25:",
    "            status = \"🔴 Crítico\"",
    "        elif impacto <= 50:",
    "            status = \"🟠 Baixo\"",
    "        elif impacto <= 70:",
    "            status = \"🟡 Razoável\"",
    "        elif impacto <= 85:",
    "            status = \"🟢 Positivo\"",
    "        else:",
    "            status = \"🟩 Excelente\"",
    "        st.write(f\"Resultado: **{status}** ({impacto}%)\")",
    "",
    "    if checklist_pontos is not None:",
    "        st.subheader(\"Check List Técnico\")",
    "        st.write(f\"Resultado: **{checklist_pontos} pontos de 100**\")",
    "",
    "    st.subheader(\"Análise da Ligação\")",
    "    st.markdown(f\"<div class='result-box'>{output}</div>\", unsafe_allow_html=True)"
]

# Salvar o novo .py
path_corrigido = "/mnt/data/streamlit_app.py"
with open(path_corrigido, "w") as f:
    for linha in codigo_corrigido:
        f.write(linha + "\n")

path_corrigido
