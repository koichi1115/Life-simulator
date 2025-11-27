"""
職業データの重複排除ユーティリティ
異なるデータソースから取得した職業の重複を検出・統合
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from fuzzywuzzy import fuzz
from Levenshtein import distance as levenshtein_distance


@dataclass
class DuplicateMatch:
    """重複マッチの結果"""
    occupation_1: Dict
    occupation_2: Dict
    similarity_score: float
    match_method: str  # 'exact', 'fuzzy', 'code'


class OccupationDeduplicator:
    """
    職業データの重複排除クラス

    複数のデータソースから取得した職業データの重複を検出し、
    統合された職業リストを生成します。
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        exact_match_threshold: float = 0.95
    ):
        """
        Args:
            similarity_threshold: 重複と判定する類似度の閾値（0.0～1.0）
            exact_match_threshold: 完全一致と判定する類似度の閾値
        """
        self.similarity_threshold = similarity_threshold
        self.exact_match_threshold = exact_match_threshold

    def normalize_string(self, text: str) -> str:
        """
        文字列を正規化（小文字化、トリム、特殊文字除去）

        Args:
            text: 正規化する文字列

        Returns:
            正規化された文字列
        """
        if not text:
            return ""

        # 小文字化
        text = text.lower()

        # 前後の空白を削除
        text = text.strip()

        # 複数の空白を1つに
        import re
        text = re.sub(r'\s+', ' ', text)

        return text

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        2つの文字列の類似度を計算

        複数の類似度指標の平均を使用:
        - Levenshtein距離ベースの類似度
        - トークンソート比
        - トークンセット比

        Args:
            text1: 文字列1
            text2: 文字列2

        Returns:
            類似度スコア（0.0～1.0）
        """
        if not text1 or not text2:
            return 0.0

        # 正規化
        text1_norm = self.normalize_string(text1)
        text2_norm = self.normalize_string(text2)

        # 完全一致
        if text1_norm == text2_norm:
            return 1.0

        # Levenshtein距離ベースの類似度
        max_len = max(len(text1_norm), len(text2_norm))
        if max_len == 0:
            return 0.0

        lev_dist = levenshtein_distance(text1_norm, text2_norm)
        lev_similarity = 1.0 - (lev_dist / max_len)

        # FuzzyWuzzyの類似度指標
        token_sort_ratio = fuzz.token_sort_ratio(text1_norm, text2_norm) / 100.0
        token_set_ratio = fuzz.token_set_ratio(text1_norm, text2_norm) / 100.0

        # 平均スコア
        avg_similarity = (lev_similarity + token_sort_ratio + token_set_ratio) / 3.0

        return avg_similarity

    def are_occupations_duplicate(
        self,
        occ1: Dict,
        occ2: Dict
    ) -> Tuple[bool, float, str]:
        """
        2つの職業が重複しているか判定

        判定基準:
        1. コードによる一致（ISCO、O*NET等）
        2. 職業名の高い類似度

        Args:
            occ1: 職業データ1
            occ2: 職業データ2

        Returns:
            (重複判定, 類似度スコア, マッチ方法)
        """
        # コードによる完全一致チェック
        codes_to_check = [
            ('isco_code', 'isco_code'),
            ('onet_code', 'onet_code'),
            ('occupation_code_isco', 'occupation_code_isco'),
            ('occupation_code_onet', 'occupation_code_onet'),
        ]

        for code1_key, code2_key in codes_to_check:
            code1 = occ1.get(code1_key)
            code2 = occ2.get(code2_key)

            if code1 and code2 and code1 == code2:
                return True, 1.0, 'code'

        # 職業名による類似度チェック
        name1 = occ1.get('title') or occ1.get('occupation_name') or ""
        name2 = occ2.get('title') or occ2.get('occupation_name') or ""

        if not name1 or not name2:
            return False, 0.0, 'none'

        similarity = self.calculate_similarity(name1, name2)

        if similarity >= self.exact_match_threshold:
            return True, similarity, 'exact'
        elif similarity >= self.similarity_threshold:
            return True, similarity, 'fuzzy'
        else:
            return False, similarity, 'none'

    def find_duplicates(
        self,
        occupations: List[Dict]
    ) -> List[List[int]]:
        """
        職業リストから重複グループを検出

        Args:
            occupations: 職業データのリスト

        Returns:
            重複グループのリスト（各グループは職業のインデックスリスト）
        """
        n = len(occupations)
        duplicate_groups = []
        processed = set()

        for i in range(n):
            if i in processed:
                continue

            current_group = [i]

            for j in range(i + 1, n):
                if j in processed:
                    continue

                is_dup, score, method = self.are_occupations_duplicate(
                    occupations[i],
                    occupations[j]
                )

                if is_dup:
                    current_group.append(j)
                    processed.add(j)

            if len(current_group) > 1:
                duplicate_groups.append(current_group)
                processed.add(i)

        return duplicate_groups

    def merge_occupations(
        self,
        occupations: List[Dict],
        strategy: str = 'comprehensive'
    ) -> Dict:
        """
        複数の職業データを1つに統合

        統合戦略:
        - 'comprehensive': 全ての情報を統合（デフォルト）
        - 'first': 最初のエントリを優先
        - 'longest': 最も詳細な情報を優先

        Args:
            occupations: 統合する職業データのリスト
            strategy: 統合戦略

        Returns:
            統合された職業データ
        """
        if not occupations:
            return {}

        if len(occupations) == 1:
            return occupations[0]

        if strategy == 'first':
            return occupations[0]

        # 'comprehensive'または'longest'戦略
        merged = {}

        # 全てのキーを収集
        all_keys = set()
        for occ in occupations:
            all_keys.update(occ.keys())

        # 各キーについて、最も詳細な値を選択
        for key in all_keys:
            values = [occ.get(key) for occ in occupations if occ.get(key)]

            if not values:
                continue

            # 文字列の場合は最長のものを選択
            if isinstance(values[0], str):
                merged[key] = max(values, key=len)
            # リストの場合はマージ
            elif isinstance(values[0], list):
                merged_list = []
                for v in values:
                    if isinstance(v, list):
                        merged_list.extend(v)
                merged[key] = list(set(merged_list))  # 重複削除
            # その他の場合は最初の値
            else:
                merged[key] = values[0]

        # データソース情報を追加
        merged['merged_from_sources'] = len(occupations)

        return merged

    def deduplicate(
        self,
        occupations: List[Dict],
        merge_strategy: str = 'comprehensive'
    ) -> List[Dict]:
        """
        職業リストの重複を排除

        Args:
            occupations: 職業データのリスト
            merge_strategy: 統合戦略

        Returns:
            重複排除された職業リスト
        """
        if not occupations:
            return []

        print(f"重複排除を開始: {len(occupations)}件の職業")

        # 重複グループを検出
        duplicate_groups = self.find_duplicates(occupations)

        print(f"  検出された重複グループ: {len(duplicate_groups)}個")

        # 重複グループに含まれないインデックスを取得
        all_duplicates = set()
        for group in duplicate_groups:
            all_duplicates.update(group)

        unique_indices = [
            i for i in range(len(occupations))
            if i not in all_duplicates
        ]

        # 重複排除されたリストを作成
        deduplicated = []

        # ユニークな職業を追加
        for i in unique_indices:
            deduplicated.append(occupations[i])

        # 重複グループをマージして追加
        for group in duplicate_groups:
            group_occupations = [occupations[i] for i in group]
            merged = self.merge_occupations(group_occupations, merge_strategy)
            deduplicated.append(merged)

        print(f"重複排除完了: {len(deduplicated)}件の職業（{len(occupations) - len(deduplicated)}件削減）")

        return deduplicated

    def generate_deduplication_report(
        self,
        occupations: List[Dict]
    ) -> Dict:
        """
        重複排除レポートを生成

        Args:
            occupations: 職業データのリスト

        Returns:
            レポートデータ
        """
        duplicate_groups = self.find_duplicates(occupations)

        report = {
            "total_occupations": len(occupations),
            "duplicate_groups": len(duplicate_groups),
            "total_duplicates": sum(len(group) for group in duplicate_groups),
            "unique_occupations": len(occupations) - sum(len(group) - 1 for group in duplicate_groups),
            "duplicate_details": []
        }

        for group in duplicate_groups:
            group_detail = {
                "group_size": len(group),
                "occupations": []
            }

            for idx in group:
                occ = occupations[idx]
                name = occ.get('title') or occ.get('occupation_name', 'Unknown')
                codes = {
                    'isco': occ.get('isco_code') or occ.get('occupation_code_isco'),
                    'onet': occ.get('onet_code') or occ.get('occupation_code_onet'),
                }

                group_detail["occupations"].append({
                    "index": idx,
                    "name": name,
                    "codes": codes
                })

            report["duplicate_details"].append(group_detail)

        return report


def main():
    """動作確認用のメイン関数"""
    print("\n=== 重複排除ユーティリティ テスト ===\n")

    # テストデータ
    test_occupations = [
        {"title": "Software Developer", "isco_code": "2512"},
        {"title": "Software Engineer", "onet_code": "15-1252.00"},  # 類似
        {"title": "software developer", "isco_code": "2512"},  # 重複
        {"title": "Web Developer", "isco_code": "2513"},
        {"title": "Nurse", "isco_code": "2221"},
        {"title": "Registered Nurse", "onet_code": "29-1141.00"},  # 類似
        {"title": "Teacher", "isco_code": "2310"},
    ]

    deduplicator = OccupationDeduplicator(similarity_threshold=0.80)

    # 重複排除
    deduplicated = deduplicator.deduplicate(test_occupations)

    print("\n重複排除後の職業:")
    for i, occ in enumerate(deduplicated, 1):
        print(f"{i}. {occ.get('title', 'Unknown')}")
        if 'merged_from_sources' in occ:
            print(f"   （{occ['merged_from_sources']}個のソースから統合）")

    # レポート生成
    print("\n\n重複排除レポート:")
    report = deduplicator.generate_deduplication_report(test_occupations)
    print(f"  総職業数: {report['total_occupations']}")
    print(f"  重複グループ数: {report['duplicate_groups']}")
    print(f"  ユニークな職業: {report['unique_occupations']}")


if __name__ == "__main__":
    main()
