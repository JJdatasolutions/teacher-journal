import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import hashlib
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config("Leerkrachtenmonitor", "❤️", layout="wide")

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------
# SECURITY
# -------------------------------------------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def normalize_email(email):
    return email.strip().lower()

# -------------------------------------------------
# USERS
# -------------------------------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=["email", "password", "role"]).to_csv(USERS_FILE, index=False)
    return pd.read_csv(USERS_FILE)

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def day_file(email):
    return f"{DATA_DIR}/{email.split('@')[0]}_day.csv"

def lesson_file(email):
    return f"{DATA_DIR}/{email.split('@')[0]}_lessons.csv"

# -------------------------------------------------
# AUTO LOGIN
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
st.title("🍎 Leerkrachtenmonitor")
users = load_users()

if "user" not in st.session_state:
    tab1, tab2 = st.tabs(["🔐 Inloggen", "🆕 Registreren"])

    with tab1:
        email = normalize_email(st.text_input("Email"))
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
        r_email = normalize_email(st.text_input("School-email"))
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
# SESSION
# -------------------------------------------------
user = st.session_state.user
st.sidebar.success(f"Ingelogd als {user['email']}")

if st.sidebar.button("Uitloggen"):
    st.query_params.clear()
    st.session_state.clear()
    st.rerun()

# -------------------------------------------------
# MOOD DEFINITIES
# -------------------------------------------------
POS_MOODS = [
    "Inspirerend", "Motiverend", "Actief",
    "Verbonden", "Respectvol", "Rustig", "Gefocust"
]

NEG_MOODS = [
    "Demotiverend", "Ontmoedigend", "Passief",
    "Afgesloten", "Onrespectvol", "Chaotisch", "Afgeleid"
]

# -------------------------------------------------
# TEACHER VIEW
# -------------------------------------------------
if user["role"] == "teacher":
    DAY_FILE = day_file(user["email"])
    LES_FILE = lesson_file(user["email"])

    if not os.path.exists(DAY_FILE):
        pd.DataFrame(columns=["Datum", "Energie", "Stress"]).to_csv(DAY_FILE, index=False)
    if not os.path.exists(LES_FILE):
        pd.DataFrame(columns=["Datum", "Klas", "Lesaanpak", "Klasmanagement", "Positief", "Negatief"]).to_csv(LES_FILE, index=False)

    day_df = pd.read_csv(DAY_FILE)
    day_df["Datum"] = pd.to_datetime(day_df["Datum"], errors="coerce")
    les_df = pd.read_csv(LES_FILE, parse_dates=["Datum"])

    # ---- tabs staan nu binnen de teacher if ----
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧠 Daggevoel",
        "📝 Lesregistratie",
        "📊 Visualisaties",
        "📄 PDF-export"
    ])

    # -------- DAGREGISTRATIE --------
    with tab1:
        with st.form("day_log"):
            d = st.date_input("Datum", date.today())
            energie = st.slider("Energie", 1, 5, 3, help="1 = Uitgeput · 5 = Zeer energiek", key="energie_slider")
            stress = st.slider("Stress", 1, 5, 3, help="1 = Rustig · 5 = Enorm gestresseerd", key="stress_slider")

            if st.form_submit_button("Opslaan"):
                day_df.loc[len(day_df)] = [d, st.session_state.energie_slider, st.session_state.stress_slider]
                day_df.to_csv(DAY_FILE, index=False)
                st.success("Geregistreerd!")
                st.session_state.energie_slider = 3
                st.session_state.stress_slider = 3
                st.rerun()
    if not day_df.empty:
        fig = px.line(
            day_df.sort_values("Datum"),
            x="Datum",
            y=["Energie", "Stress"],
            markers=True,
            title="Energie & stress doorheen de tijd",
            color_discrete_map={"Energie": "#FF6B6B", "Stress": "#1F77B4"}
        )
        st.plotly_chart(fig, use_container_width=True)


    # -------- LESREGISTRATIE --------
    with tab2:
        with st.form("lesson_log"):
            d = st.date_input("Lesdatum", date.today(), key="lesdatum")
            klas = st.selectbox("Klas", ["5MT", "6MT", "5HW", "6WEWI"])
            lesaanpak = st.slider(
                "Lesaanpak",
                1, 5, 3,
                help="1 = sloeg niet aan · 5 = zeer geslaagd"
            )
            km = st.slider(
                "Klasmanagement",
                1, 5, 3,
                help="1 = geen controle · 5 = zeer vlot"
            )

            pos = st.multiselect("Positieve lesmood", POS_MOODS)
            neg = st.multiselect("Negatieve lesmood", NEG_MOODS)

            if st.form_submit_button("Les opslaan"):
                les_df.loc[len(les_df)] = [
                    d, klas, lesaanpak, km,
                    ", ".join(pos), ", ".join(neg)
                ]
                les_df.to_csv(LES_FILE, index=False)
                st.success("Les opgeslagen")
                st.rerun()

    # -------- VISUALISATIES --------
    with tab3:
        if not les_df.empty:
            heat = les_df.groupby("Klas")[["Lesaanpak", "Klasmanagement"]].mean()
            fig = px.imshow(
                heat,
                text_auto=True,
                color_continuous_scale="GnBu",
                title="Leskwaliteit per klas"
            )
            st.plotly_chart(fig, use_container_width=True)

            mood = []
            for _, r in les_df.iterrows():
                for p in str(r["Positief"]).split(", "):
                    if p:
                        mood.append([r["Klas"], p, "Positief"])
                for n in str(r["Negatief"]).split(", "):
                    if n:
                        mood.append([r["Klas"], n, "Negatief"])

            mood_df = pd.DataFrame(mood, columns=["Klas", "Mood", "Type"])

            klas_filter = st.selectbox("Filter per klas", ["Alle"] + sorted(mood_df.Klas.unique()))
            plot_df = mood_df if klas_filter == "Alle" else mood_df[mood_df.Klas == klas_filter]

            fig2 = px.bar_polar(
                plot_df.groupby(["Mood", "Type"]).size().reset_index(name="Aantal"),
                r="Aantal",
                theta="Mood",
                color="Type",
                title="Lesmood balans"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # -------- PDF EXPORT --------
    # -------- PDF EXPORT (Aangepast voor lege data) --------
    with tab4:
        if day_df.empty:
            st.info("Vul eerst daggegevens in bij 'Daggevoel' om een PDF te kunnen genereren.")
        else:
            # We maken een lijst van maanden die aanwezig zijn in de data
            beschikbare_maanden = sorted(day_df["Datum"].dt.to_period("M").astype(str).unique())
            
            maand = st.selectbox("Selecteer Maand", beschikbare_maanden)

            if st.button("Genereer PDF"):
                pdf_file = f"{DATA_DIR}/{user['email'].split('@')[0]}_{maand}.pdf"
                doc = SimpleDocTemplate(pdf_file)
                styles = getSampleStyleSheet()
                story = []

                story.append(Paragraph(f"<b>Maandoverzicht {maand}</b>", styles["Title"]))

                subset = day_df[day_df["Datum"].dt.to_period("M").astype(str) == maand]
                avg_e = subset["Energie"].mean()
                avg_s = subset["Stress"].mean()

                story.append(Paragraph(
                    f"Gemiddelde energie: {avg_e:.2f}<br/>Gemiddelde stress: {avg_s:.2f}",
                    styles["Normal"]
                ))

                doc.build(story)
                with open(pdf_file, "rb") as f:
                    st.download_button("Download PDF", f, file_name=f"Rapport_{maand}.pdf")
                st.success("PDF gereed!")

# -------------------------------------------------
# DIRECTOR VIEW (Gecorrigeerd)
# -------------------------------------------------
else:
    st.header("🏫 Directie-overzicht")

    day_logs = []
    for f in os.listdir(DATA_DIR):
        if f.endswith("_day.csv"):
            path = os.path.join(DATA_DIR, f)
            temp_df = pd.read_csv(path, parse_dates=["Datum"])
            if not temp_df.empty:
                day_logs.append(temp_df)

    if day_logs:
        big_day = pd.concat(day_logs)
        # numeric_only=True is verplicht om crashes te voorkomen bij het middelen
        avg_day = big_day.groupby("Datum").mean(numeric_only=True).reset_index()

        fig = px.line(
            avg_day,
            x="Datum",
            y=["Energie", "Stress"],
            title="Gemiddelde energie & stress (schoolbreed)",
            color_discrete_map={"Energie": "#2ECC71", "Stress": "#E74C3C"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nog geen data van leerkrachten beschikbaar.")






