import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import time
from statsbombpy import sb
from mplsoccer import Pitch


st.markdown("<h1 style='color: green;'>Análise Interativa de Partidas de Futebol</h1>", unsafe_allow_html=True)


col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    competicoes = sb.competitions()

    id_competicao_selecionada = st.selectbox(
        "Selecione um Campeonato",
        list(set(competicoes['competition_id'].tolist())),
        format_func=lambda x: competicoes[competicoes['competition_id'] == x]['competition_name'].values[0]
    )

    temporadas = competicoes[competicoes['competition_id'] == id_competicao_selecionada]

    id_temporada_selecionada = st.selectbox(
        "Selecione uma Temporada",
        temporadas['season_id'].tolist(),
        format_func=lambda x: temporadas[temporadas['season_id'] == x]['season_name'].values[0]
    )

    partidas = sb.matches(competition_id=id_competicao_selecionada, season_id=id_temporada_selecionada)
    
    id_partida_selecionada = st.selectbox(
        "Selecione uma Partida",
        partidas['match_id'].tolist(),
        format_func=lambda x: f"Partida ID: {x}"
    )

with col2:
    partida_selecionada = partidas[partidas['match_id'] == id_partida_selecionada]

    eventos_competicao = pd.concat([sb.events(match_id) for match_id in partida_selecionada['match_id']])

    passes_por_jogador = eventos_competicao[eventos_competicao['type'] == 'Pass'].groupby('player').size()
    jogador_mais_passes = passes_por_jogador.idxmax()
    quantidade_passes = passes_por_jogador.max()

    st.subheader(f"**O jogador com mais passes: {jogador_mais_passes} com {quantidade_passes} passes**")

    eventos_partida = sb.events(match_id=id_partida_selecionada)

    eventos_gols = eventos_competicao[eventos_competicao['type'] == 'Shot']
    gols_por_time = eventos_gols[eventos_gols['shot_outcome'] == 'Goal'].groupby('team').size()
    chutes_por_time = eventos_gols.groupby('team').size()

    relacao_gols_chutes = pd.DataFrame({
        '⚽ Gols': gols_por_time,
        '🥅 Chutes': chutes_por_time
    }).fillna(0)

    st.markdown("**📊 Relação entre Gols e Chutes por Equipe**")
    st.dataframe(relacao_gols_chutes)

with col3:
    eventos_partida_selecionada = eventos_competicao[eventos_competicao['match_id'] == id_partida_selecionada]
    principais_eventos = eventos_partida_selecionada[['player', 'type', 'team']].drop_duplicates().dropna().head(5)

    st.markdown("**Principais eventos da partida selecionada**")
    st.dataframe(principais_eventos, hide_index=True)


st.sidebar.subheader("⚽️ Informações Disponíveis")

tab1, tab2, tab3 = st.sidebar.tabs(["🏆 Campeonatos", "📅 Temporadas", "⚔️ Partidas"])

with tab1:
    st.dataframe(competicoes['competition_name'].drop_duplicates(), hide_index=True)

with tab2:
    st.dataframe(temporadas['season_name'], hide_index=True)

with tab3:
    st.dataframe(partidas[['match_id', 'home_team', 'away_team']], hide_index=True)


passes_data = eventos_partida[eventos_partida['type'] == 'Pass']
chutes_data = eventos_partida[eventos_partida['type'] == 'Shot']

with st.spinner("⏳ Carregando eventos..."):
    time.sleep(2)
    progress_bar = st.progress(0)

    for percent in range(100):
        time.sleep(0.02)
        progress_bar.progress(percent + 1)

    jogadores = eventos_partida['player'].unique()

    with st.form("form_eventos"):
        jogador_selecionado = st.selectbox("👤 Selecione um Jogador", jogadores)
        intervalo_tempo = st.slider("⏱️ Intervalo de tempo da partida (minutos)", 0, 90, (0, 90))
        submit_button = st.form_submit_button("🔎 Filtrar")

if submit_button:
    eventos_jogador = eventos_partida[eventos_partida['player'] == jogador_selecionado]

    passes_jogador = eventos_jogador[eventos_jogador['type'] == 'Pass']
    chutes_jogador = eventos_jogador[eventos_jogador['type'] == 'Shot']

    pitch = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='white', stripe=True)

    total_gols = chutes_jogador.shape[0]
    passes_bem_sucedidos = passes_jogador[passes_jogador['pass_outcome'].isna()].shape[0]
    
    taxa_conversao = total_gols / passes_bem_sucedidos

    tab3, tab4 = st.tabs(["⚽ Total de Gols", "🔄 Passes Bem-Sucedidos"])

    if total_gols > 2:
        delta_color_gols = "inverse"
    else:
        delta_color_gols = "normal"

    if passes_bem_sucedidos > 8:
        delta_color_passes = "normal"
    else:
        delta_color_passes = "inverse"

    with tab3:
        st.metric("⚽ Total de Gols", total_gols, delta_color=delta_color_gols)

    with tab4:
        st.metric("🔄 Passes Bem-Sucedidos", passes_bem_sucedidos, delta_color=delta_color_passes)

    col5, col6 = st.columns(2, gap="large")

    with col5:
        st.subheader("🔀 Passes")
        fig, ax = pitch.draw()
        for i, row in passes_jogador.iterrows():
            pitch.arrows(row['location'][0], row['location'][1],
                         row['pass_end_location'][0], row['pass_end_location'][1],
                         color='red', ax=ax, width=2)
        st.pyplot(fig)
        st.markdown("🔴 A direção das setas indica para onde o passe foi enviado, enquanto o comprimento da seta mostra a distância do passe")
    
    with col6:
        st.subheader("🎯 Chutes")
        fig, ax = pitch.draw()
        for i, row in chutes_jogador.iterrows():
            pitch.scatter(row['location'][0], row['location'][1], color='yellow', s=100, ax=ax)
        st.pyplot(fig)
        st.markdown("🟡 Cada ponto amarelo representa um chute realizado pelo jogador")


    @st.cache_data
    def baixar_csv(df):
        return df.to_csv().encode('utf-8')

    csv_passes = baixar_csv(passes_jogador)
    st.download_button(label="⬇️ Baixar passes do jogador", data=csv_passes, file_name=f'passes_{jogador_selecionado}.csv')

    csv_chutes = baixar_csv(chutes_jogador)
    st.download_button(label="⬇️ Baixar chutes do jogador", data=csv_chutes, file_name=f'chutes_{jogador_selecionado}.csv')
