import dash
from dash import dcc, html
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import date 
import pandas as pd
import plotly.express as px
from database_setup import Base, Race, Result, Driver 

# ====================================================================
# A. 全局設定與顏色配置
# ====================================================================
TEAM_COLORS = {
    "McLaren": "orange",
    "Red Bull": "#000093", 
    "Mercedes": "cyan",
}

engine = create_engine('sqlite:///f1_records.db')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)

# ====================================================================
# B. 數據查詢與圖表函數 (修正排序與顏色)
# ====================================================================
def get_total_standings():
    session = Session()
    data = (session.query(Driver.name, Driver.team, func.sum(Result.points).label('Total_Points'))
            .join(Result).group_by(Driver.driver_id).order_by(func.sum(Result.points).desc()).all())
    session.close()
    return pd.DataFrame(data, columns=['Driver', 'Team', 'Total_Points'])

def get_team_standings():
    session = Session()
    data = (session.query(Driver.team, func.sum(Result.points).label('Total_Points'))
            .join(Result).group_by(Driver.team).order_by(func.sum(Result.points).desc()).all())
    session.close()
    return pd.DataFrame(data, columns=['Team', 'Total_Points'])

def create_ranking_figure(df):
    fig = px.bar(df, x='Total_Points', y='Driver', color='Team', orientation='h',
                 text='Total_Points', color_discrete_map=TEAM_COLORS, height=500,
                 title='**車手總積分排名 (高分在上)**')
    # 🚨 關鍵修正：確保高分在上 🚨
    fig.update_layout(yaxis={'categoryorder': 'total ascending', 'autorange': 'reversed'}, xaxis_title="積分")
    fig.update_traces(textposition='outside')
    return fig

def create_team_figure(df):
    fig = px.bar(df, x='Total_Points', y='Team', color='Team', orientation='h',
                 text='Total_Points', color_discrete_map=TEAM_COLORS, height=350,
                 title='**車隊總積分排名 (高分在上)**')
    # 🚨 關鍵修正：確保高分在上 🚨
    fig.update_layout(yaxis={'categoryorder': 'total ascending', 'autorange': 'reversed'}, xaxis_title="積分")
    fig.update_traces(textposition='outside')
    return fig

# ====================================================================
# C. 完整數據集 (包含 日本 到 奧地利 共五站)
# ====================================================================
race_data = [
    # 1. 日本 (假設為第一站)
    {'name': '日本正賽', 'type': 'Race', 'date': date(2025, 2, 16), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 18, 'position': 2},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 15, 'position': 3},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 12, 'position': 4},
    ]},
    # 2. 巴林
    {'name': '巴林衝刺賽', 'type': 'Sprint', 'date': date(2025, 3, 1), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 7, 'position': 2},
    ]},
    {'name': '巴林正賽', 'type': 'Race', 'date': date(2025, 3, 2), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 18, 'position': 2},
    ]},
    # 3. 沙烏地
    {'name': '沙烏地阿拉伯衝刺賽', 'type': 'Sprint', 'date': date(2025, 3, 15), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 7, 'position': 2},
    ]},
    {'name': '沙烏地阿拉伯正賽', 'type': 'Race', 'date': date(2025, 3, 16), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 18, 'position': 2},
    ]},
    # 4. 伊莫拉
    {'name': '伊莫拉衝刺賽', 'type': 'Sprint', 'date': date(2025, 4, 19), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 7, 'position': 2},
    ]},
    {'name': '伊莫拉正賽', 'type': 'Race', 'date': date(2025, 4, 20), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 18, 'position': 2},
    ]},
    # 5. 奧地利
    {'name': '奧地利衝刺賽', 'type': 'Sprint', 'date': date(2025, 5, 10), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 7, 'position': 2},
    ]},
    {'name': '奧地利正賽', 'type': 'Race', 'date': date(2025, 5, 11), 'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 18, 'position': 2},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 15, 'position': 3},
    ]}
]

# 資料庫初始化邏輯 (保持不變)
def init_db():
    session = Session()
    # 確保車手存在
    drivers = [('mimicethan', 'McLaren'), ('henrythanks69', 'McLaren'), 
               ('RUUR', 'Mercedes'), ('Lavender', 'Mercedes'), 
               ('Tulio', 'Red Bull'), ('leegino2558', 'Red Bull')]
    for name, team in drivers:
        if not session.query(Driver).filter_by(name=name).first():
            session.add(Driver(name=name, team=team))
    session.commit()
    # 插入比賽
    for r in race_data:
        race = session.query(Race).filter_by(name=r['name']).first()
        if not race:
            race = Race(name=r['name'], type=r['type'], date=r['date'])
            session.add(race); session.commit()
        for res in r['results']:
            d = session.query(Driver).filter_by(name=res['driver_name']).first()
            if d and not session.query(Result).filter_by(driver_id=d.driver_id, race_id=race.race_id).first():
                session.add(Result(driver_id=d.driver_id, race_id=race.race_id, points=res['points'], position=res['position']))
    session.commit(); session.close()

# ====================================================================
# D. App 啟動
# ====================================================================
init_db()
app = dash.Dash(__name__)
server = app.server

df_s = get_total_standings()
df_t = get_team_standings()

app.layout = html.Div([
    html.H1('F1 積分排名復原版', style={'textAlign': 'center', 'color': '#FF1801'}),
    dcc.Graph(figure=create_team_figure(df_t)),
    dcc.Graph(figure=create_ranking_figure(df_s)),
    html.Div('數據已包含：日本、巴林、沙烏地、伊莫拉、奧地利。', style={'textAlign': 'center'})
])

if __name__ == '__main__':
    # app.run_server(debug=True)
    pass