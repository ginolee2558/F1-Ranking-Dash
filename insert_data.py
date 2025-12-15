from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Driver, Race, Result # 匯入我們定義的表格

# 連接到資料庫
engine = create_engine('sqlite:///f1_records.db')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
session = Session()

# ----------------------------------------------------
# 1. 新增所有選手資料 (Drivers)
# ----------------------------------------------------

# 定義所有 6 位選手及其車隊
drivers_data = [
    {'id': 1, 'name': 'mimicethan', 'team': 'McLaren'},
    {'id': 2, 'name': 'henrythanks69', 'team': 'McLaren'},
    {'id': 3, 'name': 'RUUR', 'team': 'Mercedes'},
    {'id': 4, 'name': 'Lavender', 'team': 'Mercedes'},
    {'id': 5, 'name': 'Tulio', 'team': 'Red Bull'},
    {'id': 6, 'name': 'leegino2558', 'team': 'Red Bull'},
]

# 檢查並新增選手 (如果 ID 不存在則新增)
for d in drivers_data:
    if not session.query(Driver).filter_by(driver_id=d['id']).first():
        session.add(Driver(driver_id=d['id'], name=d['name'], team=d['team']))

# ----------------------------------------------------
# 2. 新增比賽資料 (Races)
# ----------------------------------------------------

# 注意：這裡的 race_id 請勿重複，後續比賽將從 3 開始編號
# 我們假設 race_id 1 = 日本衝刺賽, race_id 2 = 日本正賽
races_data = [
    {'id': 1, 'name': '日本 GP', 'type': 'Sprint', 'date': '2025-12-15'},
    {'id': 2, 'name': '日本 GP', 'type': 'Main Race', 'date': '2025-12-15'},
]

for r in races_data:
    if not session.query(Race).filter_by(race_id=r['id']).first():
        session.add(Race(race_id=r['id'], name=r['name'], type=r['type'], date=r['date']))

session.commit() # 提交 Driver 和 Race 資料

# ----------------------------------------------------
# 3. 新增成績 (Results) - 第 1 場比賽
# ----------------------------------------------------

# (driver_id, race_id, points, position)
results_list = [
    # 日本衝刺賽 (race_id=1)
    (1, 1, 8, 1),  # mimicethan
    (2, 1, 7, 2),  # henrythanks69
    (3, 1, 6, 3),  # RUUR
    (4, 1, 5, 4),  # Lavender
    (5, 1, 0, 9),  # Tulio
    (6, 1, 0, 10), # leegino2558
    
    # 日本正賽 (race_id=2)
    (1, 2, 18, 2), # mimicethan
    (2, 2, 18, 3), # henrythanks69
    (3, 2, 12, 4), # RUUR
    (4, 2, 2, 9),  # Lavender
    (5, 2, 0, 10), # Tulio
    (6, 2, 22, 1), # leegino2558
]

for res_data in results_list:
    # 這裡我們不使用 result_id，讓資料庫自動生成
    new_result = Result(
        driver_id=res_data[0], 
        race_id=res_data[1], 
        points=res_data[2], 
        position=res_data[3]
    )
    session.add(new_result)

session.commit()
session.close()

print("✅ 第 1 場比賽 (日本 GP) 數據已成功錄入資料庫！")