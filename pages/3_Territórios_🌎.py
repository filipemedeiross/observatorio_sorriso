import pandas as pd
import plotly.express as px
import streamlit as st


# Definindo constantes
TERRITORIOS = st.session_state.escolas["escola.território"].unique()
IDADES = st.session_state.idades

# Funções auxiliares
@st.cache
def idades_fe(fe):
    idades = []

    for idade in fe:
        if "-" in idade:  # caracter '-' denota um intervalo de valores
            inicio, fim = map(int, idade.split("-"))
            idades.extend(str(i) for i in range(inicio, fim + 1))
        else:
            idades.append(idade)
    
    return idades

@st.cache
def dados_por_territorio(fato, escolas, faixa_etaria):
    dados = fato.join(escolas["escola.território"], on="escola_id")
    dados = dados.join(faixa_etaria, on="faixa_etaria_id")

    dados = dados.astype({"idade" : str})

    return dados

@st.cache
def agrupar_territorio(dados, territorios, fe):
    tabela_territorio = dados.query(f"`escola.território` in {territorios} & idade in {idades_fe(fe)}")
    tabela_territorio = tabela_territorio.groupby("escola.território")[["C", "P", "O", "soma_cpo", "quantidade_populacao"]].sum()

    tabela_territorio["cpo-d"] = tabela_territorio["soma_cpo"] / tabela_territorio["quantidade_populacao"]
    tabela_territorio["cpo-d"] = tabela_territorio["cpo-d"].apply(lambda cpo: round(cpo, 2))

    tabela_territorio.rename(columns={"C" : "Cariados", "P" : "Perdidos", "O" : "Obturados"}, inplace=True)

    return tabela_territorio

@st.cache
def agrupar_territorio_idade(dados, territorios, fe):
    dados = dados.groupby(["escola.território", "idade"])[["soma_cpo", "quantidade_populacao"]].sum()

    alunos_15_19 = dados[dados.index.get_level_values(1).isin(idades_fe(["15-19"]))].groupby(level=0).sum()
    alunos_15_19.index = pd.MultiIndex.from_product([TERRITORIOS, ["15-19"]])

    tabela_territorio_idade = pd.concat([dados, alunos_15_19])

    tabela_territorio_idade = tabela_territorio_idade[tabela_territorio_idade.index.get_level_values(0).isin(territorios) &
                                                      tabela_territorio_idade.index.get_level_values(1).isin(fe)]

    tabela_territorio_idade["cpo-d"] = tabela_territorio_idade["soma_cpo"] / tabela_territorio_idade["quantidade_populacao"]
    tabela_territorio_idade["cpo-d"] = tabela_territorio_idade["cpo-d"].apply(lambda cpo: round(cpo, 2))

    return tabela_territorio_idade.sort_values(by="idade")

@st.cache
def filtrar_dados(dados, territorios, fe):
    return agrupar_territorio(dados, territorios, fe), agrupar_territorio_idade(dados, territorios, fe)

# Configurações iniciais da página
st.set_page_config(page_title="Territórios 🌎", layout="wide")

# Obtendo a entrada do usuário e filtrando os dados
st.sidebar.multiselect("Filtrar dados por área", TERRITORIOS, TERRITORIOS, lambda x: x.capitalize(), key="territorios")
st.sidebar.multiselect("Filtrar dados por idade", IDADES, IDADES, key="fe")

dados = dados_por_territorio(st.session_state.tabela_fato, st.session_state.escolas, st.session_state.faixa_etaria)

alunos_territorio, alunos_territorio_idade = filtrar_dados(dados, st.session_state.territorios, st.session_state.fe)

# Sumário inicial dos dados
st.title("🌎 Análise por Territórios")
st.markdown("##")

col_esquerda, col_centro, col_direita = st.columns(3)

col_esquerda.markdown("Idades analisadas")
col_centro.markdown("Número total de alunos")
col_direita.markdown("CPO-D")

if st.session_state.territorios and st.session_state.fe:
    soma_cpo = alunos_territorio['soma_cpo'].sum()
    quant_populacao = alunos_territorio['quantidade_populacao'].sum()

    col_esquerda.markdown("## `" + "` `".join(st.session_state.fe) + "`")
    col_centro.markdown(f"## {quant_populacao}")
    col_direita.markdown(f"## {round(soma_cpo / quant_populacao, 2)}")

st.markdown("""---""")

# Constantes e funções auxiliares
labels = {col : "" for col in alunos_territorio.columns}
labels[alunos_territorio.index.name] = labels["value"] = labels["variable"] = ""

labels_cpo_d_territorio = {"x" : "faixa etária", "y" : "CPO-D", "color" : "território"}

multi_indice = lambda x: alunos_territorio_idade.index.get_level_values(x)

# Exibindo dados

col1, col2 = st.columns(2)
col3, col4 = st.columns((6, 4))

# CPO-D por território
fig1 = px.bar(alunos_territorio, y="cpo-d", labels=labels, text_auto=True, title="CPO-D por território")
fig1.update_traces(textfont_size=14)
fig1.update_yaxes(showticklabels=False)

col1.plotly_chart(fig1, use_container_width=True)

# Composição CPO-D por território
fig2 = px.bar(alunos_territorio, y=["Cariados", "Perdidos", "Obturados"], labels=labels, title="Composição CPO-D por território")
fig2.update_layout(legend_x=0)

col2.plotly_chart(fig2, use_container_width=True)

# Evolução CPO-D por território
fig3 = px.line(alunos_territorio_idade, x=[str(i) + " anos" for i in multi_indice(1)], y="cpo-d", text="cpo-d",
               color=multi_indice(0), labels=labels_cpo_d_territorio, title="Evolução CPO-D por território")
fig3.update_layout(legend_x=1)
fig3.update_traces(textposition="top center")
fig3.update_yaxes(showticklabels=False)

# Corrigindo inconsistência de integração entre plotly express e streamlit
for data in fig3.data:
    if len(data["x"]) == 1:
        data["mode"] = "markers+text"

col3.plotly_chart(fig3, use_container_width=True)

# Quantidade de alunos por território de Palmas
fig4 = px.bar(alunos_territorio, y="quantidade_populacao", labels=labels,
              text_auto=True, title="Quantidade de alunos por território")
fig4.update_traces(textfont_size=14)
fig4.update_yaxes(showticklabels=False)

col4.plotly_chart(fig4, use_container_width=True)
