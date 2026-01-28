import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os
import hashlib
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

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
# TEACHER VIEW
# -------------------------------------------------
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

    # 2. ALGEMENE WORDCLOUD (Alle data)
    st.subheader("🖌 Alle labels (Totaaloverzicht)")
    if not les_df.empty:
        # Data voorbereiden
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
            # Kleurenmap maken
            label_color_map = dict(zip(counts["Label"], ["green" if t == "Positief" else "red" for t in counts["Type"]]))

            from wordcloud import WordCloud
            import matplotlib.pyplot as plt

            wc = WordCloud(width=800, height=400, background_color="white", random_state=42).generate_from_frequencies(words_freq)
            
            # FIX: Gebruik 'word' als expliciet keyword argument in de lambda
            fig, ax = plt.subplots()
            ax.imshow(wc.recolor(color_func=lambda word, **kwargs: label_color_map.get(word, "black")), interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
    else:
        st.info("Nog geen lesdata voor een WordCloud.")

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





























