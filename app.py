import io
import random
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")  # Bezpečný backend pro Streamlit
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from scheduler import SchedulePlaner

st.set_page_config(page_title="Happening Aplikace", layout="wide")

# --- KONSTANTY A DATA ---
schedule_planer = SchedulePlaner()

DEFAULT_PAUZA_MINUT: int = schedule_planer.DEFAULT_TRAVEL_TIME
POCET_SLOUPCU_MRIZKY: int = 4

VSECHNA_PREDSTAVENI: list[str] = schedule_planer.ALL_CLASSES
PREDSTAVENI_HEREC: list[str] = VSECHNA_PREDSTAVENI
KATEGORIE_POROTCE: list[str] = schedule_planer.REFEREE_CATEGORIES
POVINNA_PREDSTAVENI_POROTCE: dict[str, list[str]] = schedule_planer.REFEREE_MANDATORY

MISTNOSTI: list[str] = [  # Pouze pro testování
    "Hlavní scéna", "Komorní sál", "Divadelní klub", 
    "Sál pod střechou", "Zkušebna A", "Experimentální prostor"
]

# Responzivní CSS pro výběr představení (2 sloupce na mobilu, 4 na desktopu)
st.markdown(
    """
    <style>
    @media (max-width: 768px) {
        /* Přepínače představení se na mobilu zobrazí ve 2 sloupcích vedle sebe */
        [data-testid="stHorizontalBlock"]:has([data-testid="stToggle"]) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 0.5rem 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has([data-testid="stToggle"]) > [data-testid="column"] {
            min-width: 48% !important;
            flex: 1 1 48% !important;
            padding: 0 4px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ==========================================
# POMOCNÉ FUNKCE PRO EXPORT
# ==========================================
def vytvor_graficky_rozvrh(rozvrh_data: list[dict], format_souboru: str = "pdf") -> bytes:
    """
    Vygeneruje čistou tabulku rozvrhu jako PDF nebo obrázek (PNG) pomocí Matplotlibu.
    """
    df = pd.DataFrame(rozvrh_data).sort_values(by="Čas konce", ascending=True).reset_index(drop=True)
    vyska = max(2.5, len(df) * 0.45 + 1.2)
    fig, ax = plt.subplots(figsize=(10, vyska))
    ax.axis("off")
    ax.axis("tight")

    tabulka = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc="center",
        cellLoc="center"
    )
    tabulka.auto_set_font_size(False)
    tabulka.set_fontsize(10)
    tabulka.scale(1.15, 1.7)

    for (row, col), bunka in tabulka.get_celld().items():
        if row == 0:
            bunka.set_text_props(weight="bold", color="white")
            bunka.set_facecolor("#1E3D59")
        else:
            bunka.set_facecolor("#F7F9FB" if row % 2 == 0 else "#FFFFFF")

    buf = io.BytesIO()
    fig.savefig(buf, format=format_souboru, bbox_inches="tight", dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def vykresli_tlacitka_exportu(rozvrh_data: list[dict], prefix_souboru: str):
    """
    Zobrazí dvě vyrovnaná tlačítka pro stažení do PDF a PNG.
    """
    if not rozvrh_data:
        return

    st.write("#### Možnosti exportu")
    col_pdf, col_png = st.columns(2)

    with col_pdf:
        pdf_bytes = vytvor_graficky_rozvrh(rozvrh_data, "pdf")
        st.download_button(
            label="📄 Stáhnout jako PDF",
            data=pdf_bytes,
            file_name=f"{prefix_souboru}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_png:
        png_bytes = vytvor_graficky_rozvrh(rozvrh_data, "png")
        st.download_button(
            label="🖼️ Stáhnout jako Obrázek (PNG)",
            data=png_bytes,
            file_name=f"{prefix_souboru}.png",
            mime="image/png",
            use_container_width=True
        )


# --- STAV APLIKACE ---
if "krok" not in st.session_state:
    st.session_state["krok"] = "vyber_role"
if "role" not in st.session_state:
    st.session_state["role"] = None
if "vybrana_polozka" not in st.session_state:
    st.session_state["vybrana_polozka"] = None
if "generovany_rozvrh" not in st.session_state:
    st.session_state["generovany_rozvrh"] = []
if "vyplneny_rozvrh" not in st.session_state:
    st.session_state["vyplneny_rozvrh"] = []
if "vybrana_predstaveni" not in st.session_state:
    st.session_state["vybrana_predstaveni"] = []
if "cas_na_presun" not in st.session_state:
    st.session_state["cas_na_presun"] = DEFAULT_PAUZA_MINUT


def reset_stavu():
    for key in list(st.session_state.keys()):
        if key.startswith("toggle_") or key.startswith("locked_"):
            del st.session_state[key]
    st.session_state["krok"] = "vyber_role"
    st.session_state["role"] = None
    st.session_state["vybrana_polozka"] = None
    st.session_state["generovany_rozvrh"] = []
    st.session_state["vyplneny_rozvrh"] = []
    st.session_state["vybrana_predstaveni"] = []
    st.session_state["cas_na_presun"] = DEFAULT_PAUZA_MINUT


def vykresli_stred():
    st.write("")
    st.write("")
    _, center_col, _ = st.columns([1, 2, 1])
    return center_col


# ==========================================
# KROK 1: VÝBĚR ROLE
# ==========================================
if st.session_state["krok"] == "vyber_role":
    with vykresli_stred():
        st.markdown("<h2 style='text-align: center;'>Vyberte svou roli</h2>", unsafe_allow_html=True)
        st.write("")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🎭 Herec", use_container_width=True):
                st.session_state["role"] = "Herec"
                st.session_state["krok"] = "vyber_detail"
                st.rerun()

        with col2:
            if st.button("⚖️ Porotce", use_container_width=True):
                st.session_state["role"] = "Porotce"
                st.session_state["krok"] = "vyber_detail"
                st.rerun()

        with col3:
            if st.button("👥 Divák", use_container_width=True):
                st.session_state["role"] = "Divák"
                st.session_state["vybrana_polozka"] = None
                st.session_state["krok"] = "panel"
                st.rerun()

# ==========================================
# KROK 2: DETAILNÍ VÝBĚR (Herec / Porotce)
# ==========================================
elif st.session_state["krok"] == "vyber_detail":
    with vykresli_stred():
        role = st.session_state["role"]

        if role == "Herec":
            st.markdown("<h2 style='text-align: center;'>V jakém představení hraješ?</h2>", unsafe_allow_html=True)
            volba = st.selectbox("Vyber své představení:", options=PREDSTAVENI_HEREC)

        elif role == "Porotce":
            st.markdown("<h2 style='text-align: center;'>Co hodnotíš?</h2>", unsafe_allow_html=True)
            volba = st.selectbox("Vyber kategorii hodnocení:", options=KATEGORIE_POROTCE)

        col_back, col_next = st.columns(2)
        with col_back:
            if st.button("⬅️ Zpět na výběr role", use_container_width=True):
                reset_stavu()
                st.rerun()
        with col_next:
            if st.button("Potvrdit a vstoupit ➡️", use_container_width=True):
                st.session_state["vybrana_polozka"] = volba
                st.session_state["krok"] = "panel"
                st.rerun()

# ==========================================
# KROK 3: PANEL
# ==========================================
elif st.session_state["krok"] == "panel":
    role = st.session_state["role"]
    detail = st.session_state["vybrana_polozka"]

    varovna_lista_placeholder = st.empty()

    top_left, top_right = st.columns([3, 1])
    with top_left:
        st.title(f"Panel: {role}")
        if role == "Herec":
            st.caption(f"🎭 Hraješ v: **{detail}** (představení je automaticky zamčeno)")
        elif role == "Porotce":
            st.caption(f"⚖️ Hodnotíš: **{detail}** (povinná představení jsou zamčena)")
        elif role == "Divák":
            st.caption("👥 Výběr je plně na tobě, žádná představení nejsou uzamčena.")

    with top_right:
        st.write("")
        if st.button("🔄 Změnit roli", use_container_width=True):
            reset_stavu()
            st.rerun()

    st.divider()

    # Vstup času
    col_time, _ = st.columns([1, 2])
    with col_time:
        cas_mezi_predstavenimi = st.number_input(
            "Požadovaný čas mezi představeními (v minutách):",
            value=int(st.session_state.get("cas_na_presun", DEFAULT_PAUZA_MINUT)),
            step=5,
            help="Časový prostor potřebný na přesun a odpočinek mezi hrami (povoleno 0 až 1000 min)."
        )

    # Validace
    cas_je_platny = (
        cas_mezi_predstavenimi is not None 
        and 0 <= cas_mezi_predstavenimi <= 1000
    )

    st.write("### Výběr představení")

    zamknuta_predstaveni: set[str] = set()
    if role == "Herec" and detail:
        zamknuta_predstaveni.add(detail)
    elif role == "Porotce" and detail:
        zamknuta_predstaveni.update(POVINNA_PREDSTAVENI_POROTCE.get(detail, []))

    vybrana_predstaveni: list[str] = []

    # Vykreslení řádek po řádku pro zachování přesného pořadí na mobilu i počítači
    for i in range(0, len(VSECHNA_PREDSTAVENI), POCET_SLOUPCU_MRIZKY):
        radek = VSECHNA_PREDSTAVENI[i:i + POCET_SLOUPCU_MRIZKY]
        cols = st.columns(POCET_SLOUPCU_MRIZKY)
        for idx, hra in enumerate(radek):
            with cols[idx]:
                je_zamknuto = hra in zamknuta_predstaveni

                if je_zamknuto:
                    st.toggle(
                        label=f"🔒 **{hra}**",
                        value=True,
                        disabled=True,
                        key=f"locked_{hra}",
                        help="Toto představení je pro tebe povinné."
                    )
                    vybrana_predstaveni.append(hra)
                else:
                    aktivni = st.toggle(
                        label=hra,
                        key=f"toggle_{hra}"
                    )
                    if aktivni:
                        vybrana_predstaveni.append(hra)

    # Vyhodnocení f1 se spustí jen při validním čase
    if role == "Herec":
        vysledek_f1 = schedule_planer.check_priority_schedule(detail, None, vybrana_predstaveni, int(cas_mezi_predstavenimi)) if cas_je_platny else None
    elif role == "Porotce":
        vysledek_f1 = schedule_planer.check_priority_schedule(None, detail, vybrana_predstaveni, int(cas_mezi_predstavenimi)) if cas_je_platny else None
    else:
        vysledek_f1 = schedule_planer.check_priority_schedule(None, None, vybrana_predstaveni, int(cas_mezi_predstavenimi)) if cas_je_platny else None

    # Zobrazení varování
    if not cas_je_platny:
        varovna_lista_placeholder.markdown(
            """
            <div style="
                min-height: 52px; padding: 12px 18px; margin-bottom: 1rem;
                background-color: rgba(244, 67, 54, 0.16); border: 1px solid rgba(244, 67, 54, 0.45);
                border-radius: 8px; display: flex; align-items: center; gap: 12px; font-size: 15px; box-sizing: border-box;
            ">
                <span style="font-size: 20px; line-height: 1;">❌</span>
                <span><b>Chyba:</b> Čas na přesun musí být v rozmezí <b>0 až 1000 minut</b>.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif vysledek_f1 is None:
        varovna_lista_placeholder.markdown(
            """
            <div style="
                min-height: 52px; padding: 12px 18px; margin-bottom: 1rem;
                background-color: rgba(255, 179, 0, 0.16); border: 1px solid rgba(255, 179, 0, 0.45);
                border-radius: 8px; display: flex; align-items: center; gap: 12px; font-size: 15px; box-sizing: border-box;
            ">
                <span style="font-size: 20px; line-height: 1;">⚠️</span>
                <span><b>Varování:</b> Všechna tato představení nejde najednou projít. Uprav výběr nebo zkrať čas na přesun.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        varovna_lista_placeholder.markdown(
            """
            <div style="
                min-height: 52px; padding: 12px 18px; margin-bottom: 1rem;
                border: 1px solid transparent; border-radius: 8px; visibility: hidden; box-sizing: border-box;
            ">&nbsp;</div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Tlačítko pro generování
    col_btn_spacer1, col_action, col_btn_spacer2 = st.columns([1, 2, 1])
    with col_action:
        tlacitko_zakazano = (not cas_je_platny) or (vysledek_f1 is None)

        if not cas_je_platny:
            napoveda_tlacitka = "Opravte neplatný čas na přesun (musí být 0 až 1000 min)."
        elif vysledek_f1 is None:
            napoveda_tlacitka = "Pro vygenerování rozvrhu nejprve vyřešte varování výše."
        else:
            napoveda_tlacitka = "Kliknutím sestavíte časový harmonogram."

        if st.button(
            "📅 Vygenerovat rozvrh",
            type="primary",
            use_container_width=True,
            disabled=tlacitko_zakazano,
            help=napoveda_tlacitka
        ):
            herec_hra = detail if role == "Herec" else None
            porotce_kat = detail if role == "Porotce" else None

            st.session_state["vybrana_predstaveni"] = vybrana_predstaveni
            st.session_state["cas_na_presun"] = int(cas_mezi_predstavenimi)

            priority_result = schedule_planer.make_priority_schedule(herec_hra, porotce_kat, vybrana_predstaveni, int(cas_mezi_predstavenimi))
            st.session_state["generovany_rozvrh"] = priority_result[0]
            st.session_state["list_performances"] = priority_result[1]

            st.session_state["krok"] = "result"
            st.rerun()

# ==========================================
# KROK 4: RESULT (PRIORITNÍ ROZVRH)
# ==========================================
elif st.session_state["krok"] == "result":
    role = st.session_state["role"]
    rozvrh_data = st.session_state["generovany_rozvrh"]

    col_title, col_back = st.columns([3, 1])
    with col_title:
        st.title("📋 Prioritní harmonogram")
        st.caption(f"Role: **{role}** | Celkem vybráno her: **{len(rozvrh_data)}**")
    with col_back:
        st.write("")
        if st.button("⬅️ Zpět na úpravu výběru", use_container_width=True):
            st.session_state["krok"] = "panel"
            st.rerun()

    st.divider()

    if not rozvrh_data:
        st.info("Nebylo vybráno žádné představení k naplánování.")
    else:
        df_rozvrh = pd.DataFrame(rozvrh_data).sort_values(by="Čas konce", ascending=True).reset_index(drop=True)
        st.dataframe(
            df_rozvrh,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Představení": st.column_config.TextColumn("Název hry", width="large"),
                "Místnost": st.column_config.TextColumn("Místnost / Sál", width="medium"),
                "Čas začátku": st.column_config.TextColumn("Začátek", width="small"),
                "Čas konce": st.column_config.TextColumn("Konec", width="small"),
                "Délka": st.column_config.TextColumn("Trvání", width="small"),
            }
        )

        vykresli_tlacitka_exportu(rozvrh_data, prefix_souboru="harmonogram_predstaveni")

    st.divider()

    col_res_sp1, col_res_action, col_res_sp2 = st.columns([1, 2, 1])
    with col_res_action:
        if st.button("✍️ Vyplnit rozvrh", type="primary", use_container_width=True):
            st.session_state["vyplneny_rozvrh"] = schedule_planer.fill_priority_schedule(
                st.session_state["list_performances"],
                st.session_state["cas_na_presun"],
                VSECHNA_PREDSTAVENI
            )
            st.session_state["krok"] = "result_filled"
            st.rerun()

# ==========================================
# KROK 5: RESULT_FILLED (DOPLNĚNÝ ROZVRH)
# ==========================================
elif st.session_state["krok"] == "result_filled":
    role = st.session_state["role"]
    vyplneny_data = st.session_state["vyplneny_rozvrh"]

    col_title, col_back = st.columns([3, 1])
    with col_title:
        st.title("✅ Vyplněný rozvrh")
        st.caption(f"Role: **{role}** | Celkem položek harmonogramu: **{len(vyplneny_data)}**")
    with col_back:
        st.write("")
        if st.button("⬅️ Zpět na předchozí rozvrh", use_container_width=True):
            st.session_state["krok"] = "result"
            st.rerun()

    st.divider()

    if not vyplneny_data:
        st.info("V rozvrhu nejsou žádná představení.")
    else:
        df_vyplneny = pd.DataFrame(vyplneny_data)
        st.dataframe(
            df_vyplneny,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Představení": st.column_config.TextColumn("Název programu", width="large"),
                "Místnost": st.column_config.TextColumn("Místnost / Sál", width="medium"),
                "Čas začátku": st.column_config.TextColumn("Začátek", width="small"),
                "Čas konce": st.column_config.TextColumn("Konec", width="small"),
                "Délka": st.column_config.TextColumn("Trvání", width="small"),
            }
        )

        vykresli_tlacitka_exportu(vyplneny_data, prefix_souboru="vyplneny_rozvrh")

    st.divider()

    col_bottom_sp1, col_bottom_action, col_bottom_sp2 = st.columns([1, 2, 1])
    with col_bottom_action:
        if st.button("🔄 Začít od začátku (Nová role)", use_container_width=True):
            reset_stavu()
            st.rerun()