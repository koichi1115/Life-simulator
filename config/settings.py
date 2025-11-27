"""
アプリケーション設定
Pydantic Settingsを使用して環境変数から設定を読み込む
"""
import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    # プロジェクトルート
    project_root: Path = Path(__file__).parent.parent

    # データベース設定
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/life_simulator",
        description="PostgreSQL接続URL"
    )
    sql_echo: bool = Field(
        default=False,
        description="SQLクエリをログ出力するか"
    )

    # O*NET API設定
    onet_username: Optional[str] = Field(
        default=None,
        description="O*NET APIユーザー名"
    )
    onet_password: Optional[str] = Field(
        default=None,
        description="O*NET APIパスワード"
    )

    # データ収集設定
    data_dir: Path = Field(
        default=Path("data"),
        description="データファイルの保存ディレクトリ"
    )
    collection_batch_size: int = Field(
        default=100,
        description="データ収集のバッチサイズ"
    )
    rate_limit_delay: float = Field(
        default=1.0,
        description="APIリクエスト間の遅延（秒）"
    )

    # ログ設定
    log_level: str = Field(
        default="INFO",
        description="ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Path = Field(
        default=Path("logs/app.log"),
        description="ログファイルのパス"
    )

    # 重複排除設定
    similarity_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="重複判定の類似度閾値"
    )
    exact_match_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="完全一致判定の類似度閾値"
    )

    # Pydantic設定
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 相対パスを絶対パスに変換
        if not self.data_dir.is_absolute():
            self.data_dir = self.project_root / self.data_dir

        if not self.log_file.is_absolute():
            self.log_file = self.project_root / self.log_file

        # 必要なディレクトリを作成
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    @property
    def isco_data_dir(self) -> Path:
        """ISCOデータディレクトリ"""
        path = self.data_dir / "isco"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def onet_data_dir(self) -> Path:
        """O*NETデータディレクトリ"""
        path = self.data_dir / "onet"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def output_data_dir(self) -> Path:
        """出力データディレクトリ"""
        path = self.data_dir / "output"
        path.mkdir(parents=True, exist_ok=True)
        return path


# グローバル設定インスタンス
settings = Settings()


def get_settings() -> Settings:
    """設定インスタンスを取得"""
    return settings
