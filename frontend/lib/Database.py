import pymysql
from pymysql.err import MySQLError

class DatabaseConnection:
    """Quản lý kết nối MySQL với pymysql"""
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                user="drb",
                password="drb123456",
                database="drb_text",
                cursorclass=pymysql.cursors.DictCursor,  # để trả về dict thay vì tuple
                autocommit=False                        # mình sẽ chủ động commit/rollback
            )
            self.cursor = self.conn.cursor()
        except MySQLError as e:
            print(f"Lỗi kết nối: {e}")
            raise

    def execute(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
        except MySQLError as e:
            print(f"Lỗi SQL: {e}")
            self.conn.rollback()
            raise

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

class BaseModel:
    """ORM mini base - classmethod version"""
    table_name = ""
    primary_key = "id"
    db: DatabaseConnection = None  # kết nối dùng chung cho mọi class

    @classmethod
    def use_db(cls, db: DatabaseConnection):
        """Gán DB connection dùng chung"""
        cls.db = db

    @classmethod
    def insert(cls, data: dict):
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {cls.table_name} ({cols}) VALUES ({placeholders})"
        cls.db.execute(query, tuple(data.values()))

    @classmethod
    def get_all(cls):
        query = f"SELECT * FROM {cls.table_name}"
        cls.db.execute(query)
        return cls.db.fetchall()

    @classmethod
    def get_by(cls, column: str, value):
        """Lấy hang theo gia tri 1 cột bất kỳ"""
        query = f"SELECT * FROM {cls.table_name} WHERE {column}=%s"
        cls.db.execute(query, (value,))
        return cls.db.fetchall()

    @classmethod
    def get_column(cls, column: str):
        """
        Lấy toàn bộ giá trị của 1 cột trong bảng
        Trả về list
        """
        query = f"SELECT {column} FROM {cls.table_name}"
        cls.db.execute(query)
        rows = cls.db.fetchall()

        result = []
        for row in rows:
            if isinstance(row, dict):  # Nếu cursor trả về dict
                result.append(row[column])
            else:  # Nếu cursor trả về tuple
                result.append(row[0])
        return result
    
    @classmethod
    def get_columns_by(cls, select_cols: list, where: dict):
        """
        Lấy giá trị từ nhiều cột với điều kiện nhiều cột
        Ví dụ:
        BaseModel.get_columns_by(
            ["user_id", "user_name", "role_group"],
            {"user_name": "abc", "password_hash": "xyz"}
        )
        """
        cols = ", ".join(select_cols)
        where_clause = " AND ".join([f"{col}=%s" for col in where.keys()])
        query = f"SELECT {cols} FROM {cls.table_name} WHERE {where_clause}"
        cls.db.execute(query, tuple(where.values()))
        return cls.db.fetchall()
    
    @classmethod
    def update(cls, column: str, value, updates: dict):
        # bọc tên cột bằng backtick để tránh trùng keyword
        set_clause = ", ".join([f"`{col}`=%s" for col in updates.keys()])
        query = f"UPDATE {cls.table_name} SET {set_clause} WHERE `{column}`=%s"
        values = list(updates.values()) + [value]
        cls.db.execute(query, tuple(values))

    @classmethod
    def delete(cls, column: str, value):
        query = f"DELETE FROM {cls.table_name} WHERE {column}=%s"
        cls.db.execute(query, (value,))

    @classmethod
    def insert_or_update(cls, data: dict):
        """
        Thêm bản ghi, nếu trùng khóa chính thì update
        """
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        updates = ", ".join([f"{col}=VALUES({col})" for col in data.keys()])

        query = f"""
            INSERT INTO {cls.table_name} ({cols})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {updates}
        """
        cls.db.execute(query, tuple(data.values()))

    

    @classmethod
    def update_by_two(cls, col1: str, val1, col2: str, val2, updates: dict):
        set_clause = ", ".join([f"`{col}`=%s" for col in updates.keys()])
        query = f"UPDATE `{cls.table_name}` SET {set_clause} WHERE `{col1}`=%s AND `{col2}`=%s"
        values = list(updates.values()) + [val1, val2]
        cls.db.execute(query, tuple(values))

# db = DatabaseConnection()
# BaseModel.use_db(db)

# Tạo bảng

class AuditTrial(BaseModel):
    table_name = "auditlog"

class Product(BaseModel):
    table_name = "product"

class ProductReport(BaseModel):
    table_name = "productreport"

class CameraSetting(BaseModel):
    table_name = "camerasettings"

class User(BaseModel):
    table_name = "users"

class LoginAudit(BaseModel):
    table_name = "loginaudit"

class CurrentSession(BaseModel):
    table_name = "current_session"