import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os
import hashlib
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

import glob
import plotly.graph_objects as go

# --- NIEUWE FUNCTIES VOOR DE DIRECTIE (ANONIEM) ---
def load_all_school_data():
    """Laadt alle CSV's uit de map, voegt ze samen en verwijdert namen."""
    all_lessons = []
    all_days = []
    
    # 1. Alle lesbestanden samenvoegen
    lesson_files = glob.glob(f"{DATA_DIR}/*_lessons.csv")
    for f in lesson_files:
        try:
            df = pd.read_csv(f)
            all_lessons.append(df)
        except:
            pass
            
    # 2. Alle dagbestanden samenvoegen
    day_files = glob.glob(f"{DATA_DIR}/*_day.csv")
    for f in day_files:
        try:
            df = pd.read_csv(f)
            all_days.append(df)
        except:
            pass

    # Samenvoegen (indien data aanwezig)
    df_lessons_total = pd.concat(all_lessons, ignore_index=True) if all_lessons else pd.DataFrame()
    df_days_total = pd.concat(all_days, ignore_index=True) if all_days else pd.DataFrame()
    
    return df_days_total, df_lessons_total

import plotly.colors as pc

def draw_ridgeline_artistic(df, kolom, titel, basis_kleur_naam="Teal"):
    """
    Maakt een 'Joyplot' met overlappende 'bergen' en een gradiënt.
    """
    if df.empty: return None
    
    klassen = sorted(df["Klas"].unique(), reverse=True)
    fig = go.Figure()

    # Genereer een kleurenpalet op basis van het aantal klassen
    # We pakken een spectrum (bijv. Teal of Sunset)
    colors = px.colors.sample_colorscale(basis_kleur_naam, [n/(len(klassen)) for n in range(len(klassen))])

    for i, klas in enumerate(klassen):
        df_k = df[df["Klas"] == klas]
        
        fig.add_trace(go.Violin(
            x=df_k[kolom],
            y=[klas] * len(df_k),
            name=klas,
            side='positive', 
            orientation='h', 
            width=2.5,  # Breder = meer overlap = mooier effect
            line_color='white', # Witte rand maakt het 'clean'
            line_width=1,
            fillcolor=colors[i], # Gradiënt kleur
            opacity=0.8,
            points=False,
            meanline_visible=False # Geen harde lijnen
        ))

    fig.update_layout(
        title=dict(text=titel, font=dict(size=20, family="Arial", color="#333")),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        height=120 + (len(klassen) * 40),
        margin=dict(l=0, r=0, t=50, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(range=[0.5, 5.5], showgrid=False, zeroline=False, visible=True),
        yaxis=dict(showgrid=False, showline=False, showticklabels=True)
    )
    return fig

def draw_sankey_butterfly(df):
    """
    Creëert een Butterfly Sankey: Negatief (links) -> Klassen (midden) -> Positief (rechts).
    """
    if df.empty: return None
    
    # 1. Data Voorbereiding
    def clean_labels(df, kolom):
        temp = df.copy()
        temp[kolom] = temp[kolom].astype(str).str.split(',')
        temp = temp.explode(kolom)
        temp[kolom] = temp[kolom].str.strip()
        return temp[(temp[kolom] != 'nan') & (temp[kolom] != '')]

    df_pos = clean_labels(df, 'Positief')
    df_neg = clean_labels(df, 'Negatief')

    counts_pos = df_pos.groupby(['Klas', 'Positief']).size().reset_index(name='Aantal')
    counts_neg = df_neg.groupby(['Negatief', 'Klas']).size().reset_index(name='Aantal')

    # 2. Nodes bepalen (Negatief -> Klassen -> Positief)
    neg_uniek = sorted(list(counts_neg['Negatief'].unique()))
    klassen_uniek = sorted(list(df['Klas'].unique()))
    pos_uniek = sorted(list(counts_pos['Positief'].unique()))
    
    all_nodes = neg_uniek + klassen_uniek + pos_uniek
    node_map = {name: i for i, name in enumerate(all_nodes)}

    # 3. Kleuren voor de Nodes
    # Roodachtig voor negatief, Grijs voor klassen, Groenachtig voor positief
    node_colors = (["#ff7675"] * len(neg_uniek) + 
                   ["#636e72"] * len(klassen_uniek) + 
                   ["#55efc4"] * len(pos_uniek))

    # 4. Links opbouwen
    sources = []
    targets = []
    values = []
    link_colors = []

    # Negatief -> Klas (Links naar Midden)
    for _, row in counts_neg.iterrows():
        sources.append(node_map[row['Negatief']])
        targets.append(node_map[row['Klas']])
        values.append(row['Aantal'])
        link_colors.append("rgba(214, 48, 49, 0.3)") # Transparant rood

    # Klas -> Positief (Midden naar Rechts)
    for _, row in counts_pos.iterrows():
        sources.append(node_map[row['Klas']])
        targets.append(node_map[row['Positief']])
        values.append(row['Aantal'])
        link_colors.append("rgba(0, 184, 148, 0.3)") # Transparant groen

    # 5. Dynamische Hoogte
    dynamic_height = max(600, len(all_nodes) * 35)

    fig = go.Figure(data=[go.Sankey(
        textfont=dict(size=13, color="black", family="Arial Black"),
        node = dict(
          pad = 35, thickness = 20,
          line = dict(color = "white", width = 1),
          label = [f" {n} " for n in all_nodes],
          color = node_colors
        ),
        link = dict(
          source = sources,
          target = targets,
          value = values,
          color = link_colors
        )
    )])

    fig.update_layout(
        title=dict(text="⚖️ Balans per Klas: Negatief vs Positief", font=dict(size=22)),
        height=dynamic_height,
        font=dict(size=12),
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig
# -------------------------------------------------
# CONFIG (mobile first)
# -------------------------------------------------
st.set_page_config(
    page_title="Leerkrachtenmonitor",
    page_icon="❤️",
    layout="centered"
)

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def normalize_email(email):
    return email.strip().lower()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def day_file(email):
    return f"{DATA_DIR}/{email.split('@')[0]}_day.csv"

def lesson_file(email):
    return f"{DATA_DIR}/{email.split('@')[0]}_lessons.csv"

# -------------------------------------------------
# USERS
# -------------------------------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=["email", "password", "role"]).to_csv(USERS_FILE, index=False)
    return pd.read_csv(USERS_FILE)

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

# -------------------------------------------------
# AUTO LOGIN (permanent)
# -------------------------------------------------
params = st.query_params
if "user" in params and "user" not in st.session_state:
    users = load_users()
    email = normalize_email(params["user"])
    u = users[users.email == email]
    if not u.empty:
        st.session_state.user = u.iloc[0].to_dict()

# -------------------------------------------------
# AUTH
# -------------------------------------------------
st.title("❤️ Leerkrachtenmonitor")
users = load_users()

if "user" not in st.session_state:
    tab1, tab2 = st.tabs(["🔐 Inloggen", "🆕 Registreren"])

    with tab1:
        email = normalize_email(st.text_input("E-mail", key="login_email"))
        pw = st.text_input("Wachtwoord", type="password", key="login_pw")
        remember = st.checkbox("Onthoud mij")

        if st.button("Inloggen"):
            u = users[users.email == email]
            if not u.empty and hash_pw(pw) == u.iloc[0].password:
                st.session_state.user = u.iloc[0].to_dict()
                if remember:
                    st.query_params["user"] = email
                st.rerun()
            else:
                st.error("Ongeldige login")

    with tab2:
        r_email = normalize_email(st.text_input("School-e-mail", key="reg_email"))
        r_pw = st.text_input("Wachtwoord", type="password", key="reg_pw")

        if st.button("Account aanmaken"):
            if r_email in users.email.values:
                st.error("Account bestaat al")
            else:
                role = "director" if r_email.startswith("directie") else "teacher"
                users.loc[len(users)] = [r_email, hash_pw(r_pw), role]
                save_users(users)
                st.success("Account aangemaakt")

    st.stop()

# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
user = st.session_state.user
st.sidebar.success(f"Ingelogd als {user['email']}")

if st.sidebar.button("Uitloggen"):
    st.query_params.clear()
    st.session_state.clear()
    st.rerun()

# -------------------------------------------------
# CONSTANTEN
# -------------------------------------------------
POS_MOODS = [
    "Inspirerend", "Motiverend", "Actief", "Verbonden",
    "Respectvol", "Gefocust", "Veilig", "Energiek"
]

NEG_MOODS = [
    "Demotiverend", "Passief", "Onrespectvol",
    "Chaotisch", "Afgeleid", "Spannend", "Onveilig"
]

KLASSEN = [
    "5ECWI", "5HW", "5ECMT", "5MT", "3HW",
    "6ECWI-HW", "6MT", "6WEWI", "6ECMT"
]

# -------------------------------------------------
# LOGIC CONTROLLER (ROLE BASED)
# -------------------------------------------------

# DIRECTIE VIEW
if user["role"] == "director":
    st.markdown("## 🏫 Dashboard Schoolwelzijn")
    st.markdown("---")
    
    df_days_all, df_lessons_all = load_all_school_data()
    
    if not df_lessons_all.empty:
        # --- TOP LEVEL METRICS (Clean style) ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Aantal Lessen", len(df_lessons_all))
        c2.metric("School Energie", f"{df_days_all['Energie'].mean():.1f}" if not df_days_all.empty else "-")
        c3.metric("School Stress", f"{df_days_all['Stress'].mean():.1f}" if not df_days_all.empty else "-")
        
        st.write("") # Spacer

        # --- ARTISTIEKE RIDGELINES ---
        st.subheader("🎨 Landschap van de Lessen")
        st.caption("De vorm toont de ervaring. Breed = verdeeldheid, Smal = consensus.")
        
        tab_ridge1, tab_ridge2 = st.tabs(["Lesaanpak (Blauw)", "Klasmanagement (Rood)"])
        
        with tab_ridge1:
            # We gebruiken 'Tealgrn' voor een rustige blauw/groene vibe
            fig_aanpak = draw_ridgeline_artistic(df_lessons_all, "Lesaanpak", "", "Tealgrn")
            st.plotly_chart(fig_aanpak, use_container_width=True)
            
        with tab_ridge2:
            # We gebruiken 'Purp' of 'Sunset' voor contrast
            fig_mgmt = draw_ridgeline_artistic(df_lessons_all, "Klasmanagement", "", "Sunset")
            st.plotly_chart(fig_mgmt, use_container_width=True)

        st.divider()

        # --- ARTISTIEKE SANKEY ---
        st.subheader("🌊 Emotionele Stromen")
        st.caption("Hoe klassen zich vertalen naar positieve ervaringen.")
        
        fig_sankey = draw_sankey_butterfly(df_lessons_all)
        if fig_sankey:
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.info("Nog niet genoeg data voor de flow-chart.")

    else:
        st.warning("Er is nog geen data beschikbaar van het team.")

# LEERKRACHT VIEW (JOUW ORIGINELE CODE)
else:
    DAY_FILE = day_file(user["email"])
    LES_FILE = lesson_file(user["email"])

    if not os.path.exists(DAY_FILE):
        pd.DataFrame(columns=["Datum", "Energie", "Stress"]).to_csv(DAY_FILE, index=False)

    if not os.path.exists(LES_FILE):
        pd.DataFrame(columns=[
            "Datum", "Klas", "Lesaanpak", "Klasmanagement", "Positief", "Negatief"
        ]).to_csv(LES_FILE, index=False)

    day_df = pd.read_csv(DAY_FILE)
    day_df["Datum"] = pd.to_datetime(day_df["Datum"], errors="coerce")
    day_df = day_df.dropna(subset=["Datum"])

    les_df = pd.read_csv(LES_FILE)
    les_df["Datum"] = pd.to_datetime(les_df["Datum"], errors="coerce")
    les_df = les_df.dropna(subset=["Datum"])

    tab1, tab2, tab3, tab4 = st.tabs([
        "🧠 Daggevoel", "📝 Lesregistratie", "📊 Visualisaties", "📄 Maandrapport"
    ])

    # -------------------------------------------------
    # DAGGEVOEL
    # -------------------------------------------------
    with tab1:
        with st.form("daggevoel", clear_on_submit=True):
            d = st.date_input("Datum", date.today())

            energie = st.slider("Energie", 1, 5, 3)
            st.caption("1 = uitgeput · 5 = barstend van energie")

            stress = st.slider("Stress", 1, 5, 3)
            st.caption("1 = volkomen rustig · 5 = enorm gestresseerd")

            if st.form_submit_button("Opslaan"):
                day_df.loc[len(day_df)] = [d, energie, stress]
                day_df.to_csv(DAY_FILE, index=False)
                st.success("Geregistreerd! ✔️")

    # -------------------------------------------------
    # LESREGISTRATIE
    # -------------------------------------------------
    with tab2:
        with st.form("lesregistratie", clear_on_submit=True):
            klas = st.selectbox("Klas", KLASSEN)

            lesaanpak = st.slider("Lesaanpak", 1, 5, 3)
            st.caption("1 = werkte niet · 5 = groot succes")

            klasmanagement = st.slider("Klasmanagement", 1, 5, 3)
            st.caption("1 = niet bij de les · 5 = volledig onder controle")

            st.markdown("**Positieve lesmood**")
            c1, c2 = st.columns(2)
            positief = []
            for i, m in enumerate(POS_MOODS):
                if (c1 if i % 2 == 0 else c2).checkbox(m, key=f"p_{m}"):
                    positief.append(m)

            st.markdown("**Negatieve lesmood**")
            c3, c4 = st.columns(2)
            negatief = []
            for i, m in enumerate(NEG_MOODS):
                if (c3 if i % 2 == 0 else c4).checkbox(m, key=f"n_{m}"):
                    negatief.append(m)

            # Let op: alles hieronder **ingesprongen** binnen de form
            if st.form_submit_button("Les opslaan"):
                # Unieke timestamp voor deze registratie
                timestamp = pd.Timestamp.now()
                
                new_row = {
                    "Datum": timestamp,
                    "Klas": klas,
                    "Lesaanpak": lesaanpak,
                    "Klasmanagement": klasmanagement,
                    "Positief": ", ".join(positief),
                    "Negatief": ", ".join(negatief)
                }
                
                # Voeg toe aan dataframe
                les_df = pd.concat([les_df, pd.DataFrame([new_row])], ignore_index=True)
                
                # Opslaan naar CSV
                les_df.to_csv(LES_FILE, index=False)
                
                st.success("Les opgeslagen ✔️")

    # -----------------------------
    # TAB 3: VISUALISATIES
    # -----------------------------
    with tab3:
        st.header("📊 Visualisaties")

        # 1. DAGGEVOEL LIJNGRAFIEK
        st.subheader("📈 Daggevoel (Energie & Stress)")
        if not day_df.empty:
            day_df_clean = day_df.copy()
            day_df_clean["Datum"] = pd.to_datetime(day_df_clean["Datum"], errors="coerce")
            day_df_clean = day_df_clean.dropna(subset=["Datum"]).sort_values("Datum")

            if not day_df_clean.empty:
                fig_line = px.line(
                    day_df_clean,
                    x="Datum",
                    y=["Energie", "Stress"],
                    markers=True,
                    title="Daggevoel door de tijd",
                    color_discrete_map={"Energie": "#2ecc71", "Stress": "#e74c3c"}
                )
                fig_line.update_layout(yaxis_range=[0.5, 5.5])
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Nog geen daggevoel geregistreerd.")

        st.divider()

        # 2. ALGEMENE STATISTIEKEN & WORDCLOUD
        st.subheader("🌍 Totaaloverzicht (Alle lessen)")
        
        if not les_df.empty:
            # --- NIEUW: Algemene gemiddeldes visueel weergeven ---
            avg_aanpak_totaal = les_df["Lesaanpak"].mean()
            avg_mgmt_totaal = les_df["Klasmanagement"].mean()

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Gem. Lesaanpak", f"{avg_aanpak_totaal:.2f} / 5")
            with col_m2:
                st.metric("Gem. Klasmanagement", f"{avg_mgmt_totaal:.2f} / 5")
            
            st.write("---") # Subtiele scheidingslijn tussen cijfers en WordCloud

            # --- WordCloud Logica ---
            pos_series = les_df["Positief"].dropna().astype(str).str.split(",").explode().str.strip()
            neg_series = les_df["Negatief"].dropna().astype(str).str.split(",").explode().str.strip()
            
            all_labels = pd.concat([
                pd.DataFrame({"Label": pos_series, "Type": "Positief"}),
                pd.DataFrame({"Label": neg_series, "Type": "Negatief"})
            ])
            all_labels = all_labels[all_labels["Label"].str.len() > 0]

            if not all_labels.empty:
                counts = all_labels.groupby(["Label", "Type"]).size().reset_index(name="Aantal")
                words_freq = dict(zip(counts["Label"], counts["Aantal"]))
                label_color_map = dict(zip(counts["Label"], ["green" if t == "Positief" else "red" for t in counts["Type"]]))

                from wordcloud import WordCloud
                import matplotlib.pyplot as plt

                wc = WordCloud(width=800, height=400, background_color="white", random_state=42).generate_from_frequencies(words_freq)
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wc.recolor(color_func=lambda word, **kwargs: label_color_map.get(word, "black")), interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)
            else:
                st.info("Geen labels beschikbaar om de WordCloud te tonen.")
        else:
            st.info("Nog geen lesdata beschikbaar voor het totaaloverzicht.")

        st.divider()

        # 3. KLASSENVERGELIJKING
        st.subheader("🔎 Vergelijk 2 klassen")
        if not les_df.empty:
            beschikbare_klassen = sorted(les_df["Klas"].unique())
            selected_klassen = st.multiselect("Selecteer exact 2 klassen:", beschikbare_klassen, max_selections=2)

            if len(selected_klassen) == 2:
                k1, k2 = selected_klassen
                col1, col2 = st.columns(2)

                for i, (current_klas, current_col) in enumerate(zip([k1, k2], [col1, col2])):
                    with current_col:
                        st.markdown(f"### Klas: {current_klas}")
                        df_k = les_df[les_df["Klas"] == current_klas]

                        # Scores
                        avg_aanpak = df_k["Lesaanpak"].mean()
                        avg_mgmt = df_k["Klasmanagement"].mean()
                        st.metric("Gem. Lesaanpak", f"{avg_aanpak:.1f} / 5")
                        st.metric("Gem. Management", f"{avg_mgmt:.1f} / 5")

                        # Klas-specifieke WordCloud
                        p_k = df_k["Positief"].dropna().astype(str).str.split(",").explode().str.strip()
                        n_k = df_k["Negatief"].dropna().astype(str).str.split(",").explode().str.strip()
                        labels_k = pd.concat([
                            pd.DataFrame({"Label": p_k, "Type": "Positief"}),
                            pd.DataFrame({"Label": n_k, "Type": "Negatief"})
                        ])
                        labels_k = labels_k[labels_k["Label"].str.len() > 0]

                        if not labels_k.empty:
                            counts_k = labels_k.groupby(["Label", "Type"]).size().reset_index(name="Aantal")
                            freq_k = dict(zip(counts_k["Label"], counts_k["Aantal"]))
                            color_map_k = dict(zip(counts_k["Label"], ["green" if t == "Positief" else "red" for t in counts_k["Type"]]))

                            wc_k = WordCloud(width=400, height=400, background_color="white").generate_from_frequencies(freq_k)
                            fig_k, ax_k = plt.subplots()
                            # FIX: Ook hier de lambda aanpassen
                            ax_k.imshow(wc_k.recolor(color_func=lambda word, **kwargs: color_map_k.get(word, "black")), interpolation="bilinear")
                            ax_k.axis("off")
                            st.pyplot(fig_k)
                        else:
                            st.write("Geen labels voor deze klas.")
            else:
                st.info("Kies twee klassen uit de lijst om de vergelijking te starten.")
        else:
            st.info("Nog geen lesdata beschikbaar.")

    # -------------------------------------------------
    # PDF – VORIGE MAAND
    # -------------------------------------------------
    with tab4:
        today = date.today()
        last_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        # --- ABSOLUUT VEILIGE DATUMAFHANDELING ---
        day_df["Datum"] = pd.to_datetime(day_df["Datum"], errors="coerce")
        day_df = day_df.dropna(subset=["Datum"])

        subset = day_df[
            day_df["Datum"].apply(lambda x: x.strftime("%Y-%m")) == last_month
        ]


        if subset.empty:
            st.info("Nog geen gegevens voor vorige maand.")
        else:
            if st.button("Genereer maandrapport"):
                path = f"{DATA_DIR}/{user['email'].split('@')[0]}_{last_month}.pdf"
                doc = SimpleDocTemplate(path)
                styles = getSampleStyleSheet()
                story = [
                    Paragraph(f"<b>Maandrapport {last_month}</b>", styles["Title"]),
                    Spacer(1, 12),
                    Paragraph(f"Gemiddelde energie: {subset['Energie'].mean():.2f}", styles["Normal"]),
                    Paragraph(f"Gemiddelde stress: {subset['Stress'].mean():.2f}", styles["Normal"])
                ]
                doc.build(story)

                with open(path, "rb") as f:
                    st.download_button("Download PDF", f, file_name=f"Maandrapport_{last_month}.pdf")



