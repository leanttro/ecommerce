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

# --- CORREÇÃO DE ERRO 404 (BARRAS NA URL) ---
# Isso faz o sistema aceitar tanto "/loja/slug" quanto "/loja/slug/"
app.url_map.strict_slashes = False 

# Em produção, defina uma SECRET_KEY fixa no .env
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_super_segura_saas_2026")

# --- CONFIGURAÇÃO DE DOMÍNIO BASE ---
DOMINIO_BASE = "leanttro.com"

# --- CONFIGURAÇÕES GERAIS ---
# Remove barra final da URL para evitar erros de concatenação
DIRECTUS_URL = os.getenv("DIRECTUS_URL", "https://api2.leanttro.com").rstrip('/')
DIRECTUS_TOKEN = os.getenv("DIRECTUS_TOKEN", "") 
SUPERFRETE_TOKEN = os.getenv("SUPERFRETE_TOKEN", "")
SUPERFRETE_URL = os.getenv("SUPERFRETE_URL", "https://api.superfrete.com/api/v0/calculator")
CEP_ORIGEM_PADRAO = "01026000" # Fallback se a loja não tiver CEP configurado

# --- FUNÇÕES AUXILIARES ---
def get_headers():
    return {"Authorization": f"Bearer {DIRECTUS_TOKEN}", "Content-Type": "application/json"}

def get_upload_headers():
    # Para upload não se usa Content-Type json
    return {"Authorization": f"Bearer {DIRECTUS_TOKEN}"}

def get_img_url(image_id_or_obj):
    """Trata URLs de imagens vindas do Directus (ID, Objeto ou URL completa)"""
    if not image_id_or_obj: return ""
    if isinstance(image_id_or_obj, dict): return f"{DIRECTUS_URL}/assets/{image_id_or_obj.get('id')}"
    if isinstance(image_id_or_obj, str) and image_id_or_obj.startswith('http'): return image_id_or_obj
    return f"{DIRECTUS_URL}/assets/{image_id_or_obj}"

def upload_file_to_directus(file_storage):
    """Faz upload de arquivo para o Directus e retorna o ID"""
    try:
        url = f"{DIRECTUS_URL}/files"
        filename = secure_filename(file_storage.filename)
        files = {'file': (filename, file_storage, file_storage.mimetype)}
        
        response = requests.post(url, headers=get_upload_headers(), files=files)
        
        if response.status_code in [200, 201]:
            return response.json()['data']['id']
        else:
            print(f"Erro no Upload Directus: {response.text}")
    except Exception as e:
        print(f"Exceção no upload: {e}")
    return None

def gerar_slug(texto):
    if not texto: return ""
    import unicodedata
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto.lower().strip().replace(' ', '-').replace('/', '-').replace('.', '')

# --- MIDDLEWARE: IDENTIFICAÇÃO DA LOJA (PATH-BASED) ---
@app.before_request
def identificar_loja():
    """Identifica qual loja está sendo acessada baseada na URL /loja/<slug>"""
    
    # Ignora arquivos estáticos
    if request.path.startswith('/static'):
        return

    # Reinicia variáveis globais
    g.loja = None
    g.loja_id = None
    g.slug_atual = None
    g.layout_list = []

    # Lógica de Path: /loja/<slug>/...
    # Split da URL: ['', 'loja', 'slug', 'resto']
    path_parts = request.path.split('/')
    
    if len(path_parts) > 2 and path_parts[1] == 'loja':
        slug_url = path_parts[2]
        g.slug_atual = slug_url

        try:
            headers = get_headers()
            # Filtra pelo campo SLUG no banco de dados
            url = f"{DIRECTUS_URL}/items/lojas?filter[slug][_eq]={slug_url}&fields=*.*"
            resp = requests.get(url, headers=headers)
            
            if resp.status_code == 200 and len(resp.json()['data']) > 0:
                g.loja = resp.json()['data'][0]
                g.loja_id = g.loja['id']
                
                # Tratamento de Layout e Configs Visuais (Fallback se vazio)
                if not g.loja.get('layout_order'):
                    g.loja['layout_order'] = "banner,busca,categorias,produtos,banners_menores,novidades,blog,footer"
                
                # Configs Visuais Padrão
                if not g.loja.get('font_tamanho_base'): g.loja['font_tamanho_base'] = 16
                if not g.loja.get('cor_titulo'): g.loja['cor_titulo'] = "#111827"
                if not g.loja.get('cor_texto'): g.loja['cor_texto'] = "#374151"
                if not g.loja.get('cor_fundo'): g.loja['cor_fundo'] = "#ffffff"
                
                g.layout_list = g.loja['layout_order'].split(',')
                
                # Adiciona URL base da loja para uso nos templates
                g.loja['base_url'] = f"/loja/{slug_url}"

        except Exception as e:
            print(f"Erro Middleware: {e}")

# --- ROTA RAIZ DO SAAS ---
@app.route('/')
def home_saas():
    # Redireciona a raiz do domínio principal para o cadastro
    return redirect('/cadastro')

# --- ROTA DE CADASTRO (CRIAR NOVA LOJA) ---
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        slug_input = request.form.get('slug')
        
        # Garante slug limpo
        slug = slug_input.lower().strip().replace(' ', '-') if slug_input else ""
        
        email = request.form.get('email').strip()
        whatsapp = request.form.get('whatsapp', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        senha = request.form.get('senha')

        # Link agora é baseado em caminho
        link_loja = f"{DOMINIO_BASE}/loja/{slug}"

        # 1. Validações Básicas
        if not all([nome, slug, email, whatsapp, senha]):
            flash('Preencha todos os campos obrigatórios.', 'error')
            return render_template('cadastro.html')

        # 2. Verifica se já existe Slug ou Email
        headers = get_headers()
        filtro = f"?filter[_or][0][slug][_eq]={slug}&filter[_or][1][email][_eq]={email}"
        try:
            check = requests.get(f"{DIRECTUS_URL}/items/lojas{filtro}", headers=headers)
            if check.status_code == 200 and len(check.json()['data']) > 0:
                existing = check.json()['data'][0]
                if existing.get('slug') == slug:
                    flash(f'O endereço "{slug}" já está em uso. Escolha outro.', 'error')
                else:
                    flash('Este e-mail já possui uma loja cadastrada.', 'error')
                return render_template('cadastro.html')
        except Exception as e:
            print(f"Erro ao verificar existência: {e}")
            flash('Erro de conexão ao verificar disponibilidade.', 'error')
            return render_template('cadastro.html')

        # 3. Cria a Loja com Configurações Padrão
        senha_hash = generate_password_hash(senha)

        payload = {
            "status": "published",
            "nome": nome,
            "dominio": link_loja, # Salva referência
            "slug": slug,             
            "email": email,
            "whatsapp_comercial": whatsapp,
            "senha_admin": senha_hash,
            
            # Configurações Visuais Padrão
            "cor_primaria": "#db2777",
            "cor_titulo": "#111827",
            "cor_texto": "#374151",
            "cor_fundo": "#ffffff",
            "font_tamanho_base": 16,
            "font_titulo": "Poppins",
            "font_corpo": "Inter",
            "layout_order": "banner,busca,categorias,produtos,banners_menores,novidades,footer",
            
            "linkbannerprincipal1": "#",
            "linkbannerprincipal2": "#"
        }

        try:
            r = requests.post(f"{DIRECTUS_URL}/items/lojas", headers=headers, json=payload)
            
            if r.status_code in [200, 201]:
                data = r.json().get('data')
                novo_id = data['id']
                
                # --- LOGIN AUTOMÁTICO ---
                session['loja_admin_id'] = novo_id
                session.permanent = True
                
                flash('Loja criada com sucesso!', 'success')
                
                # --- REDIRECIONA PARA O PAINEL COM A NOVA URL ---
                return redirect(f"/loja/{slug}/admin/painel")
            else:
                try:
                    erro_msg = r.json().get('errors', [{'message': 'Erro desconhecido'}])[0]['message']
                except:
                    erro_msg = r.text
                flash(f'Erro ao criar loja: {erro_msg}', 'error')
                
        except Exception as e:
            print(f"Erro Exception Create: {e}")
            flash('Erro interno de conexão.', 'error')

    return render_template('cadastro.html')


# --- ROTA: INDEX (A VITRINE DA LOJA) ---
# Adicionado parametro loja_slug na rota
@app.route('/loja/<loja_slug>/')
def index(loja_slug):
    if not g.loja: 
        return "Loja não encontrada", 404

    headers = get_headers()
    
    # 1. Busca Categorias
    categorias = []
    try:
        url_cat = f"{DIRECTUS_URL}/items/categorias?filter[loja_id][_eq]={g.loja_id}&filter[status][_eq]=published&sort=sort"
        r_cat = requests.get(url_cat, headers=headers)
        if r_cat.status_code == 200: categorias = r_cat.json()['data']
    except: pass

    # 2. Busca Produtos
    cat_filter = request.args.get('categoria')
    busca_query = request.args.get('busca') 
    
    filter_str = f"filter[loja_id][_eq]={g.loja_id}&filter[status][_eq]=published"
    
    if cat_filter: 
        filter_str += f"&filter[categoria_id][_eq]={cat_filter}"
        
    if busca_query:
        filter_str += f"&filter[nome][_icontains]={busca_query}"

    produtos = []
    novidades = []

    try:
        url_prod = f"{DIRECTUS_URL}/items/produtos?{filter_str}&fields=*.*"
        r_prod = requests.get(url_prod, headers=headers)
        
        if r_prod.status_code == 200:
            raw_prods = r_prod.json()['data']
            for p in raw_prods:
                img = get_img_url(p.get('imagem_destaque') or p.get('imagem1'))
                
                variantes = []
                if p.get('variantes'):
                    for v in p['variantes']:
                        v_foto = get_img_url(v.get('foto')) if v.get('foto') else img
                        variantes.append({"nome": v.get('nome'), "foto": v_foto})

                try: preco_float = float(p.get('preco', 0))
                except: preco_float = 0.0
                
                try: estoque_val = int(p.get('estoque')) if p.get('estoque') is not None else 0
                except: estoque_val = 0

                prod_obj = {
                    "id": p['id'], "nome": p['nome'], "slug": p['slug'],
                    "preco": preco_float,
                    "imagem": img, "categoria_id": p.get('categoria_id'),
                    "variantes": variantes, "origem": p.get('origem'),
                    "urgencia": p.get('status_urgencia'), "classe_frete": p.get('classe_frete'),
                    "estoque": estoque_val, "consulte": p.get('consulte', False)
                }
                produtos.append(prod_obj)
                
                if p.get('status_urgencia') in ['Alta Procura', 'Lancamento']:
                    novidades.append(prod_obj)

    except Exception as e:
        print(f"Erro produtos: {e}")

    # 3. Busca Posts
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

    loja_visual = {
        **g.loja,
        "logo": get_img_url(g.loja.get('logo')),
        "banner1": get_img_url(g.loja.get('bannerprincipal1')),
        "banner2": get_img_url(g.loja.get('bannerprincipal2')),
        "bannermenor1": get_img_url(g.loja.get('bannermenor1')),
        "bannermenor2": get_img_url(g.loja.get('bannermenor2')),
        "slug_url": loja_slug # Passamos o slug para montar links no HTML
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
@app.route('/loja/<loja_slug>/produto/<slug>')
def produto(loja_slug, slug):
    if not g.loja: return "Loja não encontrada", 404

    headers = get_headers()
    url = f"{DIRECTUS_URL}/items/produtos?filter[slug][_eq]={slug}&filter[loja_id][_eq]={g.loja_id}&fields=*.*"
    r = requests.get(url, headers=headers)
    
    if r.status_code == 200 and r.json()['data']:
        p = r.json()['data'][0]
        
        p['imagem_destaque'] = get_img_url(p.get('imagem_destaque'))
        p['imagem1'] = get_img_url(p.get('imagem1'))
        p['imagem2'] = get_img_url(p.get('imagem2'))
        
        galeria = []
        if p.get('imagem_destaque'): galeria.append(p['imagem_destaque'])
        if p.get('imagem1'): galeria.append(p['imagem1'])
        if p.get('imagem2'): galeria.append(p['imagem2'])
        
        if not galeria:
            galeria = ["https://placehold.co/600x600?text=Sem+Imagem"]
            
        p['galeria'] = galeria

        if p.get('variantes'):
            for v in p['variantes']:
                v['foto'] = get_img_url(v.get('foto')) if v.get('foto') else p['imagem_destaque']

        try: p['preco'] = float(p.get('preco', 0))
        except: p['preco'] = 0.0
            
        try: p['estoque'] = int(p.get('estoque')) if p.get('estoque') is not None else 0
        except: p['estoque'] = 0

        loja_visual = {
            **g.loja,
            "logo": get_img_url(g.loja.get('logo')),
            "slug_url": loja_slug
        }

        return render_template('produtos.html', p=p, loja=loja_visual, directus_url=DIRECTUS_URL)
    
    return "Produto não encontrado nesta loja", 404


# --- ROTA: ADMIN LOGIN ---
@app.route('/loja/<loja_slug>/admin', methods=['GET', 'POST'])
def admin_login(loja_slug):
    if not g.loja:
        return "Loja não encontrada", 404

    if session.get('loja_admin_id') == g.loja_id:
        return redirect(f'/loja/{loja_slug}/admin/painel')

    if request.method == 'POST':
        senha = request.form.get('senha')
        
        if g.loja.get('senha_admin') and check_password_hash(g.loja['senha_admin'], senha):
            session['loja_admin_id'] = g.loja_id
            session.permanent = True
            return redirect(f'/loja/{loja_slug}/admin/painel')
        else:
            flash('Senha incorreta', 'error')
    
    loja_visual = {**g.loja, "logo": get_img_url(g.loja.get('logo')), "slug_url": loja_slug}
    return render_template('login_admin.html', loja=loja_visual)


# --- ROTA: PAINEL DE EDIÇÃO ---
@app.route('/loja/<loja_slug>/admin/painel', methods=['GET', 'POST'])
def admin_painel(loja_slug):
    if not g.loja: return redirect('/')
    
    if session.get('loja_admin_id') != g.loja_id:
        return redirect(f'/loja/{loja_slug}/admin')

    headers = get_headers()

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
            "cor_titulo": request.form.get('cor_titulo'), 
            "cor_texto": request.form.get('cor_texto'),
            "cor_fundo": request.form.get('cor_fundo'),
            "font_tamanho_base": request.form.get('font_tamanho_base'),
            "font_titulo": request.form.get('font_titulo'),
            "font_corpo": request.form.get('font_corpo'),
            "linkbannerprincipal1": request.form.get('link1'),
            "linkbannerprincipal2": request.form.get('link2'),
            "linkbannermenor1": request.form.get('linkbannermenor1'),
            "linkbannermenor2": request.form.get('linkbannermenor2'),
            "frase1": request.form.get('frase1'),
            "frase2": request.form.get('frase2'),
            "frase3": request.form.get('frase3'),
            "layout_order": request.form.get('layout_order'),
            "titulo_produtos": request.form.get('titulo_produtos'),
            "ocultar_produtos": True if request.form.get('ocultar_produtos') else False,
            "titulo_categorias": request.form.get('titulo_categorias'),
            "ocultar_categorias": True if request.form.get('ocultar_categorias') else False,
            "titulo_novidades": request.form.get('titulo_novidades'),
            "ocultar_novidades": True if request.form.get('ocultar_novidades') else False,
            "titulo_blog": request.form.get('titulo_blog'),
            "ocultar_blog": True if request.form.get('ocultar_blog') else False,
            "ocultar_busca": True if request.form.get('ocultar_busca') else False,
            "ocultar_banner": True if request.form.get('ocultar_banner') else False,
            "ocultar_banners_menores": True if request.form.get('ocultar_banners_menores') else False
        }
        
        payload.update(files_map)

        try:
            requests.patch(f"{DIRECTUS_URL}/items/lojas/{g.loja_id}", headers=headers, json=payload)
            flash('Loja atualizada com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao salvar: {e}', 'error')
        
        return redirect(f'/loja/{loja_slug}/admin/painel')

    categorias = []
    produtos = []
    posts = []

    try:
        r_cat = requests.get(f"{DIRECTUS_URL}/items/categorias?filter[loja_id][_eq]={g.loja_id}&sort=sort", headers=headers)
        if r_cat.status_code == 200: categorias = r_cat.json()['data']

        r_prod = requests.get(f"{DIRECTUS_URL}/items/produtos?filter[loja_id][_eq]={g.loja_id}&limit=100&sort=-date_created&fields=*.*", headers=headers)
        if r_prod.status_code == 200: 
            produtos = r_prod.json()['data']
            for p in produtos:
                p['imagem_destaque'] = get_img_url(p.get('imagem_destaque'))
                try: p['preco'] = float(p['preco']) if p.get('preco') else 0.0
                except: p['preco'] = 0.0

        r_post = requests.get(f"{DIRECTUS_URL}/items/posts?filter[loja_id][_eq]={g.loja_id}&limit=20&sort=-date_created&fields=id,titulo,date_created", headers=headers)
        if r_post.status_code == 200: posts = r_post.json()['data']
    except Exception as e:
        print(f"Erro ao carregar dados do painel: {e}")

    if g.loja.get('layout_order') and 'banners_menores' not in g.loja['layout_order']:
        g.loja['layout_order'] += ",banners_menores"

    loja_visual = {
        **g.loja,
        "logo_url": get_img_url(g.loja.get('logo')),
        "banner1_url": get_img_url(g.loja.get('bannerprincipal1')),
        "banner2_url": get_img_url(g.loja.get('bannerprincipal2')),
        "bannermenor1_url": get_img_url(g.loja.get('bannermenor1')),
        "bannermenor2_url": get_img_url(g.loja.get('bannermenor2')),
        "slug_url": loja_slug
    }

    return render_template('painel.html', 
                           loja=loja_visual, 
                           categorias=categorias, 
                           produtos=produtos, 
                           posts=posts)

# --- CRUD CATEGORIAS ---
@app.route('/loja/<loja_slug>/admin/categoria/salvar', methods=['POST'])
def admin_salvar_categoria(loja_slug):
    if session.get('loja_admin_id') != g.loja_id: return redirect('/')
    
    nome = request.form.get('nome')
    cat_id = request.form.get('id')
    
    if not nome:
        flash('Nome da categoria é obrigatório', 'error')
        return redirect(f'/loja/{loja_slug}/admin/painel')

    headers = get_headers()
    payload = {
        "nome": nome,
        "slug": gerar_slug(nome),
        "loja_id": g.loja_id,
        "status": "published"
    }

    try:
        if cat_id:
            requests.patch(f"{DIRECTUS_URL}/items/categorias/{cat_id}", headers=headers, json=payload)
            flash('Categoria atualizada!', 'success')
        else:
            requests.post(f"{DIRECTUS_URL}/items/categorias", headers=headers, json=payload)
            flash('Categoria criada!', 'success')
    except Exception as e:
        flash(f'Erro ao salvar categoria: {e}', 'error')

    return redirect(f'/loja/{loja_slug}/admin/painel')

@app.route('/loja/<loja_slug>/admin/categoria/excluir/<int:id>')
def admin_excluir_categoria(loja_slug, id):
    if session.get('loja_admin_id') != g.loja_id: return redirect('/')
    requests.delete(f"{DIRECTUS_URL}/items/categorias/{id}", headers=get_headers())
    flash('Categoria removida!', 'success')
    return redirect(f'/loja/{loja_slug}/admin/painel')


# --- CRUD PRODUTOS ---
@app.route('/loja/<loja_slug>/admin/produto/salvar', methods=['POST'])
def admin_salvar_produto(loja_slug):
    if session.get('loja_admin_id') != g.loja_id: return redirect('/')
    
    prod_id = request.form.get('id')
    nome = request.form.get('nome')
    
    cat_id = request.form.get('categoria_id')
    if not cat_id or cat_id == "": cat_id = None
        
    preco = request.form.get('preco')
    try: preco = float(preco) if preco else 0
    except: preco = 0
        
    estoque = request.form.get('estoque')
    try: estoque = int(estoque) if estoque else 0
    except: estoque = 0
    
    consulte_form = request.form.get('consulte')
    consulte = True if consulte_form == 'on' else False

    payload = {
        "status": "published",
        "loja_id": g.loja_id,
        "nome": nome,
        "preco": preco,
        "estoque": estoque,
        "consulte": consulte,
        "descricao": request.form.get('descricao'),
        "categoria_id": cat_id
    }
    
    if not prod_id and nome:
        payload["slug"] = gerar_slug(nome) + "-" + str(uuid.uuid4())[:4]

    f = request.files.get('imagem')
    if f and f.filename:
        fid = upload_file_to_directus(f)
        if fid: payload['imagem_destaque'] = fid

    headers = get_headers()
    try:
        if prod_id:
            requests.patch(f"{DIRECTUS_URL}/items/produtos/{prod_id}", headers=headers, json=payload)
            flash('Produto atualizado!', 'success')
        else:
            requests.post(f"{DIRECTUS_URL}/items/produtos", headers=headers, json=payload)
            flash('Produto criado!', 'success')
    except Exception as e:
        flash(f'Erro interno ao salvar produto: {e}', 'error')
        
    return redirect(f'/loja/{loja_slug}/admin/painel')

@app.route('/loja/<loja_slug>/admin/produto/excluir/<int:id>')
def admin_excluir_produto(loja_slug, id):
    if session.get('loja_admin_id') != g.loja_id: return redirect('/')
    requests.delete(f"{DIRECTUS_URL}/items/produtos/{id}", headers=get_headers())
    flash('Produto removido!', 'success')
    return redirect(f'/loja/{loja_slug}/admin/painel')


# --- CRUD POSTS (BLOG) ---
@app.route('/loja/<loja_slug>/admin/post/salvar', methods=['POST'])
def admin_salvar_post(loja_slug):
    if session.get('loja_admin_id') != g.loja_id: return redirect('/')
    
    post_id = request.form.get('id')
    titulo = request.form.get('titulo')
    
    payload = {
        "status": "published",
        "loja_id": g.loja_id,
        "titulo": titulo,
        "resumo": request.form.get('resumo'),
        "conteudo": request.form.get('conteudo')
    }

    if not post_id and titulo:
        payload["slug"] = gerar_slug(titulo)

    f = request.files.get('capa')
    if f and f.filename:
        fid = upload_file_to_directus(f)
        if fid: payload['capa'] = fid

    headers = get_headers()
    try:
        if post_id:
            requests.patch(f"{DIRECTUS_URL}/items/posts/{post_id}", headers=headers, json=payload)
            flash('Post atualizado!', 'success')
        else:
            requests.post(f"{DIRECTUS_URL}/items/posts", headers=headers, json=payload)
            flash('Post criado!', 'success')
    except Exception as e:
        flash(f'Erro ao salvar post: {e}', 'error')

    return redirect(f'/loja/{loja_slug}/admin/painel')

@app.route('/loja/<loja_slug>/admin/post/excluir/<int:id>')
def admin_excluir_post(loja_slug, id):
    if session.get('loja_admin_id') != g.loja_id: return redirect('/')
    requests.delete(f"{DIRECTUS_URL}/items/posts/{id}", headers=get_headers())
    flash('Post removido!', 'success')
    return redirect(f'/loja/{loja_slug}/admin/painel')


# --- ROTA: RECUPERAR SENHA ---
@app.route('/loja/<loja_slug>/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha(loja_slug):
    if not g.loja: return redirect('/')

    if request.method == 'POST':
        email = request.form.get('email')
        
        if email == g.loja.get('email'):
            token = str(uuid.uuid4())
            expiracao = (datetime.now() + timedelta(hours=1)).isoformat()
            
            requests.patch(f"{DIRECTUS_URL}/items/lojas/{g.loja_id}", 
                         headers=get_headers(),
                         json={'reset_token': token, 'reset_expires': expiracao})
            
            link = f"{DOMINIO_BASE}/loja/{loja_slug}/nova-senha/{token}"
            print(f"--- LINK RECUPERAÇÃO: {link} ---")
            
            flash('Link de recuperação enviado para seu e-mail.', 'success')
        else:
            flash('E-mail não corresponde ao cadastro desta loja.', 'error')
    
    loja_visual = {**g.loja, "logo": get_img_url(g.loja.get('logo')), "slug_url": loja_slug}
    return render_template('esqueceu_senha.html', loja=loja_visual)

@app.route('/loja/<loja_slug>/nova-senha/<token>', methods=['GET', 'POST'])
def nova_senha(loja_slug, token):
    r = requests.get(f"{DIRECTUS_URL}/items/lojas?filter[reset_token][_eq]={token}", headers=get_headers())
    data = r.json().get('data')
    
    if not data: 
        return "Link inválido ou expirado.", 400
    
    loja_alvo = data[0]

    if request.method == 'POST':
        nova = request.form.get('senha')
        hash_senha = generate_password_hash(nova)
        
        requests.patch(f"{DIRECTUS_URL}/items/lojas/{loja_alvo['id']}", 
                     headers=get_headers(),
                     json={'senha_admin': hash_senha, 'reset_token': None, 'reset_expires': None})
        
        flash('Senha alterada com sucesso! Faça login.', 'success')
        return redirect(f'/loja/{loja_slug}/admin')

    return render_template('nova_senha.html', token=token)


# --- API FRETE ---
@app.route('/api/calcular-frete', methods=['POST'])
def api_frete():
    return jsonify([]) 


# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)