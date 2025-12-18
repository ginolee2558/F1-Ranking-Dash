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
    # ... (其他顏色)
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
# 1. 獲取總積分排名 (用於排序基準)
# ----------------------------------------------------
def get_total_standings():
    """從資料庫中獲取並計算總積分排名"""
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
# 2. 獲取詳細單場成績 (必須包含日期 Race_Date)
# ----------------------------------------------------
def get_detailed_results():
    """從資料庫中獲取每位選手在每場比賽的詳細成績"""
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
# 3. 繪製車手總積分圖表 (修正為非堆疊式 + 車隊顏色 + 高分在上)
# ----------------------------------------------------
def create_ranking_figure(df_detailed):
    """
    修正: 使用非堆疊式，並鎖定車隊顏色，按總積分排名。
    """
    df_standings = get_total_standings()
    driver_order = df_standings['Driver'].tolist()
    
    fig = px.bar(
        df_standings, # 🚨 數據源切回 df_standings 繪製總分 🚨
        x='Total_Points',      
        y='Driver',          
        color='Team',         # 🚨 修正: 依據車隊設定顏色 🚨
        title='**車手總積分排名 (Driver Standings)**',
        orientation='h',     
        text='Total_Points',       
        color_discrete_map=TEAM_COLORS, # 🚨 修正: 使用定義的車隊顏色 🚨
        height=600
    )

    fig.update_traces(
        texttemplate='%{text}', 
        textposition='outside', # 顯示在長條外部
        hovertemplate="<b>%{y}</b><br>總積分: %{x}<extra></extra>" # 簡化懸浮提示
    )
    
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        title_font_size=20,
        # 🚨 修正: 確保積分高的排在上方 🚨
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title="總積分",
        legend_title_text="車隊 (Team)"
    )
    
    return fig

# ----------------------------------------------------
# 4. 獲取車隊總積分 (用於排序基準)
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
# 5. 繪製車隊總積分排名圖表 (修正為非堆疊式 + 車隊顏色 + 高分在上)
# ----------------------------------------------------
def create_team_ranking_figure(df_detailed):
    """
    修正: 使用非堆疊式，並鎖定車隊顏色，按總積分排名。
    """
    df_team_standings = get_team_standings() # 獲取車隊總分和排序
    team_order = df_team_standings['Team'].tolist()
    
    fig = px.bar(
        df_team_standings, # 🚨 數據源切回 df_team_standings 繪製總分 🚨
        x='Total_Points',       
        y='Team',              
        color='Team',          # 🚨 修正: 依據車隊設定顏色 🚨
        title='**車隊總積分排名 (Team Standings)**',
        orientation='h',       
        text='Total_Points',    
        color_discrete_map=TEAM_COLORS, # 🚨 修正: 使用定義的車隊顏色 🚨
        height=400
    )

    fig.update_traces(
        texttemplate='%{text}', 
        textposition='outside', # 顯示在長條外部
        hovertemplate="<b>%{y}</b><br>總積分: %{x}<extra></extra>" # 簡化懸浮提示
    )
    
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        title_font_size=20,
        # 🚨 修正: 確保積分高的排在上方 🚨
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title="總積分",
        legend_title_text="車隊 (Team)"
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
# C. 數據插入函數 (確保 Render 部署時有數據)
# ====================================================================

def find_or_create_race(session, race_name, race_type, race_date):
    race = session.query(Race).filter_by(name=race_name, type=race_type).first()
    if not race:
        race = Race(name=race_name, type=race_type, date=race_date)
        session.add(race)
        session.commit()
    return race

def get_driver(session, driver_name):
    driver = session.query(Driver).filter_by(name=driver_name).first()
    if not driver:
        raise ValueError(f"錯誤：找不到車手 {driver_name}")
    return driver

# 數據定義：將所有站點數據寫入此處 (保持不變)
race_data = [
    # ---- 站點 1：巴林衝刺賽 ----
    {'name': '日本衝刺賽', 'type': 'Sprint', 'date': date(2025, 3, 1), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 0, 'position': 10},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 6, 'position': 3},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 7, 'position': 2},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 5, 'position': 4},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 0, 'position': 9},
    ]},
    
    # ---- 站點 2：巴林正賽 ----
    {'name': '日本正賽', 'type': 'Race', 'date': date(2025, 3, 2), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 18, 'position': 2},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 12, 'position': 4},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 22, 'position': 1},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 18, 'position': 3},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 0, 'position': 10},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 2, 'position': 9}, 
    ]},
    # ---- 站點 2：巴林衝刺賽 ----
    {'name': '巴林衝刺賽', 'type': 'Sprint', 'date': date(2025, 3, 1), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 7, 'position': 2},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 6, 'position': 3},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 5, 'position': 4},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 4, 'position': 5},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 3, 'position': 6},
    ]},
    
    # ---- 站點 2：巴林正賽 ----
    {'name': '巴林正賽', 'type': 'Race', 'date': date(2025, 3, 2), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 18, 'position': 2},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 15, 'position': 3},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 12, 'position': 4},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 10, 'position': 5},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 0, 'position': 10}, 
    ]},

    # ---- 站點 3：沙烏地阿拉伯衝刺賽 ----
    {'name': '沙烏地阿拉伯衝刺賽', 'type': 'Sprint', 'date': date(2025, 3, 15), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 7, 'position': 2},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 6, 'position': 3},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 5, 'position': 4},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 0, 'position': 10}, 
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 0, 'position': 9},
    ]},
    
    # ---- 站點 3：沙烏地阿拉伯正賽 ----
    {'name': '沙烏地阿拉伯正賽', 'type': 'Race', 'date': date(2025, 3, 16), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 18, 'position': 2},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 15, 'position': 3},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 12, 'position': 4},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 0, 'position': 9},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 0, 'position': 10},
    ]},

    # ---- 站點 4：伊莫拉衝刺賽 ----
    {'name': '伊莫拉衝刺賽', 'type': 'Sprint', 'date': date(2025, 4, 19), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 7, 'position': 2},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 6, 'position': 3},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 2, 'position': 7},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 0, 'position': 9},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 0, 'position': 10}, 
    ]},

    # ---- 站點 4：伊莫拉正賽 ----
    {'name': '伊莫拉正賽', 'type': 'Race', 'date': date(2025, 4, 20), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 18, 'position': 2},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 15, 'position': 3},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 12, 'position': 4},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 2, 'position': 9},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 1, 'position': 10},
    ]},

    # ---- 站點 5：奧地利衝刺賽 ----
    {'name': '奧地利衝刺賽', 'type': 'Sprint', 'date': date(2025, 5, 10), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 7, 'position': 2},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 3, 'position': 6},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 1, 'position': 8},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 0, 'position': 9},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 0, 'position': 10},
    ]},

    # ---- 站點 5：奧地利正賽 ----
    {'name': '奧地利正賽', 'type': 'Race', 'date': date(2025, 5, 11), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 18, 'position': 2},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 15, 'position': 3},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 12, 'position': 4},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 10, 'position': 5},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 0, 'position': 10},
    ]}
]


# ----------------------------------------------------
# 6. 車手數據初始化 (確保車手存在)
# ----------------------------------------------------
def create_initial_drivers():
    Session_temp = sessionmaker(bind=engine)
    session = Session_temp()
    
    initial_drivers = [
        {'name': 'mimicethan', 'team': 'McLaren'},
        {'name': 'henrythanks69', 'team': 'McLaren'},
        {'name': 'RUUR', 'team': 'Mercedes'},
        {'name': 'Lavender', 'team': 'Mercedes'},
        {'name': 'Tulio', 'team': 'Red Bull'},
        {'name': 'leegino2558', 'team': 'Red Bull'},
    ]
    
    print("--- 正在檢查並創建車手數據 ---")
    
    for d in initial_drivers:
        driver = session.query(Driver).filter_by(name=d['name']).first()
        if not driver:
            new_driver = Driver(name=d['name'], team=d['team'])
            session.add(new_driver)
            print(f"已創建車手: {d['name']} ({d['team']})")
            
    session.commit()
    session.close()
    print("--- 車手數據已確保存在於資料庫中 ---")
def insert_all_race_data():
    Session_temp = sessionmaker(bind=engine)
    session = Session_temp()
    
    print("--- 正在檢查並插入所有比賽數據 ---")
    
    for race_info in race_data:
        race = find_or_create_race(session, race_info['name'], race_info['type'], race_info['date']) 
        
        for result_info in race_info['results']:
            try:
                driver = get_driver(session, result_info['driver_name'])
                
                existing_result = session.query(Result).filter_by(
                    driver_id=driver.driver_id, 
                    race_id=race.race_id
                ).first()
                
                if existing_result:
                    continue
                    
                new_result = Result(
                    driver_id=driver.driver_id,
                    race_id=race.race_id,
                    points=result_info['points'],
                    position=result_info['position']
                )
                session.add(new_result)
            except ValueError as e:
                print(e)
                session.rollback()
                session.close()
                return

    session.commit()
    session.close()
    print("--- 所有數據已確保存在於資料庫中 ---")
# ----------------------------------------------------
# 數據插入函數定義結束
# ----------------------------------------------------


# ====================================================================
# D. 主體執行區塊：數據處理與佈局定義
# ====================================================================

# 🚨 步驟 1: 數據庫初始化 🚨
create_initial_drivers()
insert_all_race_data() 
# -----------------------------------------------------------------

# 初始化 Dash 應用程式 (server 變量用於 Gunicorn 部署)
app = dash.Dash(__name__)
server = app.server

# --- A. 數據準備和圖表/表格創建 ---

# 1. 獲取總積分排名數據 (Total Standings) - 用於排序
df_standings = get_total_standings() 

# 2. 獲取詳細單場數據 (Detailed Results) - 🚨 必須先定義 df_detailed 🚨
df_detailed = get_detailed_results()

# 3. 處理 df_detailed 並創建 'GP_Name' 欄位（用於修正計數錯誤）
df_detailed['GP_Name'] = df_detailed['Race_Name'].apply(extract_gp_name)
# 修正後的總大獎賽場次 (4 個 GP)
total_grand_prix_count = len(df_detailed['GP_Name'].unique())

# 4. 創建圖表 (現在 df_detailed 已經定義，使用 df_standings 繪製總分)
ranking_fig = create_ranking_figure(df_detailed) # 車手總分圖

# 5. 創建車隊總積分圖表 (使用 df_detailed 繪製總分)
team_ranking_fig = create_team_ranking_figure(df_detailed) 

# --- 樞紐分析 (用於詳細表格) ---
# 將 'Race_Type' 和 'Points/Position' 進行合併，以便進行樞紐分析
df_detailed['Col_Name'] = df_detailed['Race_Type'] + '_' + df_detailed['Race_Name']

# 執行樞紐分析 (Pivot): 以 Driver 和 Team 為索引，Col_Name 為欄位
df_pivot = df_detailed.pivot_table(
    index=['Driver', 'Team'], 
    columns='Col_Name', 
    values=['Points', 'Position'], 
    aggfunc='first'
).reset_index()

# 調整欄位名稱，使其更清晰
df_pivot.columns = ['Driver', 'Team'] + [f'{col[0]}_{col[1]}' for col in df_pivot.columns.tolist() if col[0] in ['Driver', 'Team', 'Points', 'Position'] and col[0] not in ['Driver', 'Team']]

# 💡 NEW STEP: 合併車手總積分到詳細表格
df_pivot_merged = pd.merge(
    df_pivot,
    df_standings[['Driver', 'Total_Points']],
    on='Driver',
    how='left'
)

# 排序欄位以便顯示，並將 'Total_Points' 放在 'Team' 後面
desired_cols = ['Driver', 'Team', 'Total_Points'] + sorted([col for col in df_pivot_merged.columns if col not in ['Driver', 'Team', 'Total_Points']], key=lambda x: (x.split('_')[1], x.split('_')[0]))

df_final_table = df_pivot_merged[desired_cols]

# ----------------------------------------------------
# 6. 重新定義網站佈局 (使用修正後的計數)
# ----------------------------------------------------
app.layout = html.Div(children=[
    html.H1(children='我們遊戲的 F1 總積分排名紀錄', style={'textAlign': 'center', 'color': '#FF1801', 'font-size': '36px'}),
    # 🚨 修正: 使用 total_grand_prix_count 和實際賽事數量 🚨
    html.Div(children=f'資料來源: 已完成 {total_grand_prix_count} 個大獎賽（共 {len(df_detailed.Race_Name.unique())} 場比賽）', style={'textAlign': 'center', 'margin-bottom': '20px'}),
    
    # 新增車隊總積分圖表 (現在是統一車隊顏色)
    html.Div(children=[
        dcc.Graph(
            id='team-ranking-graph',
            figure=team_ranking_fig
        )
    ], style={'padding': '20px'}),
    
    # 放置總積分圖表 (現在是統一車隊顏色)
    dcc.Graph(
        id='total-ranking-graph',
        figure=ranking_fig,
        style={'height': '500px'}
    ),
    
    html.H2(children='詳細單場成績', style={'margin-top': '40px'}),
    # 放置詳細的單場成績表格 (已優化)
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
    # 網站啟動時運行 insert_all_race_data()
    # 如果您想在本地調試，取消註釋下面一行：
    # app.run_server(debug=True)
    pass