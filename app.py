from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g, flash
import requests
import os
import json
import uuid
import traceback
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
# Define a chave secreta (use uma fixa no .env para produção)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_padrao_dev_123")

# --- CONFIGURAÇÕES GERAIS ---
# Remove barra final da URL para evitar erros de concatenação
# Se não houver variável, usa localhost como fallback seguro para não quebrar
DIRECTUS_URL = os.getenv("DIRECTUS_URL", "http://172.17.0.1:8055").rstrip('/')
DIRECTUS_TOKEN = os.getenv("DIRECTUS_TOKEN", "") 
SUPERFRETE_TOKEN = os.getenv("SUPERFRETE_TOKEN", "")
SUPERFRETE_URL = os.getenv("SUPERFRETE_URL", "https://api.superfrete.com/api/v0/calculator")
CEP_ORIGEM_PADRAO = "01026000" # Fallback se a loja não tiver CEP configurado

# --- FUNÇÕES AUXILIARES ---
def get_headers():
    return {"Authorization": f"Bearer {DIRECTUS_TOKEN}"}

def get_img_url(image_id_or_obj):
    """Trata URLs de imagens vindas do Directus (ID, Objeto ou URL completa)"""
    if not image_id_or_obj: return ""
    if isinstance(image_id_or_obj, dict): return f"{DIRECTUS_URL}/assets/{image_id_or_obj.get('id')}"
    if image_id_or_obj.startswith('http'): return image_id_or_obj
    return f"{DIRECTUS_URL}/assets/{image_id_or_obj}"

def upload_file_to_directus(file_storage):
    """Faz upload de arquivo para o Directus e retorna o ID"""
    try:
        url = f"{DIRECTUS_URL}/files"
        filename = secure_filename(file_storage.filename)
        files = {'file': (filename, file_storage, file_storage.mimetype)}
        # Importante: Directus requer multipart/form-data, não mande JSON header aqui
        headers = {"Authorization": f"Bearer {DIRECTUS_TOKEN}"}
        
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code in [200, 201]:
            return response.json()['data']['id']
        else:
            print(f"Erro no Upload Directus: {response.text}")
    except Exception as e:
        print(f"Exceção no upload: {e}")
    return None

# --- MIDDLEWARE: IDENTIFICAÇÃO DA LOJA (MULTI-TENANT) ---
@app.before_request
def identificar_loja():
    """Identifica qual loja está sendo acessada baseada no domínio ou subdomínio"""
    
    # Ignora arquivos estáticos para não processar desnecessariamente
    if request.path.startswith('/static'):
        return

    # Pega o domínio que o usuário digitou (ex: doces.leanttro.com)
    host = request.headers.get('Host')
    
    # --- MODO DESENVOLVIMENTO (DEBUG) ---
    # Descomente a linha abaixo se quiser forçar um domínio localmente
    # host = "lojavirtual.leanttro.com" 
    
    try:
        # Busca no Directus qual loja possui este domínio
        headers = get_headers()
        
        # LOG DE DEBUG (Aparecerá nos logs do Dokploy)
        # Isso ajuda a saber se o Python está conseguindo falar com o Directus
        print(f"[DEBUG] Tentando conectar Directus em: {DIRECTUS_URL} buscando host: {host}", flush=True)
        
        url = f"{DIRECTUS_URL}/items/lojas?filter[dominio][_eq]={host}&fields=*.*"
        
        # Timeout de 5s para não travar o servidor se o Directus estiver fora
        resp = requests.get(url, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            if len(data) > 0:
                g.loja = data[0]
                g.loja_id = g.loja['id']
                
                # Tratamento de Layout e Configs Visuais (Fallback se vazio)
                if not g.loja.get('layout_order'):
                    g.loja['layout_order'] = "banner,busca,categorias,produtos,novidades,blog,footer"
                
                g.layout_list = g.loja['layout_order'].split(',')
            else:
                # Se não achar a loja pelo domínio, verifica se é uma rota de sistema (cadastro)
                if request.path == '/cadastro' or request.path.startswith('/api/'):
                    g.loja = None
                    g.loja_id = None
                    return
                # Caso contrário, exibe 404
                g.loja = None
                return render_template('404_saas.html', host=host), 404
        else:
            print(f"[ERRO DIRECTUS] Status: {resp.status_code} | Msg: {resp.text}")
            return f"Erro de comunicação com o Banco de Dados (Directus): {resp.status_code}", 500

    except Exception as e:
        # Imprime o erro completo no Log do Dokploy
        print("--- ERRO CRÍTICO NO MIDDLEWARE ---")
        traceback.print_exc()
        return f"Erro interno de conexão: {str(e)} | URL Directus: {DIRECTUS_URL}", 500


# --- ROTA DE CADASTRO (CRIAR NOVA LOJA) ---
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    # Se já estiver logado como admin de alguma loja, redireciona
    if session.get('loja_admin_id'):
        return redirect('/admin/painel')

    if request.method == 'POST':
        nome = request.form.get('nome')
        # Normaliza o slug (link)
        slug = request.form.get('slug').lower().strip().replace(' ', '-')
        email = request.form.get('email').strip()
        # Remove caracteres não numéricos do WhatsApp
        whatsapp = request.form.get('whatsapp', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        senha = request.form.get('senha')

        # 1. Validações Básicas
        if not all([nome, slug, email, whatsapp, senha]):
            flash('Preencha todos os campos obrigatórios.', 'error')
            return render_template('cadastro.html')

        # 2. Verifica se já existe (Slug/Domínio ou Email) no Directus
        headers = get_headers()
        # Filtro OR: (dominio == slug) OU (email == email)
        filtro = f"?filter[_or][0][dominio][_eq]={slug}&filter[_or][1][email][_eq]={email}"
        
        try:
            check = requests.get(f"{DIRECTUS_URL}/items/lojas{filtro}", headers=headers)
            
            if check.status_code == 200 and len(check.json()['data']) > 0:
                # Identifica qual deu conflito
                existing = check.json()['data'][0]
                if existing.get('dominio') == slug:
                    flash(f'O link "{slug}" já está em uso. Escolha outro.', 'error')
                else:
                    flash('Este e-mail já possui uma loja cadastrada.', 'error')
                return render_template('cadastro.html')

            # 3. Cria a Loja com Configurações Padrão
            senha_hash = generate_password_hash(senha)

            payload = {
                "status": "published", 
                "nome": nome,
                "dominio": slug,          # O subdomínio vira o identificador principal
                "slug": slug,             # Mantemos slug também por compatibilidade
                "email": email,
                "whatsapp_comercial": whatsapp,
                "senha_admin": senha_hash,
                
                # Configurações Visuais Padrão (Seed)
                "cor_primaria": "#db2777", # Pink padrão
                "font_titulo": "Poppins",
                "font_corpo": "Inter",
                "layout_order": "banner,busca,categorias,produtos,novidades,footer",
                
                # Placeholders
                "linkbannerprincipal1": "#",
                "linkbannerprincipal2": "#"
            }

            r = requests.post(f"{DIRECTUS_URL}/items/lojas", headers=headers, json=payload)
            
            if r.status_code in [200, 201]:
                flash('Loja criada com sucesso! Faça login para começar.', 'success')
                # Manda pro admin genérico. O usuário deve acessar pelo domínio correto depois.
                return redirect('/admin') 
            else:
                print(f"Erro Directus Create: {r.text}")
                flash('Erro ao criar loja. Tente novamente.', 'error')

        except Exception as e:
            print(f"Erro Exception Create: {e}")
            flash(f'Erro interno: {str(e)}', 'error')

    return render_template('cadastro.html')


# --- ROTA: INDEX (A VITRINE DA LOJA) ---
@app.route('/')
def index():
    if not g.loja: return redirect('/cadastro') # Se não tiver loja identificada, manda criar

    headers = get_headers()
    
    # 1. Busca Categorias
    categorias = []
    try:
        url_cat = f"{DIRECTUS_URL}/items/categorias?filter[loja_id][_eq]={g.loja_id}&filter[status][_eq]=published&sort=sort"
        r_cat = requests.get(url_cat, headers=headers)
        if r_cat.status_code == 200: categorias = r_cat.json()['data']
    except: pass

    # 2. Busca Produtos (com filtros)
    cat_filter = request.args.get('categoria')
    filter_str = f"&filter[loja_id][_eq]={g.loja_id}&filter[status][_eq]=published"
    if cat_filter: filter_str += f"&filter[categoria_id][_eq]={cat_filter}"

    produtos = []
    novidades = []

    try:
        url_prod = f"{DIRECTUS_URL}/items/produtos?{filter_str}&fields=*.*"
        r_prod = requests.get(url_prod, headers=headers)
        if r_prod.status_code == 200:
            raw_prods = r_prod.json()['data']
            for p in raw_prods:
                img = get_img_url(p.get('imagem_destaque') or p.get('imagem1'))
                
                # Trata Variantes
                variantes = []
                if p.get('variantes'):
                    for v in p['variantes']:
                        v_foto = get_img_url(v.get('foto')) if v.get('foto') else img
                        variantes.append({"nome": v.get('nome'), "foto": v_foto})

                prod_obj = {
                    "id": p['id'], "nome": p['nome'], "slug": p['slug'],
                    "preco": float(p['preco']) if p.get('preco') else 0,
                    "imagem": img, "categoria_id": p.get('categoria_id'),
                    "variantes": variantes, "origem": p.get('origem'),
                    "urgencia": p.get('status_urgencia'), "classe_frete": p.get('classe_frete')
                }
                produtos.append(prod_obj)
                
                # Separa Novidades (Ex: Status 'Lancamento' ou 'Alta Procura')
                if p.get('status_urgencia') in ['Alta Procura', 'Lancamento']:
                    novidades.append(prod_obj)
    except Exception as e:
        print(f"Erro produtos: {e}")

    # 3. Busca Posts do Blog
    posts = []
    try:
        url_blog = f"{DIRECTUS_URL}/items/posts?filter[loja_id][_eq]={g.loja_id}&filter[status][_eq]=published&limit=3&sort=-date_created"
        r_blog = requests.get(url_blog, headers=headers)
        if r_blog.status_code == 200:
            for post in r_blog.json()['data']:
                posts.append({
                    "titulo": post['titulo'], "slug": post['slug'],
                    "resumo": post.get('resumo', ''),
                    "capa": get_img_url(post.get('capa')),
                    "data": datetime.fromisoformat(post['date_created'].split('T')[0]).strftime('%d/%m/%Y')
                })
    except: pass

    # 4. Trata URLs de imagens da loja para o template
    loja_visual = {
        **g.loja,
        "logo": get_img_url(g.loja.get('logo')),
        "banner1": get_img_url(g.loja.get('bannerprincipal1')),
        "banner2": get_img_url(g.loja.get('bannerprincipal2')),
        "bannermenor1": get_img_url(g.loja.get('bannermenor1')),
        "bannermenor2": get_img_url(g.loja.get('bannermenor2')),
    }

    return render_template('index.html', 
                         loja=loja_visual, 
                         layout=g.layout_list,
                         categorias=categorias, 
                         produtos=produtos, 
                         novidades=novidades, 
                         posts=posts,
                         directus_url=DIRECTUS_URL)


# --- ROTA: DETALHE DO PRODUTO ---
@app.route('/produto/<slug>')
def produto(slug):
    if not g.loja: return redirect('/cadastro')

    headers = get_headers()
    # Filtra pelo slug E pela loja_id (segurança)
    url = f"{DIRECTUS_URL}/items/produtos?filter[slug][_eq]={slug}&filter[loja_id][_eq]={g.loja_id}&fields=*.*"
    r = requests.get(url, headers=headers)
    
    if r.status_code == 200 and r.json()['data']:
        p = r.json()['data'][0]
        
        # Tratamento de dados para o template
        p['imagem_destaque'] = get_img_url(p.get('imagem_destaque'))
        p['imagem1'] = get_img_url(p.get('imagem1'))
        p['imagem2'] = get_img_url(p.get('imagem2'))
        
        # Galeria
        galeria = [p['imagem_destaque']]
        if p.get('imagem1'): galeria.append(p['imagem1'])
        if p.get('imagem2'): galeria.append(p['imagem2'])
        p['galeria'] = galeria

        # Variantes com foto
        if p.get('variantes'):
            for v in p['variantes']:
                v['foto'] = get_img_url(v.get('foto')) if v.get('foto') else p['imagem_destaque']

        # Loja visual (logo, cores)
        loja_visual = {
            **g.loja,
            "logo": get_img_url(g.loja.get('logo'))
        }

        return render_template('produtos.html', p=p, loja=loja_visual, directus_url=DIRECTUS_URL)
    
    return "Produto não encontrado nesta loja", 404


# --- ROTA: ADMIN LOGIN ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if not g.loja:
        return "Loja não identificada. Acesse pelo domínio correto (ex: seunome.leanttro.com).", 404

    # Se já estiver logado nesta loja, vai pro painel
    if session.get('loja_admin_id') == g.loja_id:
        return redirect('/admin/painel')

    if request.method == 'POST':
        senha = request.form.get('senha')
        
        # Verifica Hash da senha salva no Directus
        # g.loja['senha_admin'] deve ser o hash
        senha_banco = g.loja.get('senha_admin')
        
        if senha_banco:
            # Tenta verificar hash ou texto puro (fallback para senhas antigas)
            is_valid = False
            try:
                is_valid = check_password_hash(senha_banco, senha)
            except:
                is_valid = (senha_banco == senha) # Fallback inseguro temporário
                
            if is_valid:
                session['loja_admin_id'] = g.loja_id
                session.permanent = True
                return redirect('/admin/painel')
            else:
                flash('Senha incorreta', 'error')
        else:
            flash('Erro de configuração: Loja sem senha definida.', 'error')
    
    loja_visual = {**g.loja, "logo": get_img_url(g.loja.get('logo'))}
    return render_template('login_admin.html', loja=loja_visual)


# --- ROTA: PAINEL DE EDIÇÃO (SAAS) ---
@app.route('/admin/painel', methods=['GET', 'POST'])
def admin_painel():
    if not g.loja: return redirect('/')
    
    # Segurança: Garante que está logado NA LOJA ATUAL
    if session.get('loja_admin_id') != g.loja_id:
        return redirect('/admin')

    if request.method == 'POST':
        # 1. Uploads de Imagens
        files_map = {}
        for key in ['logo', 'bannerprincipal1', 'bannerprincipal2', 'bannermenor1', 'bannermenor2']:
            f = request.files.get(key)
            if f and f.filename:
                fid = upload_file_to_directus(f)
                if fid: files_map[key] = fid

        # 2. Dados de Texto e Configuração
        payload = {
            "nome": request.form.get('nome'),
            "whatsapp_comercial": request.form.get('whatsapp'),
            "cor_primaria": request.form.get('cor_primaria'),
            "font_titulo": request.form.get('font_titulo'),
            "font_corpo": request.form.get('font_corpo'),
            "linkbannerprincipal1": request.form.get('link1'),
            "linkbannerprincipal2": request.form.get('link2'),
            # O Sortable.js do front manda a string ordenada aqui
            "layout_order": request.form.get('layout_order') 
        }
        
        # Mescla uploads com dados
        payload.update(files_map)

        # 3. Salva no Directus
        try:
            requests.patch(f"{DIRECTUS_URL}/items/lojas/{g.loja_id}", 
                        headers=get_headers(), 
                        json=payload)
            flash('Loja atualizada com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao salvar: {e}', 'error')
        
        return redirect('/admin/painel')

    # Trata imagens para preview no painel
    loja_visual = {
        **g.loja,
        "logo_url": get_img_url(g.loja.get('logo')),
        "banner1_url": get_img_url(g.loja.get('bannerprincipal1')),
        "banner2_url": get_img_url(g.loja.get('bannerprincipal2'))
    }

    return render_template('painel.html', loja=loja_visual)


# --- ROTA: RECUPERAR SENHA ---
@app.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    if not g.loja: return redirect('/')

    if request.method == 'POST':
        email = request.form.get('email')
        
        # Verifica se o email bate com o cadastro da loja atual
        if email == g.loja.get('email'):
            token = str(uuid.uuid4())
            expiracao = (datetime.now() + timedelta(hours=1)).isoformat()
            
            # Salva token no Directus
            requests.patch(f"{DIRECTUS_URL}/items/lojas/{g.loja_id}", 
                         headers=get_headers(),
                         json={'reset_token': token, 'reset_expires': expiracao})
            
            # --- ENVIO DE E-MAIL ---
            # Simulando envio. Em produção, use SMTP real.
            link = f"https://{request.headers.get('Host')}/nova-senha/{token}"
            print(f"--- LINK RECUPERAÇÃO: {link} ---")
            
            flash('Link de recuperação enviado para seu e-mail (Verifique o Spam).', 'success')
        else:
            flash('E-mail não corresponde ao cadastro desta loja.', 'error')
            
    return render_template('esqueceu_senha.html', loja=g.loja)

@app.route('/nova-senha/<token>', methods=['GET', 'POST'])
def nova_senha(token):
    # Busca qual loja tem esse token
    r = requests.get(f"{DIRECTUS_URL}/items/lojas?filter[reset_token][_eq]={token}", headers=get_headers())
    data = r.json().get('data')
    
    if not data: 
        return "Link inválido ou expirado.", 400
    
    loja_alvo = data[0]

    if request.method == 'POST':
        nova = request.form.get('senha')
        hash_senha = generate_password_hash(nova)
        
        # Atualiza senha e limpa token
        requests.patch(f"{DIRECTUS_URL}/items/lojas/{loja_alvo['id']}", 
                     headers=get_headers(),
                     json={'senha_admin': hash_senha, 'reset_token': None, 'reset_expires': None})
        
        flash('Senha alterada com sucesso! Faça login.', 'success')
        return redirect('/admin')

    return render_template('nova_senha.html', token=token)


# --- API FRETE (MOCK/PLACEHOLDER) ---
@app.route('/api/calcular-frete', methods=['POST'])
def api_frete():
    # Retorna JSON vazio para o front não quebrar enquanto você não configura o SuperFrete
    return jsonify([]) 


# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    # Roda na porta 5000 acessível externamente
    app.run(host='0.0.0.0', port=5000)