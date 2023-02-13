import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# Definindo constantes
BASE_DE_DADOS = "observatorio_sorriso"

# Função auxiliar para carregar os dados
@st.cache
def carregar_dados(base_dados):
    # Conectando a base de dados e obtendo o cursor
    conn = sqlite3.connect(base_dados)
    cur = conn.cursor()

    # Obtendo a tabela fato
    res = cur.execute("SELECT * FROM CPO_D")
    tabela_fato = pd.DataFrame(res.fetchall(), columns=np.array(res.description)[:, 0])
    tabela_fato.drop(columns=["index"], inplace=True)
    
    # Obtendo a dimensão 'Escola'
    res = cur.execute("SELECT * FROM Escola")
    escolas = pd.DataFrame(res.fetchall(), columns=np.array(res.description)[:, 0])
    escolas.drop(columns=["index"], inplace=True)

    # Obtendo a dimensão 'Faixa_etaria'
    res = cur.execute("SELECT * FROM Faixa_etaria")
    faixa_etaria = pd.DataFrame(res.fetchall(), columns=np.array(res.description)[:, 0])
    faixa_etaria.drop(columns=["index"], inplace=True)

    # Obtendo a dimensão 'Exame'
    res = cur.execute("SELECT * FROM Exame")
    exame = pd.DataFrame(res.fetchall(), columns=np.array(res.description)[:, 0])
    exame.drop(columns=["index"], inplace=True)
    
    conn.close()  # fechar conexão

    return tabela_fato, escolas, faixa_etaria, exame

# Configurações iniciais da página
st.set_page_config(page_title="Observatório do Sorriso", layout="centered", initial_sidebar_state="expanded")

# Carregando dados que serão utilizados em todas as pages do app
st.session_state.f, st.session_state.e, st.session_state.fe, st.session_state.ex = carregar_dados(BASE_DE_DADOS)

# Obtendo dados a serem utilizados
fato, escolas = st.session_state.f, st.session_state.e

fato_regiao = fato.join(escolas["escola.região"], on="escola_id")
fato_regiao = fato_regiao.groupby("escola.região")["quantidade_populacao"].sum()  # quantidade de alunos por região

# Cabeçalho inicial
# Sumário de informações relevantes
# Média do CPO-D em Palmas/TO
# Quantidade de alunos, escolas, territórios e regiões analisadas
st.markdown("<h1 style='text-align: center'>Observatório do Sorriso</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center'>Quantidade de alunos examinados em Palmas-TO</h3>", unsafe_allow_html=True)

col1, col2 = st.columns((8.5, 1.5))

fig = px.pie(values=fato_regiao, names=fato_regiao.index, hole=.7)
fig.update_layout(legend_x=-.25, annotations=[dict(text=f"<b>{fato_regiao.sum()}</b>", x=.5, y=.55, font_size=30, showarrow=False),
                                              dict(text="alunos", x=.5, y=.45, font_size=20, showarrow=False)])
col1.plotly_chart(fig, use_container_width=True)

col2.markdown(f"<h4> </h4>\
                <h3>{round(fato['soma_cpo'].sum() / fato['quantidade_populacao'].sum(), 2)}</h3>\
                <h6>CPO-D Palmas</h6>", unsafe_allow_html=True)
col2.markdown(f"<h3>{escolas.shape[0]}</h3> <h6>escolas</h6>", unsafe_allow_html=True)
col2.markdown(f"<h3>{escolas['escola.território'].nunique()}</h3> <h6>territórios</h6>", unsafe_allow_html=True)
col2.markdown(f"<h3>{escolas['escola.região'].nunique()}</h3> <h6>regiões</h6>", unsafe_allow_html=True)

# Mais informações sobre o projeto
# Referência aos dados brutos
with st.expander("Mais informações"):
    st.caption("Dados brutos disponíveis na [página do github](https://github.com/filipemedeiross/observatorio_sorriso/tree/main/dados) do projeto.")
