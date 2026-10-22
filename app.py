import hashlib
import base64
from datetime import datetime

import streamlit as st

from supabase_client import (
    current_user_id,
    delete_row,
    ensure_studio,
    get_supabase_client,
    insert_row,
    load_workspace,
    sign_in,
    sign_out,
    sign_up,
    signed_photo_url,
    update_row,
    upsert_row,
    upload_photo,
    verify_email_token,
)


CATALOGO_INICIAL = [
    {"id": 1, "nome": "Aplicação Zero (Gel)", "valor": 180.0, "duracao": "2h 30m", "cor": "#E91E63"},
    {"id": 2, "nome": "Manutenção de Gel", "valor": 110.0, "duracao": "1h 30m", "cor": "#9C27B0"},
    {"id": 3, "nome": "Banho de Gel", "valor": 90.0, "duracao": "1h 00m", "cor": "#03A9F4"},
    {"id": 4, "nome": "Conserto por Unha", "valor": 20.0, "duracao": "0h 20m", "cor": "#4CAF50"},
]
ETAPAS_EVOLUCAO = ("Antes", "Estrutura Pronta", "Resultado Final")


def inicializar_estado():
    defaults = {
        "configurado": False,
        "nome_estudio": "",
        "cor_primaria": "#e91e63",
        "logo_arquivo": None,
        "fundo_arquivo": None,
        "fundo_opacidade": 0.92,
        "modulos": {"agenda": True, "caixa": True, "anamnese": True},
        "caixa_registros": [],
        "clientes": [],
        "fichas_anamnese": {},
        "galeria_evolucao": {},
        "catalogo_servicos": [item.copy() for item in CATALOGO_INICIAL],
        "agendamentos": [],
        "auth_user": None,
        "demo_mode": False,
        "studio_id": None,
        "workspace_loaded": False,
        "client_records": {},
        "service_records": {},
    }
    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def aplicar_estilos():
    cor = st.session_state.cor_primaria
    fundo = st.session_state.fundo_arquivo
    fundo_css = ""
    if fundo is not None:
        mime = getattr(fundo, "type", "image/jpeg")
        imagem = base64.b64encode(fundo.getvalue()).decode("ascii")
        fundo_css = (
            f"background-image: linear-gradient(rgba(255,250,251,{st.session_state.fundo_opacidade}), "
            f"rgba(255,250,251,{st.session_state.fundo_opacidade})), url('data:{mime};base64,{imagem}');"
            "background-size: cover; background-attachment: fixed; background-position: center;"
        )
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
        :root {{ --brand: {cor}; --rose-gold: #D4838D; --rose-deep: #B85C68; --ink: #2D2727; --muted: #7A6E76; --nude: #FDFBFB; --line: #F3E8E8; }}
        .stApp {{ background: linear-gradient(135deg, #fffafb 0%, #f9f4f5 100%); {fundo_css} color: var(--ink); font-family: 'Poppins', sans-serif; }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stSidebar"] {{ background: #fff; border-right: 1px solid #f0e4e8; }}
        [data-testid="stSidebar"] * {{ font-family: 'Poppins', sans-serif; }}
        h1, h2, h3, h4 {{ font-family: 'Playfair Display', serif !important; color: var(--ink); letter-spacing: -.02em; }}
        p, label, input, textarea, button, [data-testid="stMetricValue"] {{ font-family: 'Poppins', sans-serif !important; }}
        [data-testid="stMetric"] {{ background: #fff; border: 1px solid var(--line); border-radius: 20px; padding: 1rem; box-shadow: 0 10px 30px rgba(180, 100, 110, .05); }}
        [data-testid="stVerticalBlockBorderWrapper"] {{ border: 1px solid var(--line); border-radius: 20px; background: rgba(255,255,255,.94); box-shadow: 0 10px 30px rgba(180, 100, 110, .05); }}
        [data-testid="stExpander"] {{ border: 1px solid var(--line); border-radius: 20px; background: rgba(255,255,255,.88); box-shadow: 0 10px 30px rgba(180, 100, 110, .04); }}
        [data-testid="stSidebar"] .stRadio label {{ border-radius: 10px; padding: .3rem .5rem; }}
        .stButton > button, .stFormSubmitButton > button {{
            width: 100%; border-radius: 14px; font-weight: 600; min-height: 2.8rem;
            letter-spacing: .02em; background: linear-gradient(135deg, var(--rose-gold), var(--rose-deep));
            color: white; border: 0; box-shadow: 0 6px 20px rgba(184, 92, 104, .25); transition: all .3s ease;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            transform: translateY(-2px); box-shadow: 0 8px 25px rgba(184, 92, 104, .4);
            background: linear-gradient(135deg, var(--rose-deep), var(--rose-gold)); color: white;
        }}
        [data-testid="stFileUploaderDropzone"] {{ border-radius: 14px; background: var(--nude); }}
        input, select, textarea {{ border-radius: 12px !important; border: 1px solid #E6D5D5 !important; background: #FAFAFA !important; }}
        input:focus, select:focus, textarea:focus {{ border-color: var(--rose-deep) !important; box-shadow: 0 0 0 2px rgba(184, 92, 104, .2) !important; }}
        .card {{ background: rgba(255,255,255,.92); border: 1px solid var(--line); border-radius: 20px; padding: .9rem 1rem; margin: .6rem 0; box-shadow: 0 10px 30px rgba(180, 100, 110, .05); }}
        .muted {{ color: var(--muted); font-size: .85rem; }}
        .stButton > button, .stFormSubmitButton > button {{
            font-size: .9rem;
        }}
        .service-pill {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 7px; }}
        .eyebrow {{ color: var(--rose-deep); text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; font-weight: 700; }}
        .hero {{ position: relative; overflow: hidden; background: linear-gradient(120deg, rgba(255,255,255,.94), rgba(255,241,246,.72)); border: 1px solid #f1dfe6; border-radius: 28px; padding: 1.5rem; margin: .4rem 0 1.3rem; box-shadow: 0 18px 42px rgba(80, 35, 54, .08); }}
        .hero::after {{ content: '✦'; position: absolute; right: 8%; top: 8%; color: var(--brand); font-size: 5rem; opacity: .12; }}
        .hero-title {{ font-family: 'Playfair Display', serif; font-size: clamp(2rem, 6vw, 3.5rem); line-height: 1.03; max-width: 620px; }}
        .hero-copy {{ color: var(--muted); max-width: 560px; margin: .7rem 0 0; }}
        .status-pill {{ display: inline-block; border-radius: 999px; padding: .3rem .65rem; font-size: .72rem; font-weight: 700; background: #fce8ef; color: #a51f55; }}
        .status-pill.success {{ background: #e4f6ee; color: #18734d; }}
        .status-pill.warning {{ background: #fff2d9; color: #91651c; }}
        .quick-action {{ background: rgba(255,255,255,.78); border: 1px solid #f1dfe6; border-radius: 16px; padding: .8rem; text-align: center; }}
        @media (max-width: 640px) {{
            .block-container {{ padding: 1.2rem .8rem 4rem; }}
            h1 {{ font-size: 2rem !important; }} h2 {{ font-size: 1.55rem !important; }}
            [data-testid="column"] {{ width: 100% !important; flex: 1 1 100% !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def cadastrar_cliente(nome):
    nome = nome.strip()
    if nome and nome.casefold() not in {c.casefold() for c in st.session_state.clientes}:
        st.session_state.clientes.append(nome)
    return nome


def persistente() -> bool:
    return not st.session_state.demo_mode and get_supabase_client() is not None


def executar_persistencia(operacao):
    try:
        return operacao()
    except Exception as error:
        st.error(f"Não foi possível sincronizar este dado: {error}")
        return None


def carregar_workspace_persistente():
    if st.session_state.workspace_loaded or not persistente():
        return
    workspace = executar_persistencia(load_workspace)
    if workspace is None:
        return
    studio = workspace["studio"]
    st.session_state.studio_id = studio["id"]
    st.session_state.nome_estudio = studio["name"]
    st.session_state.cor_primaria = studio["primary_color"]
    st.session_state.clientes = [item["name"] for item in workspace["clients"]]
    st.session_state.client_records = {item["name"]: item for item in workspace["clients"]}
    st.session_state.service_records = {item["id"]: item for item in workspace["services"]}
    st.session_state.catalogo_servicos = [
        {
            "id": item["id"],
            "nome": item["name"],
            "valor": float(item["price"]),
            "duracao": item["duration"],
            "cor": item["color"],
        }
        for item in workspace["services"]
    ]
    if persistente() and not st.session_state.catalogo_servicos:
        for item in CATALOGO_INICIAL:
            salvo = executar_persistencia(
                lambda item=item: insert_row(
                    "services",
                    {
                        "studio_id": st.session_state.studio_id,
                        "name": item["nome"],
                        "price": item["valor"],
                        "duration": item["duracao"],
                        "color": item["cor"],
                    },
                )
            )
            if salvo:
                st.session_state.catalogo_servicos.append({
                    "id": salvo["id"],
                    "nome": salvo["name"],
                    "valor": float(salvo["price"]),
                    "duracao": salvo["duration"],
                    "cor": salvo["color"],
                })
    st.session_state.agendamentos = [
        {
            "id": item["id"],
            "client_id": item["client_id"],
            "service_id": item["service_id"],
            "cliente": next((c["name"] for c in workspace["clients"] if c["id"] == item["client_id"]), "Cliente"),
            "servico": next((s["name"] for s in workspace["services"] if s["id"] == item["service_id"]), "Serviço"),
            "data": item["appointment_date"],
            "horario": item["appointment_time"][:5],
            "valor": float(item["value"]),
            "pagamento": item["payment_method"],
            "cor": next((s["color"] for s in workspace["services"] if s["id"] == item["service_id"]), st.session_state.cor_primaria),
            "status": item["status"],
        }
        for item in workspace["appointments"]
    ]
    st.session_state.caixa_registros = [
        {
            "id": item["id"],
            "appointment_id": item["appointment_id"],
            "data": item["entry_date"],
            "cliente": next((c["name"] for c in workspace["clients"] if c["id"] == item["client_id"]), "Cliente"),
            "servico": item["service_name"],
            "valor": float(item["value"]),
            "pagamento": item["payment_method"],
        }
        for item in workspace["cash"]
    ]
    st.session_state.fichas_anamnese = {
        next((c["name"] for c in workspace["clients"] if c["id"] == item["client_id"]), "Cliente"): {
            "cliente": next((c["name"] for c in workspace["clients"] if c["id"] == item["client_id"]), "Cliente"),
            "tipos_lamina": item["nail_types"],
            "observacoes": item["observations"] or "",
            "alergias": item["allergies"] or "",
            "saude": item["health_conditions"],
            "detalhes_saude": item["health_details"] or "",
            "assinatura": item["signature"],
            "aceite": item["accepted"],
            "id": item["id"],
        }
        for item in workspace["anamneses"]
    }
    st.session_state.galeria_evolucao = {}
    for item in workspace["photos"]:
        cliente = next((c["name"] for c in workspace["clients"] if c["id"] == item["client_id"]), "Cliente")
        url = executar_persistencia(lambda path=item["storage_path"]: signed_photo_url(path))
        st.session_state.galeria_evolucao.setdefault(cliente, []).append({
            "id": item["id"],
            "etapa": item["stage"],
            "nome": item["file_name"],
            "url": url,
            "data": item["created_at"][:16].replace("T", " "),
        })
    st.session_state.workspace_loaded = True


def persistir_cliente(nome: str, telefone: str = "") -> dict | None:
    if not persistente():
        return None
    client = executar_persistencia(
        lambda: insert_row("clients", {"studio_id": st.session_state.studio_id, "name": nome, "phone": telefone or None})
    )
    return client


def cliente_id_por_nome(nome: str) -> str | None:
    registro = st.session_state.client_records.get(nome)
    return registro["id"] if registro else None


def garantir_cliente_persistente(nome: str, telefone: str = "") -> str | None:
    client_id = cliente_id_por_nome(nome)
    if client_id:
        return client_id
    registro = persistir_cliente(nome, telefone)
    if registro:
        st.session_state.client_records[nome] = registro
        return registro["id"]
    return None


def render_autenticacao():
    st.markdown(
        '<meta name="referrer" content="no-referrer">'
        '<meta http-equiv="Referrer-Policy" content="no-referrer">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero"><div class="eyebrow">Casal da Unha · Área segura</div>'
        '<div class="hero-title">Seu estúdio, organizado com intenção ✨</div>'
        '<div class="hero-copy">Entre para acessar agenda, clientes, fichas técnicas e evolução visual em um espaço individual.</div></div>',
        unsafe_allow_html=True,
    )
    supabase_configurado = get_supabase_client() is not None
    if not supabase_configurado:
        st.warning(
            "Modo local de demonstração: configure o Supabase antes de publicar este link no Instagram. "
            "Neste modo, os dados ficam apenas na sessão atual."
        )
        if st.button("Entrar no modo demonstração"):
            st.session_state.demo_mode = True
            st.session_state.auth_user = {"email": "demo@casaldaunha.local"}
            st.rerun()
        return

    token_hash = st.query_params.get("token_hash")
    confirmation_type = st.query_params.get("type", "signup")
    if token_hash and "pending_email_token" not in st.session_state:
        st.session_state.pending_email_token = token_hash
        st.session_state.pending_email_token_type = confirmation_type
        st.query_params.clear()
        st.rerun()

    pending_token = st.session_state.pop("pending_email_token", None)
    pending_type = st.session_state.pop("pending_email_token_type", "signup")
    if pending_token:
        usuario, erro = verify_email_token(pending_token, pending_type)
        if erro:
            st.error(erro)
        else:
            st.session_state.auth_user = usuario
            st.success("E-mail confirmado. Sua conta está pronta.")
            st.rerun()
        return

    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar minha conta"])
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("E-mail", autocomplete="email")
            senha = st.text_input("Senha", type="password", autocomplete="current-password")
            if st.form_submit_button("Entrar no meu estúdio"):
                if not email.strip() or not senha:
                    st.error("Informe e-mail e senha.")
                else:
                    usuario, erro = sign_in(email, senha)
                    if erro:
                        st.error(erro)
                    else:
                        st.session_state.auth_user = usuario
                        st.session_state.demo_mode = False
                        st.rerun()
    with tab_cadastro:
        with st.form("signup_form"):
            email = st.text_input("E-mail profissional", key="signup_email")
            senha = st.text_input("Crie uma senha", type="password", key="signup_password")
            confirmacao = st.text_input("Confirme sua senha", type="password")
            if st.form_submit_button("Criar conta"):
                if len(senha) < 8:
                    st.error("Use uma senha com pelo menos 8 caracteres.")
                elif senha != confirmacao:
                    st.error("As senhas não conferem.")
                else:
                    usuario, erro = sign_up(email, senha)
                    if erro:
                        st.error(erro)
                    else:
                        st.success("Conta criada. Verifique seu e-mail para confirmar o acesso.")
                        if usuario is not None and st.session_state.get("supabase_session"):
                            st.session_state.auth_user = usuario
                            st.rerun()


def render_usuario_sidebar():
    usuario = st.session_state.auth_user
    email = usuario.get("email", "modo demonstração") if isinstance(usuario, dict) else getattr(usuario, "email", "usuária")
    st.sidebar.caption(f"✦ {email}")
    if st.sidebar.button("Sair", key="logout_button"):
        if not st.session_state.demo_mode:
            sign_out()
        st.session_state.auth_user = None
        st.session_state.demo_mode = False
        st.rerun()


def render_onboarding():
    st.subheader("Bem-vinda ao seu painel personalizado! 💅")
    st.write("Deixe o aplicativo com a cara do seu estúdio.")
    with st.form("form_onboarding"):
        nome = st.text_input("Nome do seu estúdio", placeholder="Ex.: Studio Marina Nails")
        cor = st.color_picker("Cor principal do app", st.session_state.cor_primaria)
        st.write("**Quais funções você quer usar agora?**")
        agenda = st.checkbox("📅 Agenda & Clientes", value=True)
        caixa = st.checkbox("💰 Controle de Caixa Autônomo", value=True)
        anamnese = st.checkbox("📄 Anamnese & Fotos", value=True)
        if st.form_submit_button("🚀 Criar meu app"):
            if not nome.strip():
                st.warning("Por favor, digite o nome do seu estúdio.")
                return
            st.session_state.nome_estudio = nome.strip()
            st.session_state.cor_primaria = cor
            st.session_state.modulos = {
                "agenda": agenda,
                "caixa": caixa,
                "anamnese": anamnese,
            }
            if persistente():
                studio = executar_persistencia(
                    lambda: ensure_studio(st.session_state.nome_estudio, st.session_state.cor_primaria)
                )
                if studio:
                    st.session_state.studio_id = studio["id"]
            st.session_state.configurado = True
            st.rerun()


def render_inicio():
    st.markdown('<div class="eyebrow">Visão geral do estúdio</div>', unsafe_allow_html=True)
    st.markdown(
        f'<section class="hero"><div class="hero-title">Olá, {st.session_state.nome_estudio} ✨</div>'
        '<div class="hero-copy">Seu espaço de gestão para criar experiências impecáveis, acompanhar cada detalhe e fazer seu estúdio crescer.</div></section>',
        unsafe_allow_html=True,
    )
    if st.session_state.modulos["caixa"]:
        st.markdown("### 📊 Resumo rápido de hoje")
        hoje = datetime.now().strftime("%d/%m/%Y")
        total = sum(r["valor"] for r in st.session_state.caixa_registros if r["data"] == hoje)
        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento hoje", f"R$ {total:.2f}")
        col2.metric(
            "Agendamentos ativos",
            len([a for a in st.session_state.agendamentos if a.get("status", "").casefold() == "agendado"]),
        )
        col3.metric("Serviços ativos", len(st.session_state.catalogo_servicos))
    if st.session_state.modulos["anamnese"]:
        st.caption(f"{len(st.session_state.fichas_anamnese)} ficha(s) e {len(st.session_state.clientes)} cliente(s) cadastrada(s).")
    col_agenda, col_ficha, col_catalogo = st.columns(3)
    with col_agenda:
        st.markdown('<div class="quick-action">📅<br><b>Agenda</b><br><span class="muted">Organize seu dia</span></div>', unsafe_allow_html=True)
    with col_ficha:
        st.markdown('<div class="quick-action">📝<br><b>Fichas</b><br><span class="muted">Conheça sua cliente</span></div>', unsafe_allow_html=True)
    with col_catalogo:
        st.markdown('<div class="quick-action">💅<br><b>Serviços</b><br><span class="muted">Seu menu de beleza</span></div>', unsafe_allow_html=True)
    agendamentos = [
        a for a in st.session_state.agendamentos
        if a.get("status", "").casefold() == "agendado"
    ]
    if agendamentos:
        st.markdown("### ✦ Próximos atendimentos")
        for item in agendamentos[:3]:
            st.markdown(
                f'<div class="card"><span class="service-pill" style="background:{item.get("cor", st.session_state.cor_primaria)}"></span>'
                f'<b>{item["cliente"]}</b> · {item["servico"]}'
                f'<span class="status-pill" style="float:right">{item["data"]} · {item["horario"]}</span></div>',
                unsafe_allow_html=True,
            )


def obter_servico(servico_id):
    return next((s for s in st.session_state.catalogo_servicos if s["id"] == servico_id), None)


def render_agenda():
    st.markdown('<div class="eyebrow">Rotina do estúdio</div>', unsafe_allow_html=True)
    st.header("📅 Agenda inteligente")
    if not st.session_state.catalogo_servicos:
        st.warning("Cadastre ao menos um serviço em Configurações para lançar atendimentos.")
        return
    tab_novo, tab_lista = st.tabs(["➕ Novo agendamento", "📋 Próximos atendimentos"])

    with tab_novo:
        with st.form("form_novo_agendamento"):
            st.subheader("Agendar cliente")
            cliente = st.text_input("Nome da cliente")
            telefone = st.text_input("WhatsApp da cliente", placeholder="(00) 00000-0000")
            servico_nome = st.selectbox(
                "Serviço",
                [s["nome"] for s in st.session_state.catalogo_servicos],
            )
            servico = next(s for s in st.session_state.catalogo_servicos if s["nome"] == servico_nome)
            st.caption(f"● {servico['duracao']} · R$ {servico['valor']:.2f}")
            col_data, col_hora = st.columns(2)
            with col_data:
                data_atendimento = st.date_input("Data do atendimento")
            with col_hora:
                horario_atendimento = st.time_input("Horário")
            valor = st.number_input("Valor combinado (R$)", min_value=0.0, value=float(servico["valor"]), step=5.0)
            pagamento = st.selectbox(
                "Forma de pagamento prevista",
                ["Pix / Dinheiro", "Cartão de Crédito", "Cartão de Débito"],
            )
            if st.form_submit_button("📅 Confirmar agendamento"):
                if not cliente.strip():
                    st.error("Informe o nome da cliente.")
                else:
                    cliente = cadastrar_cliente(cliente)
                    client_id = garantir_cliente_persistente(cliente, telefone)
                    dados_agendamento = {
                        "studio_id": st.session_state.studio_id,
                        "client_id": client_id,
                        "service_id": servico["id"],
                        "appointment_date": data_atendimento.isoformat(),
                        "appointment_time": horario_atendimento.strftime("%H:%M:%S"),
                        "value": valor,
                        "payment_method": pagamento,
                        "status": "Agendado",
                    }
                    salvo = (
                        executar_persistencia(lambda: insert_row("appointments", dados_agendamento))
                        if persistente() else None
                    )
                    novo_id = salvo["id"] if salvo else max((a.get("id", 0) for a in st.session_state.agendamentos), default=0) + 1
                    st.session_state.agendamentos.append({
                        "id": novo_id,
                        "client_id": client_id,
                        "service_id": servico["id"],
                        "cliente": cliente,
                        "telefone": telefone.strip(),
                        "servico": servico["nome"],
                        "data": data_atendimento.strftime("%d/%m/%Y"),
                        "horario": horario_atendimento.strftime("%H:%M"),
                        "valor": valor,
                        "pagamento": pagamento,
                        "cor": servico["cor"],
                        "status": "Agendado",
                    })
                    st.success(f"Agendamento de {cliente} salvo com sucesso!")
                    st.rerun()

    with tab_lista:
        st.subheader("⏰ Seus próximos atendimentos")
        agendados = [
            a for a in st.session_state.agendamentos
            if a.get("status", "").casefold() == "agendado"
        ]
        if not agendados:
            st.info("Nenhum atendimento agendado no momento.")
        for agendamento in agendados:
            with st.container(border=True):
                st.markdown(
                    f'<span class="service-pill" style="background:{agendamento.get("cor", st.session_state.cor_primaria)}"></span>'
                    f'<b>{agendamento["cliente"]}</b> · {agendamento["servico"]}<br>'
                    f'<span class="muted">📅 {agendamento["data"]} às {agendamento["horario"]}'
                    f' · 💰 R$ {agendamento["valor"]:.2f}'
                    f'{" · 📱 " + agendamento["telefone"] if agendamento.get("telefone") else ""}</span>',
                    unsafe_allow_html=True,
                )
                col_concluir, col_reagendar, col_cancelar = st.columns(3)
                with col_concluir:
                    concluir = st.button("✅ Concluir", key=f"concluir_{agendamento['id']}")
                with col_reagendar:
                    reagendar = st.button("🔁 Reagendar", key=f"reagendar_{agendamento['id']}")
                with col_cancelar:
                    cancelar = st.button("🚫 Falta/cancelar", key=f"cancelar_{agendamento['id']}")
                if concluir:
                    dados_caixa = {
                        "studio_id": st.session_state.studio_id,
                        "appointment_id": agendamento["id"],
                        "client_id": agendamento.get("client_id"),
                        "service_name": agendamento["servico"],
                        "entry_date": datetime.strptime(agendamento["data"], "%d/%m/%Y").date().isoformat(),
                        "value": agendamento["valor"],
                        "payment_method": agendamento["pagamento"],
                    }
                    salvo = (
                        executar_persistencia(lambda: insert_row("cash_entries", dados_caixa))
                        if persistente() else None
                    )
                    st.session_state.caixa_registros.append({
                        "id": salvo["id"] if salvo else None,
                        "appointment_id": agendamento["id"],
                        "data": agendamento["data"],
                        "cliente": agendamento["cliente"],
                        "servico": agendamento["servico"],
                        "valor": agendamento["valor"],
                        "pagamento": agendamento["pagamento"],
                    })
                    if persistente():
                        executar_persistencia(lambda: update_row("appointments", agendamento["id"], {"status": "Concluído"}))
                    agendamento["status"] = "Concluído"
                    st.success("Atendimento concluído e lançado no caixa!")
                    st.rerun()
                if reagendar:
                    agendamento["status"] = "Reagendado"
                    if persistente():
                        executar_persistencia(lambda: update_row("appointments", agendamento["id"], {"status": "Reagendado"}))
                    st.info("Atendimento marcado para reagendamento.")
                    st.rerun()
                if cancelar:
                    agendamento["status"] = "Cancelado"
                    if persistente():
                        executar_persistencia(lambda: update_row("appointments", agendamento["id"], {"status": "Cancelado"}))
                    st.warning("Atendimento marcado como falta/cancelado.")
                    st.rerun()


def render_caixa():
    st.header("💰 Controle de caixa autônomo")
    if not st.session_state.caixa_registros:
        st.info("Nenhum atendimento registrado ainda.")
        return
    st.subheader("Histórico de lançamentos")
    for registro in reversed(st.session_state.caixa_registros):
        st.markdown(
            f"- **{registro['cliente']}** | {registro['servico']} | "
            f"**R$ {registro['valor']:.2f}** ({registro['pagamento']})"
        )
    total = sum(r["valor"] for r in st.session_state.caixa_registros)
    st.divider()
    st.metric("Total acumulado", f"R$ {total:.2f}")


def salvar_foto(cliente, etapa, arquivo):
    conteudo = arquivo.getvalue()
    foto_id = hashlib.sha256(conteudo).hexdigest()
    fotos_cliente = st.session_state.galeria_evolucao.setdefault(cliente, [])
    if not any(f["id"] == foto_id and f["etapa"] == etapa for f in fotos_cliente):
        url = None
        if persistente():
            user_id = current_user_id()
            client_id = garantir_cliente_persistente(cliente)
            if user_id and client_id:
                caminho = f"{user_id}/{client_id}/{etapa}/{foto_id}-{arquivo.name}"
                url = executar_persistencia(
                    lambda: upload_photo(caminho, conteudo, arquivo.type)
                )
                if url:
                    executar_persistencia(
                        lambda: insert_row(
                            "evolution_photos",
                            {
                                "studio_id": st.session_state.studio_id,
                                "client_id": client_id,
                                "stage": etapa,
                                "storage_path": caminho,
                                "file_name": arquivo.name,
                            },
                        )
                    )
        fotos_cliente.append({
            "id": foto_id,
            "etapa": etapa,
            "nome": arquivo.name,
            "tipo": arquivo.type,
            "bytes": conteudo,
            "url": url,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        })


def render_galeria(cliente):
    st.subheader("📸 Galeria de evolução visual")
    st.caption("Registre uma imagem para cada etapa e acompanhe a transformação da cliente.")
    for etapa in ETAPAS_EVOLUCAO:
        with st.container(border=True):
            st.markdown(f"**{etapa}**")
            arquivo = st.file_uploader(
                f"Enviar foto — {etapa}",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"foto_{cliente}_{etapa}",
            )
            if arquivo is not None:
                salvar_foto(cliente, etapa, arquivo)
        fotos = [f for f in st.session_state.galeria_evolucao.get(cliente, []) if f["etapa"] == etapa]
        if fotos:
            cols = st.columns(min(len(fotos), 3))
            for coluna, foto in zip(cols, fotos):
                with coluna:
                    st.image(foto.get("url") or foto["bytes"], use_container_width=True, caption=foto["data"])
                    st.caption(foto["nome"])


def render_anamnese():
    st.header("📄 Ficha técnica & evolução visual")
    if st.session_state.clientes:
        cliente_existente = st.selectbox("Cliente", ["+ Cadastrar nova cliente"] + st.session_state.clientes)
    else:
        cliente_existente = "+ Cadastrar nova cliente"
    if cliente_existente == "+ Cadastrar nova cliente":
        nome_cliente = st.text_input("Nome completo da cliente", key="nova_cliente_anamnese")
    else:
        nome_cliente = cliente_existente
    if not nome_cliente.strip():
        st.info("Cadastre ou selecione uma cliente para preencher a ficha.")
        return
    cliente = cadastrar_cliente(nome_cliente)
    ficha_atual = st.session_state.fichas_anamnese.get(cliente, {})

    with st.form("form_anamnese"):
        st.subheader("Mapeamento da lâmina ungueal")
        tipos = st.multiselect(
            "Características observadas",
            ["Oleosa", "Seca", "Roída / onicofagia", "Fina ou flexível", "Sensível"],
            default=ficha_atual.get("tipos_lamina", []),
        )
        observacoes = st.text_area(
            "Observações técnicas",
            value=ficha_atual.get("observacoes", ""),
            placeholder="Ex.: descolamento recorrente, comprimento desejado...",
        )
        st.subheader("Saúde, alergias e segurança")
        alergias = st.text_area(
            "Histórico de alergias a monômeros, acrilatos ou outros produtos",
            value=ficha_atual.get("alergias", ""),
            placeholder="Informe alergias conhecidas ou escreva 'não informado'.",
        )
        saude = st.multiselect(
            "Condições relevantes",
            ["Diabetes", "Dermatite", "Psoríase", "Uso de medicamentos", "Nenhuma informada"],
            default=ficha_atual.get("saude", []),
        )
        detalhes_saude = st.text_area(
            "Detalhes e recomendações",
            value=ficha_atual.get("detalhes_saude", ""),
            placeholder="Orientações, contraindicações ou encaminhamento médico.",
        )
        st.subheader("Termo de responsabilidade digital")
        st.caption(
            "Declaro que as informações fornecidas são verdadeiras e que comuniquei "
            "alergias e condições de saúde relevantes antes do procedimento."
        )
        assinatura = st.text_input(
            "Assinatura digital — digite o nome completo",
            value=ficha_atual.get("assinatura", ""),
        )
        aceite = st.checkbox(
            "Li e aceito o termo de responsabilidade.",
            value=ficha_atual.get("aceite", False),
        )
        if st.form_submit_button("💾 Salvar ficha e aceite"):
            if not assinatura.strip() or not aceite:
                st.error("Digite a assinatura e confirme o aceite do termo para continuar.")
            else:
                st.session_state.fichas_anamnese[cliente] = {
                    "cliente": cliente,
                    "tipos_lamina": tipos,
                    "observacoes": observacoes.strip(),
                    "alergias": alergias.strip(),
                    "saude": saude,
                    "detalhes_saude": detalhes_saude.strip(),
                    "assinatura": assinatura.strip(),
                    "aceite": True,
                    "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                client_id = garantir_cliente_persistente(cliente)
                if persistente() and client_id:
                    executar_persistencia(
                        lambda: upsert_row(
                            "anamneses",
                            {
                                "studio_id": st.session_state.studio_id,
                                "client_id": client_id,
                                "nail_types": tipos,
                                "observations": observacoes.strip(),
                                "allergies": alergias.strip(),
                                "health_conditions": saude,
                                "health_details": detalhes_saude.strip(),
                                "signature": assinatura.strip(),
                                "accepted": True,
                            },
                            "client_id",
                        )
                    )
                st.success("Ficha técnica e aceite salvos com segurança nesta sessão.")
    render_galeria(cliente)


def render_catalogo_servicos():
    st.markdown('<div class="eyebrow">Identidade do seu atendimento</div>', unsafe_allow_html=True)
    st.subheader("⚙️ Catálogo de serviços")
    st.caption("Personalize preços, duração e cores que aparecem na agenda.")
    with st.expander("➕ Cadastrar novo serviço", expanded=False):
        with st.form("novo_servico_form"):
            nome = st.text_input("Nome do serviço", placeholder="Ex.: Esmaltação em Gel")
            col1, col2 = st.columns(2)
            with col1:
                valor = st.number_input("Valor (R$)", min_value=0.0, value=50.0, step=5.0)
            with col2:
                duracao = st.selectbox("Duração estimada", ["0h 15m", "0h 20m", "0h 30m", "1h 00m", "1h 30m", "2h 00m", "2h 30m"])
            cor = st.color_picker("Cor da etiqueta na agenda", "#FF4081")
            if st.form_submit_button("💾 Salvar serviço"):
                if not nome.strip():
                    st.error("Informe o nome do serviço.")
                elif any(s["nome"].casefold() == nome.strip().casefold() for s in st.session_state.catalogo_servicos):
                    st.error("Já existe um serviço com esse nome.")
                else:
                    dados_servico = {
                        "studio_id": st.session_state.studio_id,
                        "name": nome.strip(),
                        "price": valor,
                        "duration": duracao,
                        "color": cor,
                    }
                    salvo = (
                        executar_persistencia(lambda: insert_row("services", dados_servico))
                        if persistente() else None
                    )
                    novo_id = salvo["id"] if salvo else max((s["id"] for s in st.session_state.catalogo_servicos), default=0) + 1
                    st.session_state.catalogo_servicos.append({
                        "id": novo_id, "nome": nome.strip(), "valor": valor, "duracao": duracao, "cor": cor,
                    })
                    if salvo:
                        st.session_state.service_records[novo_id] = salvo
                    st.success(f"Serviço '{nome.strip()}' adicionado.")
                    st.rerun()

    for servico in st.session_state.catalogo_servicos:
        with st.container(border=True):
            col_info, col_edit, col_delete = st.columns([5, 2, 2])
            with col_info:
                st.markdown(
                    f'<span class="service-pill" style="background:{servico["cor"]}"></span>'
                    f'<b>{servico["nome"]}</b><br><span class="muted">'
                    f'R$ {servico["valor"]:.2f} · {servico["duracao"]}</span>',
                    unsafe_allow_html=True,
                )
            with col_edit:
                editar = st.button("✏️ Editar", key=f"editar_servico_{servico['id']}")
            with col_delete:
                excluir = st.button("🗑️ Excluir", key=f"excluir_servico_{servico['id']}")
            if excluir:
                if persistente():
                    executar_persistencia(lambda: delete_row("services", servico["id"]))
                st.session_state.catalogo_servicos = [
                    item for item in st.session_state.catalogo_servicos if item["id"] != servico["id"]
                ]
                st.rerun()
            if editar:
                st.session_state[f"editando_servico_{servico['id']}"] = True
            if st.session_state.get(f"editando_servico_{servico['id']}", False):
                with st.form(f"editar_form_{servico['id']}"):
                    novo_nome = st.text_input("Nome", value=servico["nome"])
                    novo_valor = st.number_input("Valor (R$)", min_value=0.0, value=float(servico["valor"]), step=5.0)
                    opcoes_duracao = ["0h 15m", "0h 20m", "0h 30m", "1h 00m", "1h 30m", "2h 00m", "2h 30m"]
                    nova_duracao = st.selectbox("Duração", opcoes_duracao, index=opcoes_duracao.index(servico["duracao"]) if servico["duracao"] in opcoes_duracao else 0)
                    nova_cor = st.color_picker("Cor", value=servico["cor"])
                    if st.form_submit_button("Atualizar serviço"):
                        if not novo_nome.strip():
                            st.error("Informe o nome do serviço.")
                        else:
                            servico.update({"nome": novo_nome.strip(), "valor": novo_valor, "duracao": nova_duracao, "cor": nova_cor})
                            if persistente():
                                executar_persistencia(
                                    lambda: update_row(
                                        "services",
                                        servico["id"],
                                        {"name": servico["nome"], "price": servico["valor"], "duration": servico["duracao"], "color": servico["cor"]},
                                    )
                                )
                            st.session_state[f"editando_servico_{servico['id']}"] = False
                            st.success("Serviço atualizado.")
                            st.rerun()


def render_configuracoes():
    st.markdown('<div class="eyebrow">Marca e operação</div>', unsafe_allow_html=True)
    st.header("⚙️ Personalização do estúdio")
    with st.form("form_config"):
        nome = st.text_input("Nome do estúdio", value=st.session_state.nome_estudio)
        cor = st.color_picker("Cor principal do tema", value=st.session_state.cor_primaria)
        st.write("**Ativar / desativar módulos:**")
        agenda = st.checkbox("📅 Agenda", value=st.session_state.modulos["agenda"])
        caixa = st.checkbox("💰 Caixa autônomo", value=st.session_state.modulos["caixa"])
        anamnese = st.checkbox("📄 Anamnese & fotos", value=st.session_state.modulos["anamnese"])
        if st.form_submit_button("💾 Salvar personalização"):
            if not nome.strip():
                st.error("O nome do estúdio não pode ficar vazio.")
            else:
                st.session_state.nome_estudio = nome.strip()
                st.session_state.cor_primaria = cor
                st.session_state.modulos = {"agenda": agenda, "caixa": caixa, "anamnese": anamnese}
                if persistente() and st.session_state.studio_id:
                    executar_persistencia(
                        lambda: update_row(
                            "studios",
                            st.session_state.studio_id,
                            {"name": st.session_state.nome_estudio, "primary_color": cor},
                        )
                    )
                st.success("Alterações salvas!")
                st.rerun()
    st.divider()
    st.subheader("🖼️ Logotipo do estúdio")
    logo = st.file_uploader("Envie sua logo (PNG ou JPG)", type=["png", "jpg", "jpeg"])
    if logo is not None:
        st.session_state.logo_arquivo = logo
        st.success("Logo carregada com sucesso!")
    st.divider()
    st.subheader("🎨 Atmosfera visual do app")
    st.caption("Escolha uma imagem autoral do seu estúdio, uma textura ou um fundo da sua identidade visual.")
    fundo = st.file_uploader(
        "Imagem de fundo (PNG, JPG ou WEBP)",
        type=["png", "jpg", "jpeg", "webp"],
        key="fundo_visual_upload",
    )
    if fundo is not None:
        st.session_state.fundo_arquivo = fundo
        st.success("Fundo visual atualizado. Aplique uma opacidade para manter a leitura confortável.")
    st.session_state.fundo_opacidade = st.slider(
        "Opacidade do véu de leitura",
        min_value=0.55,
        max_value=1.0,
        value=float(st.session_state.fundo_opacidade),
        step=0.05,
        help="Valores maiores deixam o fundo mais discreto e o texto mais legível.",
    )
    if st.session_state.fundo_arquivo is not None:
        st.image(st.session_state.fundo_arquivo, caption="Pré-visualização do fundo", use_container_width=True)
    st.divider()
    render_catalogo_servicos()


def render_app():
    st.sidebar.markdown(f"### 🌸 {st.session_state.nome_estudio}")
    render_usuario_sidebar()
    if st.session_state.logo_arquivo is not None:
        st.sidebar.image(st.session_state.logo_arquivo, width=120)
    else:
        st.sidebar.info("💡 Envie a logo do seu estúdio em Configurações.")
    st.sidebar.divider()
    opcoes = ["🏠 Início / Resumo"]
    if st.session_state.modulos["agenda"]:
        opcoes.append("📅 Agenda")
    if st.session_state.modulos["caixa"]:
        opcoes.append("💰 Caixa & Fechamento")
    if st.session_state.modulos["anamnese"]:
        opcoes.append("📄 Anamnese & Fichas")
    opcoes.append("⚙️ Configurações & Marca")
    menu = st.sidebar.radio("Navegação", opcoes)
    if menu == "🏠 Início / Resumo":
        render_inicio()
    elif menu == "📅 Agenda":
        render_agenda()
    elif menu == "💰 Caixa & Fechamento":
        render_caixa()
    elif menu == "📄 Anamnese & Fichas":
        render_anamnese()
    else:
        render_configuracoes()


st.set_page_config(page_title="Casal da Unha - Gestão", page_icon="💅", layout="centered")
inicializar_estado()
aplicar_estilos()
if st.session_state.auth_user is None:
    render_autenticacao()
else:
    carregar_workspace_persistente()
    if st.session_state.configurado:
        render_app()
    else:
        render_onboarding()
