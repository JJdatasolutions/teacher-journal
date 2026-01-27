import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Teacher's Strava", page_icon="🍎", layout="centered")
FILE_PATH = 'teaching_journal.csv'

# --- 2. DATA HANDLING ---
def load_data():
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=['Date', 'Class_Group', 'Mental_State', 'Energy', 'Stress', 'Didactics', 'Class_Management', 'Tags', 'Notes'])
        df.to_csv(FILE_PATH, index=False)
    df = pd.read_csv(FILE_PATH)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def save_data(df):
    df.to_csv(FILE_PATH, index=False)

# --- 3. UI: APP HEADER ---
st.title("🍎 Teacher's Strava")
df = load_data()

# --- 4. LOGGING FORM ---
with st.expander("➕ Log New Session", expanded=False):
    with st.form(key='log_form', clear_on_submit=True):
        c1, c2 = st.columns(2)
        entry_date = c1.date_input("Date", date.today())
        class_group = c2.selectbox("Class Group", ['5MT', '6MT', '5HW', '6WEWI', '5ECMT', '5ECWI', '3MT'])
        
        tag_options = ["Respectful", "Energizing", "Inspiring", "Collaborative", "Active", "Stressful", "Unrespectful", "Rebellious", "Lazy", "Passive", "Chaotic", "Funny", "Focused", "Drained", "Proud"]
        tags = st.multiselect("Select Tags:", tag_options)
        
        st.write("**Internal State (1-10)**")
        mental = st.slider("🧠 Mental Clarity", 1, 10, 7)
        energy = st.slider("⚡ Energy Level", 1, 10, 6)
        stress = st.slider("😰 Stress Level", 1, 10, 3)
        
        st.write("**Performance (1-5)**")
        col_p1, col_p2 = st.columns(2)
        didactics = col_p1.selectbox("Didactics", [1, 2, 3, 4, 5], index=2)
        management = col_p2.selectbox("Class Mgmt", [1, 2, 3, 4, 5], index=2)
        
        notes = st.text_area("Notes")
        
        if st.form_submit_button("💾 Save Entry", type="primary"):
            new_entry = {'Date': pd.Timestamp(entry_date), 'Class_Group': class_group, 'Mental_State': mental, 'Energy': energy, 'Stress': stress, 'Didactics': didactics, 'Class_Management': management, 'Tags': ", ".join(tags), 'Notes': notes}
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)
            st.success("Session logged!")
            st.rerun()

# --- 5. DASHBOARD ---
if not df.empty:
    st.markdown("---")
    
    # NAVIGATION TABS
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 Activity", "⚔️ Compare Classes", "🔍 Search", "📧 Report"])

    # TAB 1: OVERALL ACTIVITY
    with tab1:
        st.subheader("Global Performance")
        fig_line = px.line(df.sort_values('Date'), x='Date', y=['Energy', 'Stress'], markers=True, color_discrete_map={"Energy": "#2ECC71", "Stress": "#E74C3C"})
        st.plotly_chart(fig_line, use_container_width=True)

    # TAB 2: CLASS VS CLASS COMPARISON (HEATMAPS ADDED HERE)
    with tab2:
        st.subheader("Class Showdown")
        c_opts = sorted(df['Class_Group'].unique())
        if len(c_opts) < 2:
            st.warning("Log entries for at least two different classes to see a comparison.")
        else:
            col_a, col_b = st.columns(2)
            class_a = col_a.selectbox("Select Class A", c_opts, index=0)
            class_b = col_b.selectbox("Select Class B", c_opts, index=1)
            
            df_a = df[df['Class_Group'] == class_a]
            df_b = df[df['Class_Group'] == class_b]

            # RADAR CHART
            categories = ['Mental', 'Energy', 'Didactics (x2)', 'Mgmt (x2)', 'Calm (10-Stress)']
            def get_stats(sub_df):
                return [sub_df['Mental_State'].mean(), sub_df['Energy'].mean(), sub_df['Didactics'].mean()*2, sub_df['Class_Management'].mean()*2, 10-sub_df['Stress'].mean()]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=get_stats(df_a), theta=categories, fill='toself', name=class_a))
            fig_radar.add_trace(go.Scatterpolar(r=get_stats(df_b), theta=categories, fill='toself', name=class_b))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=350, margin=dict(t=30, b=30))
            st.plotly_chart(fig_radar, use_container_width=True)

            # VIBE HEATMAPS
            st.markdown("### 🌡️ Vibe Heatmaps")
            st.caption("Darker color = Vibe occurs more frequently in this class.")

            def get_vibe_heatmap(sub_df, class_name):
                tags = sub_df['Tags'].dropna().str.split(', ').explode()
                tags = tags[tags != ""]
                if tags.empty:
                    return None
                counts = tags.value_counts().reset_index()
                counts.columns = ['Vibe', 'Frequency']
                # Create horizontal bar colored by frequency (mimicking heatmap behavior)
                fig = px.bar(counts.sort_values('Frequency'), 
                             x='Frequency', y='Vibe', 
                             title=f"Vibe Intensity: {class_name}",
                             orientation='h',
                             color='Frequency', 
                             color_continuous_scale='GnBu')
                fig.update_layout(coloraxis_showscale=False, height=300, margin=dict(l=0, r=0, t=40, b=0))
                return fig

            fig_h_a = get_vibe_heatmap(df_a, class_a)
            fig_h_b = get_vibe_heatmap(df_b, class_b)

            if fig_h_a: st.plotly_chart(fig_h_a, use_container_width=True)
            if fig_h_b: st.plotly_chart(fig_h_b, use_container_width=True)

    # TAB 3 & 4 (Notes Search & Report)
    with tab3:
        search = st.text_input("🔍 Search your notes...")
        if search:
            results = df[df['Notes'].str.contains(search, case=False, na=False)]
            st.dataframe(results[['Date', 'Class_Group', 'Notes']], use_container_width=True, hide_index=True)

    with tab4:
        if st.button("Generate Weekly Report"):
            last_week = df[df['Date'] > (pd.Timestamp.now() - timedelta(days=7))]
            report = f"Weekly Summary for ambrasdata@gmail.com\n\nAvg Energy: {last_week['Energy'].mean():.1f}\nAvg Stress: {last_week['Stress'].mean():.1f}\n\nNotes Log:\n"
            for _, row in last_week.iterrows():
                report += f"- {row['Date'].date()} ({row['Class_Group']}): {row['Notes']}\n"
            st.text_area("Copy and Send:", report, height=250)

    # DATA MANAGEMENT
    with st.expander("⚙️ Settings"):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Backup to CSV", data=csv, file_name='teaching_log.csv', mime='text/csv')
        edited = st.data_editor(df.sort_values('Date', ascending=False), num_rows="dynamic")
        if st.button("Save Database Changes"):
            save_data(edited)
            st.success("Changes Saved!")
            st.rerun()
else:
    st.info("Log your first class to see the dashboard!")
