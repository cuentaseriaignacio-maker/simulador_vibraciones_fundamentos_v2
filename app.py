import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(
    page_title="Simulador Didáctico de Vibraciones Mecánicas",
    layout="wide",
)

st.title("🌀 Simulador Didáctico de Vibraciones: Regímenes de Movimiento")
st.markdown("""
Selecciona en la barra lateral el **Régimen Dinámico** que deseas analizar para observar el comportamiento físico del resorte, la masa y las curvas de respuesta en frecuencia (Bode).
""")

# ==============================================================================
# 1. BARRA LATERAL: SELECCIÓN DE RÉGIMEN Y PARÁMETROS
# ==============================================================================
st.sidebar.header("🕹️ Configuración del Sistema")

regimen = st.sidebar.selectbox(
    "Selecciona el Tipo de Movimiento:",
    [
        "1. Movimiento Armónico Simple (Sin Amortiguamiento, c = 0)",
        "2. Movimiento Libre Amortiguado (Decaimiento Natural)",
        "3. Movimiento Forzado por Impacto Único (Golpe de Martillo / Bump Test)",
        "4. Movimiento Forzado Continuo por Motor (Resonancia)",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Propiedades Mecánicas Base")
m = st.sidebar.slider("Masa (m) [kg]", 1.0, 100.0, 10.0, step=1.0)
k = st.sidebar.slider(
    "Rigidez del Resorte (k) [N/m]", 100.0, 10000.0, 2000.0, step=100.0
)

# Cálculo de Frecuencia Natural
wn = np.sqrt(k / m)  # rad/s
fn = wn / (2 * np.pi)  # Hz
c_critico = 2 * np.sqrt(k * m)  # N*s/m

# Ajuste dinámico de parámetros según el régimen seleccionado
if "1. Movimiento Armónico" in regimen:
  zeta = 0.0
  c = 0.0
  st.sidebar.info(
      "💡 Movimiento Armónico Simple: Sin amortiguamiento (c = 0). Oscilación"
      " perpetua."
  )
  x0 = st.sidebar.slider(
      "Desplazamiento Inicial x(0) [m]", 0.01, 0.20, 0.10, step=0.01
  )
  v0 = 0.0
  F0 = 0.0
  w_motor = 0.0

elif "2. Movimiento Libre Amortiguado" in regimen:
  zeta = st.sidebar.slider(
      "Razón de Amortiguamiento (ζ)",
      0.02,
      0.80,
      0.10,
      step=0.01,
      help="Controla la velocidad con la que se frena naturally la masa.",
  )
  c = zeta * c_critico
  x0 = st.sidebar.slider(
      "Desplazamiento Inicial x(0) [m]", 0.01, 0.20, 0.10, step=0.01
  )
  v0 = 0.0
  F0 = 0.0
  w_motor = 0.0

elif "3. Movimiento Forzado por Impacto" in regimen:
  zeta = st.sidebar.slider(
      "Razón de Amortiguamiento (ζ)", 0.02, 0.50, 0.08, step=0.01
  )
  c = zeta * c_critico
  F0_impacto = st.sidebar.slider(
      "Fuerza del Impacto (Impulso) [N]", 10.0, 500.0, 100.0, step=10.0
  )
  x0 = 0.0
  v0 = F0_impacto / m  # Velocidad inicial por el golpe
  F0 = 0.0
  w_motor = 0.0

else:  # 4. Motor andando
  zeta = st.sidebar.slider(
      "Razón de Amortiguamiento (ζ)",
      0.02,
      0.60,
      0.10,
      step=0.01,
      help="Disminuye la altura del pico de resonancia.",
  )
  c = zeta * c_critico
  F0 = st.sidebar.slider(
      "Fuerza Armónica del Motor F0 [N]", 10.0, 500.0, 100.0, step=10.0
  )
  freq_motor_hz = st.sidebar.slider(
      "Frecuencia Motor (f_motor) [Hz]",
      0.1,
      float(2.2 * fn),
      float(fn * 0.5),
      step=0.1,
  )
  w_motor = 2 * np.pi * freq_motor_hz
  r = w_motor / wn
  x0 = 0.0
  v0 = 0.0

wd = wn * np.sqrt(max(0, 1 - zeta**2))  # Frecuencia amortiguada

# ==============================================================================
# 2. CÁLCULO DE LA RESPUESTA TEMPORAL x(t)
# ==============================================================================
if "4. Movimiento Forzado Continuo" in regimen:
  t = np.linspace(0, 5.0 / (freq_motor_hz if freq_motor_hz > 0 else 1.0), 120)
  M = 1.0 / np.sqrt((1 - r**2) ** 2 + (2 * zeta * r) ** 2)
  phi_rad = np.arctan2(2 * zeta * r, 1 - r**2)
  phi_deg = np.degrees(phi_rad)
  if phi_deg < 0:
    phi_deg += 360
  X_amp = (F0 / k) * M
  x_t = X_amp * np.cos(w_motor * t - phi_rad)
  envolvente_pos = None
  envolvente_neg = None
else:
  t = np.linspace(0, 6.0 / fn, 120)
  if zeta == 0:  # Armónico Simple
    x_t = x0 * np.cos(wn * t) + (v0 / wn) * np.sin(wn * t)
    envolvente_pos = None
    envolvente_neg = None
  else:  # Libre Amortiguado o Impacto
    A = np.sqrt(x0**2 + ((v0 + zeta * wn * x0) / wd) ** 2)
    phi_init = np.arctan2(x0 * wd, v0 + zeta * wn * x0)
    x_t = A * np.exp(-zeta * wn * t) * np.sin(wd * t + phi_init)
    envolvente_pos = A * np.exp(-zeta * wn * t)
    envolvente_neg = -A * np.exp(-zeta * wn * t)

# ==============================================================================
# 3. DESPLIEGUE DE MÉTRICAS Y TARJETAS INFORMATIVAS
# ==============================================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Frecuencia Natural (fn)", f"{fn:.2f} Hz", f"ωn = {wn:.1f} rad/s")

if "1. Movimiento Armónico" in regimen:
  c2.metric("Estado", "Oscilación Perpetua", "c = 0 (Sin Fricción)")
  c3.metric("Amplitud Máxima", f"{np.max(np.abs(x_t))*1000:.1f} mm")
  c4.metric("Período (T)", f"{1/fn:.3f} s")

elif "2. Movimiento Libre" in regimen:
  c2.metric("Frec. Amortiguada (fd)", f"{wd/(2*np.pi):.2f} Hz")
  c3.metric("Razón Amortiguamiento (ζ)", f"{zeta:.3f}")
  c4.metric("Tiempo de Detención (~98%)", f"{4/(zeta*wn):.2f} s")

elif "3. Movimiento Forzado por Impacto" in regimen:
  c2.metric("Tipo Excitación", "Golpe Único (Impulso)")
  c3.metric("Respuesta", "Decaimiento Lib. Amortiguado")
  c4.metric("Velocidad Inicial v(0)", f"{v0:.2f} m/s")

else:
  Q = 1.0 / (2 * zeta)
  c2.metric("Factor Q (Resonancia)", f"{Q:.1f} X")
  c3.metric("Razón Frecuencias (r)", f"{r:.2f}", "f_motor/fn")
  c4.metric("Desfase (ϕ)", f"{phi_deg:.1f}°")

st.markdown("---")

# ==============================================================================
# 4. GRÁFICAS Y ANIMACIÓN FÍSICA AUTOMÁTICA
# ==============================================================================
col_graf, col_anim = st.columns([1.3, 1.0])

with col_graf:
  st.subheader("📈 Gráfica de Desplazamiento x(t)")

  fig_t = go.Figure()
  fig_t.add_trace(
      go.Scatter(
          x=t,
          y=x_t * 1000,
          mode="lines",
          name="Desplazamiento x(t)",
          line=dict(color="crimson", width=2.5),
      )
  )

  if envolvente_pos is not None:
    fig_t.add_trace(
        go.Scatter(
            x=t,
            y=envolvente_pos * 1000,
            mode="lines",
            name="Envolvente e^(-ζω_n t)",
            line=dict(color="gray", width=1.5, dash="dash"),
        )
    )
    fig_t.add_trace(
        go.Scatter(
            x=t,
            y=envolvente_neg * 1000,
            mode="lines",
            showlegend=False,
            line=dict(color="gray", width=1.5, dash="dash"),
        )
    )

  fig_t.update_layout(
      xaxis_title="Tiempo (s)",
      yaxis_title="Desplazamiento (mm)",
      template="plotly_white",
      height=400,
  )
  st.plotly_chart(fig_t, use_container_width=True)

with col_anim:
  st.subheader("🏗 Animación Física del Resorte-Masa")

  frames = []
  for i in range(len(t)):
    t_act = t[i]
    pos_x = x_t[i]

    y_spring_f = np.linspace(0.8, pos_x + 0.2, 15)
    x_spring_f = -0.15 + 0.08 * np.sin(np.pi * np.arange(15))

    frames.append(
        go.Frame(
            data=[
                # Resorte
                go.Scatter(x=x_spring_f, y=y_spring_f, mode="lines"),
                # Amortiguador
                go.Scatter(x=[0.15, 0.15], y=[0.8, pos_x + 0.2], mode="lines"),
                # Bloque de Masa
                go.Scatter(
                    x=[-0.35, 0.35, 0.35, -0.35, -0.35],
                    y=[
                        pos_x + 0.2,
                        pos_x + 0.2,
                        pos_x - 0.2,
                        pos_x - 0.2,
                        pos_x + 0.2,
                    ],
                    fill="toself",
                    fillcolor="crimson"
                    if ("4. Movimiento" in regimen and abs(r - 1.0) < 0.15)
                    else "#1f77b4",
                ),
            ],
            layout=go.Layout(
                title_text=(
                    f"Tiempo t = {t_act:.2f} s | x = {pos_x*1000:.1f} mm"
                )
            ),
            name=f"f_{i}",
        )
    )

  pos_0 = x_t
  y_spring_0 = np.linspace(0.8, pos_0 + 0.2, 15)
  x_spring_0 = -0.15 + 0.08 * np.sin(np.pi * np.arange(15))

  fig_anim = go.Figure(
      data=[
          go.Scatter(
              x=x_spring_0,
              y=y_spring_0,
              mode="lines",
              line=dict(color="blue", width=2.5),
              name="Resorte (k)",
          ),
          go.Scatter(
              x=[0.15, 0.15],
              y=[0.8, pos_0 + 0.2],
              mode="lines",
              line=dict(color="orange", width=4),
              name="Amortiguador (c)",
          ),
          go.Scatter(
              x=[-0.35, 0.35, 0.35, -0.35, -0.35],
              y=[
                  pos_0 + 0.2,
                  pos_0 + 0.2,
                  pos_0 - 0.2,
                  pos_0 - 0.2,
                  pos_0 + 0.2,
              ],
              fill="toself",
              fillcolor="#1f77b4",
              line=dict(color="black"),
              name="Masa (m)",
          ),
      ],
      frames=frames,
  )

  fig_anim.update_layout(
      updatemenus=[
          dict(
              type="buttons",
              showactive=False,
              x=0.05,
              y=-0.08,
              buttons=[
                  dict(
                      label="▶ Reproducir Animación",
                      method="animate",
                      args=[
                          None,
                          dict(
                              frame=dict(duration=25, redraw=True),
                              fromcurrent=True,
                              transition=dict(duration=0),
                          ),
                      ],
                  ),
                  dict(
                      label="⏸ Pausa",
                      method="animate",
                      args=[
                          [None],
                          dict(
                              frame=dict(duration=0, redraw=False),
                              mode="immediate",
                              transition=dict(duration=0),
                          ),
                      ],
                  ),
              ],
          )
      ],
      xaxis=dict(range=[-1, 1], visible=False),
      yaxis=dict(range=[-0.8, 1.0], title="Desplazamiento Vertical (m)"),
      template="plotly_white",
      height=420,
  )

  st.plotly_chart(fig_anim, use_container_width=True)

# ==============================================================================
# 5. DIAGRAMAS DE BODE LADO A LADO: MAGNIFICACIÓN M(r) Y ÁNGULO DE DESFASE ϕ(r)
# ==============================================================================
if "4. Movimiento Forzado Continuo" in regimen:
  st.markdown("---")
  st.subheader("📊 Diagramas de Respuesta en Frecuencia (Bode)")

  r_vec = np.linspace(0.01, 2.5, 400)
  M_vec = 1.0 / np.sqrt((1 - r_vec**2) ** 2 + (2 * zeta * r_vec) ** 2)
  phi_vec = np.degrees(np.arctan2(2 * zeta * r_vec, 1 - r_vec**2))
  phi_vec = np.where(phi_vec < 0, phi_vec + 360, phi_vec)

  # Subplots de 1 fila y 2 columnas (Lado a lado)
  fig_bode = make_subplots(
      rows=1,
      cols=2,
      subplot_titles=(
          "a) Factor de Magnificación Dinámica M(r)",
          "b) Ángulo de Desfase ϕ(r) [Fuerza vs Desplazamiento]",
      ),
  )

  # Columna 1 (Izquierda): Magnificación M(r)
  fig_bode.add_trace(
      go.Scatter(
          x=r_vec,
          y=M_vec,
          mode="lines",
          name="Magnificación M(r)",
          line=dict(color="#1f77b4", width=2.5),
      ),
      row=1,
      col=1,
  )
  fig_bode.add_trace(
      go.Scatter(
          x=[r],
          y=[M],
          mode="markers+text",
          name="Punto Actual M",
          marker=dict(color="red", size=12, symbol="diamond"),
          text=[f"r={r:.2f}, M={M:.1f}"],
          textposition="top center",
      ),
      row=1,
      col=1,
  )
  fig_bode.add_vline(
      x=1.0,
      line_dash="dash",
      line_color="orange",
      annotation_text="Resonancia (r = 1.0)",
      row=1,
      col=1,
  )

  # Columna 2 (Derecha): Ángulo de Desfase ϕ(r)
  fig_bode.add_trace(
      go.Scatter(
          x=r_vec,
          y=phi_vec,
          mode="lines",
          name="Desfase ϕ(r)",
          line=dict(color="#2ca02c", width=2.5),
      ),
      row=1,
      col=2,
  )
  fig_bode.add_trace(
      go.Scatter(
          x=[r],
          y=[phi_deg],
          mode="markers+text",
          name="Punto Actual ϕ",
          marker=dict(color="red", size=12, symbol="diamond"),
          text=[f"ϕ={phi_deg:.1f}°"],
          textposition="top center",
      ),
      row=1,
      col=2,
  )
  fig_bode.add_vline(
      x=1.0, line_dash="dash", line_color="orange", row=1, col=2
  )
  fig_bode.add_hline(
      y=90.0,
      line_dash="dot",
      line_color="gray",
      annotation_text="90° en Resonancia",
      row=1,
      col=2,
  )

  fig_bode.update_layout(template="plotly_white", height=380, showlegend=False)
  fig_bode.update_xaxes(title_text="Razón de Frecuencias r = ω / ωn", row=1, col=1)
  fig_bode.update_xaxes(title_text="Razón de Frecuencias r = ω / ωn", row=1, col=2)
  fig_bode.update_yaxes(title_text="Magnificación M = X / δ_st", row=1, col=1)
  fig_bode.update_yaxes(
      title_text="Desfase ϕ (°)", range=[-10, 200], row=1, col=2
  )

  st.plotly_chart(fig_bode, use_container_width=True)
