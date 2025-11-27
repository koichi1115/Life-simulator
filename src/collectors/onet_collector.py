"""
O*NET データコレクター
O*NET Web Servicesを使用して職業データを収集
"""
import os
import time
from typing import Dict, List, Optional
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth


class OnetCollector:
    """
    O*NET API クライアント

    O*NET Web Servicesから職業データを取得するためのコレクター
    APIキーが必要（https://services.onetcenter.org/で取得）
    """

    BASE_URL = "https://services.onetcenter.org/ws"

    def __init__(self, username: str = None, password: str = None):
        """
        Args:
            username: O*NET APIユーザー名（環境変数 ONET_USERNAME から取得可能）
            password: O*NET APIパスワード（環境変数 ONET_PASSWORD から取得可能）
        """
        self.username = username or os.getenv("ONET_USERNAME")
        self.password = password or os.getenv("ONET_PASSWORD")

        if not self.username or not self.password:
            print("警告: O*NET APIの認証情報が設定されていません")
            print("環境変数 ONET_USERNAME と ONET_PASSWORD を設定するか、")
            print("https://services.onetcenter.org/ でアカウントを作成してください")

        self.session = requests.Session()
        if self.username and self.password:
            self.session.auth = HTTPBasicAuth(self.username, self.password)

        self.rate_limit_delay = 1  # 秒単位のレート制限

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        APIリクエストを実行

        Args:
            endpoint: APIエンドポイント（例: "/online/occupations"）
            params: クエリパラメータ

        Returns:
            APIレスポンス（JSON）
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()

            # レート制限に配慮
            time.sleep(self.rate_limit_delay)

            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("O*NET API認証エラー: ユーザー名とパスワードを確認してください")
            elif e.response.status_code == 429:
                raise Exception("O*NET APIレート制限超過: しばらく待ってから再試行してください")
            else:
                raise Exception(f"O*NET APIエラー: {e}")
        except Exception as e:
            raise Exception(f"O*NET APIリクエスト失敗: {e}")

    def get_all_occupations(self) -> List[Dict]:
        """
        全職業のリストを取得

        Returns:
            職業情報のリスト
        """
        print("O*NET: 職業リストを取得中...")

        occupations = []
        start = 1
        end = 20  # 最初のバッチ

        while True:
            response = self._make_request(
                "/online/occupations",
                params={"start": start, "end": end}
            )

            if "occupation" not in response:
                break

            batch = response["occupation"]
            occupations.extend(batch)

            print(f"  取得済み: {len(occupations)}件")

            # 次のバッチ
            if len(batch) < (end - start + 1):
                break

            start = end + 1
            end = start + 19

        print(f"O*NET: 合計 {len(occupations)}件の職業を取得")
        return occupations

    def get_occupation_details(self, onet_code: str) -> Dict:
        """
        特定の職業の詳細情報を取得

        Args:
            onet_code: O*NETコード（例: "15-1252.00"）

        Returns:
            職業の詳細情報
        """
        endpoint = f"/online/occupations/{onet_code}"
        return self._make_request(endpoint)

    def get_occupation_skills(self, onet_code: str) -> List[Dict]:
        """
        職業に必要なスキル情報を取得

        Args:
            onet_code: O*NETコード

        Returns:
            スキル情報のリスト
        """
        endpoint = f"/online/occupations/{onet_code}/summary/skills"
        response = self._make_request(endpoint)
        return response.get("skill", [])

    def get_occupation_knowledge(self, onet_code: str) -> List[Dict]:
        """
        職業に必要な知識情報を取得

        Args:
            onet_code: O*NETコード

        Returns:
            知識情報のリスト
        """
        endpoint = f"/online/occupations/{onet_code}/summary/knowledge"
        response = self._make_request(endpoint)
        return response.get("knowledge", [])

    def get_occupation_education(self, onet_code: str) -> Dict:
        """
        職業に必要な教育・訓練情報を取得

        Args:
            onet_code: O*NETコード

        Returns:
            教育情報
        """
        endpoint = f"/online/occupations/{onet_code}/summary/education_training"
        return self._make_request(endpoint)

    def collect_comprehensive_data(
        self,
        limit: Optional[int] = None,
        include_details: bool = True
    ) -> List[Dict]:
        """
        包括的な職業データを収集

        Args:
            limit: 取得する職業数の上限（Noneの場合は全件）
            include_details: 詳細情報も取得するか

        Returns:
            包括的な職業データのリスト
        """
        occupations = self.get_all_occupations()

        if limit:
            occupations = occupations[:limit]

        comprehensive_data = []

        for i, occ in enumerate(occupations, 1):
            onet_code = occ.get("code")
            title = occ.get("title")

            print(f"[{i}/{len(occupations)}] 処理中: {title} ({onet_code})")

            data = {
                "onet_code": onet_code,
                "title": title,
                "description": occ.get("description", ""),
                "tags": occ.get("tags", {})
            }

            if include_details and onet_code:
                try:
                    # 詳細情報
                    details = self.get_occupation_details(onet_code)
                    data["details"] = details

                    # スキル
                    skills = self.get_occupation_skills(onet_code)
                    data["skills"] = skills

                    # 知識
                    knowledge = self.get_occupation_knowledge(onet_code)
                    data["knowledge"] = knowledge

                    # 教育
                    education = self.get_occupation_education(onet_code)
                    data["education"] = education

                except Exception as e:
                    print(f"  警告: {onet_code} の詳細取得に失敗: {e}")

            comprehensive_data.append(data)

        return comprehensive_data

    def search_occupations(self, keyword: str) -> List[Dict]:
        """
        キーワードで職業を検索

        Args:
            keyword: 検索キーワード

        Returns:
            検索結果の職業リスト
        """
        response = self._make_request(
            "/online/search",
            params={"keyword": keyword}
        )
        return response.get("occupation", [])


def main():
    """動作確認用のメイン関数"""
    collector = OnetCollector()

    # 職業リストの取得テスト
    print("\n=== O*NET 職業データ収集テスト ===\n")

    try:
        # 最初の10件のみ取得してテスト
        data = collector.collect_comprehensive_data(limit=10, include_details=False)

        print(f"\n収集完了: {len(data)}件")
        print("\n最初の3件:")
        for i, occ in enumerate(data[:3], 1):
            print(f"\n{i}. {occ['title']}")
            print(f"   コード: {occ['onet_code']}")
            print(f"   説明: {occ['description'][:100]}...")

    except Exception as e:
        print(f"\nエラー: {e}")
        print("\nO*NET APIを使用するには、以下の環境変数を設定してください:")
        print("  export ONET_USERNAME='your_username'")
        print("  export ONET_PASSWORD='your_password'")


if __name__ == "__main__":
    main()
