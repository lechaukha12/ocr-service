from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Đường dẫn tới file SQLite. File này sẽ được tạo trong thư mục user_service.
# Bạn có thể thay đổi đường dẫn nếu muốn, ví dụ: /data/user_service.db khi dùng Docker volume
SQLALCHEMY_DATABASE_URL = "sqlite:///./user_service.db"
# Đối với PostgreSQL sau này:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

# create_engine là điểm vào chính của SQLAlchemy.
# connect_args={"check_same_thread": False} chỉ cần thiết cho SQLite.
# Nó cho phép nhiều thread truy cập cùng một kết nối, điều mà SQLite không hỗ trợ mặc định.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Mỗi instance của SessionLocal sẽ là một database session.
# autocommit=False và autoflush=False là các cài đặt mặc định tốt.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base sẽ được sử dụng để tạo các model ORM (các lớp đại diện cho bảng trong DB).
Base = declarative_base()

# Dependency để lấy DB session trong các API endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hàm để tạo tất cả các bảng trong database
# Sẽ được gọi khi ứng dụng khởi động
def create_db_tables():
    Base.metadata.create_all(bind=engine)

