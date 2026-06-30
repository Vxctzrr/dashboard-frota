import streamlit as st
from banco import (
    verificar_login,
    criar_usuario
)

def tela_login():
    if "logado" not in st.session_state:
        st.session_state["logado"] = False

    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None

    if st.session_state["logado"]:
        return
    
    st.title("Login - dashboard de Frota")

    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])

    with aba_login:
        usuario = st.text_input(
            "Usuário",
            key="login_u"
        )
        senha = st.text_input(
            "Senha",
            type="password",
            key="login_senha"
        )

    if st.button("Entrar"):
        if verificar_login(usuario, senha):
            st.session_state["logado"] = True
            st.session_state["usuario"] = usuario
            st.rerun()
        else:
            st.error("Usuario ou senha incorretos, favor tentar novamente.")


    #cadastro de usuário
    with aba_cadastro:
        novo_usuario = st.text_input(
            "CPF",
            key="cadastro_cpf"
        )

        nova_senha = st.text_input (
            "Crie sua senha",
            type="password",
            key="cadastro_senha"
        )

        if st.button(
            "Criar conta",
            key="btn_criar_conta"
        ):
            if novo_usuario.strip() == "" or nova_senha.strip() == "":
                st.warning("Preencha Usuário e Senha.")

        else:
            codigo = criar_usuario(novo_usuario, nova_senha)

            if codigo:
                st.success(f"""
        Conta criada com sucesso!
    
        Seu usuário é: {codigo}

        Guarde esse código. você precisará dele para fazer login.
        """)
            else:
                st.error("Este usuário ja está cadastrado.")
    st.stop()

#cria botão de deslogar
def botao_sair():
    st.write(f"Usuário logado: {st.session_state.get('usuario')}")

    if st.button ("Sair"):
        st.session_state["Logado"] = False
        st.session_state["usuario"] = None
        st.rerun()
        