import pandas as pd
import plotly.express as px
import streamlit as st


# Definindo constantes
AREAS = "RURAL", "URBANO"
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
def dados_por_area(fato, escolas, faixa_etaria):
    dados = fato.join(escolas["escola.região"], on="escola_id")
    dados = dados.join(faixa_etaria, on="faixa_etaria_id")

    dados.loc[dados["escola.região"] != "RURAL", "escola.região"] = "URBANO"

    dados = dados.astype({"idade" : str})
    dados.rename(columns={"escola.região" : "escola.area"}, inplace=True)

    return dados

@st.cache
def agrupar_area(dados, areas, fe):
    tabela_area = dados.query(f"`escola.area` in {areas} & idade in {idades_fe(fe)}")
    tabela_area = tabela_area.groupby("escola.area")[["C", "P", "O", "soma_cpo", "quantidade_populacao"]].sum()

    tabela_area["cpo-d"] = tabela_area["soma_cpo"] / tabela_area["quantidade_populacao"]
    tabela_area["cpo-d"] = tabela_area["cpo-d"].apply(lambda cpo: round(cpo, 2))

    tabela_area.rename(columns={"C" : "Cariados", "P" : "Perdidos", "O" : "Obturados"}, inplace=True)

    return tabela_area

@st.cache
def agrupar_area_idade(dados, areas, fe):
    dados = dados.groupby(["escola.area", "idade"])[["soma_cpo", "quantidade_populacao"]].sum()

    alunos_15_19 = dados[dados.index.get_level_values(1).isin(idades_fe(["15-19"]))].groupby(level=0).sum()
    alunos_15_19.index = pd.MultiIndex.from_product([AREAS, ["15-19"]])

    tabela_area_idade = pd.concat([dados, alunos_15_19])

    tabela_area_idade = tabela_area_idade[tabela_area_idade.index.get_level_values(0).isin(areas) &
                                          tabela_area_idade.index.get_level_values(1).isin(fe)]

    tabela_area_idade["cpo-d"] = tabela_area_idade["soma_cpo"] / tabela_area_idade["quantidade_populacao"]
    tabela_area_idade["cpo-d"] = tabela_area_idade["cpo-d"].apply(lambda cpo: round(cpo, 2))

    return tabela_area_idade.sort_values(by="idade")

@st.cache
def filtrar_dados(dados, areas, fe):    
    return agrupar_area(dados, areas, fe), agrupar_area_idade(dados, areas, fe)

# Configurações iniciais da página
st.set_page_config(page_title="Áreas", layout="wide")

# Obtendo a entrada do usuário e filtrando os dados
st.sidebar.multiselect("Filtrar dados por área", AREAS, AREAS, lambda x: x.capitalize(), key="areas")
st.sidebar.multiselect("Filtrar dados por idade", IDADES, IDADES, key="fe")

dados = dados_por_area(st.session_state.tabela_fato, st.session_state.escolas, st.session_state.faixa_etaria)

alunos_area, alunos_area_idade = filtrar_dados(dados, st.session_state.areas, st.session_state.fe)

# Sumário inicial dos dados
st.title("🌇 🌄 Análise por Áreas")
st.markdown("##")

col_esquerda, col_centro, col_direita = st.columns(3)

col_esquerda.markdown("Idades analisadas")
col_centro.markdown("Número total de alunos")
col_direita.markdown("CPO-D")

if st.session_state.areas and st.session_state.fe:
    soma_cpo = alunos_area['soma_cpo'].sum()
    quant_populacao = alunos_area['quantidade_populacao'].sum()

    col_esquerda.markdown("## `" + "` `".join(st.session_state.fe) + "`")
    col_centro.markdown(f"## {quant_populacao}")
    col_direita.markdown(f"## {round(soma_cpo / quant_populacao, 2)}")

st.markdown("""---""")

# Constantes e funções auxiliares
labels = {col : "" for col in alunos_area.columns}
labels[alunos_area.index.name] = labels["value"] = labels["variable"] = ""

labels_cpo_d_zona = {"x" : "faixa etária", "y" : "CPO-D", "color" : "zona"}

multi_indice = lambda x: alunos_area_idade.index.get_level_values(x)

# Exibindo dados

col1, col2 = st.columns(2)
col3, col4 = st.columns((7, 3))

# CPO-D por zona
fig1 = px.bar(alunos_area, y="cpo-d", labels=labels, text_auto=True, title="CPO-D por zona")
fig1.update_traces(textfont_size=14)
fig1.update_yaxes(showticklabels=False)

col1.plotly_chart(fig1, use_container_width=True)

# Composição CPO-D por zona
fig2 = px.bar(alunos_area, y=["Cariados", "Perdidos", "Obturados"], labels=labels, title="Composição CPO-D por zona")
fig2.update_layout(legend_x=0)

col2.plotly_chart(fig2, use_container_width=True)

# Evolução CPO-D por zona
fig3 = px.line(alunos_area_idade, x=[str(i) + " anos" for i in multi_indice(1)], y="cpo-d", text="cpo-d",
               color=multi_indice(0), labels=labels_cpo_d_zona, title="Evolução CPO-D por zona")
fig3.update_layout(legend_x=1)
fig3.update_traces(textposition="top center")
fig3.update_yaxes(showticklabels=False)

# Corrigindo inconsistência de integração entre plotly express e streamlit
for data in fig3.data:
    if len(data["x"]) == 1:
        data["mode"] = "markers+text"

col3.plotly_chart(fig3, use_container_width=True)

# Quantidade de alunos por zona de Palmas
fig4 = px.pie(values=alunos_area.quantidade_populacao, names=alunos_area.index,
              hole=.7, title="Quantidade de alunos por zona")

col4.plotly_chart(fig4, use_container_width=True)
