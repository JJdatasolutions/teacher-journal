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
# VISUALISATIES
# -----------------------------
import plotly.graph_objects as go  # Zorg dat dit bovenaan staat
import matplotlib.pyplot as plt
from wordcloud import WordCloud

with tab3:
    st.header("📊 Visualisaties")

    if les_df.empty:
        st.info("Nog geen lesdata beschikbaar.")
    else:
        # -----------------------------
        # FILTER KLAS
        # -----------------------------
        klassen = sorted(les_df["Klas"].dropna().unique().tolist())
        klas_keuze = st.multiselect(
            "Selecteer klassen om te vergelijken:",
            klassen,
            default=klassen[:2]  # standaard max 2 voor vergelijking
        )

        if not klas_keuze:
            st.info("Selecteer minstens één klas")
        else:
            df = les_df[les_df["Klas"].isin(klas_keuze)].copy()

            # -----------------------------
            # GEMIDDELDE LESAANPAK (BAR)
            # -----------------------------
            st.subheader("📘 Gemiddelde lesaanpak per klas")
            avg_lesaanpak = df.groupby("Klas", as_index=False)["Lesaanpak"].mean()
            fig_bar = px.bar(
                avg_lesaanpak,
                x="Klas",
                y="Lesaanpak",
                text_auto=".2f",
                title="Gemiddelde score lesaanpak per klas",
            )
            fig_bar.update_layout(yaxis_range=[1, 5])
            st.plotly_chart(fig_bar, use_container_width=True)

            # -----------------------------
            # DAGGEVOEL (LIJNGRAFIEK)
            # -----------------------------
            st.subheader("📈 Daggevoel (Energie & Stress)")
            day_df_clean = day_df.copy()
            day_df_clean["Datum"] = pd.to_datetime(day_df_clean["Datum"], errors="coerce")
            day_df_clean = day_df_clean.dropna(subset=["Datum"])
            if not day_df_clean.empty:
                fig_line = px.line(
                    day_df_clean.sort_values("Datum"),
                    x="Datum",
                    y=["Energie", "Stress"],
                    markers=True,
                    title="Daggevoel door de tijd"
                )
                fig_line.update_layout(yaxis_range=[1, 5])
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Nog geen daggevoel geregistreerd.")

            # -----------------------------
            # ALGEMENE WORDCLOUDS
            # -----------------------------
            st.subheader("🖌 Algemene WordClouds")

            # Positieve en negatieve labels
            pos_series = les_df["Positief"].dropna().astype(str).str.split(",").explode().str.strip()
            neg_series = les_df["Negatief"].dropna().astype(str).str.split(",").explode().str.strip()
            if not pos_series.empty or not neg_series.empty:
                all_labels = pd.concat([
                    pd.DataFrame({"Label": pos_series, "Type": "Positief"}),
                    pd.DataFrame({"Label": neg_series, "Type": "Negatief"})
                ])
                label_counts = all_labels.groupby(["Label", "Type"]).size().reset_index(name="Aantal")
                words_freq = dict(zip(label_counts["Label"], label_counts["Aantal"]))
                label_color = dict(zip(label_counts["Label"],
                                       ["green" if t=="Positief" else "red" for t in label_counts["Type"]]))
                def color_func(word, **kwargs):
                    return label_color.get(word, "black")
                wc = WordCloud(width=800, height=400, background_color="white",
                               prefer_horizontal=0.9, min_font_size=10, max_font_size=100,
                               random_state=42).generate_from_frequencies(words_freq)
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.imshow(wc.recolor(color_func=color_func, random_state=42), interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

            # Lesaanpak WordCloud
            st.markdown("**Lesaanpak**")
            lesaanpak_counts = les_df["Lesaanpak"].value_counts().sort_index()
            if not lesaanpak_counts.empty:
                freq_dict = {str(k): v for k, v in lesaanpak_counts.items()}
                wc = WordCloud(width=600, height=300, background_color="white",
                               colormap="Blues", prefer_horizontal=0.9,
                               min_font_size=10, max_font_size=100, random_state=42
                               ).generate_from_frequencies(freq_dict)
                fig, ax = plt.subplots(figsize=(12, 3))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

            # Klasmanagement WordCloud
            st.markdown("**Klasmanagement**")
            km_counts = les_df["Klasmanagement"].value_counts().sort_index()
            if not km_counts.empty:
                freq_dict = {str(k): v for k, v in km_counts.items()}
                wc = WordCloud(width=600, height=300, background_color="white",
                               colormap="Oranges", prefer_horizontal=0.9,
                               min_font_size=10, max_font_size=100, random_state=42
                               ).generate_from_frequencies(freq_dict)
                fig, ax = plt.subplots(figsize=(12, 3))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

            # -----------------------------
            # VERGELIJKING TUSSEN KLASSEN
            # -----------------------------
            if len(klas_keuze) == 2:
                st.subheader("⚖️ Vergelijking tussen klassen")
                k1, k2 = klas_keuze

                # Labels WordClouds
                df1 = df[df["Klas"]==k1]
                df2 = df[df["Klas"]==k2]

                pos1 = df1["Positief"].dropna().astype(str).str.split(",").explode().str.strip()
                neg1 = df1["Negatief"].dropna().astype(str).str.split(",").explode().str.strip()
                all1 = pd.concat([pd.DataFrame({"Label": pos1, "Type":"Positief"}),
                                  pd.DataFrame({"Label": neg1, "Type":"Negatief"})])
                counts1 = all1.groupby(["Label", "Type"]).size().reset_index(name="Aantal")
                words_freq1 = dict(zip(counts1["Label"], counts1["Aantal"]))
                label_color1 = dict(zip(counts1["Label"], ["green" if t=="Positief" else "red" for t in counts1["Type"]]))

                pos2 = df2["Positief"].dropna().astype(str).str.split(",").explode().str.strip()
                neg2 = df2["Negatief"].dropna().astype(str).str.split(",").explode().str.strip()
                all2 = pd.concat([pd.DataFrame({"Label": pos2, "Type":"Positief"}),
                                  pd.DataFrame({"Label": neg2, "Type":"Negatief"})])
                counts2 = all2.groupby(["Label", "Type"]).size().reset_index(name="Aantal")
                words_freq2 = dict(zip(counts2["Label"], counts2["Aantal"]))
                label_color2 = dict(zip(counts2["Label"], ["green" if t=="Positief" else "red" for t in counts2["Type"]]))

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**{k1}**")
                    wc1 = WordCloud(width=400, height=300, background_color="white").generate_from_frequencies(words_freq1)
                    fig, ax = plt.subplots(figsize=(6,4))
                    ax.imshow(wc1.recolor(color_func=lambda w, **kw: label_color1.get(w,"black")), interpolation="bilinear")
                    ax.axis("off")
                    st.pyplot(fig)
                with c2:
                    st.markdown(f"**{k2}**")
                    wc2 = WordCloud(width=400, height=300, background_color="white").generate_from_frequencies(words_freq2)
                    fig, ax = plt.subplots(figsize=(6,4))
                    ax.imshow(wc2.recolor(color_func=lambda w, **kw: label_color2.get(w,"black")), interpolation="bilinear")
                    ax.axis("off")
                    st.pyplot(fig)

                # Clustered bar chart Lesaanpak
                les_bar = df.groupby("Klas")["Lesaanpak"].mean().reset_index()
                fig_bar2 = px.bar(
                    les_bar,
                    x="Klas",
                    y="Lesaanpak",
                    text_auto=".2f",
                    barmode="group",
                    title="Gemiddelde Lesaanpak per klas"
                )
                fig_bar2.update_layout(yaxis_range=[1,5])
                st.plotly_chart(fig_bar2, use_container_width=True)

                # Clustered bar chart Klasmanagement
                km_bar = df.groupby("Klas")["Klasmanagement"].mean().reset_index()
                fig_bar3 = px.bar(
                    km_bar,
                    x="Klas",
                    y="Klasmanagement",
                    text_auto=".2f",
                    barmode="group",
                    title="Gemiddeld Klasmanagement per klas"
                )
                fig_bar3.update_layout(yaxis_range=[1,5])
                st.plotly_chart(fig_bar3, use_container_width=True)


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
















