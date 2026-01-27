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
        # Create fresh DB with all necessary columns
        df = pd.DataFrame(columns=[
            'Date', 'Class_Group', 
            'Mental_State', 'Energy', 'Stress', 
            'Didactics', 'Class_Management', 
            'Tags', 'Notes'
        ])
        df.to_csv(FILE_PATH, index=False)
    
    df = pd.read_csv(FILE_PATH)
    # Ensure Date is datetime for sorting/filtering
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def save_data(df):
    df.to_csv(FILE_PATH, index=False)

# --- 3. UI: APP HEADER ---
st.title("🍎 Teacher's Strava")
st.caption("Track. Reflect. Improve.")

# --- 4. LOGGING FORM (Mobile Friendly) ---
with st.expander("➕ Log New Session", expanded=False):
    with st.form(key='log_form', clear_on_submit=True):
        st.subheader("1. The Basics")
        c1, c2 = st.columns(2)
        entry_date = c1.date_input("Date", date.today())
        # Your specific class list
        class_options = ['5MT', '6MT', '5HW', '6WEWI', '5ECMT', '5ECWI', '3MT']
        class_group = c2.selectbox("Class Group", class_options)
        
        st.markdown("---")
        st.subheader("2. Vibe Check")
        # Your specific tags + extras
        tag_options = [
            "Respectful", "Energizing", "Inspiring", "Collaborative", "Active", 
            "Stressful", "Unrespectful", "Rebellious", "Lazy", "Passive",
            "Chaotic", "Funny", "Focused", "Drained", "Proud"
        ]
        tags = st.multiselect("Select Tags:", tag_options)
        
        # Sliders for internal state
        st.write("**Internal State (1-10)**")
        mental = st.slider("🧠 Mental Clarity", 1, 10, 7)
        energy = st.slider("⚡ Energy Level", 1, 10, 6)
        stress = st.slider("😰 Stress Level", 1, 10, 3)
        
        st.markdown("---")
        st.subheader("3. Performance")
        # Dropdowns are easier on mobile than sliders
        col_p1, col_p2 = st.columns(2)
        didactics = col_p1.selectbox("Didactics", [1, 2, 3, 4, 5], index=2, help="Methodology success")
        management = col_p2.selectbox("Class Mgmt", [1, 2, 3, 4, 5], index=2, help="Behavior control")
        
        notes = st.text_area("Notes", placeholder="Aha moment? Struggle?")
        
        if st.form_submit_button("💾 Save Entry", type="primary"):
            df = load_data()
            new_entry = {
                'Date': pd.Timestamp(entry_date),
                'Class_Group': class_group,
                'Mental_State': mental,
                'Energy': energy,
                'Stress': stress,
                'Didactics': didactics,
                'Class_Management': management,
                'Tags': ", ".join(tags),
                'Notes': notes
            }
            # Append and save
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)
            st.success("Session logged!")
            st.rerun()

# --- 5. MAIN DASHBOARD ---
df = load_data()

if not df.empty:
    # A. TOP METRICS
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Classes", len(df))
    # Calculate Arrow for Energy (Current vs Average)
    avg_en = df['Energy'].mean()
    curr_en = df.iloc[-1]['Energy']
    m2.metric("Avg Energy", f"{avg_en:.1f}", delta=f"{curr_en - avg_en:.1f} recent")
    m3.metric("Avg Stress", f"{df['Stress'].mean():.1f}")

    # --- B. TABS FOR FUNCTIONALITY ---
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 Activity", "⚔️ Compare", "🔍 Search", "📧 Report"])

    # TAB 1: STRAVA-STYLE HEATMAP
    with tab1:
        st.subheader("Consistency Log")
        # Create a heatmap: Week of Year vs Day of Week
        df['Week'] = df['Date'].dt.isocalendar().week
        df['Day'] = df['Date'].dt.day_name()
        
        # Aggregate logic: If multiple classes in one day, take average Energy
        heatmap_data = df.groupby(['Week', 'Day'])['Energy'].mean().reset_index()
        
        # Ensure correct day order
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        fig_heat = px.density_heatmap(
            heatmap_data, x="Week", y="Day", z="Energy", 
            nbinsx=52, category_orders={"Day": days_order},
            color_continuous_scale="Greens", title="Energy Heatmap (Darker = Higher Energy)"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # TAB 2: CLASS VS CLASS COMPARISON
    with tab2:
        st.subheader("Class Showdown")
        c_opts = df['Class_Group'].unique()
        if len(c_opts) < 2:
            st.warning("Log at least two different classes to compare them!")
        else:
            col_a, col_b = st.columns(2)
            class_a = col_a.selectbox("Class A", c_opts, index=0)
            class_b = col_b.selectbox("Class B", c_opts, index=1 if len(c_opts)>1 else 0)
            
            # Filter Data
            df_a = df[df['Class_Group'] == class_a]
            df_b = df[df['Class_Group'] == class_b]
            
            # Categories to compare
            categories = ['Mental Clarity', 'Energy', 'Didactics (x2)', 'Mgmt (x2)', 'Calmness (Inv. Stress)']
            
            def get_stats(sub_df):
                if sub_df.empty: return [0]*5
                return [
                    sub_df['Mental_State'].mean(),
                    sub_df['Energy'].mean(),
                    sub_df['Didactics'].mean() * 2, # Scale to 10
                    sub_df['Class_Management'].mean() * 2, # Scale to 10
                    10 - sub_df['Stress'].mean() # Invert stress
                ]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=get_stats(df_a), theta=categories, fill='toself', name=class_a))
            fig_radar.add_trace(go.Scatterpolar(r=get_stats(df_b), theta=categories, fill='toself', name=class_b))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=True)
            st.plotly_chart(fig_radar, use_container_width=True)

    # TAB 3: AHA MOMENT SEARCH
    with tab3:
        st.subheader("Find Past Notes")
        search_term = st.text_input("Search keywords (e.g., 'grammar', 'noisy', 'test')")
        
        if search_term:
            # Filter notes containing the term (case insensitive)
            mask = df['Notes'].str.contains(search_term, case=False, na=False)
            results = df[mask][['Date', 'Class_Group', 'Notes']]
            if not results.empty:
                st.dataframe(results, hide_index=True, use_container_width=True)
            else:
                st.info("No notes found with that keyword.")
        else:
            # Show recent notes
            st.write("Recent Notes:")
            st.dataframe(df[['Date', 'Class_Group', 'Notes']].tail(5).sort_values(by='Date', ascending=False), hide_index=True)

    # TAB 4: WEEKLY REPORT GENERATOR
    with tab4:
        st.subheader("Weekly Recap")
        st.write("Generate a summary to email to yourself.")
        
        if st.button("Generate Report"):
            # Filter last 7 days
            end_date = df['Date'].max()
            start_date = end_date - timedelta(days=7)
            mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
            weekly_df = df[mask]
            
            if not weekly_df.empty:
                total_classes = len(weekly_df)
                avg_stress_w = weekly_df['Stress'].mean()
                best_class = weekly_df.loc[weekly_df['Didactics'].idxmax()]['Class_Group']
                
                report_text = f"""
Subject: Teaching Reflection: {start_date.date()} to {end_date.date()}

SUMMARY:
- Total Classes: {total_classes}
- Average Stress: {avg_stress_w:.1f}/10
- Highlight: Best session was with {best_class}

REFLECTIONS:
{weekly_df[['Date', 'Class_Group', 'Notes']].to_string(index=False)}
                """
                st.text_area("Copy this draft:", report_text, height=250)
                st.caption(f"Tip: Send this to ambrasdata@gmail.com")
            else:
                st.warning("No logs found in the last 7 days of data.")

    # --- 6. DATA MANAGEMENT (Footer) ---
    st.markdown("---")
    with st.expander("⚙️ Manage Data (Edit / Delete / Download)"):
        # 1. Download
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full CSV",
            data=csv_data,
            file_name='teaching_journal_backup.csv',
            mime='text/csv'
        )
        
        # 2. Edit/Delete
        st.write("Edit values below. To delete, select rows on the left and press Delete.")
        edited_df = st.data_editor(
            df.sort_values(by='Date', ascending=False), 
            num_rows="dynamic", 
            use_container_width=True
        )
        
        if st.button("⚠️ Confirm Changes"):
            save_data(edited_df)
            st.success("Database updated successfully.")
            st.rerun()

else:
    st.info("👈 Tap 'Log New Session' to start your first entry!")
