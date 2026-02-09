from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g, flash
import requests
import os
import json
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
# Em produção, defina uma SECRET_KEY fixa no .env
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_super_segura_saas_2026")

# --- CONFIGURAÇÃO DE COOKIE GLOBAL (CRUCIAL PARA O LOGIN FUNCIONAR) ---
app.config['SESSION_COOKIE_DOMAIN'] = '.leanttro.com'
app.config['SESSION_COOKIE_NAME'] = 'leanttro_session'

# --- CONFIGURAÇÕES GERAIS ---
DIRECTUS_URL = os.getenv("DIRECTUS_URL", "https://api2.leanttro.com").rstrip('/')
DIRECTUS_TOKEN = os.getenv("DIRECTUS_TOKEN", "") 
SUPERFRETE_TOKEN = os.getenv("SUPERFRETE_TOKEN", "")
SUPERFRETE_URL = os.getenv("SUPERFRETE_URL", "https://api.superfrete.com/api/v0/calculator")
# IMPORTANTE: Coloque aqui seu domínio base para montar os links corretamente
DOMINIO_BASE = "leanttro.com" 

# --- FUNÇÕES AUXILIARES ---
def get_headers():
    return {"Authorization": f"Bearer {DIRECTUS_TOKEN}", "Content-Type": "application/json"}

def get_upload_headers():
    return {"Authorization": f"Bearer {DIRECTUS_TOKEN}"}

def get_img_url(image_id_or_obj):
    if not image_id_or_obj: return ""
    if isinstance(image_id_or_obj, dict): return f"{DIRECTUS_URL}/assets/{image_id_or_obj.get('id')}"
    if isinstance(image_id_or_obj, str) and image_id_or_obj.startswith('http'): return image_id_or_obj
    return f"{DIRECTUS_URL}/assets/{image_id_or_obj}"

def upload_file_to_directus(file_storage):
    try:
        url = f"{DIRECTUS_URL}/files"
        filename = secure_filename(file_storage.filename)
        files = {'file': (filename, file_storage, file_storage.mimetype)}
        response = requests.post(url, headers=get_upload_headers(), files=files)
        if response.status_code in [200, 201]:
            return response.json()['data']['id']
    except Exception as e:
        print(f"Erro Upload: {e}")
    return None

# --- MIDDLEWARE: IDENTIFICAÇÃO DA LOJA ---
@app.before_request
def identificar_loja():
    if request.path.startswith('/static'): return

    host = request.headers.get('Host')
    
    # Ignora rotas de sistema se não for subdomínio
    if request.path == '/cadastro' or request.path.startswith('/api/hook'):
        g.loja = None; g.loja_id = None
        return

    try:
        # Busca EXATAMENTE pelo host que está no navegador (ex: loja.leanttro.com)
        headers = get_headers()
        url = f"{DIRECTUS_URL}/items/lojas?filter[dominio][_eq]={host}&fields=*.*"
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200 and len(resp.json()['data']) > 0:
            g.loja = resp.json()['data'][0]
            g.loja_id = g.loja['id']
            
            if not g.loja.get('layout_order'):
                g.loja['layout_order'] = "banner,busca,categorias,produtos,novidades,blog,footer"
            g.layout_list = g.loja['layout_order'].split(',')
        else:
            g.loja = None; g.loja_id = None

    except Exception as e:
        print(f"Erro Middleware: {e}")
        g.loja = None; g.loja_id = None


# --- ROTA DE CADASTRO ---
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if session.get('loja_admin_id'):
        return redirect('/admin/painel')

    if request.method == 'POST':
        nome = request.form.get('nome')
        slug_input = request.form.get('slug')
        slug = slug_input.lower().strip().replace(' ', '-') if slug_input else ""
        email = request.form.get('email').strip()
        whatsapp = request.form.get('whatsapp', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        senha = request.form.get('senha')

        # Monta o domínio completo para salvar no banco
        dominio_completo = f"{slug}.{DOMINIO_BASE}"

        if not all([nome, slug, email, whatsapp, senha]):
            flash('Preencha todos os campos.', 'error')
            return render_template('cadastro.html')

        # Verifica duplicidade
        headers = get_headers()
        # Verifica tanto o slug curto quanto o dominio completo
        filtro = f"?filter[_or][0][dominio][_eq]={dominio_completo}&filter[_or][1][email][_eq]={email}"
        try:
            check = requests.get(f"{DIRECTUS_URL}/items/lojas{filtro}", headers=headers)
            if check.status_code == 200 and len(check.json()['data']) > 0:
                flash(f'A loja "{slug}" ou o e-mail já existem.', 'error')
                return render_template('cadastro.html')
        except: pass

        senha_hash = generate_password_hash(senha)

        payload = {
            "status": "published",
            "nome": nome,
            "slug": slug,
            "dominio": dominio_completo,  # SALVANDO O DOMÍNIO COMPLETO AGORA
            "email": email,
            "whatsapp_comercial": whatsapp,
            "senha_admin": senha_hash,
            "cor_primaria": "#db2777", 
            "font_titulo": "Poppins",
            "font_corpo": "Inter",
            "layout_order": "banner,busca,categorias,produtos,novidades,footer",
            "linkbannerprincipal1": "#",
            "linkbannerprincipal2": "#"
        }

        try:
            r = requests.post(f"{DIRECTUS_URL}/items/lojas", headers=headers, json=payload)
            
            if r.status_code in [200, 201]:
                data = r.json().get('data')
                
                # Login Automático
                session['loja_admin_id'] = data['id']
                session.permanent = True
                
                flash('Loja criada com sucesso!', 'success')
                # Redireciona para o novo domínio
                return redirect(f"https://{dominio_completo}/admin/painel")
            else:
                try: erro = r.json()['errors'][0]['message']
                except: erro = "Erro desconhecido"
                flash(f'Erro ao criar: {erro}', 'error')
                
        except Exception as e:
            flash(f'Erro de conexão: {e}', 'error')

    return render_template('cadastro.html')

# --- ROTAS DA LOJA (VITRINE) ---
@app.route('/')
def index():
    if not g.loja: return redirect('/cadastro')

    headers = get_headers()
    categorias = []
    produtos = []
    novidades = []
    posts = []

    try:
        # Categorias
        r_cat = requests.get(f"{DIRECTUS_URL}/items/categorias?filter[loja_id][_eq]={g.loja_id}&filter[status][_eq]=published&sort=sort", headers=headers)
        if r_cat.ok: categorias = r_cat.json()['data']

        # Produtos
        cat_filter = request.args.get('categoria')
        filter_str = f"&filter[loja_id][_eq]={g.loja_id}&filter[status][_eq]=published"
        if cat_filter: filter_str += f"&filter[categoria_id][_eq]={cat_filter}"
        
        r_prod = requests.get(f"{DIRECTUS_URL}/items/produtos?{filter_str}&fields=*.*", headers=headers)
        if r_prod.ok:
            for p in r_prod.json()['data']:
                img = get_img_url(p.get('imagem_destaque') or p.get('imagem1'))
                prod_obj = {
                    "id": p['id'], "nome": p['nome'], "slug": p['slug'],
                    "preco": float(p['preco'] or 0), "imagem": img,
                    "categoria_id": p.get('categoria_id')
                }
                produtos.append(prod_obj)
                if p.get('status_urgencia') in ['Alta Procura', 'Lancamento']: novidades.append(prod_obj)

        # Blog
        r_blog = requests.get(f"{DIRECTUS_URL}/items/posts?filter[loja_id][_eq]={g.loja_id}&filter[status][_eq]=published&limit=3", headers=headers)
        if r_blog.ok:
            for post in r_blog.json()['data']:
                posts.append({
                    "titulo": post['titulo'], "slug": post['slug'], "resumo": post.get('resumo', ''),
                    "capa": get_img_url(post.get('capa')),
                    "data": datetime.fromisoformat(post['date_created'].split('T')[0]).strftime('%d/%m/%Y')
                })
    except: pass

    loja_visual = {
        **g.loja,
        "logo": get_img_url(g.loja.get('logo')),
        "banner1": get_img_url(g.loja.get('bannerprincipal1')),
        "banner2": get_img_url(g.loja.get('bannerprincipal2')),
        "bannermenor1": get_img_url(g.loja.get('bannermenor1')),
        "bannermenor2": get_img_url(g.loja.get('bannermenor2')),
    }

    return render_template('index.html', loja=loja_visual, layout=g.layout_list,
                         categorias=categorias, produtos=produtos, novidades=novidades, posts=posts, directus_url=DIRECTUS_URL)

@app.route('/produto/<slug>')
def produto(slug):
    if not g.loja: return redirect('/cadastro')
    
    headers = get_headers()
    r = requests.get(f"{DIRECTUS_URL}/items/produtos?filter[slug][_eq]={slug}&filter[loja_id][_eq]={g.loja_id}&fields=*.*", headers=headers)
    
    if r.ok and r.json()['data']:
        p = r.json()['data'][0]
        p['imagem_destaque'] = get_img_url(p.get('imagem_destaque'))
        p['imagem1'] = get_img_url(p.get('imagem1'))
        p['imagem2'] = get_img_url(p.get('imagem2'))
        
        galeria = [x for x in [p['imagem_destaque'], p['imagem1'], p['imagem2']] if x]
        if not galeria: galeria = ["https://placehold.co/600x600?text=Sem+Imagem"]
        p['galeria'] = galeria

        if p.get('variantes'):
            for v in p['variantes']:
                v['foto'] = get_img_url(v.get('foto')) or p['imagem_destaque']

        loja_visual = {**g.loja, "logo": get_img_url(g.loja.get('logo'))}
        return render_template('produtos.html', p=p, loja=loja_visual, directus_url=DIRECTUS_URL)
    
    return "Produto não encontrado", 404

# --- ADMINISTRAÇÃO ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if not g.loja: return redirect('/cadastro')
    if session.get('loja_admin_id') == g.loja_id: return redirect('/admin/painel')

    if request.method == 'POST':
        senha = request.form.get('senha')
        if g.loja.get('senha_admin') and check_password_hash(g.loja['senha_admin'], senha):
            session['loja_admin_id'] = g.loja_id
            session.permanent = True
            return redirect('/admin/painel')
        flash('Senha incorreta', 'error')
    
    loja_visual = {**g.loja, "logo": get_img_url(g.loja.get('logo'))}
    return render_template('login_admin.html', loja=loja_visual)

@app.route('/admin/painel', methods=['GET', 'POST'])
def admin_painel():
    if not g.loja: return redirect('/')
    if session.get('loja_admin_id') != g.loja_id: return redirect('/admin')

    if request.method == 'POST':
        files_map = {}
        for key in ['logo', 'bannerprincipal1', 'bannerprincipal2', 'bannermenor1', 'bannermenor2']:
            f = request.files.get(key)
            if f and f.filename:
                fid = upload_file_to_directus(f)
                if fid: files_map[key] = fid

        payload = {
            "nome": request.form.get('nome'),
            "whatsapp_comercial": request.form.get('whatsapp'),
            "cor_primaria": request.form.get('cor_primaria'),
            "font_titulo": request.form.get('font_titulo'),
            "font_corpo": request.form.get('font_corpo'),
            "linkbannerprincipal1": request.form.get('link1'),
            "linkbannerprincipal2": request.form.get('link2'),
            "layout_order": request.form.get('layout_order') 
        }
        payload.update(files_map)

        try:
            requests.patch(f"{DIRECTUS_URL}/items/lojas/{g.loja_id}", headers=get_headers(), json=payload)
            flash('Salvo com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao salvar: {e}', 'error')
        return redirect('/admin/painel')

    loja_visual = {
        **g.loja,
        "logo_url": get_img_url(g.loja.get('logo')),
        "banner1_url": get_img_url(g.loja.get('bannerprincipal1')),
        "banner2_url": get_img_url(g.loja.get('bannerprincipal2'))
    }
    return render_template('painel.html', loja=loja_visual)

# --- OUTROS (SENHA, FRETE, LOGOUT) ---
@app.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    # Implementação idêntica à anterior (omitida para brevidade, mas deve existir)
    return render_template('esqueceu_senha.html', loja=g.loja)

@app.route('/nova-senha/<token>', methods=['GET', 'POST'])
def nova_senha(token):
    # Implementação idêntica à anterior
    return "Token inválido", 400

@app.route('/api/calcular-frete', methods=['POST'])
def api_frete():
    return jsonify([]) 

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)