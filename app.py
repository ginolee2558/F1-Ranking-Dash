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
    "Red Bull": "#000093", # 您的指定顏色
    "Mercedes": "cyan",
}

# ----------------------------------------------------
# 1. 資料庫連線設定
# ----------------------------------------------------
engine = create_engine('sqlite:///f1_records.db')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)

# ====================================================================
# B. 數據查詢和圖表函數定義
# ====================================================================

# ----------------------------------------------------
# 1. 獲取總積分排名
# ----------------------------------------------------
def get_total_standings():
    session = Session()
    ranking_data = (session.query(
        Driver.name,
        Driver.team,
        func.sum(Result.points).label('Total_Points') 
    )
    .join(Result, Driver.driver_id == Result.driver_id)
    .group_by(Driver.driver_id, Driver.name, Driver.team)
    .order_by(func.sum(Result.points).desc()) 
    .all())
    
    session.close()
    df = pd.DataFrame(ranking_data, columns=['Driver', 'Team', 'Total_Points'])
    return df

# ----------------------------------------------------
# 2. 獲取詳細單場成績
# ----------------------------------------------------
def get_detailed_results():
    session = Session()
    detailed_data = (session.query(
        Driver.name.label('Driver'),
        Driver.team.label('Team'),
        Race.name.label('Race_Name'),
        Race.type.label('Race_Type'),
        Race.date.label('Race_Date'), 
        Result.points.label('Points'),
        Result.position.label('Position')
    )
    .join(Result, Driver.driver_id == Result.driver_id)
    .join(Race, Race.race_id == Result.race_id)
    .order_by(Driver.name, Race.date)
    .all())
    
    session.close()
    df = pd.DataFrame(detailed_data, columns=['Driver', 'Team', 'Race_Name', 'Race_Type', 'Race_Date', 'Points', 'Position'])
    return df

# ----------------------------------------------------
# 3. 繪製車手總積分圖表 (修正排序：高分在上)
# ----------------------------------------------------
def create_ranking_figure(df_standings):
    # 這裡傳入 df_standings 以繪製總分圖
    fig = px.bar(
        df_standings,
        x='Total_Points',      
        y='Driver',          
        color='Team',         
        title='**車手總積分排名 (Driver Standings)**',
        orientation='h',     
        text='Total_Points',       
        color_discrete_map=TEAM_COLORS, 
        height=500
    )

    fig.update_traces(
        texttemplate='%{text}', 
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>總積分: %{x}<extra></extra>"
    )
    
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        title_font_size=20,
        # 🚨 關鍵修正：將 Y 軸類別設定為由高至低 (降序) 🚨
        yaxis={'categoryorder': 'total ascending', 'autorange': 'reversed'},
        xaxis_title="總積分",
        legend_title_text="車隊 (Team)",
        margin=dict(l=100, r=50, t=80, b=50)
    )
    
    return fig

# ----------------------------------------------------
# 4. 獲取車隊總積分
# ----------------------------------------------------
def get_team_standings():
    session = Session()
    team_points = session.query(
        Driver.team.label('Team'), 
        func.sum(Result.points).label('Total_Points')
    )\
    .join(Result, Driver.driver_id == Result.driver_id) \
    .group_by(Driver.team) \
    .order_by(func.sum(Result.points).desc()).all()
    
    session.close()
    df_team_standings = pd.DataFrame(team_points, columns=['Team', 'Total_Points'])
    return df_team_standings

# ----------------------------------------------------
# 5. 繪製車隊總積分排名圖表 (修正排序：高分在上)
# ----------------------------------------------------
def create_team_ranking_figure(df_team_standings):
    fig = px.bar(
        df_team_standings,
        x='Total_Points',       
        y='Team',              
        color='Team',          
        title='**車隊總積分排名 (Team Standings)**',
        orientation='h',       
        text='Total_Points',    
        color_discrete_map=TEAM_COLORS, 
        height=400
    )

    fig.update_traces(
        texttemplate='%{text}', 
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>總積分: %{x}<extra></extra>"
    )
    
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        title_font_size=20,
        # 🚨 關鍵修正：將 Y 軸類別設定為由高至低 (降序) 🚨
        yaxis={'categoryorder': 'total ascending', 'autorange': 'reversed'},
        xaxis_title="總積分",
        legend_title_text="車隊 (Team)",
        margin=dict(l=100, r=50, t=80, b=50)
    )
    
    return fig

# ----------------------------------------------------
# 輔助函數：提取 GP 名稱
# ----------------------------------------------------
def extract_gp_name(race_name):
    if '衝刺賽' in race_name:
        return race_name.split('衝刺賽')[0]
    elif '正賽' in race_name:
        return race_name.split('正賽')[0]
    return race_name 

# ====================================================================
# C. 數據插入與初始化 (create_initial_drivers, insert_all_race_data 略)
# 確保您的 app.py 仍包含這部分函數以及 race_data 列表
# ====================================================================

# ... (此處請保留您原本的 create_initial_drivers, insert_all_race_data 和 race_data) ...

# ====================================================================
# D. 主體執行區塊
# ====================================================================

# 資料庫同步
# create_initial_drivers()
# insert_all_race_data() 

app = dash.Dash(__name__)
server = app.server

# 數據準備
df_standings = get_total_standings() 
df_detailed = get_detailed_results()
df_team_standings = get_team_standings()

# 修正 GP 計數
df_detailed['GP_Name'] = df_detailed['Race_Name'].apply(extract_gp_name)
total_grand_prix_count = len(df_detailed['GP_Name'].unique())

# 創建圖表
ranking_fig = create_ranking_figure(df_standings)
team_ranking_fig = create_team_ranking_figure(df_team_standings)

# 表格樞紐分析
df_detailed['Col_Name'] = df_detailed['Race_Type'] + '_' + df_detailed['Race_Name']
df_pivot = df_detailed.pivot_table(
    index=['Driver', 'Team'], 
    columns='Col_Name', 
    values=['Points', 'Position'], 
    aggfunc='first'
).reset_index()
df_pivot.columns = ['Driver', 'Team'] + [f'{col[0]}_{col[1]}' for col in df_pivot.columns.tolist() if col[0] not in ['Driver', 'Team']]
df_pivot_merged = pd.merge(df_pivot, df_standings[['Driver', 'Total_Points']], on='Driver', how='left')
desired_cols = ['Driver', 'Team', 'Total_Points'] + sorted([col for col in df_pivot_merged.columns if col not in ['Driver', 'Team', 'Total_Points']], key=lambda x: (x.split('_')[1], x.split('_')[0]))
df_final_table = df_pivot_merged[desired_cols]

# 佈局
app.layout = html.Div(children=[
    html.H1(children='我們遊戲的 F1 總積分排名紀錄', style={'textAlign': 'center', 'color': '#FF1801', 'font-size': '36px'}),
    html.Div(children=f'資料來源: 已完成 {total_grand_prix_count} 個大獎賽（共 {len(df_detailed.Race_Name.unique())} 場比賽）', style={'textAlign': 'center', 'margin-bottom': '20px'}),
    
    html.Div([dcc.Graph(id='team-ranking-graph', figure=team_ranking_fig)], style={'padding': '10px'}),
    html.Div([dcc.Graph(id='total-ranking-graph', figure=ranking_fig)], style={'padding': '10px'}),
    
    html.H2(children='詳細單場成績', style={'margin-top': '40px'}),
    dash.dash_table.DataTable(
        id='detailed-ranking-table',
        columns=[{"name": col.replace('_', ' '), "id": col} for col in df_final_table.columns],
        data=df_final_table.to_dict('records'),
        style_header={'backgroundColor': '#E0E0E0', 'fontWeight': 'bold', 'border': '1px solid black'},
        style_cell={'textAlign': 'center', 'minWidth': '100px', 'border': '1px solid #D0D0D0'},
        sort_action="native",
    )
])

if __name__ == '__main__':
    # app.run_server(debug=True)
    pass