-- Life Simulator Database Schema
-- 職業データベースのスキーマ定義

-- Extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================
-- 職業マスターテーブル
-- ===========================
CREATE TABLE occupations (
    occupation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    occupation_name VARCHAR(255) NOT NULL,
    occupation_code_isco VARCHAR(10),      -- ISCO-08コード
    occupation_code_onet VARCHAR(10),      -- O*NETコード
    occupation_code_local VARCHAR(20),     -- 各国の職業分類コード
    category_major VARCHAR(100),           -- 大分類
    category_minor VARCHAR(100),           -- 中分類
    description TEXT,                      -- 職業の説明
    is_future_occupation BOOLEAN DEFAULT FALSE,  -- 将来職業フラグ
    estimated_emergence_year INT,          -- 誕生予測年
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    CONSTRAINT unique_occupation_name UNIQUE(occupation_name)
);

CREATE INDEX idx_occupations_isco ON occupations(occupation_code_isco);
CREATE INDEX idx_occupations_onet ON occupations(occupation_code_onet);
CREATE INDEX idx_occupations_category_major ON occupations(category_major);
CREATE INDEX idx_occupations_future ON occupations(is_future_occupation);

-- ===========================
-- 多言語対応テーブル
-- ===========================
CREATE TABLE occupation_translations (
    translation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    occupation_id UUID NOT NULL REFERENCES occupations(occupation_id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL,     -- ja, en, zh, es等（ISO 639-1）
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_occupation_language UNIQUE(occupation_id, language_code)
);

CREATE INDEX idx_translations_occupation ON occupation_translations(occupation_id);
CREATE INDEX idx_translations_language ON occupation_translations(language_code);

-- ===========================
-- 統計データテーブル
-- ===========================
CREATE TABLE occupation_statistics (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    occupation_id UUID NOT NULL REFERENCES occupations(occupation_id) ON DELETE CASCADE,
    country_code VARCHAR(3) NOT NULL,      -- ISO 3166-1 alpha-3
    year INT NOT NULL,
    employed_count BIGINT,                 -- 従事者数
    avg_salary_usd DECIMAL(12, 2),         -- 平均年収（USD換算）
    avg_salary_local DECIMAL(12, 2),       -- 平均年収（現地通貨）
    currency_code VARCHAR(3),              -- ISO 4217
    data_source VARCHAR(255) NOT NULL,     -- データソース名
    source_url TEXT,                       -- データソースURL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_occupation_country_year UNIQUE(occupation_id, country_code, year),
    CONSTRAINT check_year CHECK (year >= 1900 AND year <= 2100),
    CONSTRAINT check_employed_count CHECK (employed_count >= 0),
    CONSTRAINT check_salary_usd CHECK (avg_salary_usd >= 0),
    CONSTRAINT check_salary_local CHECK (avg_salary_local >= 0)
);

CREATE INDEX idx_statistics_occupation ON occupation_statistics(occupation_id);
CREATE INDEX idx_statistics_country ON occupation_statistics(country_code);
CREATE INDEX idx_statistics_year ON occupation_statistics(year);

-- ===========================
-- 教育要件テーブル
-- ===========================
CREATE TABLE education_requirements (
    requirement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    occupation_id UUID NOT NULL REFERENCES occupations(occupation_id) ON DELETE CASCADE,
    country_code VARCHAR(3),               -- 国別要件（NULL=グローバル共通）
    education_level VARCHAR(50),           -- 高卒、大卒、修士、博士等
    required_certifications TEXT[],        -- 必要な資格（配列）
    required_skills TEXT[],                -- 必要なスキル（配列）
    typical_career_path TEXT,              -- 典型的なキャリアパス
    years_of_experience_required INT,      -- 必要な経験年数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_occupation_country_education UNIQUE(occupation_id, country_code),
    CONSTRAINT check_experience_years CHECK (years_of_experience_required >= 0)
);

CREATE INDEX idx_education_occupation ON education_requirements(occupation_id);
CREATE INDEX idx_education_country ON education_requirements(country_code);
CREATE INDEX idx_education_level ON education_requirements(education_level);

-- ===========================
-- データソーステーブル
-- ===========================
CREATE TABLE data_sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,      -- api, web_scraping, manual, etc.
    source_url TEXT,
    reliability_level VARCHAR(20),         -- highest, high, medium, low
    last_updated TIMESTAMP,
    update_frequency VARCHAR(50),          -- daily, weekly, monthly, quarterly, yearly
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_source_name UNIQUE(source_name),
    CONSTRAINT check_reliability CHECK (reliability_level IN ('highest', 'high', 'medium', 'low'))
);

-- ===========================
-- 職業関連性テーブル（関連職業のマッピング）
-- ===========================
CREATE TABLE occupation_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    occupation_id_from UUID NOT NULL REFERENCES occupations(occupation_id) ON DELETE CASCADE,
    occupation_id_to UUID NOT NULL REFERENCES occupations(occupation_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,  -- similar, prerequisite, career_progression, etc.
    similarity_score DECIMAL(3, 2),          -- 0.00 - 1.00
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_occupation_relationship UNIQUE(occupation_id_from, occupation_id_to, relationship_type),
    CONSTRAINT check_different_occupations CHECK (occupation_id_from != occupation_id_to),
    CONSTRAINT check_similarity_score CHECK (similarity_score >= 0 AND similarity_score <= 1)
);

CREATE INDEX idx_relationships_from ON occupation_relationships(occupation_id_from);
CREATE INDEX idx_relationships_to ON occupation_relationships(occupation_id_to);
CREATE INDEX idx_relationships_type ON occupation_relationships(relationship_type);

-- ===========================
-- データ収集履歴テーブル
-- ===========================
CREATE TABLE collection_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES data_sources(source_id),
    collection_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    collection_type VARCHAR(50) NOT NULL,  -- full, incremental, manual
    records_collected INT,
    records_updated INT,
    records_failed INT,
    status VARCHAR(20) NOT NULL,           -- success, partial, failed
    error_message TEXT,
    execution_time_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_history_source ON collection_history(source_id);
CREATE INDEX idx_history_date ON collection_history(collection_date);
CREATE INDEX idx_history_status ON collection_history(status);

-- ===========================
-- 更新日時自動更新のトリガー関数
-- ===========================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- トリガーの適用
CREATE TRIGGER update_occupations_updated_at BEFORE UPDATE ON occupations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_translations_updated_at BEFORE UPDATE ON occupation_translations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_statistics_updated_at BEFORE UPDATE ON occupation_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_education_updated_at BEFORE UPDATE ON education_requirements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===========================
-- ビュー: 職業の完全情報
-- ===========================
CREATE VIEW occupation_full_info AS
SELECT
    o.occupation_id,
    o.occupation_name,
    o.occupation_code_isco,
    o.occupation_code_onet,
    o.category_major,
    o.category_minor,
    o.description,
    o.is_future_occupation,
    o.estimated_emergence_year,
    COALESCE(
        jsonb_agg(
            DISTINCT jsonb_build_object(
                'language', ot.language_code,
                'name', ot.name,
                'description', ot.description
            )
        ) FILTER (WHERE ot.translation_id IS NOT NULL),
        '[]'::jsonb
    ) as translations,
    COALESCE(
        jsonb_agg(
            DISTINCT jsonb_build_object(
                'country', os.country_code,
                'year', os.year,
                'employed_count', os.employed_count,
                'avg_salary_usd', os.avg_salary_usd
            )
        ) FILTER (WHERE os.stat_id IS NOT NULL),
        '[]'::jsonb
    ) as statistics,
    COALESCE(
        jsonb_agg(
            DISTINCT jsonb_build_object(
                'country', er.country_code,
                'education_level', er.education_level,
                'certifications', er.required_certifications,
                'skills', er.required_skills
            )
        ) FILTER (WHERE er.requirement_id IS NOT NULL),
        '[]'::jsonb
    ) as education_requirements
FROM occupations o
LEFT JOIN occupation_translations ot ON o.occupation_id = ot.occupation_id
LEFT JOIN occupation_statistics os ON o.occupation_id = os.occupation_id
LEFT JOIN education_requirements er ON o.occupation_id = er.occupation_id
GROUP BY o.occupation_id;

-- ===========================
-- サンプルデータ（開発用）
-- ===========================
-- データソースの例
INSERT INTO data_sources (source_name, source_type, source_url, reliability_level, update_frequency) VALUES
('ILO ISCO-08', 'manual', 'https://www.ilo.org/public/english/bureau/stat/isco/', 'highest', 'yearly'),
('O*NET Online', 'api', 'https://services.onetcenter.org/', 'highest', 'quarterly'),
('US Bureau of Labor Statistics', 'api', 'https://www.bls.gov/', 'highest', 'monthly'),
('日本標準職業分類', 'manual', 'https://www.stat.go.jp/index/seido/shokgyou/', 'highest', 'yearly');

-- ===========================
-- コメント
-- ===========================
COMMENT ON TABLE occupations IS '職業マスターテーブル - 全ての職業の基本情報を格納';
COMMENT ON TABLE occupation_translations IS '職業の多言語翻訳情報';
COMMENT ON TABLE occupation_statistics IS '職業の統計データ（従事者数、給与等）';
COMMENT ON TABLE education_requirements IS '職業に必要な教育・資格要件';
COMMENT ON TABLE data_sources IS 'データ収集元の情報';
COMMENT ON TABLE occupation_relationships IS '職業間の関連性（類似職業、キャリアパス等）';
COMMENT ON TABLE collection_history IS 'データ収集の履歴とログ';
