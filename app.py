import dash
from dash import dcc, html
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
import plotly.express as px
from database_setup import Base, Race, Result, Driver

# --- 1. 資料庫連線與查詢 ---
engine = create_engine('sqlite:///f1_records.db')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)

def get_total_standings():
    """從資料庫中獲取並計算總積分排名"""
    session = Session()
    
    # 使用 SQLAlchemy 進行 GROUP BY 和 SUM 操作
    ranking_data = (session.query(
        Driver.name,
        Driver.team,
        func.sum(Result.points).label('Total_Points') # 計算總積分
    )
    .join(Result, Driver.driver_id == Result.driver_id)
    .group_by(Driver.driver_id, Driver.name, Driver.team)
    .order_by(func.sum(Result.points).desc()) # 按總積分倒序排列
    .all())
    
    session.close()
    
    # 將查詢結果轉換為 Pandas DataFrame 方便繪圖
    df = pd.DataFrame(ranking_data, columns=['Driver', 'Team', 'Total_Points'])
    return df

# --- 1. 資料庫連線與查詢 ---
# ... (這裡省略了 app.py 中已經存在的設定)

def get_detailed_results():
    """從資料庫中獲取每位選手在每場比賽的詳細成績"""
    session = Session()
    
    # 查詢所有成績，並加入選手姓名、車隊、比賽名稱和類型
    detailed_data = (session.query(
        Driver.name.label('Driver'),
        Driver.team.label('Team'),
        Race.name.label('Race_Name'),
        Race.type.label('Race_Type'),
        Result.points.label('Points'),
        Result.position.label('Position')
    )
    .join(Result, Driver.driver_id == Result.driver_id)
    .join(Race, Race.race_id == Result.race_id)
    .order_by(Driver.name, Race.race_id) # 按選手姓名和比賽場次排序
    .all())
    
    session.close()
    
    # 轉換為 Pandas DataFrame
    df = pd.DataFrame(detailed_data, columns=['Driver', 'Team', 'Race_Name', 'Race_Type', 'Points', 'Position'])
    return df
# --- 2. Dash 應用程式設定 ---
app = dash.Dash(__name__)
server = app.server

# --- 3. 建立儀表板佈局 ---

def create_ranking_figure(df):
    """根據 DataFrame 創建排名圖表"""
    # 創建條形圖，X 軸是積分，Y 軸是車手，顏色用車隊區分
    fig = px.bar(df, x='Total_Points', y='Driver', orientation='h',
                 color='Team', 
                 title='F1 總積分排名',
                 # 設置圖表的順序，排名第一在最上面
                 category_orders={"Driver": df['Driver'].tolist()[::-1]} 
                )
    
    # 調整圖表樣式
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    fig.update_traces(texttemplate='%{x}', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    
    return fig

# ----------------------------------------------------
# 5. 獲取車隊總積分
# ----------------------------------------------------
# app.py 檔案中

# 確保在 app.py 頂部匯入 Driver 模型


def get_team_standings():
    Session = sessionmaker(bind=engine)
    session = Session()

    # 計算每個車隊的總積分
    # *** 這裡使用 JOIN 來連接 Result 和 Driver，並使用 Driver.team ***
    team_points = session.query(
        Driver.team.label('Team'), # <--- 修正：使用 Driver 模型中的 team 欄位
        func.sum(Result.points).label('Total_Points')
    )\
    .join(Driver, Result.driver_id == Driver.driver_id)   \
    .group_by(Driver.team) \
    .order_by(func.sum(Result.points).desc()).all()
    
    session.close()
    
    # 轉換為 DataFrame
    df_team_standings = pd.DataFrame(team_points, columns=['Team', 'Total_Points'])
    return df_team_standings

# ----------------------------------------------------
# 6. 繪製車隊總積分排名圖表
# ----------------------------------------------------
def create_team_ranking_figure(df_team_standings):
    fig = px.bar(
        df_team_standings,
        x='Team',
        y='Total_Points',
        text='Total_Points',
        title='**車隊總積分排名 (Team Standings)**',
        color='Team',
        height=400
    )
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', title_font_size=20)
    return fig
# ... (省略 ranking_fig = create_ranking_figure(df_standings) 上方的程式碼)
# --- A. 數據準備和圖表/表格創建 ---

# 1. 獲取總積分排名數據 (Total Standings)
df_standings = get_total_standings() 
ranking_fig = create_ranking_figure(df_standings)

# 1.1 獲取車隊總積分數據 (Team Standings) <--- NEW
df_team_standings = get_team_standings()
team_ranking_fig = create_team_ranking_figure(df_team_standings) # <--- NEW

# 2. 獲取詳細單場數據 (Detailed Results)
df_detailed = get_detailed_results()

# 將 'Race_Type' 和 'Points/Position' 進行合併，以便進行樞紐分析
df_detailed['Col_Name'] = df_detailed['Race_Type'] + '_' + df_detailed['Race_Name']

# 執行樞紐分析 (Pivot): 以 Driver 和 Team 為索引，Col_Name 為欄位
df_pivot = df_detailed.pivot_table(
    index=['Driver', 'Team'], 
    columns='Col_Name', 
    values=['Points', 'Position'], 
    aggfunc='first' # 每個組合只有一個值
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

# ... (其餘程式碼，例如 df_final_table 的欄位名稱替換等，保持不變)


# --- 4. 重新定義網站佈局 (使用新的詳細表格) ---
app.layout = html.Div(children=[
    html.H1(children='我們遊戲的 F1 總積分排名紀錄', style={'textAlign': 'center', 'color': '#FF1801', 'font-size': '36px'}),
    html.Div(children=f'資料來源: 已完成 {len(df_standings)} 位玩家的 1 場比賽', style={'textAlign': 'center', 'margin-bottom': '20px'}),
    # ... (您的個人總積分圖表 (ranking-graph) 結束) ...

    # 新增車隊總積分圖表 <--- NEW
    html.Div(children=[
        dcc.Graph(
            id='team-ranking-graph',
            figure=team_ranking_fig
        )
    ], style={'padding': '20px'}),
    
    # ... (後續的詳細成績表 (dataTable) 保持不變) ...
    # 放置總積分圖表 (保持不變)
    dcc.Graph(
        id='total-ranking-graph',
        figure=ranking_fig,
        style={'height': '500px'}
    ),
    
    html.H2(children='詳細單場成績', style={'margin-top': '40px'}),
    # 放置詳細的單場成績表格 (已優化)
    dash.dash_table.DataTable(
        id='detailed-ranking-table',
        # 將欄位名稱從 Python 欄位名轉換成更易讀的表頭
        columns=[{"name": col.replace('_', ' '), "id": col} for col in df_final_table.columns],
        data=df_final_table.to_dict('records'),
        style_header={'backgroundColor': '#E0E0E0', 'fontWeight': 'bold', 'border': '1px solid black'},
        style_cell={'textAlign': 'center', 'minWidth': '100px', 'border': '1px solid #D0D0D0'},
        sort_action="native", # 允許使用者排序
    )
])

if __name__ == '__main__':
    pass