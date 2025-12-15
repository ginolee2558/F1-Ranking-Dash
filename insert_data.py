# insert_data.py

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database_setup import Base, Race, Result, Driver
from datetime import date

# 創建資料庫引擎
engine = create_engine('sqlite:///f1_records.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

print("開始寫入數據...")

# ----------------------------------------------------
# 輔助函數：查找或創建比賽
# ----------------------------------------------------
def find_or_create_race(race_name, race_type, race_date):
    # 檢查該比賽是否已存在
    race = session.query(Race).filter_by(name=race_name, type=race_type).first()
    if not race:
        # 如果不存在，則創建新的比賽記錄
        race = Race(name=race_name, type=race_type, date=race_date)
        session.add(race)
        session.commit()
        print(f"已新增比賽: {race_name} ({race_type})")
    return race

# ----------------------------------------------------
# 輔助函數：查找車手
# ----------------------------------------------------
def get_driver(driver_name):
    driver = session.query(Driver).filter_by(name=driver_name).first()
    if not driver:
        # 這裡不應該發生，因為我們假設車手已在第一次運行時創建
        raise ValueError(f"錯誤：找不到車手 {driver_name}")
    return driver

# ----------------------------------------------------
# A. 數據定義 (所有數據)
# ----------------------------------------------------

# ** 第一站：巴林衝刺賽和正賽 (2025年賽季開始) **
race_data = [
    # ---- 巴林衝刺賽 ----
    {'name': '巴林衝刺賽', 'type': 'Sprint', 'date': date(2025, 3, 1), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 8, 'position': 1},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 7, 'position': 2},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 6, 'position': 3},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 5, 'position': 4},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 4, 'position': 5},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 3, 'position': 6},
    ]},
    
    # ---- 巴林正賽 ----
    {'name': '巴林正賽', 'type': 'Race', 'date': date(2025, 3, 2), 
     'results': [
        {'driver_name': 'mimicethan', 'team': 'McLaren', 'points': 25, 'position': 1},
        {'driver_name': 'RUUR', 'team': 'Mercedes', 'points': 18, 'position': 2},
        {'driver_name': 'leegino2558', 'team': 'Red Bull', 'points': 15, 'position': 3},
        {'driver_name': 'henrythanks69', 'team': 'McLaren', 'points': 12, 'position': 4},
        {'driver_name': 'Tulio', 'team': 'Red Bull', 'points': 10, 'position': 5},
        {'driver_name': 'Lavender', 'team': 'Mercedes', 'points': 0, 'position': 10}, # 假設第 10 名為 0 分，但仍記錄排名
    ]}
]

# ----------------------------------------------------
# B. 寫入比賽成績
# ----------------------------------------------------
for race_info in race_data:
    race = find_or_create_race(race_info['name'], race_info['type'], race_info['date'])
    
    for result_info in race_info['results']:
        driver = get_driver(result_info['driver_name'])
        
        # 檢查該車手在該場比賽的成績是否已存在，如果存在則跳過
        existing_result = session.query(Result).filter_by(
            driver_id=driver.driver_id, 
            race_id=race.race_id
        ).first()
        
        if existing_result:
            # print(f"跳過：{driver.name} 在 {race.name} 的成績已存在。")
            continue
            
        # 創建新的成績記錄
        new_result = Result(
            driver_id=driver.driver_id,
            race_id=race.race_id,
            points=result_info['points'],
            position=result_info['position']
            # 注意：Team 資訊不再這裡儲存，而是從 Driver 模型中獲取
        )
        session.add(new_result)
        print(f"已新增成績: {driver.name} 在 {race.name} 獲得 {new_result.points} 分")

    session.commit()

session.close()
print("所有比賽成績數據已成功寫入資料庫。")