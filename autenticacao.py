import streamlit as st
from banco import verificar_login, criar_usuario


def usuario_admin():
    return st.session_state.get("usuario") == "0"

#login
def tela_login():
    if "logado" not in st.session_state:
        st.session_state["logado"] = False

    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None

    if st.session_state["logado"]:
        return

    st.title("Login - Dashboard de Frota")

    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])

    #entrar usuarios que ja são cadastrados
    with aba_login:
        usuario = st.text_input("Usuário", key="login_u")
        senha = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar", key="btn_entrar"):
            if verificar_login(usuario, senha):
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos, favor tentar novamente.")
    
    #cadastrar
    with aba_cadastro:
        cpf = st.text_input("CPF", key="cadastro_cpf")
        nova_senha = st.text_input("Crie sua senha", type="password", key="cadastro_senha")

        if st.button("Criar conta", key="btn_criar_conta"):
            if cpf.strip() == "" or nova_senha.strip() == "":
                st.warning("Preencha CPF e senha.")
            else:
                codigo = criar_usuario(cpf, nova_senha)

                if codigo:
                    st.success(f"Conta criada com sucesso! Seu usuário é: {codigo}")
                else:
                    st.error("Este CPF já está cadastrado.")

    st.stop()

#cria botão d sair
def botao_sair():
    with st.sidebar:
        st.title("🚛 Fleet Analytics")
        st.caption("Sistema de Gestão de Frotas")

        st.divider()

        if usuario_admin():
            st.success("👑 Administrador")
        else:
            st.info(f"👤 Usuário: {st.session_state.get('usuario')}")

        st.divider()

        if st.button("🚪 Sair", use_container_width=True, key="btn_sair"):
            st.session_state.clear()
            st.rerun()