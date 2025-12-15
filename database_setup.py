from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# --- 1. 資料庫連線設定 ---
# 創建一個 SQLite 引擎，並將資料庫檔案命名為 'f1_records.db'
engine = create_engine('sqlite:///f1_records.db')
Base = declarative_base() # 所有資料表的基類

# --- 2. 定義表格結構 (Models) ---

class Driver(Base):
    __tablename__ = 'drivers'
    driver_id = Column(Integer, primary_key=True)
    name = Column(String)
    
    team = Column(String) # 例如: McLaren, Red Bull Racing
    
    # 設置關係，方便查詢某選手的所有成績
    results = relationship("Result", back_populates="driver")

class Race(Base):
    __tablename__ = 'races'
    race_id = Column(Integer, primary_key=True)
    name = Column(String) # 例如: Abu Dhabi GP
    type = Column(String)
    date = Column(String)
    
    # 設置關係
    results = relationship("Result", back_populates="race")

class Result(Base):
    __tablename__ = 'results'
    result_id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('drivers.driver_id'))  # 外鍵: 連結到 drivers 表
    race_id = Column(Integer, ForeignKey('races.race_id'))        # 外鍵: 連結到 races 表
    points = Column(Integer)  # 獲得的積分
    position = Column(Integer) # 最終排名 (例如: 1, 2, 3...)
    
    # 定義物件關係
    driver = relationship("Driver", back_populates="results")
    race = relationship("Race", back_populates="results")


# --- 3. 執行創建 ---
# 根據上面定義的 Class，在資料庫中創建對應的表格
Base.metadata.create_all(engine)

print("✅ 資料庫 f1_records.db 和所有表格已成功創建！")