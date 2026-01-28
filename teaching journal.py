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

        if st.form_submit_button("Les opslaan"):
            les_df.loc[len(les_df)] = [
                date.today(), klas, lesaanpak, klasmanagement,
                ", ".join(positief), ", ".join(negatief)
            ]
            les_df.to_csv(LES_FILE, index=False)
            st.success("Les opgeslagen ✔️")

# -------------------------------------------------
# VISUALISATIES
# -------------------------------------------------
with tab3:
    if not les_df.empty:
        stats = les_df.groupby("Klas")[["Lesaanpak", "Klasmanagement"]].mean().reset_index()
        fig = px.bar(stats, x="Klas", y=["Lesaanpak", "Klasmanagement"], barmode="group")
        st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# PDF – VORIGE MAAND
# -------------------------------------------------
with tab4:
    today = date.today()
    last_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    subset = day_df[day_df["Datum"].dt.strftime("%Y-%m") == last_month]

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
