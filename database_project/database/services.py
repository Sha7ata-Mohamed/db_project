"""
Data handler service for managing all database operations and search logic.
This service provides a clean interface for handling research data, researchers,
keywords, and complex searches.
"""

from django.db import connection
from typing import List, Dict, Any, Optional
import re


def dictfetchall(cursor) -> List[Dict[str, Any]]:
    """Convert database cursor results to list of dictionaries."""
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


class ResearchDataHandler:
    """Handles all research data operations."""

    # NOTE:
    # - journals table has journal_name column
    # - conferences id column is `ï»¿Conference ID` (BOM) so we use backticks
    # - ONLY_FULL_GROUP_BY is ON, so we aggregate non-grouped fields using MAX()
    RESEARCH_FULL_SELECT = """
        SELECT
            rd.research_id,

            MAX(rd.title) AS title,
            MAX(rd.publication_date) AS publication_date,
            MAX(rd.research_type) AS research_type,

            MAX(rd.journal_id) AS journal_id,
            MAX(j.journal_name) AS journal_name,

            MAX(rd.conference_id) AS conference_id,
            MAX(c.`Conference Name`) AS conference_name,

            GROUP_CONCAT(DISTINCT k.keyword ORDER BY k.keyword SEPARATOR ', ') AS keywords,
            GROUP_CONCAT(
                DISTINCT CONCAT(r.researcher_id, ' - ', r.name)
                ORDER BY r.researcher_id SEPARATOR ' | '
            ) AS researchers
        FROM research_data rd
        LEFT JOIN journals j ON j.journal_id = rd.journal_id
        LEFT JOIN conferences c ON c.`ï»¿Conference ID` = rd.conference_id
        LEFT JOIN research_keywords rk ON rk.research_id = rd.research_id
        LEFT JOIN keywords k ON k.keyword_id = rk.keyword_id
        LEFT JOIN research_researchers rr ON rr.research_id = rd.research_id
        LEFT JOIN researcher_data r ON r.researcher_id = rr.researcher_id
    """

    @staticmethod
    def get_by_id(research_id: str) -> Optional[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                ResearchDataHandler.RESEARCH_FULL_SELECT
                + """
                WHERE rd.research_id = %s
                GROUP BY rd.research_id
                """,
                [research_id.upper()],
            )
            rows = dictfetchall(cursor)
            return rows[0] if rows else None

    @staticmethod
    def get_by_ids(research_ids: List[str], limit: int = 200) -> List[Dict[str, Any]]:
        if not research_ids:
            return []

        placeholders = ", ".join(["%s"] * len(research_ids))
        with connection.cursor() as cursor:
            cursor.execute(
                ResearchDataHandler.RESEARCH_FULL_SELECT
                + f"""
                WHERE rd.research_id IN ({placeholders})
                GROUP BY rd.research_id
                ORDER BY MAX(rd.publication_date) DESC
                LIMIT %s
                """,
                research_ids + [limit],
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_by_keyword_ids(
        keyword_ids: List[int], limit: int = 200
    ) -> List[Dict[str, Any]]:
        if not keyword_ids:
            return []

        placeholders = ", ".join(["%s"] * len(keyword_ids))
        with connection.cursor() as cursor:
            cursor.execute(
                ResearchDataHandler.RESEARCH_FULL_SELECT
                + f"""
                WHERE rk.keyword_id IN ({placeholders})
                GROUP BY rd.research_id
                ORDER BY MAX(rd.publication_date) DESC
                LIMIT %s
                """,
                keyword_ids + [limit],
            )
            return dictfetchall(cursor)

    @staticmethod
    def get_by_researcher_id(
        researcher_id: str, limit: int = 200
    ) -> List[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                ResearchDataHandler.RESEARCH_FULL_SELECT
                + """
                WHERE rr.researcher_id = %s
                GROUP BY rd.research_id
                ORDER BY MAX(rd.publication_date) DESC
                LIMIT %s
                """,
                [researcher_id.upper(), limit],
            )
            return dictfetchall(cursor)

    @staticmethod
    def search_by_name_prefix(
        name_prefix: str, limit: int = 200
    ) -> List[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                ResearchDataHandler.RESEARCH_FULL_SELECT
                + """
                WHERE LOWER(r.name) LIKE %s
                GROUP BY rd.research_id
                ORDER BY MAX(rd.publication_date) DESC
                LIMIT %s
                """,
                [f"{name_prefix.lower()}%", limit],
            )
            return dictfetchall(cursor)

    @staticmethod
    def search_by_name(name: str, limit: int = 200) -> List[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                ResearchDataHandler.RESEARCH_FULL_SELECT
                + """
                WHERE LOWER(r.name) LIKE %s
                GROUP BY rd.research_id
                ORDER BY MAX(rd.publication_date) DESC
                LIMIT %s
                """,
                [f"%{name.lower()}%", limit],
            )
            return dictfetchall(cursor)

    @staticmethod
    def search_by_title(title: str, limit: int = 200) -> List[Dict[str, Any]]:
        """Search research by title (full title or any word in title)."""
        with connection.cursor() as cursor:
            cursor.execute(
                ResearchDataHandler.RESEARCH_FULL_SELECT
                + """
                WHERE LOWER(rd.title) LIKE %s
                GROUP BY rd.research_id
                ORDER BY MAX(rd.publication_date) DESC
                LIMIT %s
                """,
                [f"%{title.lower()}%", limit],
            )
            return dictfetchall(cursor)


class ResearcherDataHandler:
    """Handles all researcher data operations."""

    @staticmethod
    def get_by_id(researcher_id: str) -> Optional[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT researcher_id, name, affiliation, country, email, specialty
                FROM researcher_data
                WHERE researcher_id = %s
                """,
                [researcher_id.upper()],
            )
            rows = dictfetchall(cursor)
            return rows[0] if rows else None

    @staticmethod
    def search_by_name_prefix(
        name_prefix: str, limit: int = 200
    ) -> List[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT researcher_id, name, affiliation, country, email, specialty
                FROM researcher_data
                WHERE LOWER(name) LIKE %s
                ORDER BY name
                LIMIT %s
                """,
                [f"{name_prefix.lower()}%", limit],
            )
            return dictfetchall(cursor)

    @staticmethod
    def search_by_name(name: str, limit: int = 200) -> List[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT researcher_id, name, affiliation, country, email, specialty
                FROM researcher_data
                WHERE LOWER(name) LIKE %s
                   OR LOWER(email) LIKE %s
                   OR LOWER(affiliation) LIKE %s
                ORDER BY name
                LIMIT %s
                """,
                [f"%{name.lower()}%"] * 3 + [limit],
            )
            return dictfetchall(cursor)


class KeywordDataHandler:
    """Handles all keyword data operations."""

    @staticmethod
    def search_exact(keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT keyword_id, keyword
                FROM keywords
                WHERE LOWER(keyword) = %s
                ORDER BY keyword
                LIMIT %s
                """,
                [keyword.lower(), limit],
            )
            return dictfetchall(cursor)

    @staticmethod
    def search_contains(keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT keyword_id, keyword
                FROM keywords
                WHERE LOWER(keyword) LIKE %s
                ORDER BY keyword
                LIMIT %s
                """,
                [f"%{keyword.lower()}%", limit],
            )
            return dictfetchall(cursor)


class SearchHandler:
    """
    Main search handler that coordinates different search types and data handlers.
    Priority: Research ID > Researcher ID > Keyword > Name prefix > Name contains.
    """

    RESEARCH_ID_PATTERN = r"P\d{3}"
    RESEARCHER_ID_PATTERN = r"R\d{3}"

    @staticmethod
    def is_research_id(query: str) -> bool:
        return bool(re.fullmatch(SearchHandler.RESEARCH_ID_PATTERN, query.upper()))

    @staticmethod
    def is_researcher_id(query: str) -> bool:
        return bool(re.fullmatch(SearchHandler.RESEARCHER_ID_PATTERN, query.upper()))

    @staticmethod
    def is_single_char(query: str) -> bool:
        return len(query) == 1

    @staticmethod
    def search(query: str) -> Dict[str, Any]:
        result = {
            "q": query,
            "search_type": None,
            "researchers": [],
            "research": [],
            "keywords": [],
        }

        if not query or not query.strip():
            return result

        query = query.strip()

        # 1) Research ID (P###)
        if SearchHandler.is_research_id(query):
            result["search_type"] = "research_id"
            research = ResearchDataHandler.get_by_id(query)
            result["research"] = [research] if research else []
            return result

        # 2) Researcher ID (R###)
        if SearchHandler.is_researcher_id(query):
            result["search_type"] = "researcher_id"
            researcher = ResearcherDataHandler.get_by_id(query)
            result["researchers"] = [researcher] if researcher else []
            result["research"] = ResearchDataHandler.get_by_researcher_id(query)
            return result

        # 3) Keyword - ONLY exact match (full word required)
        # User must type at least a complete keyword
        keywords = KeywordDataHandler.search_exact(query)
        if keywords:
            result["search_type"] = "keyword"
            result["keywords"] = keywords
            keyword_ids = [kw["keyword_id"] for kw in keywords]
            result["research"] = ResearchDataHandler.get_by_keyword_ids(keyword_ids)
            return result

        # 4) Title search - full title or any word in title
        title_research = ResearchDataHandler.search_by_title(query)
        if title_research:
            result["search_type"] = "title"
            result["research"] = title_research
            return result

        # 5) Name search - starts with first character
        # Single char prefix
        if SearchHandler.is_single_char(query):
            result["search_type"] = "first_character"
            result["researchers"] = ResearcherDataHandler.search_by_name_prefix(query)
            result["research"] = ResearchDataHandler.search_by_name_prefix(query)
            return result

        # Multi-char name contains
        result["search_type"] = "name"
        result["researchers"] = ResearcherDataHandler.search_by_name(query)
        result["research"] = ResearchDataHandler.search_by_name(query)
        return result
