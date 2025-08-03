import streamlit as st
from playwright.sync_api import sync_playwright
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from datetime import date

st.set_page_config(page_title="Saturazione Strutture Ricettive", layout="centered")

def get_strutture(comune, checkin=None, checkout=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.booking.com")

        page.fill("input[name='ss']", comune)
        page.keyboard.press("Enter")
        page.wait_for_selector(".sr_property_block", timeout=10000)

        if checkin and checkout:
            checkin_str = checkin.strftime("%Y-%m-%d")
            checkout_str = checkout.strftime("%Y-%m-%d")
            url = f"https://www.booking.com/searchresults.html?ss={comune}&checkin={checkin_str}&checkout={checkout_str}"
            page.goto(url)
            page.wait_for_selector(".sr_property_block", timeout=10000)

        elements = page.query_selector_all(".sr_property_block")
        strutture = []
        for el in elements:
            name = el.query_selector(".sr-hotel__name")
            coord = el.get_attribute("data-coords")
            strutture.append({
                "name": name.inner_text().strip() if name else "Senza nome",
                "coords": coord
            })
        browser.close()
        return strutture

st.title("📊 Saturazione Strutture Ricettive")

with st.form("input_form"):
    comune = st.text_input("Comune", "La Spezia")
    checkin = st.date_input("Data check-in", date.today())
    checkout = st.date_input("Data check-out", date.today())
    submitted = st.form_submit_button("Verifica")

if submitted:
    with st.spinner("Recupero strutture..."):
        totali = get_strutture(comune)
        disponibili = get_strutture(comune, checkin, checkout)

    n_tot = len(totali)
    n_disp = len(disponibili)
    saturazione = round((n_tot - n_disp) / n_tot * 100, 2) if n_tot > 0 else 0

    st.success(f"Strutture disponibili: {n_disp} su {n_tot}")
    st.info(f"**Saturazione stimata:** {saturazione}%")

    # Grafico
    df = pd.DataFrame({
        "Stato": ["Disponibili", "Non Disponibili"],
        "Numero": [n_disp, n_tot - n_disp]
    })
    fig = px.pie(df, values="Numero", names="Stato", title="Distribuzione disponibilità")
    st.plotly_chart(fig)

    # Mappa
