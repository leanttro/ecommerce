import streamlit as st
import pandas as pd
import requests
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from datetime import datetime, date
import time
import os
import random
import urllib3
import json
import urllib.parse
import re
import concurrent.futures
from io import BytesIO
import base64

st.set_page_config(page_title="LEANTTRO CRM & SNIPER", layout="wide", page_icon="⚡")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["STREAMLIT_CLIENT_SHOW_ERROR_DETAILS"] = "false"

st.markdown("""
<style>
    :root {
        --bg-color: #F5F5F7;
        --surface: #FFFFFF;
        --text-main: #1D1D1F;
        --text-muted: #86868B;
        --blue: #0071E3;
        --border: #D2D2D7;
        --red: #FF3B30;
        --green: #34C759;
    }

    .stApp { background-color: var(--bg-color); color: var(--text-main); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    
    h1, h2, h3, h4, h5, h6 { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-weight: 600 !important; color: var(--text-main); letter-spacing: -0.5px; }
    p, div, label, span { font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: var(--text-main); }

    section[data-testid="stSidebar"] { background-color: var(--surface); border-right: 1px solid var(--border); }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label { color: var(--text-main) !important; }

    div.stButton > button { background-color: var(--blue) !important; color: #FFFFFF !important; border: none; border-radius: 8px; font-weight: 500; font-family: -apple-system, sans-serif; padding: 0.5rem 1rem; transition: all 0.2s ease; }
    div.stButton > button:hover { background-color: #005BB5 !important; transform: scale(0.98); }
    
    a[data-testid="stLinkButton"] { background-color: var(--blue) !important; color: #FFFFFF !important; border: none; border-radius: 8px; font-weight: 500; font-family: -apple-system, sans-serif; padding: 0.5rem 1rem; text-decoration: none; display: inline-block; text-align: center; transition: all 0.2s ease; }
    a[data-testid="stLinkButton"]:hover { background-color: #005BB5 !important; transform: scale(0.98); }

    div[data-baseweb="input"] { background-color: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    div[data-baseweb="base-input"] input { color: var(--text-main) !important; -webkit-text-fill-color: var(--text-main) !important; }

    div[data-testid="stMetric"] { background-color: var(--surface); border: 1px solid var(--border); padding: 15px; border-radius: 12px; border-left: 4px solid var(--blue); box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    div[data-testid="stMetric"] label { color: var(--text-muted); font-size: 0.85rem; font-weight: 500; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: var(--text-main); font-weight: 700; }

    div[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 1px solid var(--border); padding-bottom: 5px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; color: var(--text-muted); font-weight: 500; padding: 10px 5px; }
    .stTabs [aria-selected="true"] { color: var(--blue) !important; border-bottom: 2px solid var(--blue) !important; background-color: transparent !important; }

    .leanttro-header { border-bottom: 1px solid var(--border); padding-bottom: 20px; margin-bottom: 30px; text-align: center; }
    .leanttro-title { font-size: 2.5rem; line-height: 1.2; color: var(--text-main); margin: 0; font-weight: 700; letter-spacing: -1px; }
    .blue-text { color: var(--blue); }
    .leanttro-sub { color: var(--text-muted); font-size: 0.9rem; margin-top: 5px; font-weight: 400; }
    
    .stProgress > div > div > div > div { background-color: var(--blue); }
    span[data-baseweb="tag"] { background-color: #E5E5EA !important; color: var(--text-main) !important; border-radius: 6px; }
    span[data-baseweb="tag"] span { color: var(--text-main) !important; }
    span[data-baseweb="tag"] svg { fill: var(--text-muted) !important; }

    .lead-card { background-color: var(--surface) !important; padding: 20px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }
    .lead-card:hover { border-color: var(--blue); }
    .score-hot { border-left: 4px solid var(--blue); } 
    .score-warm { border-left: 4px solid var(--text-muted); }    
    .lead-title { font-size: 18px; font-weight: 600; color: var(--text-main); margin-bottom: 5px; text-decoration: none; display: block; }
    .lead-title:hover { color: var(--blue); }
    .tag-nicho { background-color: #F5F5F7; color: var(--text-muted); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 500; border: 1px solid var(--border); margin-right: 5px; }
    .recommendation-box { background-color: #F5F5F7; border: 1px solid var(--border); padding: 12px; margin-top: 15px; border-radius: 8px; }
    .rec-title { color: var(--blue); font-weight: 600; font-size: 12px; }
    .rec-text { font-size: 13px; color: var(--text-main); margin-top: 4px; line-height: 1.5; }
    
    .stTextArea textarea { color: var(--text-main) !important; -webkit-text-fill-color: var(--text-main) !important; background-color: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .stSelectbox > div > div { background-color: var(--surface); color: var(--text-main); border: 1px solid var(--border); border-radius: 8px; }
    .stNumberInput input { color: var(--text-main) !important; -webkit-text-fill-color: var(--text-main) !important; }
</style>
""", unsafe_allow_html=True)

DIRECTUS_URL = os.getenv("DIRECTUS_URL", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
TRACKING_WEBHOOK_KEY = os.getenv("TRACKING_WEBHOOK_KEY", "")

groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except:
        pass

def render_header():
    st.markdown("""
    <div class="leanttro-header">
        <h1 class="leanttro-title">LEAN<span class="blue-text">TTRO</span>.</h1>
        <div class="leanttro-sub">CRM & INTELLIGENCE HUB</div>
    </div>
    """, unsafe_allow_html=True)

def get_user_table_name(user_id):
    clean_id = str(user_id).replace("-", "_")
    return f"crm_{clean_id}"

def get_tracking_file(user_id):
    return f"tracking_wpp_{user_id}.json"

def get_tracking_data(user_id):
    file_path = get_tracking_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            if "manual_limit" not in data:
                data["manual_limit"] = 30
            return data
    else:
        data = {
            "start_date": str(date.today()),
            "last_run_date": str(date.today()),
            "sent_today": 0,
            "last_run_hour": str(datetime.now().strftime("%Y-%m-%d %H")),
            "sent_this_hour": 0,
            "manual_limit": 30
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return data

def save_tracking_data(user_id, data):
    with open(get_tracking_file(user_id), 'w') as f:
        json.dump(data, f)

def inicializar_crm_usuario(token, user_id):
    table_name = get_user_table_name(user_id)
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    r = requests.get(f"{base_url}/collections/{table_name}", headers=headers, verify=False)
    if r.status_code != 200:
        schema = {"collection": table_name, "schema": {}, "meta": {"icon": "rocket", "note": "Leanttro CRM Table"}}
        requests.post(f"{base_url}/collections", json=schema, headers=headers, verify=False)
    
    campos = [
        {"field": "nome", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "person"}},
        {"field": "empresa", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "domain"}},
        {"field": "email", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "email"}},
        {"field": "telefone", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "phone"}},
        {"field": "origem", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "map"}},
        {"field": "url", "type": "string", "meta": {"interface": "input", "width": "full", "icon": "link"}},
        {"field": "status", "type": "string", "meta": {"interface": "select-dropdown", "options": {"choices": [{"text": "NOVO", "value": "Novo"}, {"text": "QUENTE", "value": "Quente"}, {"text": "CLIENTE", "value": "Cliente"}, {"text": "ENVIADO EM MASSA", "value": "ENVIADO EM MASSA"}]}}},
        {"field": "obs", "type": "text", "meta": {"interface": "input-multiline"}}
    ]
    
    for campo in campos:
        try:
            requests.post(f"{base_url}/fields/{table_name}", json=campo, headers=headers, verify=False)
        except:
            pass 

    r_smtp = requests.get(f"{base_url}/collections/config_smtp", headers=headers, verify=False)
    if r_smtp.status_code != 200:
        schema_smtp = {"collection": "config_smtp", "schema": {}, "meta": {"icon": "email", "note": "SMTP Users Config"}}
        requests.post(f"{base_url}/collections", json=schema_smtp, headers=headers, verify=False)
        campos_smtp = [
            {"field": "smtp_host", "type": "string"},
            {"field": "smtp_port", "type": "integer"},
            {"field": "smtp_user", "type": "string"},
            {"field": "smtp_pass", "type": "string"}
        ]
        for c in campos_smtp: requests.post(f"{base_url}/fields/config_smtp", json=c, headers=headers, verify=False)
        
    return True, "CRM Initialized"

def criar_coluna_dinamica(token, user_id, nome_campo, tipo_interface):
    table_name = get_user_table_name(user_id)
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    slug = nome_campo.lower().strip().replace(" ", "_", ).replace("ç", "c")
    mapa = {"Texto": "string", "Número": "integer", "Data": "date"}
    type_d = mapa.get(tipo_interface, "string")
    payload = {"field": slug, "type": type_d, "meta": {"interface": "input", "width": "full"}, "schema": {"is_nullable": True}}
    r = requests.post(f"{base_url}/fields/{table_name}", json=payload, headers=headers, verify=False)
    return r.status_code == 200

def carregar_dados(token, user_id):
    try:
        table = get_user_table_name(user_id)
        r = requests.get(f"{DIRECTUS_URL}/items/{table}?limit=-1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['data'])
            if 'id' in df.columns:
                cols_pri = ['id', 'nome', 'empresa', 'email', 'telefone', 'origem', 'status']
                cols_existentes = [c for c in cols_pri if c in df.columns]
                cols_restantes = [c for c in df.columns if c not in cols_existentes]
                return df[cols_existentes + cols_restantes]
    except: pass
    return pd.DataFrame(columns=["nome", "empresa", "email", "status", "telefone"])

def salvar_lead_crm(token, user_id, dados):
    table = get_user_table_name(user_id)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"status": "Novo"}
    for k, v in dados.items():
        payload[k] = str(v)
    r = requests.post(f"{DIRECTUS_URL}/items/{table}", json=payload, headers=headers, verify=False)
    return r.status_code in [200, 204]

def carregar_dados_bot(token):
    try:
        r = requests.get(f"{DIRECTUS_URL}/items/clients_bot?limit=-1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['data'])
            if not df.empty:
                rename_map = {}
                if 'name' in df.columns: rename_map['name'] = 'nome'
                if 'whatsapp' in df.columns: rename_map['whatsapp'] = 'telefone'
                df.rename(columns=rename_map, inplace=True)
            cols_desejadas = ['id', 'nome', 'email', 'telefone', 'dor_principal', 'session_uuid']
            cols_existentes = [c for c in cols_desejadas if c in df.columns]
            return df[cols_existentes]
    except: pass
    return pd.DataFrame()

def atualizar_item(token, user_id, item_id, dados):
    table = get_user_table_name(user_id)
    requests.patch(f"{DIRECTUS_URL}/items/{table}/{item_id}", json=dados, headers={"Authorization": f"Bearer {token}"}, verify=False)

def carregar_config_smtp(token):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        r = requests.get(f"{base_url}/items/config_smtp?limit=1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            data = r.json()['data']
            if data and len(data) > 0: return data[0]
    except: pass
    return {}

def salvar_config_smtp(token, dados):
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    existente = carregar_config_smtp(token)
    if existente and 'id' in existente:
        r = requests.patch(f"{base_url}/items/config_smtp/{existente['id']}", json=dados, headers=headers, verify=False)
    else:
        r = requests.post(f"{base_url}/items/config_smtp", json=dados, headers=headers, verify=False)
    return r.status_code in [200, 204]

def contar_envios_hoje(token):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        url = f"{base_url}/items/historico_envios?filter[data_envio][_gte]={hoje_str}&filter[user_created][_eq]=$CURRENT_USER&aggregate[count]=*"
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            data = r.json()['data']
            if isinstance(data, list) and len(data) > 0:
                return int(data[0].get('count', 0))
    except: pass
    return 0

def registrar_log_envio(token, destinatario, assunto, status):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        payload = {"data_envio": datetime.now().isoformat(), "destinatario": destinatario, "assunto": assunto, "status": status, "aberto": False}
        r = requests.post(f"{base_url}/items/historico_envios", json=payload, headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code in [200, 201]: return r.json()['data']['id']
    except: pass
    return None

def atualizar_status_envio(token, log_id, novo_status, erro_msg=None):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        payload = {"status": novo_status}
        if erro_msg: payload["obs"] = erro_msg
        requests.patch(f"{base_url}/items/historico_envios/{log_id}", json=payload, headers={"Authorization": f"Bearer {token}"}, verify=False)
    except: pass

def enviar_email_smtp(smtp_config, to, subject, body, anexo=None, tracking_url=None):
    try:
        to = str(to).strip()
        subject = str(subject).strip()
        
        body = str(body).replace('\n', '<br>')
        
        if tracking_url:
            cache_buster = random.randint(1000, 999999)
            url_final = f"{tracking_url}&r={cache_buster}"
            pixel_html = f'<img src="{url_final}" width="1" height="1" style="display:block; width:1px; height:1px; opacity:0.01;" alt="" />'
            if "</body>" in body: body = body.replace("</body>", f"{pixel_html}</body>")
            else: body += pixel_html

        usar_imagem_inline = False
        if anexo is not None and "{{imagem}}" in body.lower():
            if "image" in anexo.type: usar_imagem_inline = True

        if usar_imagem_inline:
            msg = MIMEMultipart('related')
            msg['From'] = smtp_config['user']
            msg['To'] = to
            msg['Subject'] = subject
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)
            cid_id = "imagem_corpo"
            body_atualizado = body.replace("{{imagem}}", f'<br><img src="cid:{cid_id}" style="max-width:100%; height:auto;"><br>')
            msg_alternative.attach(MIMEText(body_atualizado, 'html', 'utf-8'))
            img_data = anexo.getvalue()
            image = MIMEImage(img_data)
            image.add_header('Content-ID', f'<{cid_id}>') 
            image.add_header('Content-Disposition', 'inline', filename=anexo.name)
            msg.attach(image)
        else:
            msg = MIMEMultipart()
            msg['From'] = smtp_config['user']
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            if anexo is not None:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(anexo.getvalue())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{anexo.name}"')
                msg.attach(part)

        server = smtplib.SMTP(smtp_config['host'], int(smtp_config['port']))
        server.starttls()
        server.login(smtp_config['user'], smtp_config['pass'])
        server.sendmail(smtp_config['user'], to, msg.as_string())
        server.quit()
        return True, "OK"
    except Exception as e: return False, str(e)

def gerar_copy_ia(ctx, dados_cliente=None):
    if not groq_client: return "Erro", "Configure a GROQ_API_KEY no ambiente"
    empresa = ctx.get('empresa', 'Nossa Empresa')
    descricao = ctx.get('descricao', 'Soluções Digitais')
    segmento_alvo = ctx.get('segmento_alvo', '') 
    dor_cliente = ""
    if dados_cliente is not None and 'dor_principal' in dados_cliente:
        d = dados_cliente['dor_principal']
        if d and str(d).lower() != 'none': dor_cliente = f"A principal dor ou necessidade deste cliente é: {d}. Use isso para personalizar o texto."
    instrucao_segmento = ""
    if segmento_alvo: instrucao_segmento = f"CONTEXTO IMPORTANTE: O público alvo deste disparo são empresas e pessoas do seguinte perfil e segmento: {segmento_alvo}. Adapte a linguagem e exemplos para eles."

    prompt = f"Aja como um copywriter profissional B2B. Escreva um email curto max 3 parágrafos de prospecção fria. Minha Empresa: {empresa}. O que vendemos: {descricao}. {instrucao_segmento}. {dor_cliente}. Tom Persuasivo direto e sem enrolação corporativa. Foco Marcar uma reunião ou resolver o problema dele. IMPORTANTE Não coloque Assunto no corpo apenas o texto do email."
    try:
        chat_completion = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
        return "Proposta Personalizada", chat_completion.choices[0].message.content
    except Exception as e: return "Erro IA", str(e)

def gerar_whatsapp_ia(ctx, dados_cliente=None):
    if not groq_client: return "Erro API Key não configurada"
    empresa = ctx.get('empresa', 'Leanttro')
    descricao = ctx.get('descricao', 'Landing Pages')
    nome = "Doutor"
    dor = ""
    if dados_cliente is not None:
        nome = dados_cliente.get('nome', 'Doutor')
        if 'dor_principal' in dados_cliente: dor = f"Foque na dor {dados_cliente['dor_principal']}"

    prompt = f"Aja como um especialista em vendas B2B via WhatsApp. Escreva uma mensagem MUITO CURTA máximo 2 frases e direta para abordagem fria. Contexto {empresa} vende {descricao}. Cliente {nome}. {dor}. OBRIGATÓRIO A mensagem DEVE incluir o link www.leanttro.com/zenilda-adv. Tom Informal vizinho mas profissional. Sem cara de robô. Objetivo Apenas despertar interesse para clicar no link e ver o exemplo."
    try:
        chat_completion = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
        return chat_completion.choices[0].message.content
    except Exception as e: return f"Erro IA {str(e)}"

def validar_token(token):
    try:
        r = requests.get(f"{DIRECTUS_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200: return r.json()['data']
    except: pass
    return None

def search_google_serper(query, period, num_results=10):
    url = "https://google.serper.dev/search"
    payload_dict = {"q": query, "num": num_results, "gl": "br", "hl": "pt-br"}
    if period: payload_dict["tbs"] = period
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload_dict))
        if response.status_code != 200: return []
        return response.json().get("organic", [])
    except: return []

def search_google_maps_serper(query):
    url = "https://google.serper.dev/places"
    payload_dict = {"q": query, "gl": "br", "hl": "pt-br"}
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload_dict))
        if response.status_code != 200: return []
        return response.json().get("places", [])
    except: return []

def analyze_lead_groq(title, snippet, link, groq_key, system_prompt):
    if not groq_key: return {"score": 0, "autor": "Desc.", "produto_recomendado": "ERRO CHAVE", "argumento_venda": "Sem chave Groq"}
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"TITULO: {title}\nSNIPPET: {snippet}\nLINK: {link}"}],
            temperature=0.1, response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except: return {"score": 0, "autor": "Erro", "produto_recomendado": "Erro IA", "argumento_venda": "Falha na análise"}

def process_single_item(item, system_prompt):
    titulo = item.get('title', '')
    link = item.get('link', '')
    snippet = item.get('snippet', '')
    data_pub = item.get('date', 'Data n/d')
    analise = analyze_lead_groq(titulo, snippet, link, GROQ_API_KEY, system_prompt)
    return {"item": item, "analise": analise, "titulo": titulo, "link": link, "snippet": snippet, "data_pub": data_pub}

def extrair_email(texto):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(texto))
    return match.group(0) if match else None

def extrair_whatsapp(texto):
    padrao = r'(?:(?:\+|00)?55\s?)?(?:\(?([1-9][0-9])\)?\s?)?(?:((?:9\d|[2-9])\d{3})\-?(\d{4}))'
    match = re.search(padrao, str(texto))
    if match:
        ddd, parte1, parte2 = match.groups()
        if not ddd: ddd = "11" 
        return f"55{ddd}{parte1}{parte2}".replace(" ", "").replace("-", "")
    return None

def limpar_nome(titulo):
    if "•" in titulo: return titulo.split("•")[0].strip()
    if "-" in titulo: return titulo.split("-")[0].strip()
    if "|" in titulo: return titulo.split("|")[0].strip()
    return titulo[:50]

SUGESTOES_STRATEGICAS = {
    "Sites de Freelance": ["procuro desenvolvedor site", "preciso de automação whatsapp", "criar catálogo online", "busco especialista em IA"],
    "LinkedIn": ["alguém recomenda empresa para site", "busco profissional automação", "indicação criador de catálogo", "preciso integrar IA no meu negócio"],
    "Grupos Facebook Web": ["preciso de um site", "alguém faz catálogo digital", "procuro quem faça automação", "orçamento para site"]
}
FONTES_MINERADOR = {
    "Google Maps": "maps",
    "Instagram": "site:instagram.com", 
    "Facebook": "site:facebook.com", 
    "LinkedIn": "site:linkedin.com/company", 
    "Geral": ""
}

if 'token' not in st.session_state:
    token_url = st.query_params.get("token")
    if token_url:
        user_data = validar_token(token_url)
        if user_data:
            st.session_state['token'] = token_url
            st.session_state['user'] = user_data

if 'token' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        render_header()
        st.markdown("<p style='text-align:center; color:#888'>ACESSO RESTRITO</p>", unsafe_allow_html=True)
        email = st.text_input("E-MAIL")
        senha = st.text_input("SENHA", type="password")
        if st.button("ACESSAR SISTEMA", width='stretch'):
            login_sucesso = False
            try:
                r = requests.post(f"{DIRECTUS_URL}/auth/login", json={"email": email, "password": senha}, verify=False)
                if r.status_code == 200:
                    token = r.json()['data']['access_token']
                    st.session_state['token'] = token
                    u = requests.get(f"{DIRECTUS_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, verify=False)
                    st.session_state['user'] = u.json()['data']
                    st.query_params["token"] = token
                    login_sucesso = True
                else: st.error("ACESSO NEGADO")
            except: st.error("ERRO DE CONEXÃO")
            if login_sucesso: st.rerun()
    st.stop()

token = st.session_state['token']
user = st.session_state['user']
user_id = user['id']
st.query_params["token"] = token

if 'setup_ok' not in st.session_state:
    inicializar_crm_usuario(token, user_id)
    st.session_state['setup_ok'] = True

if 'smtp_loaded' not in st.session_state:
    cfg = carregar_config_smtp(token)
    if cfg:
        st.session_state['smtp'] = {'host': cfg.get('smtp_host', 'smtp.gmail.com'), 'port': cfg.get('smtp_port', 587), 'user': cfg.get('smtp_user', ''), 'pass': cfg.get('smtp_pass', '')}
        st.session_state['smtp_host_input'] = cfg.get('smtp_host', 'smtp.gmail.com')
        st.session_state['smtp_port_input'] = int(cfg.get('smtp_port', 587))
        st.session_state['smtp_user_input'] = cfg.get('smtp_user', '')
        st.session_state['smtp_pass_input'] = cfg.get('smtp_pass', '')
    st.session_state['smtp_loaded'] = True

if "system_prompt_padrao" not in st.session_state:
    st.session_state.system_prompt_padrao = "ATUE COMO Head de Vendas. OBJETIVO Encontrar quem está COMPRANDO ou BUSCANDO serviços e ignorar quem está vendendo ou postagens gringas. TAREFAS 1 O texto deve estar em Português do Brasil. 2 Identifique se o autor ESTÁ BUSCANDO o serviço Score 80 a 100. 3 Se for alguém VENDENDO ou agência concorrente Score é ZERO. SAÍDA JSON OBRIGATÓRIA { autor Nome de quem busca score 0 a 100 resumo_post Resumo do que a pessoa precisa produto_recomendado Serviço exato argumento_venda Como abordar para vender rápido }"

if "saudacoes" not in st.session_state: st.session_state.saudacoes = ["Opa", "Olá", "Tudo bem", "Oi", "Fala"]
if "delay_min" not in st.session_state: st.session_state.delay_min = 60
if "delay_max" not in st.session_state: st.session_state.delay_max = 200
if "blacklist" not in st.session_state: st.session_state.blacklist = set()

with st.sidebar:
    st.markdown(f"<h3>USER {user.get('first_name').upper()}</h3>", unsafe_allow_html=True)
    if st.button("LOGOUT / SAIR"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
    st.divider()
    with st.expander("🛠️ CONSTRUTOR DE TABELA"):
        nc = st.text_input("NOME COLUNA")
        tc = st.selectbox("TIPO", ["Texto", "Número", "Data"])
        if st.button("CRIAR COLUNA"):
            if criar_coluna_dinamica(token, user_id, nc, tc): st.success("CRIADO"), time.sleep(1), st.rerun()
    with st.expander("🤖 DADOS DA EMPRESA IA", expanded=True):
        en = st.text_input("NOME EMPRESA", value="Leanttro Especialista em Jurídico")
        ed = st.text_area("O QUE VENDE", value="Landing Pages de Alta Conversão para Advogados Produto foco www.leanttro.com/zenilda-adv Ajuda a passar autoridade e captar clientes qualificados")
        if st.button("SALVAR CONTEXTO"): st.session_state['ctx'] = {'empresa': en, 'descricao': ed}, st.success("SALVO")

try:
    render_header()
    df = carregar_dados(token, user_id)
    df_bot = carregar_dados_bot(token)

    COTA_MAXIMA = 100
    envios_realizados = contar_envios_hoje(token)
    saldo_envios = COTA_MAXIMA - envios_realizados

    k1, k2, k3 = st.columns(3)
    k1.metric("TOTAL LEADS CRM", len(df))
    k2.metric("LEADS BOT", len(df_bot))
    k3.metric("SALDO EMAIL DIARIO", saldo_envios)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 RADAR DE INTENÇÃO", "⛏️ MINERADOR DE DADOS", "📋 CRM E AÇÕES", "🚀 DISPARO SNIPER", "⚙️ CONFIGURAÇÕES"])

    with tab1:
        st.markdown("### CAÇADOR DE OPORTUNIDADES B2B")
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
        with c1: origem = st.selectbox("Onde buscar", list(SUGESTOES_STRATEGICAS.keys()))
        with c2: termo = st.text_input("Intenção de busca", placeholder="Ex preciso de site")
        with c3: cidade_radar = st.text_input("Cidade (Opcional)", placeholder="Ex São Paulo")
        with c4: tempo = st.selectbox("Período", ["Últimas 24 Horas", "Última Semana", "Último Mês", "Qualquer data"])
        with c5: qtd = st.number_input("Qtd", 1, 50, 10)
        btn = st.button("RASTREAR COMPRADORES", key="btn_radar")

        if btn and termo:
            if not (GROQ_API_KEY and SERPER_API_KEY): st.error("Configure as chaves.")
            else:
                termo_busca = f'{termo} {cidade_radar}'.strip()
                periodo_api = "qdr:d" if "24 Horas" in tempo else "qdr:w" if "Semana" in tempo else "qdr:m" if "Mês" in tempo else ""
                query_final = f'site:linkedin.com/posts "{termo_busca}"' if origem == "LinkedIn" else f'(site:workana.com OR site:99freelas.com.br) "{termo_busca}"' if origem == "Sites de Freelance" else f'"{termo_busca}"'
                
                resultados = search_google_serper(query_final, periodo_api, qtd)
                if not resultados: st.warning("Nenhum sinal encontrado.")
                else:
                    prog = st.progress(0)
                    processed_results = []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        future_to_item = {executor.submit(process_single_item, item, st.session_state.system_prompt_padrao): item for item in resultados}
                        completed = 0
                        for future in concurrent.futures.as_completed(future_to_item):
                            try: processed_results.append(future.result())
                            except: pass
                            completed += 1
                            prog.progress(completed / len(resultados))
                    
                    processed_results.sort(key=lambda x: x['analise'].get('score', 0), reverse=True)
                    for p in processed_results:
                        analise = p['analise']
                        score = analise.get('score', 0)
                        if score < 50: continue
                        autor = analise.get('autor', 'Desconhecido')
                        css_class = "score-hot" if score >= 80 else "score-warm"
                        
                        st.markdown(f'<div class="lead-card {css_class}"><div><span style="color:var(--blue); font-weight:bold;">SCORE {score}</span> <span class="tag-nicho">Autor {autor}</span></div><div style="margin-top:10px;"><a href="{p["link"]}" target="_blank" class="lead-title">{p["titulo"]}</a></div><div class="recommendation-box"><div style="color:var(--text-main); font-weight:bold;">OFERTAR {analise.get("produto_recomendado", "N/A").upper()}</div><div class="rec-text">{analise.get("resumo_post", "")}</div></div></div>', unsafe_allow_html=True)
                        if st.button(f"Salvar {autor} no CRM", key=f"save_{p['link']}"):
                            salvar_lead_crm(token, user_id, {"nome": autor, "origem": "Radar", "url": p["link"], "obs": analise.get("resumo_post", "")})
                            st.success("Salvo no CRM")
                            time.sleep(1)
                            st.rerun()

    with tab2:
        st.markdown("### EXTRATOR DE CONTATOS LOCAIS")
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1: nicho = st.text_input("Nicho", value="Clínica Odontológica")
        with c2: cidade = st.text_input("Cidade Base", value="São Paulo")
        with c3: fonte_alvo = st.selectbox("Fonte Específica", list(FONTES_MINERADOR.keys()))
        bairros_txt = st.text_area("Lista de Bairros Separados por vírgula", value="Centro, Pinheiros", height=80)
        
        if "leads_isolados" not in st.session_state: st.session_state["leads_isolados"] = []
        
        if st.button("INICIAR EXTRAÇÃO", key="btn_zap_mine"):
            lista_bairros = [b.strip() for b in bairros_txt.split(',') if b.strip()]
            novos_leads = []
            bar = st.progress(0)
            prefixo_fonte = FONTES_MINERADOR[fonte_alvo]
            
            telefones_db = df['telefone'].dropna().astype(str).tolist() if not df.empty and 'telefone' in df.columns else []
            emails_db = df['email'].dropna().astype(str).tolist() if not df.empty and 'email' in df.columns else []
            
            for i, bairro in enumerate(lista_bairros):
                if fonte_alvo == "Google Maps":
                    query_maps = f'{nicho} em {bairro} {cidade}'
                    resultados_maps = search_google_maps_serper(query_maps)
                    
                    for r in resultados_maps:
                        nome_empresa = r.get('title', '')
                        zap_oficial = extrair_whatsapp(r.get('phoneNumber', ''))
                        endereco = r.get('address', '')
                        site = r.get('website', '')
                        
                        if zap_oficial:
                            exists_local = any(l['Whatsapp'] == zap_oficial for l in st.session_state["leads_isolados"])
                            exists_new = any(l['Whatsapp'] == zap_oficial for l in novos_leads)
                            exists_db = zap_oficial in telefones_db
                            
                            if not exists_local and not exists_new and not exists_db:
                                novos_leads.append({
                                    "Empresa": limpar_nome(nome_empresa), 
                                    "Nicho": nicho, 
                                    "Bairro": bairro, 
                                    "Endereço Real": endereco,
                                    "Whatsapp": zap_oficial, 
                                    "Email": "", 
                                    "Fonte": "Google Maps", 
                                    "Link": site
                                })
                else:
                    query_base = f'{prefixo_fonte} "{nicho}" "{bairro}" "{cidade}"'
                    for q in [f'{query_base} "whatsapp"', f'{query_base} "@gmail.com" OR "@hotmail.com"']:
                        resultados = search_google_serper(q.strip(), period="", num_results=20)
                        for r in resultados:
                            texto_completo = (r.get('title', '') + " " + r.get('snippet', '')).lower()
                            zap = extrair_whatsapp(texto_completo)
                            email = extrair_email(texto_completo)
                            
                            if zap is None: zap = ""
                            if email is None: email = ""
                            
                            if zap or email:
                                exists_local = any((l['Whatsapp'] == zap and zap) or (l['Email'] == email and email) for l in st.session_state["leads_isolados"])
                                exists_new = any((l['Whatsapp'] == zap and zap) or (l['Email'] == email and email) for l in novos_leads)
                                exists_db = (zap and zap in telefones_db) or (email and email in emails_db)
                                
                                if not exists_local and not exists_new and not exists_db:
                                    novos_leads.append({"Empresa": limpar_nome(r.get('title', '')), "Nicho": nicho, "Bairro": bairro, "Endereço Real": "N/A", "Whatsapp": zap, "Email": email, "Fonte": fonte_alvo, "Link": r.get('link')})
                bar.progress((i + 1) / len(lista_bairros))
                time.sleep(0.5) 
            if novos_leads:
                st.session_state["leads_isolados"].extend(novos_leads)
                st.success(f"{len(novos_leads)} CONTATOS INÉDITOS ENCONTRADOS")
        
        if st.session_state["leads_isolados"]:
            df_mine = pd.DataFrame(st.session_state["leads_isolados"])
            st.dataframe(df_mine, width='stretch')
            
            buffer_mine = BytesIO()
            with pd.ExcelWriter(buffer_mine, engine='openpyxl') as writer:
                df_mine.to_excel(writer, index=False)
            st.download_button(label="📥 BAIXAR EXCEL MINEIRADOS", data=buffer_mine.getvalue(), file_name="leads_mineirados.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            if st.button("SALVAR TODOS NO CRM"):
                df_atual = carregar_dados(token, user_id)
                telefones_db = df_atual['telefone'].dropna().astype(str).tolist() if not df_atual.empty and 'telefone' in df_atual.columns else []
                emails_db = df_atual['email'].dropna().astype(str).tolist() if not df_atual.empty and 'email' in df_atual.columns else []
                
                salvos = 0
                duplicados = 0
                for _, row in df_mine.iterrows():
                    zap_row = str(row["Whatsapp"]).strip()
                    email_row = str(row["Email"]).strip()
                    
                    is_dup_zap = zap_row and zap_row in telefones_db
                    is_dup_email = email_row and email_row in emails_db
                    
                    if is_dup_zap or is_dup_email:
                        duplicados += 1
                        continue
                    
                    obs_text = f"Endereço: {row.get('Endereço Real', '')}" if row.get('Endereço Real') and row.get('Endereço Real') != "N/A" else ""    
                    salvar_lead_crm(token, user_id, {"empresa": row["Empresa"], "email": email_row, "telefone": zap_row, "origem": row["Fonte"], "ramo": row["Nicho"], "url": row["Link"], "obs": obs_text, "bairro": row["Bairro"]})
                    salvos += 1
                    if zap_row: telefones_db.append(zap_row)
                    if email_row: emails_db.append(email_row)
                    
                if duplicados > 0:
                    st.warning(f"Ignorados {duplicados} contatos que ja estavam no CRM")
                st.success(f"{salvos} novos contatos enviados para o banco de dados")
                st.session_state["leads_isolados"] = []
                time.sleep(2)
                st.rerun()

    with tab3:
        with st.expander("FILTRAR E PERSONALIZAR TABELA", expanded=True):
            f_c1, f_c2 = st.columns([1, 1])
            with f_c1:
                all_cols = list(df.columns)
                if 'cols_visiveis_save' not in st.session_state: st.session_state['cols_visiveis_save'] = all_cols
                st.session_state['cols_visiveis_save'] = [c for c in st.session_state['cols_visiveis_save'] if c in all_cols]
                cols_visiveis = st.multiselect("Escolha e ordene as colunas", all_cols, default=st.session_state['cols_visiveis_save'])
                if cols_visiveis != st.session_state['cols_visiveis_save']: st.session_state['cols_visiveis_save'] = cols_visiveis; st.rerun()
            with f_c2:
                col_para_filtrar = st.selectbox("Filtrar na coluna", ["Sem Filtro"] + all_cols)
                filtro_valores = []
                if col_para_filtrar != "Sem Filtro":
                    valores_unicos = [str(x) for x in df[col_para_filtrar].unique()]
                    filtro_valores = st.multiselect(f"Selecione valores de {col_para_filtrar}", valores_unicos)
        
        df_visual = df.copy()
        if col_para_filtrar != "Sem Filtro" and filtro_valores: df_visual = df_visual[df_visual[col_para_filtrar].astype(str).isin(filtro_valores)]
        if cols_visiveis:
            cols_final = [c for c in cols_visiveis]
            if 'id' not in cols_final and 'id' in df_visual.columns: cols_final.append('id')
            df_visual = df_visual[cols_final]

        sub_t1, sub_t2 = st.tabs(["TABELA MESTRE", "TABELA BOT"])
        with sub_t1:
            col_config = {'id': st.column_config.Column("id", disabled=True, hidden=True)} if 'id' in df_visual.columns and 'id' not in cols_visiveis else {}
            edited = st.data_editor(df_visual, num_rows="dynamic", width='stretch', key="editor", column_config=col_config)
            
            buffer_crm = BytesIO()
            with pd.ExcelWriter(buffer_crm, engine='openpyxl') as writer:
                df_visual.to_excel(writer, index=False)
            st.download_button(label="📥 BAIXAR EXCEL CRM", data=buffer_crm.getvalue(), file_name="clientes_crm.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            if st.button("SALVAR ALTERACOES NA BASE"):
                chg = st.session_state["editor"]
                for idx in chg.get("deleted_rows", []):
                    try: requests.delete(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}/{df_visual.iloc[idx]['id']}", headers={"Authorization": f"Bearer {token}"}, verify=False)
                    except: pass
                for idx, row in chg["edited_rows"].items():
                    try: atualizar_item(token, user_id, df_visual.iloc[int(idx)]['id'], row)
                    except: pass
                max_id = 0
                df_fresh = carregar_dados(token, user_id)
                if not df_fresh.empty and 'id' in df_fresh.columns: max_id = pd.to_numeric(df_fresh['id'], errors='coerce').max()
                proximo_id = int(max_id) + 1 if not pd.isna(max_id) else 1
                for row in chg["added_rows"]:
                    if 'id' not in row or not row['id']: row['id'] = proximo_id; proximo_id += 1
                    requests.post(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}", json=row, headers={"Authorization": f"Bearer {token}"}, verify=False)
                st.toast("Dados atualizados", icon="✅")
                time.sleep(1)
                st.rerun()
        with sub_t2:
            st.dataframe(df_bot, width='stretch', height=400)

        st.divider()
        st.markdown("### AÇÕES RÁPIDAS LINHA UNICA")
        col_fonte, col_cli, col_vazio = st.columns([1, 2, 3])
        with col_fonte: fonte = st.radio("Fonte de Dados", ["Base Mestre", "Bot Automático"], horizontal=True)
        df_ativo = df if fonte == "Base Mestre" else df_bot
        with col_cli: sel_cli = st.selectbox("Selecione o Cliente para Agir", ["Selecione"] + (df_ativo['nome'].tolist() if not df_ativo.empty and 'nome' in df_ativo.columns else []))
        
        if sel_cli != "Selecione" and not df_ativo.empty:
            dados_cli = df_ativo[df_ativo['nome'] == sel_cli].iloc[0]
            act_c1, act_c2 = st.columns(2)
            with act_c1:
                st.markdown("#### WHATSAPP")
                if st.button("GERAR TEXTO ZAP IA"): st.session_state['ai_zap_text'] = gerar_whatsapp_ia(st.session_state.get('ctx', {}), dados_cli); st.rerun()
                msg_zap = st.text_area("Mensagem", value=st.session_state.get('ai_zap_text', "Olá tudo bem"), height=100)
                nums = re.sub(r'\D', '', str(dados_cli.get('telefone', '')))
                if nums: st.link_button("ENVIAR WHATSAPP", f"https://api.whatsapp.com/send?phone={nums if nums.startswith('55') and len(nums) > 11 else '55'+nums}&text={urllib.parse.quote(msg_zap)}", width='stretch')
            with act_c2:
                st.markdown("#### GMAIL IA")
                if st.button("GERAR TEXTO COM IA"):
                    assunto_ia, corpo_ia = gerar_copy_ia(st.session_state.get('ctx', {}), dados_cli)
                    st.link_button("ABRIR NO GMAIL", f"https://mail.google.com/mail/?view=cm&fs=1&to={dados_cli.get('email', '')}&su={urllib.parse.quote(assunto_ia)}&body={urllib.parse.quote(corpo_ia.replace('{nome}', dados_cli.get('nome', '')))}", width='stretch')

    with tab4:
        st.markdown("### DISPARO EM MASSA EMAIL E WHATSAPP")
        
        subtab_int, subtab_ext = st.tabs(["[ 1 ] DISPARO INTERNO DO CRM", "[ 2 ] IMPORTAR EXCEL EXTERNO"])
        
        with subtab_int:
            if not df.empty and not df_bot.empty:
                df_temp = df.copy()
                df_temp['fonte_dados'] = 'Mestre'
                df_bot_temp = df_bot.copy()
                df_bot_temp['fonte_dados'] = 'Bot'
                df_unificado = pd.concat([df_temp, df_bot_temp], ignore_index=True)
            elif not df.empty:
                df_unificado = df.copy()
                df_unificado['fonte_dados'] = 'Mestre'
            elif not df_bot.empty:
                df_unificado = df_bot.copy()
                df_unificado['fonte_dados'] = 'Bot'
            else:
                df_unificado = pd.DataFrame()
            
            ocultar_enviados = st.checkbox("Ocultar contatos já enviados Proteção contra duplicidade", value=True)
            if ocultar_enviados and not df_unificado.empty and 'status' in df_unificado.columns:
                df_unificado = df_unificado[df_unificado['status'] != "ENVIADO EM MASSA"]

            if not df_unificado.empty:
                with st.expander("🔍 FILTRAR LISTA DE DISPARO", expanded=True):
                    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                    with f_col1:
                        opcoes_origem = [x for x in df_unificado['origem'].dropna().astype(str).unique() if x.strip() != ''] if 'origem' in df_unificado.columns else []
                        filtro_origem = st.multiselect("Filtrar por Origem", opcoes_origem)
                    with f_col2:
                        opcoes_ramo = [x for x in df_unificado['ramo'].dropna().astype(str).unique() if x.strip() != ''] if 'ramo' in df_unificado.columns else []
                        filtro_ramo = st.multiselect("Filtrar por Ramo", opcoes_ramo)
                    with f_col3:
                        opcoes_status = [x for x in df_unificado['status'].dropna().astype(str).unique() if x.strip() != ''] if 'status' in df_unificado.columns else []
                        filtro_status = st.multiselect("Filtrar por Status", opcoes_status)
                    with f_col4:
                        opcoes_bairro = [x for x in df_unificado['bairro'].dropna().astype(str).unique() if x.strip() != ''] if 'bairro' in df_unificado.columns else []
                        filtro_bairro = st.multiselect("Filtrar por Bairro", opcoes_bairro)
                        
                    if filtro_origem: df_unificado = df_unificado[df_unificado['origem'].astype(str).isin(filtro_origem)]
                    if filtro_ramo: df_unificado = df_unificado[df_unificado['ramo'].astype(str).isin(filtro_ramo)]
                    if filtro_status: df_unificado = df_unificado[df_unificado['status'].astype(str).isin(filtro_status)]
                    if filtro_bairro: df_unificado = df_unificado[df_unificado['bairro'].astype(str).isin(filtro_bairro)]
                
            c1, c2 = st.columns([1, 1])
            with c1:
                metodo_envio = st.radio("MÉTODO DE DISPARO", ["Email SMTP", "WhatsApp Baileys API"], horizontal=True)
                
                if not df_unificado.empty:
                    if metodo_envio == "Email SMTP":
                        if 'email' in df_unificado.columns:
                            df_unificado = df_unificado[df_unificado['email'].astype(str).str.strip().str.lower().isin(['nan', 'none', '']) == False]
                        else:
                            df_unificado = pd.DataFrame()
                    else:
                        if 'telefone' in df_unificado.columns:
                            df_unificado = df_unificado[df_unificado['telefone'].astype(str).str.strip().str.lower().isin(['nan', 'none', '']) == False]
                        else:
                            df_unificado = pd.DataFrame()
                    
                    if not df_unificado.empty:
                        def make_label(r):
                            emp = str(r.get('empresa', ''))
                            nm = str(r.get('nome', ''))
                            if emp.lower() == 'nan' or not emp.strip(): emp = 'Sem Empresa'
                            if nm.lower() == 'nan' or not nm.strip(): nm = 'Sem Nome'
                            return f"Empresa: {emp} | Nome: {nm} | {r.get('fonte_dados', '')}"
                        df_unificado['label'] = df_unificado.apply(make_label, axis=1)
                
                modo_lote = st.radio("MODO DE SELECAO", ["Manual", "Lote 10 Rapido", "Lote 50 em 4 Horas"], horizontal=True)
                if modo_lote != "Manual":
                    alvos_pre = []
                    if not df_unificado.empty and 'status' in df_unificado.columns:
                        df_novos = df_unificado[df_unificado['status'].astype(str).str.upper() == 'NOVO']
                        limite = 10 if modo_lote == "Lote 10 Rapido" else 50
                        alvos_pre = df_novos['label'].tolist()[:limite]
                    alvos_finais = st.multiselect("ALVOS SELECIONADOS AUTOMATICAMENTE", alvos_pre, default=alvos_pre, disabled=True)
                else:
                    alvos_finais = st.multiselect("SELECIONE OS ALVOS DO CRM", df_unificado['label'].tolist() if not df_unificado.empty else [])
                    
            with c2:
                if metodo_envio == "Email SMTP":
                    assunto = st.text_input("ASSUNTO", key="ass_massa")
                    st.caption("Dica: Use {{imagem}} no texto para inserir a imagem inline no corpo do e-mail.")
                    corpo = st.text_area("CORPO HTML (Use {nome}, {empresa})", height=150, key="body_massa")
                    file_anexo = st.file_uploader("ANEXAR ARQUIVO (IMG vira inline, PDF vira anexo)", key="file_int_email")
                    if st.button("GERAR COPY EMAIL IA"): sug_a, sug_c = gerar_copy_ia(st.session_state.get('ctx', {})); st.info(sug_a); st.code(sug_c)
                else:
                    msg_wpp_massa = st.text_area("MENSAGEM WHATSAPP (Use {nome}, {empresa})", value="Opa {nome} tudo bem", height=150)
                    file_anexo_wpp = st.file_uploader("ANEXAR IMAGEM (Opcional - WhatsApp)", type=["png", "jpg", "jpeg"], key="img_wpp_int")
                    url_video_wpp = st.text_input("URL DO VÍDEO (Cloudinary ou MP4 direto)", key="vid_wpp_int")
                    st.info("O envio usa as travas de proteção da aba Configuração")
                    tracking = get_tracking_data(user_id)
                    st.caption(f"Limite WhatsApp Hoje {tracking.get('manual_limit', 30)}. Enviados {tracking['sent_today']}")

            if st.button("🚀 INICIAR DISPARO EM MASSA"):
                bar = st.progress(0)
                log = st.empty()
                
                if metodo_envio == "Email SMTP":
                    if not st.session_state.get('smtp') or not st.session_state['smtp'].get('host'): 
                        st.error("CONFIGURE O SMTP NA ABA CONFIGURAÇÕES GERAIS")
                    elif len(alvos_finais) > saldo_envios: st.error("SELEÇÃO MAIOR QUE SALDO")
                    else:
                        for i, label_sel in enumerate(alvos_finais):
                            tgt = df_unificado[df_unificado['label'] == label_sel].iloc[0]
                            email_real = str(tgt.get('email', '')).strip()
                            if not email_real or "@" not in email_real or email_real.lower() == 'nan':
                                log.warning(f"Sem email valido para {label_sel}")
                                continue
                                
                            assunto_final = assunto.replace("{nome}", str(tgt.get('nome', '')).strip()).replace("{empresa}", str(tgt.get('empresa', '')).strip())    
                            
                            log_id = registrar_log_envio(token, email_real, assunto_final, "Enviando")
                            url_pixel = f"{DIRECTUS_URL.rstrip('/')}/flows/trigger/{TRACKING_WEBHOOK_KEY}?log_id={log_id}" if log_id and TRACKING_WEBHOOK_KEY else None
                            
                            texto_final = corpo.replace("{nome}", str(tgt.get('nome', '')).strip()).replace("{empresa}", str(tgt.get('empresa', '')).strip())
                            
                            res, txt = enviar_email_smtp(st.session_state['smtp'], email_real, assunto_final, texto_final, file_anexo, url_pixel)
                            if log_id: atualizar_status_envio(token, log_id, "Enviado" if res else f"Erro {txt}")
                            if res and tgt.get('id'): atualizar_item(token, user_id, tgt['id'], {"status": "ENVIADO EM MASSA"})
                            
                            if res:
                                log.success(f"ENVIADO PARA {email_real}")
                            else:
                                log.error(f"ERRO {email_real}")
                                
                            bar.progress((i+1)/len(alvos_finais))
                            
                            if i < len(alvos_finais) - 1:
                                espera = random.randint(30, 90) if modo_lote != "Lote 50 em 4 Horas" else 288
                                timer_ph = st.empty()
                                for s in range(espera, 0, -1):
                                    timer_ph.info(f"Aguardando {s}s para o proximo envio")
                                    time.sleep(1)
                                timer_ph.empty()
                        
                        st.success("DISPARO FINALIZADO COM SUCESSO")
                        time.sleep(2)
                        st.rerun()
                
                elif metodo_envio == "WhatsApp Baileys API":
                    tracking = get_tracking_data(user_id)
                    daily_limit = tracking.get("manual_limit", 30)
                    today_str = str(date.today())
                    current_hour_str = str(datetime.now().strftime("%Y-%m-%d %H"))
                    
                    if tracking["last_run_date"] != today_str: tracking["sent_today"] = 0; tracking["last_run_date"] = today_str
                    if tracking["last_run_hour"] != current_hour_str: tracking["sent_this_hour"] = 0; tracking["last_run_hour"] = current_hour_str

                    for i, label_sel in enumerate(alvos_finais):
                        if tracking["sent_today"] >= daily_limit: st.warning("Limite diário atingido"); break
                        if tracking["sent_this_hour"] >= 10: st.warning("Limite de hora atingido"); break
                        
                        tgt = df_unificado[df_unificado['label'] == label_sel].iloc[0]
                        numero = extrair_whatsapp(str(tgt.get('telefone', '')))
                        if not numero or numero.lower() == 'nan':
                            log.warning(f"Sem WhatsApp para {label_sel}")
                            continue
                        
                        try:
                            msg_final_wpp = msg_wpp_massa.replace("{nome}", str(tgt.get('nome', '')).strip()).replace("{empresa}", str(tgt.get('empresa', '')).strip())
                            
                            payload = {"number": numero, "message": msg_final_wpp}
                            
                            if file_anexo_wpp is not None:
                                img_base64 = base64.b64encode(file_anexo_wpp.getvalue()).decode('utf-8')
                                payload["image"] = img_base64
                                
                            if url_video_wpp:
                                payload["videoUrl"] = url_video_wpp
                                
                            res = requests.post("http://213.199.56.207:3001/disparar", json=payload, timeout=20)
                            if res.status_code == 200:
                                tracking["sent_today"] += 1
                                tracking["sent_this_hour"] += 1
                                save_tracking_data(user_id, tracking)
                                log.success(f"WPP ENVIADO PARA {numero}")
                                if tgt.get('id'): atualizar_item(token, user_id, tgt['id'], {"status": "ENVIADO EM MASSA"})
                            else: log.error("Erro na API do Baileys")
                        except: log.error("Falha de conexão com disparador")
                        
                        bar.progress((i+1)/len(alvos_finais))
                        
                        if i < len(alvos_finais) - 1:
                            espera = random.randint(st.session_state.delay_min, st.session_state.delay_max) if modo_lote != "Lote 50 em 4 Horas" else 288
                            timer_ph = st.empty()
                            for s in range(espera, 0, -1):
                                timer_ph.info(f"Aguardando {s}s para o proximo envio")
                                time.sleep(1)
                            timer_ph.empty()
                        
                    st.success("DISPARO FINALIZADO COM SUCESSO")
                    time.sleep(2)
                    st.rerun()

        with subtab_ext:
            st.markdown("### 📂 UPLOAD DE LISTA (EXCEL .xlsx)")
            up_file = st.file_uploader("ARQUIVO EXCEL (Colunas obrigatórias: nome, email ou telefone)", type=["xlsx"])
            
            if up_file:
                try:
                    df_ext = pd.read_excel(up_file)
                    df_ext.columns = [str(c).lower().strip() for c in df_ext.columns]
                    
                    st.dataframe(df_ext.head(), width='stretch')
                    st.info(f"{len(df_ext)} LEADS ENCONTRADOS NO ARQUIVO")

                    col_imp_btn, col_imp_info = st.columns([1, 2])
                    with col_imp_btn:
                        if st.button("💾 IMPORTAR LISTA PARA O CRM", type="primary"):
                            progress_text = "Importando leads para o banco de dados..."
                            my_bar = st.progress(0, text=progress_text)
                            
                            table_name = get_user_table_name(user_id)
                            base_url = DIRECTUS_URL.rstrip('/')
                            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                            
                            total_imp = len(df_ext)
                            sucesso_imp = 0
                            
                            for idx, row in df_ext.iterrows():
                                payload = {"status": "Novo"}
                                for col in df_ext.columns:
                                    slug = col.replace(' ', '_').replace('ç', 'c').replace('ã', 'a')
                                    val = row[col]
                                    if pd.isna(val): val = ""
                                    payload[slug] = str(val)

                                try:
                                    r_imp = requests.post(f"{base_url}/items/{table_name}", json=payload, headers=headers, verify=False)
                                    if r_imp.status_code in [200, 204]:
                                        sucesso_imp += 1
                                except:
                                    pass
                                
                                my_bar.progress((idx + 1) / total_imp)
                            
                            my_bar.empty()
                            st.success(f"✅ IMPORTAÇÃO CONCLUÍDA! {sucesso_imp} LEADS SALVOS NO CRM.")
                            time.sleep(2)
                            st.rerun()

                    st.markdown("---")
                    
                    st.markdown("#### 🚀 DISPARO DIRETO DA LISTA EXTERNA")
                    metodo_envio_ext = st.radio("MÉTODO DE DISPARO EXTERNO", ["Email SMTP", "WhatsApp Baileys API"], horizontal=True, key="metodo_ext")
                    
                    if metodo_envio_ext == "Email SMTP":
                        assunto_ext = st.text_input("ASSUNTO", key="ass_ext")
                        st.caption("Dica: Use {{imagem}} no texto para inserir a imagem no corpo.")
                        corpo_ext = st.text_area("CORPO HTML (Use {nome}, {empresa})", height=150, key="body_ext")
                        file_anexo_ext = st.file_uploader("ANEXAR ARQUIVO (IMG vira inline, PDF vira anexo)", key="file_ext_up_email")
                        
                        if st.button("✨ GERAR COM IA (GROQ) - EXT"):
                            sug_a, sug_c = gerar_copy_ia(st.session_state.get('ctx', {}))
                            st.info(f"Assunto: {sug_a}")
                            st.code(sug_c)
                            
                        if st.button("🚀 DISPARAR E-MAIL PARA LISTA EXTERNA"):
                            if not st.session_state.get('smtp') or not st.session_state['smtp'].get('host'):
                                st.error("SMTP OFF - CONFIGURE NA ABA CONFIGURAÇÕES GERAIS")
                            elif 'email' not in df_ext.columns:
                                st.error("O arquivo precisa ter uma coluna chamada 'email'.")
                            elif len(df_ext[df_ext['email'].astype(str).str.contains("@")]) > saldo_envios:
                                st.error(f"LISTA MAIOR QUE SALDO ({saldo_envios})")
                            else:
                                df_validos = df_ext[df_ext['email'].astype(str).str.contains("@")]
                                bar2 = st.progress(0)
                                log2 = st.empty()
                                
                                for i, row in df_validos.iterrows():
                                    if i > 0:
                                        wait = random.randint(30, 90)
                                        timer_ext = st.empty()
                                        for s in range(wait, 0, -1):
                                            timer_ext.warning(f"⏳ ANTI-SPAM... {s}s")
                                            time.sleep(1)
                                        timer_ext.empty()
                                    
                                    nome_l = row.get('nome', 'Parceiro')
                                    email_l = str(row['email']).strip()
                                    empresa_l = row.get('empresa', '') if 'empresa' in row else ''
                                    
                                    assunto_final_ext = assunto_ext.replace("{nome}", str(nome_l)).replace("{empresa}", str(empresa_l))
                                    
                                    log_id = registrar_log_envio(token, email_l, assunto_final_ext, "Enviando... [EXT]")
                                    
                                    tracking_url = None
                                    if log_id and TRACKING_WEBHOOK_KEY != "SUA_CHAVE_AQUI":
                                        base_clean = DIRECTUS_URL.rstrip('/')
                                        tracking_url = f"{base_clean}/flows/trigger/{TRACKING_WEBHOOK_KEY}?log_id={log_id}"

                                    msg_final = corpo_ext.replace("{nome}", str(nome_l)).replace("{empresa}", str(empresa_l))
                                    
                                    res, txt = enviar_email_smtp(st.session_state['smtp'], email_l, assunto_final_ext, msg_final, file_anexo_ext, tracking_url)
                                    
                                    if log_id:
                                        novo_status = "Enviado [EXT]" if res else f"Erro: {txt}"
                                        atualizar_status_envio(token, log_id, novo_status)

                                    if res: log2.success(f"ENVIADO: {email_l}")
                                    else: log2.error(f"FALHA: {email_l}")
                                    
                                    bar2.progress((i+1)/len(df_validos))
                                st.balloons()
                                time.sleep(2)
                                st.rerun()
                                
                    else: 
                        msg_wpp_ext = st.text_area("MENSAGEM WHATSAPP (Use {nome}, {empresa})", value="Opa {nome} tudo bem", height=150, key="wpp_ext")
                        file_anexo_wpp_ext = st.file_uploader("ANEXAR IMAGEM (Opcional - WhatsApp)", type=["png", "jpg", "jpeg"], key="img_wpp_ext_up")
                        url_video_ext = st.text_input("URL DO VÍDEO (Cloudinary ou MP4 direto)", key="vid_wpp_ext")
                        tracking = get_tracking_data(user_id)
                        st.caption(f"Limite WhatsApp Hoje {tracking.get('manual_limit', 30)}. Enviados {tracking['sent_today']}")
                        
                        if st.button("🚀 DISPARAR WHATSAPP PARA LISTA EXTERNA"):
                            if 'telefone' not in df_ext.columns and 'whatsapp' not in df_ext.columns:
                                st.error("O arquivo precisa ter uma coluna chamada 'telefone' ou 'whatsapp'.")
                            else:
                                col_tel = 'telefone' if 'telefone' in df_ext.columns else 'whatsapp'
                                df_validos = df_ext[df_ext[col_tel].astype(str).str.strip() != '']
                                
                                bar3 = st.progress(0)
                                log3 = st.empty()
                                
                                daily_limit = tracking.get("manual_limit", 30)
                                today_str = str(date.today())
                                current_hour_str = str(datetime.now().strftime("%Y-%m-%d %H"))
                                
                                for i, row in df_validos.iterrows():
                                    tracking = get_tracking_data(user_id)
                                    if tracking["last_run_date"] != today_str: tracking["sent_today"] = 0; tracking["last_run_date"] = today_str
                                    if tracking["last_run_hour"] != current_hour_str: tracking["sent_this_hour"] = 0; tracking["last_run_hour"] = current_hour_str
                                    
                                    if tracking["sent_today"] >= daily_limit: st.warning("Limite diário atingido"); break
                                    if tracking["sent_this_hour"] >= 10: st.warning("Limite de hora atingido"); break
                                    
                                    nome_l = row.get('nome', 'Parceiro')
                                    empresa_l = row.get('empresa', '') if 'empresa' in row else ''
                                    numero = extrair_whatsapp(str(row[col_tel]))
                                    
                                    if not numero or numero.lower() == 'nan':
                                        continue
                                        
                                    try:
                                        msg_final_wpp = msg_wpp_ext.replace("{nome}", str(nome_l)).replace("{empresa}", str(empresa_l))
                                        payload = {"number": numero, "message": msg_final_wpp}
                                        
                                        if file_anexo_wpp_ext is not None:
                                            img_base64 = base64.b64encode(file_anexo_wpp_ext.getvalue()).decode('utf-8')
                                            payload["image"] = img_base64
                                            
                                        if url_video_ext:
                                            payload["videoUrl"] = url_video_ext
                                            
                                        res = requests.post("http://213.199.56.207:3001/disparar", json=payload, timeout=20)
                                        
                                        if res.status_code == 200:
                                            tracking["sent_today"] += 1
                                            tracking["sent_this_hour"] += 1
                                            save_tracking_data(user_id, tracking)
                                            log3.success(f"WPP ENVIADO PARA {numero}")
                                        else:
                                            log3.error("Erro na API do Baileys")
                                    except:
                                        log3.error("Falha de conexão com disparador")
                                    
                                    espera_ext = random.randint(st.session_state.delay_min, st.session_state.delay_max)
                                    timer_ext_wpp = st.empty()
                                    for s in range(espera_ext, 0, -1):
                                        timer_ext_wpp.info(f"Aguardando {s}s para o proximo envio")
                                        time.sleep(1)
                                    timer_ext_wpp.empty()
                                    bar3.progress((i+1)/len(df_validos))
                                
                                st.success("DISPARO FINALIZADO COM SUCESSO")
                                time.sleep(2)
                                st.rerun()

                except Exception as e:
                    st.error(f"ERRO AO LER EXCEL: {e}")

    with tab5:
        st.markdown("### 📧 CONFIGURAÇÃO DO E-MAIL (SMTP)")
        st.info("Salve as credenciais do seu e-mail aqui. Elas ficarão salvas no seu banco de dados (Directus) para os próximos disparos automaticamente.")
        
        c_smtp1, c_smtp2 = st.columns(2)
        with c_smtp1:
            h_val = st.text_input("SMTP HOST (Ex: smtp.gmail.com)", value=st.session_state.get('smtp_host_input', 'smtp.gmail.com'))
            u_val = st.text_input("SMTP USER (Seu e-mail)", value=st.session_state.get('smtp_user_input', ''))
        with c_smtp2:
            p_val = st.number_input("SMTP PORT", value=st.session_state.get('smtp_port_input', 587))
            pw_val = st.text_input("SMTP PASS (Senha de App)", type="password", value=st.session_state.get('smtp_pass_input', ''))
            
        if st.button("💾 SALVAR CONFIGURAÇÕES NO BANCO", width='stretch'):
            st.session_state['smtp'] = {'host': h_val, 'port': p_val, 'user': u_val, 'pass': pw_val}
            st.session_state['smtp_host_input'] = h_val
            st.session_state['smtp_port_input'] = p_val
            st.session_state['smtp_user_input'] = u_val
            st.session_state['smtp_pass_input'] = pw_val
            
            sucesso = salvar_config_smtp(token, {'smtp_host': h_val, 'smtp_port': p_val, 'smtp_user': u_val, 'smtp_pass': pw_val})
            if sucesso:
                st.success("✅ Configurações SMTP salvas com sucesso na tabela config_smtp!")
            else:
                st.error("❌ Falha ao salvar. Verifique se a tabela existe no Directus.")
                
        st.divider()

        st.markdown("### ⚙️ PROTEÇÃO DO WHATSAPP E LIMITES")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.delay_min = st.number_input("Tempo Minimo Segundos", min_value=10, max_value=600, value=st.session_state.get('delay_min', 60))
        with col2:
            st.session_state.delay_max = st.number_input("Tempo Maximo Segundos", min_value=10, max_value=800, value=st.session_state.get('delay_max', 200))
        with col3:
            tracking = get_tracking_data(user_id)
            novo_limite = st.number_input("Limite Diario Manual (Max 30)", min_value=1, max_value=30, value=tracking.get("manual_limit", 30))
            if novo_limite != tracking.get("manual_limit", 30):
                tracking["manual_limit"] = novo_limite
                save_tracking_data(user_id, tracking)
                st.success("Limite atualizado")
        
        st.divider()
        tracking = get_tracking_data(user_id)
        daily_lim = tracking.get("manual_limit", 30)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Limite Seguro de Hoje", daily_lim)
        col_b.metric("Disparos Hoje", tracking["sent_today"])
        col_c.metric("Disparos Nesta Hora", f"{tracking['sent_this_hour']} / 10")
        
        st.divider()
        st.markdown("### 🧠 INSTRUÇÕES DA IA CAÇADORA")
        st.session_state.system_prompt_padrao = st.text_area("Edite as regras de classificação da IA", value=st.session_state.system_prompt_padrao, height=150)
        
        if st.button("Zerar Contadores de Segurança Perigo"):
            os.remove(get_tracking_file(user_id))
            st.rerun()

except Exception as e:
    st.markdown("<br><br><br><h2 style='text-align: center; color: var(--red); padding: 20px;'>A TELA PRECISA SER ATUALIZADA</h2>", unsafe_allow_html=True)
    if st.button("🔄 CLIQUE AQUI PARA REINICIAR", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ['token', 'user']:
                del st.session_state[key]
        st.rerun()
