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

# -------------------------------------------------
# CONFIG
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
st.title("❤️ Leerkrachtenmonitor")
users = load_users()

if "user" not in st.session_state:
    tab1, tab2 = st.tabs(["🔐 Inloggen", "🆕 Registreren"])

    with tab1:
        email = normalize_email(st.text_input("E-mail"))
        pw = st.text_input("Wachtwoord", type="password")
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
    "Respectvol", "Gefocust", "Veilig", "Energiek", "Nieuwsgierig"
]

NEG_MOODS = [
    "Demotiverend", "Passief", "Onrespectvol",
    "Chaotisch", "Afgeleid", "Rumoerig", "Onveilig"
]

KLASSEN = [
    "5ECWI/WEWI/WEWIC", "5HW", "5ECMT/5MT/5WEMTC", "5MT",
    "3HW/3MT", "6ECWI-HW", "6MT", "6WEWI", "6ECMT/6WEMT"
]

# -------------------------------------------------
# LEERKRACHT VIEW
# -------------------------------------------------
DAY_FILE = day_file(user["email"])
LES_FILE = lesson_file(user["email"])

if not os.path.exists(DAY_FILE):
    pd.DataFrame(columns=["Datum", "Energie", "Stress"]).to_csv(DAY_FILE, index=False)

if not os.path.exists(LES_FILE):
    pd.DataFrame(columns=[
        "Datum", "Klas", "Lesaanpak", "Klasmanagement", "Positief", "Negatief"
    ]).to_csv(LES_FILE, index=False)

les_df = pd.read_csv(LES_FILE)
les_df["Datum"] = pd.to_datetime(les_df["Datum"], errors="coerce")
les_df = les_df.dropna(subset=["Datum"])

tab1, tab2, tab3 = st.tabs([
    "🧠 Daggevoel", "📝 Lesregistratie", "📊 Visualisaties"
])

# -------------------------------------------------
# TAB 1 – DAGGEVOEL
# -------------------------------------------------
with tab1:
    day_df = pd.read_csv(DAY_FILE)
    day_df["Datum"] = pd.to_datetime(day_df["Datum"], errors="coerce")
    day_df = day_df.dropna(subset=["Datum"])

    d = st.date_input("Datum", date.today())
    existing_dates = day_df["Datum"].dt.date.values

    if d in existing_dates:
        st.warning(f"⚠️ Je hebt voor {d} al een score ingevuld.")
    else:
        with st.form("daggevoel", clear_on_submit=True):
            energie = st.slider("Energie", 1, 5, 3)
            stress = st.slider("Stress", 1, 5, 3)

            if st.form_submit_button("Opslaan"):
                new_row = pd.DataFrame([{
                    "Datum": d.strftime("%Y-%m-%d"),
                    "Energie": energie,
                    "Stress": stress
                }])

                pd.concat([day_df, new_row]).to_csv(DAY_FILE, index=False)
                st.success("Geregistreerd! ✔️")
                st.rerun()

# -------------------------------------------------
# TAB 2 – LESREGISTRATIE
# -------------------------------------------------
with tab2:
    with st.form("lesregistratie", clear_on_submit=True):
        klas = st.selectbox("Klas", KLASSEN)
        lesaanpak = st.slider("Lesaanpak", 1, 5, 3)
        klasmanagement = st.slider("Klasmanagement", 1, 5, 3)

        positief = [m for m in POS_MOODS if st.checkbox(m, key=f"p_{m}")]
        negatief = [m for m in NEG_MOODS if st.checkbox(m, key=f"n_{m}")]

        if st.form_submit_button("Les opslaan"):
            les_df.loc[len(les_df)] = [
                pd.Timestamp.now(), klas, lesaanpak,
                klasmanagement, ", ".join(positief), ", ".join(negatief)
            ]
            les_df.to_csv(LES_FILE, index=False)
            st.success("Les opgeslagen ✔️")

# -------------------------------------------------
# TAB 3 – VISUALISATIES (FIX)
# -------------------------------------------------
with tab3:
    st.subheader("📈 Daggevoel")

    # 🔴 HIER zit de fix: opnieuw inlezen
    day_df = pd.read_csv(DAY_FILE)
    day_df["Datum"] = pd.to_datetime(day_df["Datum"], errors="coerce")
    day_df = day_df.dropna(subset=["Datum"]).sort_values("Datum")

    if not day_df.empty:
        fig = px.line(
            day_df,
            x="Datum",
            y=["Energie", "Stress"],
            markers=True,
            title="Daggevoel door de tijd"
        )
        fig.update_layout(yaxis_range=[0.5, 5.5])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nog geen daggevoel geregistreerd.")
