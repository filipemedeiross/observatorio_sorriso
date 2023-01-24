import pandas as pd
import plotly.express as px
import streamlit as st


# Configurações iniciais da página
st.set_page_config(page_title="Zonas", layout="wide")

# Funções auxiliares
# Obter os dados a serem utilizados
# Obter o intervalo de faixas etárias
# Obter as idades de um intervalo de faixas etárias
@st.cache
def dados_por_zona(tabela_fato, tabela_escolas, tabela_fe):
    dados = tabela_fato.join(tabela_escolas["escola.região"], on="escola_id")
    dados = dados.join(tabela_fe, on="faixa_etaria_id")

    dados.query("idade in (12, 15, 16, 17, 18, 19)", inplace=True)

    dados["escola.região"] = dados["escola.região"].map({regiao : "RURAL" if regiao=="RURAL" else "URBANO"
                                                         for regiao in dados["escola.região"].unique()})

    dados = dados.astype({"idade" : str})
    dados.rename(columns={"escola.região" : "escola.zona"}, inplace=True)
    dados.drop(["escola_id", "faixa_etaria_id", "exame_id"], axis=1, inplace=True)

    return dados

def intervalo_fe(fe):
    if fe[0] == fe[1]:
        return [fe[0]]
    elif fe[0] == "12" and fe[1] == "15-19":
        return ["12", "15", "15-19"]

    return fe

def idades_fe(fe):
    idades = []

    for i in fe:
        if "-" in i:  # caracter '-' denota um intervalo de valores
            inicio, fim = map(int, i.split("-"))
            idades.extend(str(i) for i in range(inicio, fim+1))
        else:
            idades.append(i)
    
    return idades

# Obtendo os dados a serem utilizados
dados = dados_por_zona(st.session_state.fato, st.session_state.escolas, st.session_state.fe)

# Entrada do usuário
st.sidebar.select_slider("Filtrar dados por idade", ["12", "15", "15-19"], ["12", "15-19"], key="faixa_etaria")

st.sidebar.multiselect('Filtrar dados por zona', dados["escola.zona"].unique(), dados["escola.zona"].unique(),
                       lambda x: x.capitalize(), key="zonas")

# Filtrando os dados de acordo com a entrada do usuário
@st.cache
def filtrar_dados(dados, fe, zonas):
    dados = dados.query(f"idade in {idades_fe(fe)} & `escola.zona` in {zonas}")

    # Obtendo tabelas de interesse
    alunos_zona = dados.groupby("escola.zona")[["C", "P", "O", "soma_cpo", "quantidade_populacao"]].sum()

    alunos_zona.rename(columns={"C" : "Cariados", "P" : "Perdidos", "O" : "Obturados"}, inplace=True)
    alunos_zona["cpo-d"] = (alunos_zona["soma_cpo"] / alunos_zona["quantidade_populacao"]).apply(lambda cpo: round(cpo, 2))

    alunos_zona_idade = dados.groupby(["escola.zona", "idade"])[["soma_cpo", "quantidade_populacao"]].sum()

    if "15-19" in fe:
        alunos_15_19 = alunos_zona_idade[alunos_zona_idade.index.get_level_values(1).isin([str(i) for i in range(15, 20)])].groupby(level=0).sum()
        alunos_15_19.index = pd.MultiIndex.from_product([alunos_zona_idade.index.get_level_values(0).unique(), ["15-19"]],
                                                         names=alunos_zona_idade.index.names)

        alunos_zona_idade = alunos_zona_idade.append(alunos_15_19)

    alunos_zona_idade = alunos_zona_idade[alunos_zona_idade.index.get_level_values(1).isin(fe)]
    alunos_zona_idade["cpo-d"] = (alunos_zona_idade["soma_cpo"] / alunos_zona_idade["quantidade_populacao"]).apply(lambda cpo: round(cpo, 2))
    alunos_zona_idade.sort_values(by="idade", inplace=True)

    return alunos_zona, alunos_zona_idade

alunos_zona, alunos_zona_idade = filtrar_dados(dados, intervalo_fe(st.session_state.faixa_etaria), st.session_state.zonas)

# Sumário inicial dos dados
st.title("🌇 🌄 Análise por Zonas")
st.markdown("##")

col_esquerda, col_centro, col_direita = st.columns(3)

with col_esquerda:
    st.markdown("Idades analisadas")
    st.markdown("## `" + "` `".join(intervalo_fe(st.session_state.faixa_etaria)) + "`")
with col_centro:
    st.markdown("Número total de alunos")
    st.markdown(f"## {alunos_zona['quantidade_populacao'].sum()}")
with col_direita:
    st.markdown("CPO-D")
    st.markdown(f"## {round(alunos_zona['soma_cpo'].sum() / alunos_zona['quantidade_populacao'].sum(), 2)}")

st.markdown("""---""")

# Constantes e funções auxiliares
labels = {col : "" for col in alunos_zona.columns}
labels[alunos_zona.index.name] = labels["value"] = labels["variable"] = ""

labels_cpo_d_zona = {"x" : "faixa etária", "y" : "CPO-D", "color" : "zona"}

multi_indice = lambda x: alunos_zona_idade.index.get_level_values(x)

# Exibindo dados

col1, col2 = st.columns(2)
col3, col4 = st.columns((7, 3))

# CPO-D por zona
fig1 = px.bar(alunos_zona, y="cpo-d", labels=labels, text_auto=True, title="CPO-D por zona")
fig1.update_traces(textfont_size=14)

col1.plotly_chart(fig1, use_container_width=True)

# Composição CPO-D por zona
fig2 = px.bar(alunos_zona, y=["Cariados", "Perdidos", "Obturados"], labels=labels, title="Composição CPO-D por zona")
fig2.update_layout(legend_x=0)

col2.plotly_chart(fig2, use_container_width=True)

# Evolução CPO-D por zona
fig3 = px.line(alunos_zona_idade, x=[str(i) + " anos" for i in multi_indice(1)], y="cpo-d", text="cpo-d",
               color=multi_indice(0), labels=labels_cpo_d_zona, title="Evolução CPO-D por zona")
fig3.update_traces(textposition="top center")
fig3.update_layout(legend_x=0)

# Corrigindo inconsistência de integração entre plotly express e streamlit
for data in fig3.data:
    if len(data["x"]) == 1:
        data["mode"] = "markers+text"

col3.plotly_chart(fig3, use_container_width=True)

# Quantidade de alunos por zona de Palmas
fig4 = px.pie(values=alunos_zona.quantidade_populacao, names=alunos_zona.index, hole=.7,
              title="Quantidade de alunos por zona")

col4.plotly_chart(fig4, use_container_width=True)
