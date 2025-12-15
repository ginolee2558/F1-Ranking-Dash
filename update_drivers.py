from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Driver

# 連接到資料庫
engine = create_engine('sqlite:///f1_records.db')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
session = Session()

try:
    # --- 您的修正資訊 ---
    updates = [
        # driver_id=1: 原本是 '您的遊戲名稱' -> 修正為 'mimicethan' (McLaren)
        {'id': 1, 'name': 'mimicethan', 'team': 'McLaren'},
        
        # driver_id=2: 原本是 '同學的遊戲名稱' -> 修正為 'henrythanks69' (McLaren)
        {'id': 2, 'name': 'henrythanks69', 'team': 'McLaren'},
        
        # 確保其他選手的車隊資訊正確，根據您最初提供的數據，RUUR 和 Lavender 是 Mercedes
        {'id': 3, 'name': 'RUUR', 'team': 'Mercedes'},
        {'id': 4, 'name': 'Lavender', 'team': 'Mercedes'},
        
        # Tulio 和 leegino2558 是 Red Bull
        {'id': 5, 'name': 'Tulio', 'team': 'Red Bull'},
        {'id': 6, 'name': 'leegino2558', 'team': 'Red Bull'},
    ]
    
    for data in updates:
        # 根據 driver_id 查找選手
        driver = session.query(Driver).filter_by(driver_id=data['id']).first()
        
        if driver:
            # 進行更新
            driver.name = data['name']
            driver.team = data['team']
            print(f"✔️ 成功更新 Driver ID {data['id']} 為 {data['name']} ({data['team']})")
        else:
            print(f"⚠️ 找不到 Driver ID {data['id']}。")
            
    session.commit()
    print("\n✅ 所有選手名稱和車隊資訊已成功更新！")

except Exception as e:
    session.rollback()
    print(f"❌ 更新數據失敗: {e}")

finally:
    session.close()