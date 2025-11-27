"""
データベース接続とセッション管理
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models import Base


class DatabaseManager:
    """データベース接続マネージャー"""

    def __init__(self, database_url: str = None):
        """
        Args:
            database_url: データベース接続URL（指定がない場合は環境変数から取得）
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/life_simulator"
        )
        self.engine = create_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true"
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """全テーブルを作成"""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """全テーブルを削除（注意して使用）"""
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        セッションのコンテキストマネージャー

        Usage:
            with db_manager.get_session() as session:
                # セッションを使った処理
                session.query(Occupation).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_session_raw(self) -> Session:
        """
        セッションを取得（手動でクローズする必要がある）

        Returns:
            Session: SQLAlchemyセッション
        """
        return self.SessionLocal()


# グローバルインスタンス
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI用のデータベースセッション依存性

    Usage:
        @app.get("/occupations")
        def get_occupations(db: Session = Depends(get_db)):
            return db.query(Occupation).all()
    """
    session = db_manager.get_session_raw()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
