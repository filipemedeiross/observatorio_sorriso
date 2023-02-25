import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st


# Definindo constantes
BASE_DE_DADOS = "observatorio_sorriso"

# Função auxiliar para carregar dados
@st.cache
def carregar_dados(base_dados):
    conn = sqlite3.connect(base_dados)  # conectando a base de dados

    st.session_state.tabela_fato = pd.read_sql("SELECT * FROM CPO_D", conn, "index")
    st.session_state.escolas = pd.read_sql("SELECT * FROM Escola", conn, "index")
    st.session_state.faixa_etaria = pd.read_sql("SELECT * FROM Faixa_etaria", conn, "index")
    st.session_state.exame = pd.read_sql("SELECT * FROM Exame", conn, "index")
    
    conn.close()  # fechar conexão

# Configurações iniciais da página
st.set_page_config(page_title="Observatório do Sorriso", initial_sidebar_state="expanded")

# Carregando dados que serão utilizados em todas as pages do app
carregar_dados(BASE_DE_DADOS)

# Obtendo dados a serem utilizados
fato, escolas = st.session_state.tabela_fato, st.session_state.escolas

fato_regiao = fato.join(escolas["escola.região"], on="escola_id")
fato_regiao = fato_regiao.groupby("escola.região")["quantidade_populacao"].sum()  # quantidade de alunos por região

# Cabeçalho inicial
# Sumário de informações relevantes
st.markdown("<h1 style='text-align: center'>Observatório do Sorriso</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center'>Quantidade de alunos examinados em Palmas-TO</h3>", unsafe_allow_html=True)

_, col1, col2, col3 = st.columns((0.5, 7.5, 1, 1))

fig = px.pie(values=fato_regiao, names=fato_regiao.index, hole=.7)
fig.update_layout(legend_x=-.25, annotations=[dict(text=f"<b>{fato_regiao.sum()}</b>", x=.5, y=.55, font_size=30, showarrow=False),
                                              dict(text="alunos", x=.5, y=.45, font_size=20, showarrow=False)])
col1.plotly_chart(fig, use_container_width=True)

col2.markdown(f"<h4> </h4>\
                <h4>{round(fato['soma_cpo'].sum() / fato['quantidade_populacao'].sum(), 2)}</h4>\
                <h6>cpo-d</h6>", unsafe_allow_html=True)
col2.markdown(f"<h4>{escolas.shape[0]}</h4> <h6>escolas</h6>", unsafe_allow_html=True)

col3.markdown(f"<h4> </h4>\
                <h4>{escolas['escola.território'].nunique()}</h4>\
                <h6>territórios</h6>", unsafe_allow_html=True)
col3.markdown(f"<h4>{escolas['escola.região'].nunique()}</h4> <h6>regiões</h6>", unsafe_allow_html=True)

# Mais informações sobre o projeto
with st.expander("Mais informações"):
    st.caption("Dados brutos disponíveis na [página do github](https://github.com/filipemedeiross/observatorio_sorriso/tree/main/dados) do projeto.")
