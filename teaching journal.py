import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
import os
import hashlib
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Leerkrachtenmonitor",
    page_icon="❤️",
    layout="centered"  # mobile-first
)

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def normalize_email(email: str) -> str:
    return email.strip().lower()

def hash_pw(pw: str) -> str:
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
# SESSION STATE INIT
# -------------------------------------------------
for key, default in {
    "energie": 3,
    "stress": 3,
    "lesaanpak": 3,
    "klasmanagement": 3,
    "pos_labels": [],
    "neg_labels": []
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------------------------------------
# AUTH
# -------------------------------------------------
st.title("❤️ Leerkrachtenmonitor")
users = load_users()

if "user" not in st.session_state:
    tab1, tab2 = st.tabs(["🔐 Inloggen", "🆕 Registreren"])

    with tab1:
        email = normalize_email(st.text_input("E-mail"))
        pw = st.text_input("Wachtwoord", type="password")

        if st.button("Inloggen"):
            u = users[users.email == email]
            if not u.empty and hash_pw(pw) == u.iloc[0].password:
                st.session_state.user = u.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Ongeldige login")

    with tab2:
        r_email = normalize_email(st.text_input("School-e-mail"))
        r_pw = st.text_input("Wachtwoord", type="password")

        if st.button("Account aanmaken"):
            if r_email in users.email.values:
                st.error("Account bestaat al")
            else:
                role = "director" if r_email.startswith("directie") else "teacher"
                users.loc[len(users)] = [r_email, hash_pw(r_pw), role]
                save_users(users)
                st.success("Account aangemaakt")

    st.stop()

user = st.session_state.user

# -------------------------------------------------
# MOODS
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
        pd.DataFrame(columns=[
            "Datum", "Klas", "Lesaanpak", "Klasmanagement",
            "Positief", "Negatief"
        ]).to_csv(LES_FILE, index=False)

    day_df = pd.read_csv(DAY_FILE, parse_dates=["Datum"])
    les_df = pd.read_csv(LES_FILE, parse_dates=["Datum"])

    tab1, tab2, tab3, tab4 = st.tabs([
        "🧠 Daggevoel",
        "📝 Lesregistratie",
        "📊 Visualisaties",
        "📄 Maandrapport"
    ])

    # ---------------- DAGGEVOEL ----------------
    with tab1:
        with st.form("daggevoel"):
            st.slider(
                "Energie",
                1, 5,
                key="energie",
                help="1 = Uitgeput · 5 = Barstend van energie"
            )
            st.caption("Uitgeput · Weinig energie · Oké · Veel energie · Barstend van energie")

            st.slider(
                "Stress",
                1, 5,
                key="stress",
                help="1 = Volkomen rustig · 5 = Enorm gestresseerd"
            )
            st.caption("Volkomen rustig · Licht gespannen · Gemiddeld · Erg gestresseerd · Enorm gestresseerd")

            if st.form_submit_button("Opslaan"):
                day_df.loc[len(day_df)] = [date.today(), st.session_state.energie, st.session_state.stress]
                day_df.to_csv(DAY_FILE, index=False)
                st.success("Geregistreerd!")
                st.session_state.energie = 3
                st.session_state.stress = 3
                st.rerun()

    # ---------------- LESREGISTRATIE ----------------
    with tab2:
        with st.form("les"):
            klas = st.selectbox("Klas", ["5MT", "6MT", "5HW", "6WEWI"])

            st.slider(
                "Lesaanpak",
                1, 5,
                key="lesaanpak",
                help="1 = werkte helemaal niet · 5 = groot succes"
            )
            st.caption("Werkte niet · Zwak · Oké · Sterk · Groot succes")

            st.slider(
                "Klasmanagement",
                1, 5,
                key="klasmanagement",
                help="1 = klas niet bij de les · 5 = met gemak bij de les"
            )
            st.caption("Geen controle · Moeilijk · Oké · Goed · Met gemak")

            st.markdown("**Positieve lesmood**")
            st.session_state.pos_labels = [
                m for m in POS_MOODS if st.checkbox(m, key=f"pos_{m}")
            ]

            st.markdown("**Negatieve lesmood**")
            st.session_state.neg_labels = [
                m for m in NEG_MOODS if st.checkbox(m, key=f"neg_{m}")
            ]

            if st.form_submit_button("Les opslaan"):
                les_df.loc[len(les_df)] = [
                    date.today(), klas,
                    st.session_state.lesaanpak,
                    st.session_state.klasmanagement,
                    ", ".join(st.session_state.pos_labels),
                    ", ".join(st.session_state.neg_labels)
                ]
                les_df.to_csv(LES_FILE, index=False)
                st.success("Les opgeslagen!")
                st.session_state.lesaanpak = 3
                st.session_state.klasmanagement = 3
                st.session_state.pos_labels = []
                st.session_state.neg_labels = []
                st.rerun()

    # ---------------- VISUALISATIES ----------------
    with tab3:
        if not les_df.empty:
            avg = les_df.groupby("Klas")[["Lesaanpak", "Klasmanagement"]].mean().reset_index()
            st.plotly_chart(
                px.bar(
                    avg,
                    x="Klas",
                    y=["Lesaanpak", "Klasmanagement"],
                    barmode="group",
                    title="Gemiddelde leskwaliteit per klas"
                ),
                use_container_width=True
            )

            labels = []
            for _, r in les_df.iterrows():
                for p in str(r["Positief"]).split(", "):
                    if p:
                        labels.append(["Positief", p])
                for n in str(r["Negatief"]).split(", "):
                    if n:
                        labels.append(["Negatief", n])

            if labels:
                lbl_df = pd.DataFrame(labels, columns=["Type", "Label"])
                st.plotly_chart(
                    px.pie(
                        lbl_df,
                        names="Label",
                        hole=0.5,
                        color="Type",
                        color_discrete_map={"Positief": "green", "Negatief": "red"},
                        title="Verdeling lesmood labels"
                    ),
                    use_container_width=True
                )

    # ---------------- PDF ----------------
    with tab4:
        today = date.today()
        first_this_month = today.replace(day=1)
        last_month = first_this_month - timedelta(days=1)
        month_label = last_month.strftime("%Y-%m")

        subset = day_df[day_df["Datum"].dt.to_period("M") == last_month.strftime("%Y-%m")]
        if subset.empty:
            st.info("Nog geen data voor vorige maand.")
        else:
            if st.button("Genereer maandrapport"):
                pdf_path = f"{DATA_DIR}/{user['email'].split('@')[0]}_{month_label}.pdf"
                doc = SimpleDocTemplate(pdf_path)
                styles = getSampleStyleSheet()
                story = []

                avg_e = subset["Energie"].mean()
                avg_s = subset["Stress"].mean()

                story.append(Paragraph(f"<b>Maandrapport {month_label}</b>", styles["Title"]))
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Gemiddelde energie: {avg_e:.2f}", styles["Normal"]))
                story.append(Paragraph(f"Gemiddelde stress: {avg_s:.2f}", styles["Normal"]))

                doc.build(story)

                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", f, file_name=f"Maandrapport_{month_label}.pdf")
