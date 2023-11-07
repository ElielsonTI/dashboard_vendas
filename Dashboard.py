import pandas as pd
import streamlit as st
import requests 
import plotly.express as px
import redshift_connector
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import Conectar_Redshifit as Conectar_RD

st.set_page_config(layout='wide')
#st.set_page_config(page_title='DASHBOARD DE FINANCEIRO - HUAWEI')

def Formata_Num(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor<1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'
with st.container():
    #st.subheader('APP - HUAWEI')
    st.title('DASHBOARD DE FINANCEIRO - HUAWEI')
    #st.write('Vai ficar top')
    #st.write('Zopone [Clique aqui](https://app.zopone.com.br/login)')
    #st.write('---')

with st.container():
    url = 'https://labdados.com/produtos'
    regioes = ['Brasil', 'Centro-Oeste', 'Norte', 'Nordeste', 'Sul', 'Sudeste']
    st.sidebar.title('Filtros')
    regiao = st.sidebar.selectbox('Rigião', regioes)
    if regiao == 'Brasil':
        regiao = ''

    todos_anos = st.sidebar.checkbox('Dados de todo o periodo', value=True)
    if todos_anos:
        ano = ''
    else:
        ano = st.sidebar.slider('Ano', 2020, 2023)
    
    query_string = {'regiao':regiao.lower(), 'ano':ano}

    response = requests.get(url, params=query_string)
    dados = pd.DataFrame.from_dict(response.json())
    dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

    filter_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
    if filter_vendedores:
        dados = dados[dados['Vendedor'].isin(filter_vendedores)]

    ## Tabelas
    ### Tabelas de receita
    receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
    receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

    receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
    receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
    receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

    receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

    ### Tabelas de quantidade de vendas
    receita_vendedor = dados.groupby('Vendedor')[['Vendedor']].groups
    vendedores = dados.groupby('Vendedor')['Preço'].agg(['sum', 'count'])

    ## Graficos
    fig_mapa_receita = px.scatter_geo(receita_estados,
                                    lat='lat',
                                    lon='lon',
                                    scope='south america',
                                    size='Preço',
                                    template='seaborn',
                                    hover_name='Local da compra',
                                    hover_data={'lat': False, 'lon': False},
                                    title='Receita por estados')

    fig_receita_mensal = px.line(receita_mensal,
                                x = 'Mes',
                                y = 'Preço',
                                markers=True,
                                range_x=(0, receita_mensal.max()),
                                color='Ano',
                                line_dash='Ano',
                                title='Receita menal')
    fig_receita_mensal.update_layout(yaxis_title = 'Receita')

    fig_receita_estados = px.bar(receita_estados.head(),
                                x='Local da compra',
                                y='Preço',
                                text_auto=True,
                                title='Top Estados(receita)')
    fig_receita_estados.update_layout(yaxis_title = 'Receita')

    fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title='Receita por Categoria')
    fig_receita_categorias.update_layout(yaxis_title = 'Receita')

    ## Visualização no streamlit
    aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

    with aba1:
        coluna1, coluna2 = st.columns(2)
        with coluna1:
            st.metric('Receita', Formata_Num(dados['Preço'].sum(), 'R$'))
            st.plotly_chart(fig_mapa_receita, use_container_width=True)
            st.plotly_chart(fig_receita_estados, use_container_width=True)
        with coluna2:
            st.metric('Qtde Vendas', Formata_Num(dados.shape[0], ''))
            st.plotly_chart(fig_receita_mensal, use_container_width=True)
            st.plotly_chart(fig_receita_categorias,use_container_width=True)

    with aba2:
        coluna1, coluna2 = st.columns(2)
        with coluna1:
            st.metric('Receita', Formata_Num(dados['Preço'].sum(), 'R$'))
        with coluna2:
            st.metric('Qtde Vendas', Formata_Num(dados.shape[0], ''))
    st.dataframe(dados)

    with aba3:
        #option = st.selectbox(
        #    "Pesquisa por vendedor",
        #    (receita_vendedor),
        #    index=None,
        #    placeholder="Selecione um vendedor"
        #)
        #st.write('Seu vendedor', option)

        qtde_vend = st.number_input('Quantidade de vendedores', 2, 10, 5)
        coluna1, coluna2 = st.columns(2)
        with coluna1:
            st.metric('Receita', Formata_Num(dados['Preço'].sum(), 'R$'))
            fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtde_vend),
                                            x='sum',
                                            y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtde_vend).index,
                                            text_auto=True,
                                            title=f'Top {qtde_vend} vendedores (receita)')
            st.plotly_chart(fig_receita_vendedores)
        with coluna2:
            st.metric('Qtde Vendas', Formata_Num(dados.shape[0], ''))
            fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtde_vend),
                                            x='count',
                                            y=vendedores[['count']].sort_values('count', ascending=False).head(qtde_vend).index,
                                            text_auto=True,
                                            title=f'Top {qtde_vend} vendedores (qtde de vendas)')
            st.plotly_chart(fig_vendas_vendedores)


#dt1 = pd.DataFrame(Conectar_RD.carregar_dados())
