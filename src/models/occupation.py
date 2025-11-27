"""
職業データモデル
SQLAlchemy ORMモデルの定義
"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    ARRAY, Boolean, CheckConstraint, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Occupation(Base):
    """職業マスターテーブル"""
    __tablename__ = 'occupations'

    occupation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    occupation_name = Column(String(255), nullable=False, unique=True)
    occupation_code_isco = Column(String(10))
    occupation_code_onet = Column(String(10))
    occupation_code_local = Column(String(20))
    category_major = Column(String(100))
    category_minor = Column(String(100))
    description = Column(Text)
    is_future_occupation = Column(Boolean, default=False)
    estimated_emergence_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    translations = relationship(
        "OccupationTranslation",
        back_populates="occupation",
        cascade="all, delete-orphan"
    )
    statistics = relationship(
        "OccupationStatistic",
        back_populates="occupation",
        cascade="all, delete-orphan"
    )
    education_requirements = relationship(
        "EducationRequirement",
        back_populates="occupation",
        cascade="all, delete-orphan"
    )
    relationships_from = relationship(
        "OccupationRelationship",
        foreign_keys="OccupationRelationship.occupation_id_from",
        back_populates="occupation_from",
        cascade="all, delete-orphan"
    )
    relationships_to = relationship(
        "OccupationRelationship",
        foreign_keys="OccupationRelationship.occupation_id_to",
        back_populates="occupation_to",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Occupation(id={self.occupation_id}, name='{self.occupation_name}')>"


class OccupationTranslation(Base):
    """職業の多言語翻訳情報"""
    __tablename__ = 'occupation_translations'

    translation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    occupation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('occupations.occupation_id', ondelete='CASCADE'),
        nullable=False
    )
    language_code = Column(String(5), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    occupation = relationship("Occupation", back_populates="translations")

    __table_args__ = (
        UniqueConstraint('occupation_id', 'language_code', name='unique_occupation_language'),
    )

    def __repr__(self):
        return f"<OccupationTranslation(occupation_id={self.occupation_id}, lang='{self.language_code}')>"


class OccupationStatistic(Base):
    """職業の統計データ"""
    __tablename__ = 'occupation_statistics'

    stat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    occupation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('occupations.occupation_id', ondelete='CASCADE'),
        nullable=False
    )
    country_code = Column(String(3), nullable=False)
    year = Column(Integer, nullable=False)
    employed_count = Column(Integer)
    avg_salary_usd = Column(Numeric(12, 2))
    avg_salary_local = Column(Numeric(12, 2))
    currency_code = Column(String(3))
    data_source = Column(String(255), nullable=False)
    source_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    occupation = relationship("Occupation", back_populates="statistics")

    __table_args__ = (
        UniqueConstraint('occupation_id', 'country_code', 'year', name='unique_occupation_country_year'),
        CheckConstraint('year >= 1900 AND year <= 2100', name='check_year'),
        CheckConstraint('employed_count >= 0', name='check_employed_count'),
        CheckConstraint('avg_salary_usd >= 0', name='check_salary_usd'),
        CheckConstraint('avg_salary_local >= 0', name='check_salary_local'),
    )

    def __repr__(self):
        return f"<OccupationStatistic(occupation_id={self.occupation_id}, country='{self.country_code}', year={self.year})>"


class EducationRequirement(Base):
    """教育要件テーブル"""
    __tablename__ = 'education_requirements'

    requirement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    occupation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('occupations.occupation_id', ondelete='CASCADE'),
        nullable=False
    )
    country_code = Column(String(3))
    education_level = Column(String(50))
    required_certifications = Column(ARRAY(Text))
    required_skills = Column(ARRAY(Text))
    typical_career_path = Column(Text)
    years_of_experience_required = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    occupation = relationship("Occupation", back_populates="education_requirements")

    __table_args__ = (
        UniqueConstraint('occupation_id', 'country_code', name='unique_occupation_country_education'),
        CheckConstraint('years_of_experience_required >= 0', name='check_experience_years'),
    )

    def __repr__(self):
        return f"<EducationRequirement(occupation_id={self.occupation_id}, country='{self.country_code}')>"


class DataSource(Base):
    """データソーステーブル"""
    __tablename__ = 'data_sources'

    source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name = Column(String(255), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)
    source_url = Column(Text)
    reliability_level = Column(String(20))
    last_updated = Column(DateTime)
    update_frequency = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーションシップ
    collection_histories = relationship(
        "CollectionHistory",
        back_populates="data_source",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "reliability_level IN ('highest', 'high', 'medium', 'low')",
            name='check_reliability'
        ),
    )

    def __repr__(self):
        return f"<DataSource(name='{self.source_name}', type='{self.source_type}')>"


class OccupationRelationship(Base):
    """職業関連性テーブル"""
    __tablename__ = 'occupation_relationships'

    relationship_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    occupation_id_from = Column(
        UUID(as_uuid=True),
        ForeignKey('occupations.occupation_id', ondelete='CASCADE'),
        nullable=False
    )
    occupation_id_to = Column(
        UUID(as_uuid=True),
        ForeignKey('occupations.occupation_id', ondelete='CASCADE'),
        nullable=False
    )
    relationship_type = Column(String(50), nullable=False)
    similarity_score = Column(Numeric(3, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーションシップ
    occupation_from = relationship(
        "Occupation",
        foreign_keys=[occupation_id_from],
        back_populates="relationships_from"
    )
    occupation_to = relationship(
        "Occupation",
        foreign_keys=[occupation_id_to],
        back_populates="relationships_to"
    )

    __table_args__ = (
        UniqueConstraint(
            'occupation_id_from',
            'occupation_id_to',
            'relationship_type',
            name='unique_occupation_relationship'
        ),
        CheckConstraint(
            'occupation_id_from != occupation_id_to',
            name='check_different_occupations'
        ),
        CheckConstraint(
            'similarity_score >= 0 AND similarity_score <= 1',
            name='check_similarity_score'
        ),
    )

    def __repr__(self):
        return f"<OccupationRelationship(from={self.occupation_id_from}, to={self.occupation_id_to}, type='{self.relationship_type}')>"


class CollectionHistory(Base):
    """データ収集履歴テーブル"""
    __tablename__ = 'collection_history'

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey('data_sources.source_id'),
        nullable=True
    )
    collection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    collection_type = Column(String(50), nullable=False)
    records_collected = Column(Integer)
    records_updated = Column(Integer)
    records_failed = Column(Integer)
    status = Column(String(20), nullable=False)
    error_message = Column(Text)
    execution_time_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーションシップ
    data_source = relationship("DataSource", back_populates="collection_histories")

    def __repr__(self):
        return f"<CollectionHistory(date={self.collection_date}, status='{self.status}')>"
