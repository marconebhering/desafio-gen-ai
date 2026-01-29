import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Indicium HealthCare Inc.",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Indicium HealthCare Inc.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📈 Taxa de Aumento", "15.2%", "2.3%")
with col2:
    st.metric("💀 Taxa de Mortalidade", "3.5%", "-0.5%")
with col3:
    st.metric("🏥 Ocupação UTI", "78%", "5%")
with col4:
    st.metric("💉 Taxa de Vacinação", "82%", "3%")

st.markdown("---")

col_graficos, col_chat = st.columns([65, 35])

with col_graficos:

    # ----------------- GRÁFICO DIÁRIO -----------------
    datas_diarias = pd.date_range(end=pd.Timestamp.today(), periods=30, freq="D")
    np.random.seed(42)
    casos_diarios = np.random.poisson(120, 30) + np.linspace(0, 40, 30).astype(int)

    df_diario = pd.DataFrame({"Data": datas_diarias, "Casos": casos_diarios})

    fig_diario = go.Figure()

    fig_diario.add_trace(
        go.Scatter(
            x=df_diario["Data"],
            y=df_diario["Casos"],
            mode="lines",
            line=dict(color="#2563EB", width=3),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.25)",
            hovertemplate=(
                "<b>📅 %{x|%d/%m}</b><br><br>"
                "Casos: <b>%{y}</b>"
                "<extra></extra>"
            )
        )
    )

    fig_diario.update_layout(
        title="📈 Número diário de casos de SRAG (últimos 30 dias)",
        template="plotly_white",
        height=380,
        dragmode=False,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(title=None, fixedrange=True, showgrid=False),
        yaxis=dict(title=None, fixedrange=True),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#303030",
            bordercolor="#303030",
            font=dict(color="white", size=14),
            align="left"
        ),
        font=dict(
            family="Source Sans Pro",
            size=14
        )
    )

    st.plotly_chart(fig_diario,
        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False}
    )

    # ----------------- GRÁFICO MENSAL -----------------
    meses = pd.date_range(end=pd.Timestamp.today(), periods=12, freq="MS")
    np.random.seed(7)
    casos_mensais = np.random.randint(2500, 6000, 12)

    df_mensal = pd.DataFrame({"Mês": meses, "Casos": casos_mensais})

    fig_mensal = go.Figure()

    fig_mensal.add_trace(
        go.Bar(
            x=df_mensal["Mês"],
            y=df_mensal["Casos"],
            marker=dict(color="#2563EB", line=dict(width=0)),
            hovertemplate=(
                "<b>📅 %{x|%m/%Y}</b><br><br>"
                "Casos: <b>%{y}</b>"
                "<extra></extra>"
            )
        )
    )

    fig_mensal.update_layout(
        title="📊 Número mensal de casos de SRAG (últimos 12 meses)",
        template="plotly_white",
        height=380,
        dragmode=False,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(title=None, fixedrange=True),
        yaxis=dict(title=None, fixedrange=True),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#303030",
            bordercolor="#303030",
            font=dict(color="white", size=14),
            align="left"
        ),
        font=dict(
            family="Source Sans Pro",
            size=14
        )
    )

    st.plotly_chart(fig_mensal,
        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False}
    )

# ----------------- CHAT -----------------
with col_chat:
    st.title("💬 Echo Bot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Digite sua mensagem..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        response = f"Echo: {prompt}"
        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
