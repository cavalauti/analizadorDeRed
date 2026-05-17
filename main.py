"""
SCADA -- Analizador de Red Monofasico (Version de Ventanas Interactivas)
Compatible con Flet 0.85+ y Flet Moderno

Solución Definitiva de Actualización:
- Se reemplaza el Timer por una tarea asíncrona nativa mediante 'page.run_task'.
- Esto fuerza el refresco inmediato de los gráficos y textos cada 5 segundos
  sin requerir ninguna interacción del usuario.
"""

import flet as ft
import random
import base64
import json
import asyncio  # Reemplazo limpio para manejar los 5 segundos de espera
from datetime import datetime

# ── Paleta de Colores ─────────────────────────────────────────────────────────
BLUE   = "#378ADD"
AMBER  = "#BA7517"
GREEN  = "#639922"
TEAL   = "#1D9E75"
CORAL  = "#D85A30"
PURPLE = "#7F77DD"

BG_CARD   = "#FFFFFF"
BG_PAGE   = "#F4F3EE"
TEXT_SEC  = "#888780"
TEXT_TERT = "#B4B2A9"
BORDER    = "#D3D1C7"
WARN_BG   = "#FAEEDA"
WARN_TXT  = "#854F0B"
OK_BG     = "#EAF3DE"
OK_TXT    = "#3B6D11"

HIST_N     = 60
INTERVAL_S = 5.0  # Frecuencia exacta de 5 segundos
MB_DEF     = 18   # Margen inferior del SVG


# ── Helpers de Estilo ─────────────────────────────────────────────────────────

def bdr(all_w=None, color=BORDER, top=None, bottom=None, left=None, right=None):
    if all_w is not None:
        s = ft.BorderSide(all_w, color)
        return ft.Border(top=s, bottom=s, left=s, right=s)
    return ft.Border(
        top    = ft.BorderSide(top,    color) if top    else None,
        bottom = ft.BorderSide(bottom, color) if bottom else None,
        left   = ft.BorderSide(left,   color) if left   else None,
        right  = ft.BorderSide(right,  color) if right  else None,
    )

def pad(all_=None, h=0, v=0, top=0, bottom=0, left=0, right=0):
    if all_ is not None:
        return ft.Padding(left=all_, right=all_, top=all_, bottom=all_)
    if h or v:
        return ft.Padding(left=h, right=h, top=v, bottom=v)
    return ft.Padding(left=left, right=right, top=top, bottom=bottom)

def brad(all_=None, tl=0, tr=0, bl=0, br_=0):
    if all_ is not None:
        return ft.BorderRadius(top_left=all_, top_right=all_,
                               bottom_left=all_, bottom_right=all_)
    return ft.BorderRadius(top_left=tl, top_right=tr,
                           bottom_left=bl, bottom_right=br_)


# ── Renderizadores SVG Dinámicos Escalables ───────────────────────────────────
FONT_SVG = "font-family='Arial,sans-serif'"
TCOL     = "#888780"
GCOL     = "#00000020"

ML_DEF = 40   # Margen izquierdo
MR_DEF = 36   # Margen derecho


def svg_single(data, color, unit_y="W", W=400, H=130,
               min_y=None, max_y=None, filled=False):
    if not data:
        return ""
    mn = min_y if min_y is not None else min(data)
    mx = max_y if max_y is not None else max(data)
    rng = mx - mn or 1

    ML, MR, MB = ML_DEF, 8, MB_DEF
    pw = W - ML - MR
    ph = H - MB
    n  = len(data)
    n_grid = 4

    parts = []
    for k in range(n_grid + 1):
        frac = k / n_grid
        val  = mx - frac * rng
        y    = frac * ph
        parts.append(f'<line x1="{ML}" y1="{y:.1f}" x2="{ML+pw}" y2="{y:.1f}" '
                     f'stroke="{GCOL}" stroke-width="0.8"/>')
        parts.append(f'<text x="{ML-3}" y="{y+4:.1f}" text-anchor="end" '
                     f'{FONT_SVG} font-size="9" fill="{TCOL}">{val:.0f}</text>')
    parts.append(f'<text x="2" y="10" {FONT_SVG} font-size="9" fill="{TCOL}">{unit_y}</text>')

    total_s = (n - 1) * INTERVAL_S
    for k in range(5):
        frac   = k / 4
        x      = ML + frac * pw
        ago    = total_s * (1.0 - frac)
        lbl    = "ahora" if ago < 1 else f"-{ago:.0f}s"
        anchor = "start" if k == 0 else ("end" if k == 4 else "middle")
        parts.append(f'<text x="{x:.1f}" y="{H-3}" text-anchor="{anchor}" '
                     f'{FONT_SVG} font-size="9" fill="{TCOL}">{lbl}</text>')

    def px(i): return ML + i / (n - 1) * pw
    def py(v): return (mx - v) / rng * ph

    pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(data))
    fill_el = ""
    if filled:
        fill_el = (f'<polygon points="{px(0):.1f},{ph} {pts} {px(n-1):.1f},{ph}" '
                   f'fill="{color}" fill-opacity="0.15"/>')

    axes = "\n".join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="none"/>'
            f'{axes}{fill_el}'
            f'<polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>'
            f'</svg>')


def svg_dual(d1, d2, c1, c2, unit_y1="V", unit_y2="A",
             W=400, H=130, min_y=None, max_y=None):
    if not d1 or not d2:
        return ""

    ML, MR, MB = ML_DEF, MR_DEF, MB_DEF
    n_grid = 4

    mn1 = min_y if min_y is not None else min(d1)
    mx1 = max_y if max_y is not None else max(d1)
    
    mn2, mx2 = min(d2), max(d2)
    rng1 = mx1 - mn1 or 1
    rng2 = mx2 - mn2 or 1

    pw = W - ML - MR
    ph = H - MB
    n  = len(d1)

    parts = []
    for k in range(n_grid + 1):
        frac = k / n_grid
        val1 = mx1 - frac * rng1
        val2 = mx2 - frac * rng2
        y    = frac * ph
        parts.append(f'<line x1="{ML}" y1="{y:.1f}" x2="{ML+pw}" y2="{y:.1f}" '
                     f'stroke="{GCOL}" stroke-width="0.8"/>')
        parts.append(f'<text x="{ML-3}" y="{y+4:.1f}" text-anchor="end" '
                     f'{FONT_SVG} font-size="9" fill="{c1}">{val1:.0f}</text>')
        parts.append(f'<text x="{ML+pw+3}" y="{y+4:.1f}" text-anchor="start" '
                     f'{FONT_SVG} font-size="9" fill="{c2}">{val2:.1f}</text>')

    parts.append(f'<text x="2" y="10" {FONT_SVG} font-size="9" fill="{c1}">{unit_y1}</text>')
    parts.append(f'<text x="{W-2}" y="10" text-anchor="end" '
                 f'{FONT_SVG} font-size="9" fill="{c2}">{unit_y2}</text>')

    total_s = (n - 1) * INTERVAL_S
    for k in range(5):
        frac   = k / 4
        x      = ML + frac * pw
        ago    = total_s * (1.0 - frac)
        lbl    = "ahora" if ago < 1 else f"-{ago:.0f}s"
        anchor = "start" if k == 0 else ("end" if k == 4 else "middle")
        parts.append(f'<text x="{x:.1f}" y="{H-3}" text-anchor="{anchor}" '
                     f'{FONT_SVG} font-size="9" fill="{TCOL}">{lbl}</text>')

    axes = "\n".join(parts)

    def px(i):  return ML + i / (n - 1) * pw
    def py1(v): return (mx1 - v) / rng1 * ph
    def py2(v): return (mx2 - v) / rng2 * ph

    pts1 = " ".join(f"{px(i):.1f},{py1(v):.1f}" for i, v in enumerate(d1))
    pts2 = " ".join(f"{px(i):.1f},{py2(v):.1f}" for i, v in enumerate(d2))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="none"/>'
            f'{axes}'
            f'<polyline points="{pts1}" fill="none" stroke="{c1}" '
            f'stroke-width="1.8" stroke-linejoin="round"/>'
            f'<polyline points="{pts2}" fill="none" stroke="{c2}" '
            f'stroke-width="1.8" stroke-linejoin="round"/>'
            f'</svg>')


def svg_to_src(svg_str):
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


# ── Componentes de Interfaz Estándar ──────────────────────────────────────────

def section_title(text):
    return ft.Container(
        padding=pad(top=16, bottom=8),
        content=ft.Text(text.upper(), size=12, weight="w500", color=TEXT_SEC),
    )


def metric_card(label, value_ref, unit, sub, accent):
    return ft.Container(
        bgcolor=BG_CARD, border_radius=12, border=bdr(1),
        padding=pad(all_=16), expand=True,
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Container(height=2, bgcolor=accent, border_radius=2),
                ft.Text(label, size=12, color=TEXT_SEC),
                ft.Row(spacing=4, controls=[
                    ft.Text("--", ref=value_ref, size=24, weight="w500"),
                    ft.Text(unit, size=13, color=TEXT_SEC),
                ]),
                ft.Text(sub, size=11, color=TEXT_TERT),
            ],
        ),
    )


def alarm_row(icon, text, detail_ref, is_warn=False):
    icon_bg  = WARN_BG if is_warn else OK_BG
    icon_clr = WARN_TXT if is_warn else OK_TXT
    return ft.Container(
        border=bdr(bottom=1), padding=pad(v=8),
        content=ft.Row(controls=[
            ft.Container(
                width=24, height=24, bgcolor=icon_bg, border_radius=6,
                content=ft.Icon(icon, size=14, color=icon_clr),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Text(text, size=13, expand=True),
            ft.Text("--", ref=detail_ref, size=12, color=TEXT_SEC),
        ]),
    )


CHART_H = 130


def interactive_chart_card(title, legend_items, img_ref, on_click_card):
    legend = [
        ft.Row(spacing=4, controls=[
            ft.Container(width=8, height=8, bgcolor=c, border_radius=4),
            ft.Text(lbl, size=11, color=TEXT_SEC),
        ])
        for c, lbl in legend_items
    ]

    return ft.GestureDetector(
        on_tap=on_click_card,
        mouse_cursor=ft.MouseCursor.CLICK,
        expand=True,
        content=ft.Container(
            bgcolor=BG_CARD, border_radius=12, border=bdr(1),
            padding=pad(all_=16),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(title, size=13, weight="w500"),
                            ft.Row(spacing=12, controls=legend),
                        ],
                    ),
                    ft.Image(
                        ref=img_ref,
                        src="data:image/svg+xml;base64,",
                        height=CHART_H,
                        fit=ft.BoxFit.FILL,
                        expand=True,
                    ),
                    ft.Text(
                        "➔ Clic para ampliar y ver valores detallados",
                        size=10, color=BLUE, weight="w500", italic=True,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
            ),
        )
    )


# ── Aplicación Principal ──────────────────────────────────────────────────────

def main(page: ft.Page):
    page.title         = "SCADA -- Analizador de Red Profesional"
    page.bgcolor       = BG_PAGE
    page.padding       = 20
    page.window.width  = 960
    page.window.height = 880
    page.scroll        = ft.ScrollMode.AUTO  

    # Referencias de UI principal
    ref_v  = ft.Ref[ft.Text]()
    ref_i  = ft.Ref[ft.Text]()
    ref_p  = ft.Ref[ft.Text]()
    ref_f  = ft.Ref[ft.Text]()
    ref_ts = ft.Ref[ft.Text]()

    ref_al_v = ft.Ref[ft.Text]()
    ref_al_f = ft.Ref[ft.Text]()
    ref_al_i = ft.Ref[ft.Text]()

    ref_e_total = ft.Ref[ft.Text]()
    ref_e_avg   = ft.Ref[ft.Text]()
    ref_e_today = ft.Ref[ft.Text]()

    ref_chart_vi = ft.Ref[ft.Image]()
    ref_chart_p  = ft.Ref[ft.Image]()

    # Variables de control para la ventana interactiva flotante (Modal)
    current_expanded_type = None  
    
    ref_dialog_title = ft.Ref[ft.Text]()
    ref_dialog_img   = ft.Ref[ft.Image]()
    ref_dialog_stat1 = ft.Ref[ft.Text]()
    ref_dialog_stat2 = ft.Ref[ft.Text]()

    # Datos históricos básicos
    v_hist = [220.0 + random.uniform(-1, 1) for _ in range(HIST_N)]
    i_hist = [2.0  + random.uniform(-0.2, 0.2) for _ in range(HIST_N)]
    p_hist = [v * ii * 0.85 for v, ii in zip(v_hist, i_hist)]

    # Renderizadores locales (Ventana chica con zoom quirúrgico 215V - 225V)
    def render_vi():
        ref_chart_vi.current.src = svg_to_src(
            svg_dual(v_hist, i_hist, BLUE, AMBER, unit_y1="V", unit_y2="A", min_y=215, max_y=225)
        )

    def render_p():
        ref_chart_p.current.src = svg_to_src(
            svg_single(p_hist, PURPLE, unit_y="W", min_y=0, max_y=3000, filled=True)
        )

    # ── Gestión de la Ventana Flotante Interactiva ─────────────────────────────
    def close_dialog(e):
        nonlocal current_expanded_type
        current_expanded_type = None
        modal_dialog.open = False
        modal_dialog.update()

    modal_dialog = ft.AlertDialog(
        title=ft.Text("Detalle del Histórico", ref=ref_dialog_title, size=16, weight="w600"),
        content=ft.Container(
            width=700,
            height=360,
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Image(ref=ref_dialog_img, src="", width=640, height=220, fit=ft.BoxFit.FILL),
                    
                    ft.Container(
                        bgcolor="#F4F3EE", padding=12, border_radius=8, border=bdr(1),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text("MÉTRICAS DETALLADAS (VENTANA DE 60 SEGUNDOS):", size=10, weight="bold", color=TEXT_SEC),
                                ft.Text("", ref=ref_dialog_stat1, size=12, color="#2B2B2A"),
                                ft.Text("", ref=ref_dialog_stat2, size=12, color="#2B2B2A"),
                            ]
                        )
                    )
                ]
            )
        ),
        actions=[
            ft.TextButton("Cerrar Ventana", on_click=close_dialog)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(modal_dialog)

    # Ventana grande: rango macro 0V-500V
    def update_dialog_data():
        if current_expanded_type == "VI":
            ref_dialog_img.current.src = svg_to_src(
                svg_dual(v_hist, i_hist, BLUE, AMBER, unit_y1="V", unit_y2="A", W=640, H=220, min_y=0, max_y=500)
            )
            ref_dialog_stat1.current.value = f"Tensión ➔ Actual: {v_hist[-1]:.1f} V  |  Máxima: {max(v_hist):.1f} V  |  Mínima: {min(v_hist):.1f} V"
            ref_dialog_stat2.current.value = f"Corriente ➔ Actual: {i_hist[-1]:.1f} A  |  Máxima: {max(i_hist):.1f} A  |  Promedio: {sum(i_hist)/len(i_hist):.2f} A"
        
        elif current_expanded_type == "P":
            ref_dialog_img.current.src = svg_to_src(
                svg_single(p_hist, PURPLE, unit_y="W", W=640, H=220, min_y=0, max_y=3000, filled=True)
            )
            ref_dialog_stat1.current.value = f"Potencia Activa ➔ Actual: {p_hist[-1]:.0f} W  |  Pico Máximo: {max(p_hist):.0f} W"
            ref_dialog_stat2.current.value = f"Energía Promedio en Ventana: {sum(p_hist)/len(p_hist):.1f} W"

    def open_vi_expanded(e):
        nonlocal current_expanded_type
        current_expanded_type = "VI"
        ref_dialog_title.current.value = "Análisis Clínico: Tensión (V) y Corriente (A)"
        modal_dialog.open = True
        update_dialog_data()
        modal_dialog.update()

    def open_p_expanded(e):
        nonlocal current_expanded_type
        current_expanded_type = "P"
        ref_dialog_title.current.value = "Análisis Clínico: Potencia Activa de Carga (W)"
        modal_dialog.open = True
        update_dialog_data()
        modal_dialog.update()


    # ── Histórico Semanal de Barras ───────────────────────────────────────────
    days_labels = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Hoy"]
    week_data   = [18.4, 22.1, 19.8, 24.3, 20.7, 23.5, 0.1]
    MAX_DAY     = 30.0
    today_accum = [0.1]

    bar_refs = [ft.Ref[ft.Container]() for _ in range(7)]
    val_refs = [ft.Ref[ft.Text]()      for _ in range(7)]

    def build_day_col(idx):
        is_today   = idx == 6
        fill_color = CORAL if is_today else PURPLE
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=3,
            controls=[
                ft.Container(
                    width=36, height=80, bgcolor="#E8E7E0", border_radius=4,
                    content=ft.Stack(controls=[
                        ft.Container(
                            ref=bar_refs[idx], bgcolor=fill_color,
                            border_radius=brad(tl=4, tr=4),
                            bottom=0, left=0, right=0,
                            height=int((week_data[idx] / MAX_DAY) * 80),
                            opacity=1.0 if is_today else 0.65,
                        ),
                    ]),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Text(days_labels[idx], size=10, color=TEXT_SEC),
                ft.Text(f"{week_data[idx]:.1f}", ref=val_refs[idx],
                        size=10, weight="w500",
                        color=CORAL if is_today else None),
                ft.Text("kWh", size=9, color=TEXT_TERT),
            ],
        )

    week_columns = [build_day_col(i) for i in range(7)]


    # ── Tarea Asíncrona SCADA (Ejecución Directa de Interfaz cada 5s) ─────────
    async def scada_update_task():
        """
        Bucle asíncrono controlado que corre directamente dentro del ciclo
        de renderizado principal de Flet. Actualiza todo de manera automática inmediata.
        """
        heladera_on = False
        contador_ciclos = 0

        while True:
            try:
                contador_ciclos += 1
                
                # Generación de la simulación
                v = round(random.uniform(217.5, 223.8), 1)
                i_base = 1.2
                if contador_ciclos % 4 == 0:
                    heladera_on = not heladera_on
                i_heladera = random.uniform(2.2, 3.2) if heladera_on else 0.0
                
                ii = round(i_base + i_heladera + random.uniform(-0.1, 0.1), 1)
                fp = 0.95 if ii > 3 else round(random.uniform(0.82, 0.86), 2)
                p  = round(v * ii * fp, 0)
                f  = round(random.uniform(49.95, 50.05), 2)

                # Escribir en UI
                ref_v.current.value = str(v)
                ref_i.current.value = str(ii)
                ref_p.current.value = f"{p / 1000:.2f}"
                ref_f.current.value = str(f)

                ref_al_v.current.value = f"{v} V"
                ref_al_f.current.value = f"{f} Hz"
                ref_al_i.current.value = f"{ii} A / lim 15 A"

                # Mutar listas históricas
                v_hist.append(v);  v_hist.pop(0)
                i_hist.append(ii); i_hist.pop(0)
                p_hist.append(p);  p_hist.pop(0)

                # Renderizar SVGs
                render_vi()
                render_p()

                # Cálculo semanal energético
                today_accum[0] += (p / 1000) / 3600 * INTERVAL_S
                week_data[6] = round(today_accum[0], 2)

                total = sum(week_data)
                ref_e_total.current.value = f"{total:.1f}"
                ref_e_avg.current.value   = f"{total / len(week_data):.1f} kWh"
                ref_e_today.current.value = f"Hoy: {week_data[6]:.2f} kWh"

                for k in range(7):
                    pct = week_data[k] / MAX_DAY
                    bar_refs[k].current.height = max(2, int(pct * 80))
                    val_refs[k].current.value  = f"{week_data[k]:.1f}"

                ref_ts.current.value = datetime.now().strftime("%d/%m/%Y  |  %H:%M:%S")

                # Si el modal está abierto en primer plano, lo actualizamos vivo
                if current_expanded_type is not None:
                    update_dialog_data()
                    modal_dialog.update()

                # Actualiza la página de forma inmediata y real
                page.update()

            except Exception as exc:
                print(f"Error en bucle asíncrono: {exc}")
                
            # Espera exactamente 5 segundos sin congelar la UI
            await asyncio.sleep(INTERVAL_S)


    # ── Armado del Dashboard de Controles Directos ─────────────────────────────
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Row(spacing=10, controls=[
                ft.Container(width=10, height=10, bgcolor=OK_TXT, border_radius=5),
                ft.Text("Analizador de Red -- Monofasico", size=15, weight="w500"),
                ft.Container(
                    bgcolor=OK_BG, border_radius=6, padding=pad(h=10, v=3),
                    content=ft.Text("SCADA Activo", size=12, color=OK_TXT, weight="w500"),
                ),
            ]),
            ft.Text("", ref=ref_ts, size=12, color=TEXT_SEC),
        ],
    )

    cards_row = ft.Row(
        spacing=12,
        controls=[
            metric_card("Tension",     ref_v, "V",  "Nominal: 220 V",   BLUE),
            metric_card("Corriente",   ref_i, "A",  "Estable",          AMBER),
            metric_card("Pot. activa", ref_p, "kW", "Monitoreo",         GREEN),
            metric_card("Frecuencia",  ref_f, "Hz", "Nominal: 50 Hz",   TEAL),
        ],
    )

    charts_row = ft.Row(
        spacing=12,
        controls=[
            interactive_chart_card(
                "Tension y corriente -- Ultimos 60 s",
                [(BLUE, "Tension (V)"), (AMBER, "Corriente (A)")],
                ref_chart_vi,
                on_click_card=open_vi_expanded 
            ),
            interactive_chart_card(
                "Consumo -- Ultimos 60 s",
                [(PURPLE, "Potencia (W)")],
                ref_chart_p,
                on_click_card=open_p_expanded 
            ),
        ],
    )

    weekly_card = ft.Container(
        bgcolor=BG_CARD, border_radius=12, border=bdr(1), padding=pad(all_=16),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Container(height=2, bgcolor=CORAL, border_radius=2),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=4, controls=[
                            ft.Text("Consumo total semana", size=12, color=TEXT_SEC),
                            ft.Row(spacing=4, controls=[
                                ft.Text("--", ref=ref_e_total, size=26, weight="w500"),
                                ft.Text("kWh", size=13, color=TEXT_SEC),
                            ]),
                        ]),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=2,
                            controls=[
                                ft.Text("Promedio diario", size=11, color=TEXT_TERT),
                                ft.Text("--", ref=ref_e_avg, size=15, weight="w500"),
                                ft.Text("--", ref=ref_e_today, size=11, color=TEXT_TERT),
                            ],
                        ),
                    ],
                ),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=week_columns),
            ],
        ),
    )

    alarms_card = ft.Container(
        bgcolor=BG_CARD, border_radius=12, border=bdr(1), padding=pad(h=16, v=4),
        content=ft.Column(
            spacing=0,
            controls=[
                alarm_row(ft.Icons.CHECK_CIRCLE_OUTLINE, "Tension Estable (Rango Normal)", ref_al_v),
                alarm_row(ft.Icons.CHECK_CIRCLE_OUTLINE, "Frecuencia Filtro Activo", ref_al_f),
                alarm_row(ft.Icons.INFO_OUTLINE, "Analisis de Red Modulo Ventanas Flotantes", ref_al_i),
            ],
        ),
    )

    # Inyección en canvas
    page.add(
        header,
        section_title("Mediciones en tiempo real"),
        cards_row,
        section_title("Graficos SCADA (Haz clic en cualquiera para expandir el analisis)"),
        charts_row,
        section_title("Registro semanal acumulado"),
        weekly_card,
        section_title("Estado y diagnosticos"),
        alarms_card,
        ft.Container(height=20),
    )

    # Carga primaria e inicialización estática básica
    ref_ts.current.value = datetime.now().strftime("%d/%m/%Y  |  %H:%M:%S")
    for k in range(7):
        pct = week_data[k] / MAX_DAY
        bar_refs[k].current.height = max(2, int(pct * 80))
        val_refs[k].current.value  = f"{week_data[k]:.1f}"

    total = sum(week_data)
    ref_e_total.current.value = f"{total:.1f}"
    ref_e_avg.current.value   = f"{total / len(week_data):.1f} kWh"
    ref_e_today.current.value = f"Hoy: {week_data[6]:.2f} kWh"

    render_vi()
    render_p()
    page.update()

    # Lanzar la tarea asíncrona oficial que refresca todo automáticamente
    page.run_task(scada_update_task)


if __name__ == "__main__":
    ft.run(main)