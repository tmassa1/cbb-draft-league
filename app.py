from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
import altair as alt
from scoring import scoring_summary, load_rules

ROOT = Path(__file__).parent
st.set_page_config(page_title='CBB Draft League', page_icon='🏀', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container {padding-top:1.5rem;max-width:1300px}
[data-testid="stMetric"] {background:#172238;border:1px solid #2e3d55;border-radius:14px;padding:16px}
[data-testid="stSidebar"] {background:#111b2b}
h1,h2,h3 {letter-spacing:-.035em}
</style>''', unsafe_allow_html=True)

@st.cache_data(ttl=120)
def load_data(mode):
    draft = pd.read_csv(ROOT / 'data/draft.csv', dtype={'espn_id': str})
    file = ROOT / 'data' / 'games_live.csv'
    if not file.exists():
        return draft, pd.DataFrame(columns=['game_id','date','team','opponent','result','phase','source'])
    games = pd.read_csv(file)
    return draft, games

with st.sidebar:
    st.markdown('## 🏀 CBB DRAFT')
    st.caption('2026–27  ·  13 managers  ·  78 teams')
    mode = 'Live'
    page = st.radio('Explore', ['🏆 League Standings', '👤 Manager Profiles', '📅 Daily Scoreboard', '📈 League Analytics', '🗓️ Upcoming Games'])
    st.divider()
    st.markdown('**Scoring rules**')
    rules = load_rules()
    for key, label in [('regular','Regular season'),('conference','Conference tournament'),('ncaa','NCAA tournament'),('final_four','Final Four')]:
        w, l = rules[key]
        st.caption(f'{label}: {w:+d} W, {l:+d} L')
    st.divider()
    st.caption('Results are refreshed from saved CSV, not on every page view.')

draft, games = load_data(mode)
managers, teams, detail = scoring_summary(draft, games)
if not detail.empty:
    detail['date'] = pd.to_datetime(detail.date)
    daily = detail.groupby(['date','manager'], as_index=False)['points'].sum()
else:
    daily = pd.DataFrame(columns=['date','manager','points'])

st.markdown('### 2026–27 SEASON')
st.title('College Basketball Draft League')
st.caption('13 managers · 78 drafted teams · six selections each · 2026–27 season')
st.caption('Live ESPN results · Updated through GitHub Actions')

if page.startswith('🏆'):
    first = managers.iloc[0]
    latest = pd.to_datetime(games.date).max() if not games.empty else None
    m1,m2,m3,m4 = st.columns(4)
    m1.metric('League leader', first['manager'])
    m2.metric('Leading points', f"{first['points']:,}")
    m3.metric('Tracked teams', f'{len(draft):,}')
    m4.metric('Latest result', latest.strftime('%b %d') if latest is not None else '—')
    st.subheader('League Standings')
    table = managers.rename(columns={'rank':'Rank','manager':'Manager','points':'Points','wins':'Wins','losses':'Losses','teams':'Teams'})
    st.dataframe(table, hide_index=True, use_container_width=True, column_config={'Points': st.column_config.ProgressColumn('Points', format='%d', min_value=0, max_value=max(1,int(table.Points.max())))})
    if not daily.empty:
        st.subheader('Points race')
        top = managers.head(6).manager.tolist()
        points = daily.pivot(index='date',columns='manager',values='points').reindex(columns=top,fill_value=0).fillna(0).sort_index().cumsum().reset_index()
        chart_data = points.melt(id_vars='date',value_vars=top,var_name='Manager', value_name='Points')
        st.altair_chart(alt.Chart(chart_data).mark_line(strokeWidth=3).encode(x=alt.X('date:T',title='Date'),y=alt.Y('Points:Q'),color='Manager:N',tooltip=['date:T','Manager:N','Points:Q']).properties(height=300).interactive(),use_container_width=True)
    st.subheader('Latest scoring activity')
    if detail.empty:
        st.caption('No completed games loaded.')
    else:
        activity = detail.sort_values('date',ascending=False).head(18).copy()
        activity['date'] = activity.date.dt.strftime('%b %d')
        st.dataframe(activity[['date','manager','team','opponent','result','points']].rename(columns=str.title),hide_index=True,use_container_width=True)

elif page.startswith('👤'):
    selected = st.selectbox('Choose a manager', managers.manager.tolist())
    info = managers[managers.manager==selected].iloc[0]
    a,b,c,d=st.columns(4)
    a.metric('League rank',f"#{info['rank']}")
    b.metric('Points',int(info.points))
    c.metric('Wins',int(info.wins))
    d.metric('Losses',int(info.losses))
    st.subheader(f"{selected}'s drafted teams")
    tm = teams[teams.manager==selected].sort_values('points',ascending=False).copy()
    st.dataframe(tm[['team','conference','pick','points','wins','losses']].rename(columns=str.title),hide_index=True,use_container_width=True)
    if not detail.empty:
        own = daily[daily.manager==selected].sort_values('date').copy()
        own['Total'] = own.points.cumsum()
        st.altair_chart(alt.Chart(own).mark_area(opacity=.28,line={'color':'#38bdf8'}).encode(x='date:T',y='Total:Q',tooltip=['date:T','Total:Q']).properties(height=260),use_container_width=True)
        st.subheader('Game log')
        logs = detail[detail.manager==selected].sort_values('date',ascending=False).copy()
        logs['date']=logs.date.dt.strftime('%Y-%m-%d')
        st.dataframe(logs[['date','team','opponent','result','phase','points']].rename(columns=str.title),hide_index=True,use_container_width=True)

elif page.startswith('📅'):
    st.subheader('Daily Scoreboard')
    if games.empty:
        st.info('No games loaded yet.')
    else:
        dates = sorted(pd.to_datetime(games.date).dt.date.unique(),reverse=True)
        selected = st.selectbox('Date', dates, format_func=lambda v:v.strftime('%A, %b %d, %Y'))
        shown = detail[detail.date.dt.date==selected].sort_values(['points','manager'],ascending=[False,True]).copy()
        if shown.empty:
            st.info('No completed games on this date.')
        else:
            win_pts = int(shown.loc[shown.points>0,'points'].sum())
            x,y,z=st.columns(3)
            x.metric('Tracked games',len(shown))
            y.metric('Positive points',f'+{win_pts}')
            z.metric('Net points',f"{shown.points.sum():+d}")
            st.dataframe(shown[['manager','team','opponent','result','phase','points']].rename(columns=str.title),hide_index=True,use_container_width=True)
            st.subheader('Points by manager')
            m = shown.groupby('manager',as_index=False).points.sum().sort_values('points',ascending=False)
            st.bar_chart(m.set_index('manager')['points'],horizontal=True)

elif page.startswith('📈'):
    st.subheader('League Analytics')
    st.caption('Dive into which picks are providing the most value.')
    a,b=st.columns(2)
    with a:
        st.markdown('**Top drafted teams by points**')
        st.dataframe(teams.sort_values('points',ascending=False).head(20)[['team','manager','points','wins','losses']].rename(columns=str.title),hide_index=True,use_container_width=True)
    with b:
        st.markdown('**Best and worst picks by draft position**')
        analysis = teams.sort_values('pick').copy()
        st.altair_chart(alt.Chart(analysis).mark_circle(size=75,opacity=.75).encode(x=alt.X('pick:Q',title='Overall draft pick'),y='points:Q',color='manager:N',tooltip=['team','manager','pick','points']).properties(height=330).interactive(),use_container_width=True)
    if not daily.empty:
        st.subheader('Biggest single-day swings')
        best = daily.sort_values('points',ascending=False).head(15).copy()
        best.date=best.date.dt.strftime('%Y-%m-%d')
        st.dataframe(best.rename(columns=str.title),hide_index=True,use_container_width=True)
    st.subheader('Draft board')
    st.dataframe(draft[['pick','round','manager','team','conference']].rename(columns=str.title),hide_index=True,use_container_width=True)


else:
    st.subheader('🗓️ Upcoming Games')
    st.caption('Drafted schools are marked ⭐. Times are Eastern (EST/EDT). Odds appear only when ESPN provides them.')
    file = ROOT / 'data/upcoming_games.csv'
    if not file.exists():
        st.info('Upcoming games have not been synced yet. Run scripts/sync_upcoming.py to populate this page.')
    else:
        schedule = pd.read_csv(file, dtype=str).fillna('')
        if schedule.empty:
            st.info('No upcoming games involving drafted teams were found in the next 7 days.')
        else:
            eastern = ZoneInfo('America/New_York')
            schedule['tip'] = pd.to_datetime(schedule['start_utc'], utc=True).dt.tz_convert(eastern)
            schedule['local_day'] = schedule['tip'].dt.date
            today_et = datetime.now(eastern).date()
            a, b = st.columns(2)
            window = a.selectbox('Date range', ['Today', 'Tomorrow', 'Next 7 Days'], index=2)
            manager_filter = b.selectbox('Manager', ['All managers'] + sorted(draft['manager'].unique().tolist()))
            if window == 'Today':
                schedule = schedule[schedule['local_day'] == today_et]
            elif window == 'Tomorrow':
                schedule = schedule[schedule['local_day'] == today_et + timedelta(days=1)]
            else:
                schedule = schedule[(schedule['local_day'] >= today_et) & (schedule['local_day'] <= today_et + timedelta(days=7))]
            if manager_filter != 'All managers':
                schedule = schedule[(schedule['away_manager'] == manager_filter) | (schedule['home_manager'] == manager_filter)]
            if schedule.empty:
                st.info('No scheduled games match those filters.')
            else:
                def team_label(row, side):
                    name = row[f'{side}_team']
                    return ('⭐ ' if row[f'{side}_drafted'] == 'Y' else '') + name
                schedule = schedule.sort_values('tip')
                output = pd.DataFrame({
                    'Date / ET': schedule['tip'].dt.strftime('%a, %b %d · %-I:%M %p'),
                    'Away': schedule.apply(lambda row: team_label(row, 'away'), axis=1),
                    'Home': schedule.apply(lambda row: team_label(row, 'home'), axis=1),
                    'League Managers': schedule.apply(lambda row: ' vs '.join(x for x in [row['away_manager'], row['home_manager']] if x) or '—', axis=1),
                    'Spread (ESPN)': schedule['spread'].replace('', 'N/A'),
                    'Away ML': schedule['away_ml'].replace('', 'N/A'),
                    'Home ML': schedule['home_ml'].replace('', 'N/A'),
                })
                st.metric('Upcoming league games', len(output))
                st.dataframe(output, hide_index=True, use_container_width=True)
                st.caption('⭐ = drafted team · Two managers listed = head-to-head league matchup · Moneyline shown by away/home side. Odds are informational and may change.')

st.divider()
st.caption('Unofficial fantasy league dashboard • ESPN scoreboard access is unofficial and may change.')
