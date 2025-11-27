"""
ISCO-08 データコレクター
国際標準職業分類（International Standard Classification of Occupations）のデータを収集
"""
import csv
import os
from typing import Dict, List, Optional
from pathlib import Path

import pandas as pd
import requests


class IscoCollector:
    """
    ISCO-08 データコレクター

    ILO（国際労働機関）の国際標準職業分類データを取得・解析
    """

    # ISCO-08の公式データソース
    ISCO_DATA_URL = "https://www.ilo.org/public/english/bureau/stat/isco/isco08/"

    # ISCO-08の階層構造
    MAJOR_GROUPS = {
        "1": "管理職 (Managers)",
        "2": "専門職 (Professionals)",
        "3": "技術職および準専門職 (Technicians and Associate Professionals)",
        "4": "事務補助職 (Clerical Support Workers)",
        "5": "サービス・販売職 (Service and Sales Workers)",
        "6": "農林漁業の熟練従事者 (Skilled Agricultural, Forestry and Fishery Workers)",
        "7": "技能工およびその関連職 (Craft and Related Trades Workers)",
        "8": "設備・機械の運転・組立工 (Plant and Machine Operators and Assemblers)",
        "9": "単純作業の職業 (Elementary Occupations)",
        "0": "軍隊 (Armed Forces Occupations)",
    }

    def __init__(self, data_dir: str = "data/isco"):
        """
        Args:
            data_dir: ISCOデータファイルを保存するディレクトリ
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_isco_data(self, output_file: str = None) -> str:
        """
        ISCO-08データをダウンロード

        注意: 実際のデータは手動でダウンロードが必要な場合があります
        ILO公式サイト: https://www.ilo.org/public/english/bureau/stat/isco/isco08/

        Args:
            output_file: 保存先ファイル名

        Returns:
            保存されたファイルパス
        """
        if output_file is None:
            output_file = self.data_dir / "isco08_structure.csv"

        print("注意: ISCO-08の公式データは以下からダウンロードしてください:")
        print("https://www.ilo.org/public/english/bureau/stat/isco/isco08/index.htm")
        print(f"データを {self.data_dir} に配置してください")

        return str(output_file)

    def parse_isco_code(self, isco_code: str) -> Dict[str, str]:
        """
        ISCOコードを解析して階層情報を抽出

        ISCO-08のコード構造:
        - 1桁: 大分類 (Major Group)
        - 2桁: 中分類 (Sub-major Group)
        - 3桁: 小分類 (Minor Group)
        - 4桁: 細分類 (Unit Group)

        Args:
            isco_code: ISCOコード（例: "2511"）

        Returns:
            階層情報の辞書
        """
        code = isco_code.strip()

        result = {
            "code": code,
            "major_group": code[0] if len(code) >= 1 else None,
            "submajor_group": code[:2] if len(code) >= 2 else None,
            "minor_group": code[:3] if len(code) >= 3 else None,
            "unit_group": code if len(code) == 4 else None,
        }

        # 大分類名を追加
        if result["major_group"]:
            result["major_group_name"] = self.MAJOR_GROUPS.get(
                result["major_group"],
                "不明"
            )

        return result

    def load_from_csv(self, csv_file: str) -> List[Dict]:
        """
        CSVファイルからISCOデータを読み込む

        期待されるCSV形式:
        code,title,description

        Args:
            csv_file: CSVファイルパス

        Returns:
            職業情報のリスト
        """
        csv_path = Path(csv_file)

        if not csv_path.exists():
            raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_file}")

        occupations = []

        try:
            df = pd.read_csv(csv_path)

            for _, row in df.iterrows():
                code = str(row.get("code", "")).strip()
                title = str(row.get("title", "")).strip()
                description = str(row.get("description", "")).strip()

                if not code or not title:
                    continue

                hierarchy = self.parse_isco_code(code)

                occupation = {
                    "isco_code": code,
                    "title": title,
                    "description": description,
                    "hierarchy": hierarchy,
                    "major_group": hierarchy["major_group"],
                    "major_group_name": hierarchy.get("major_group_name"),
                }

                occupations.append(occupation)

            print(f"ISCO-08: {len(occupations)}件の職業を読み込みました")

        except Exception as e:
            print(f"CSVの読み込みエラー: {e}")
            raise

        return occupations

    def generate_sample_data(self) -> List[Dict]:
        """
        ISCO-08のサンプルデータを生成

        実際のデータが入手できない場合のテスト用

        Returns:
            サンプル職業データ
        """
        sample_data = [
            {
                "isco_code": "1111",
                "title": "Legislators",
                "description": "国や地方自治体の法律、公共政策を制定・修正する議員",
                "category": "Managers"
            },
            {
                "isco_code": "2511",
                "title": "Systems Analysts",
                "description": "情報システムの設計・開発・実装を行う専門家",
                "category": "Professionals"
            },
            {
                "isco_code": "2512",
                "title": "Software Developers",
                "description": "ソフトウェアの設計、開発、テストを行う",
                "category": "Professionals"
            },
            {
                "isco_code": "2513",
                "title": "Web and Multimedia Developers",
                "description": "Webサイトやマルチメディアアプリケーションの開発",
                "category": "Professionals"
            },
            {
                "isco_code": "2514",
                "title": "Applications Programmers",
                "description": "アプリケーションソフトウェアのプログラミング",
                "category": "Professionals"
            },
            {
                "isco_code": "2221",
                "title": "Nursing Professionals",
                "description": "看護ケアの計画、提供、評価を行う専門看護師",
                "category": "Professionals"
            },
            {
                "isco_code": "2310",
                "title": "University and Higher Education Teachers",
                "description": "大学および高等教育機関での教育・研究",
                "category": "Professionals"
            },
            {
                "isco_code": "2411",
                "title": "Accountants",
                "description": "会計記録の管理と財務諸表の作成",
                "category": "Professionals"
            },
            {
                "isco_code": "2421",
                "title": "Management and Organization Analysts",
                "description": "経営・組織の分析とコンサルティング",
                "category": "Professionals"
            },
            {
                "isco_code": "3511",
                "title": "Information and Communications Technology Operations Technicians",
                "description": "ICTシステムの運用・保守",
                "category": "Technicians"
            },
        ]

        occupations = []
        for data in sample_data:
            hierarchy = self.parse_isco_code(data["isco_code"])
            occupation = {
                "isco_code": data["isco_code"],
                "title": data["title"],
                "description": data["description"],
                "hierarchy": hierarchy,
                "major_group": hierarchy["major_group"],
                "major_group_name": hierarchy.get("major_group_name"),
            }
            occupations.append(occupation)

        return occupations

    def get_all_major_groups(self) -> Dict[str, str]:
        """
        ISCO-08の全大分類を取得

        Returns:
            大分類コードと名称の辞書
        """
        return self.MAJOR_GROUPS.copy()

    def filter_by_major_group(
        self,
        occupations: List[Dict],
        major_group_code: str
    ) -> List[Dict]:
        """
        特定の大分類に属する職業をフィルタリング

        Args:
            occupations: 職業リスト
            major_group_code: 大分類コード（例: "2"）

        Returns:
            フィルタリングされた職業リスト
        """
        return [
            occ for occ in occupations
            if occ.get("major_group") == major_group_code
        ]

    def export_to_csv(self, occupations: List[Dict], output_file: str):
        """
        職業データをCSVにエクスポート

        Args:
            occupations: 職業データリスト
            output_file: 出力CSVファイルパス
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not occupations:
                return

            fieldnames = ['isco_code', 'title', 'description', 'major_group', 'major_group_name']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for occ in occupations:
                writer.writerow({
                    'isco_code': occ.get('isco_code', ''),
                    'title': occ.get('title', ''),
                    'description': occ.get('description', ''),
                    'major_group': occ.get('major_group', ''),
                    'major_group_name': occ.get('major_group_name', ''),
                })

        print(f"CSVにエクスポートしました: {output_path}")


def main():
    """動作確認用のメイン関数"""
    collector = IscoCollector()

    print("\n=== ISCO-08 データ収集テスト ===\n")

    # サンプルデータの生成
    print("1. サンプルデータの生成")
    occupations = collector.generate_sample_data()
    print(f"   生成件数: {len(occupations)}件\n")

    # 大分類の表示
    print("2. ISCO-08 大分類:")
    major_groups = collector.get_all_major_groups()
    for code, name in major_groups.items():
        print(f"   {code}: {name}")

    # サンプル職業の表示
    print("\n3. サンプル職業データ:")
    for i, occ in enumerate(occupations[:5], 1):
        print(f"\n   {i}. {occ['title']}")
        print(f"      コード: {occ['isco_code']}")
        print(f"      大分類: {occ['major_group_name']}")
        print(f"      説明: {occ['description'][:80]}...")

    # CSVエクスポート
    output_file = "data/isco/sample_occupations.csv"
    print(f"\n4. CSVエクスポート: {output_file}")
    collector.export_to_csv(occupations, output_file)


if __name__ == "__main__":
    main()
