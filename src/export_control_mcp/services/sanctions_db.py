"""SQLite-based sanctions database service with FTS5 and fuzzy matching."""

import json
import sqlite3
from datetime import date
from pathlib import Path

from rapidfuzz import fuzz

from export_control_mcp.config import get_settings
from export_control_mcp.models.sanctions import (
    CountrySanctions,
    DeniedPersonEntry,
    EntityListEntry,
    EntityType,
    SanctionsSearchResult,
    SDNEntry,
)

# Valid table names for SQL queries (prevents SQL injection)
_VALID_TABLES = frozenset(["entity_list", "sdn_list", "denied_persons", "country_sanctions", "csl"])


class SanctionsDBService:
    """SQLite database service for sanctions list queries.

    Uses FTS5 for full-text search and rapidfuzz for fuzzy name matching.
    Supports Entity List, SDN List, Denied Persons List, and country sanctions.
    """

    def __init__(self, db_path: str | Path | None = None):
        """Initialize the sanctions database.

        Args:
            db_path: Path to SQLite database file. If None, uses config default.
        """
        settings = get_settings()
        self._db_path = Path(db_path) if db_path else Path(settings.sanctions_db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            # Enable foreign keys
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def _initialize_db(self) -> None:
        """Create database schema if not exists."""
        conn = self._get_connection()

        # Entity List table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_list (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                aliases TEXT DEFAULT '[]',
                addresses TEXT DEFAULT '[]',
                country TEXT NOT NULL,
                license_requirement TEXT DEFAULT '',
                license_policy TEXT DEFAULT '',
                federal_register_citation TEXT DEFAULT '',
                effective_date TEXT,
                standard_order TEXT DEFAULT ''
            )
        """)

        # Entity List FTS5 index
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entity_list_fts USING fts5(
                name,
                aliases,
                content='entity_list',
                content_rowid='rowid'
            )
        """)

        # SDN List table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sdn_list (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sdn_type TEXT NOT NULL,
                programs TEXT DEFAULT '[]',
                aliases TEXT DEFAULT '[]',
                addresses TEXT DEFAULT '[]',
                ids TEXT DEFAULT '[]',
                nationalities TEXT DEFAULT '[]',
                dates_of_birth TEXT DEFAULT '[]',
                places_of_birth TEXT DEFAULT '[]',
                remarks TEXT DEFAULT ''
            )
        """)

        # SDN List FTS5 index
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS sdn_list_fts USING fts5(
                name,
                aliases,
                content='sdn_list',
                content_rowid='rowid'
            )
        """)

        # Denied Persons List table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS denied_persons (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                addresses TEXT DEFAULT '[]',
                effective_date TEXT,
                expiration_date TEXT,
                standard_order TEXT DEFAULT '',
                federal_register_citation TEXT DEFAULT ''
            )
        """)

        # Denied Persons FTS5 index
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS denied_persons_fts USING fts5(
                name,
                content='denied_persons',
                content_rowid='rowid'
            )
        """)

        # Country Sanctions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS country_sanctions (
                country_code TEXT PRIMARY KEY,
                country_name TEXT NOT NULL,
                ofac_programs TEXT DEFAULT '[]',
                embargo_type TEXT DEFAULT 'none',
                ear_country_groups TEXT DEFAULT '[]',
                itar_restricted INTEGER DEFAULT 0,
                arms_embargo INTEGER DEFAULT 0,
                summary TEXT DEFAULT '',
                key_restrictions TEXT DEFAULT '[]',
                notes TEXT DEFAULT '[]'
            )
        """)

        # Consolidated Screening List table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS csl (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entry_type TEXT NOT NULL,
                source_list TEXT NOT NULL,
                programs TEXT DEFAULT '[]',
                aliases TEXT DEFAULT '[]',
                addresses TEXT DEFAULT '[]',
                countries TEXT DEFAULT '[]',
                remarks TEXT DEFAULT ''
            )
        """)

        # CSL FTS5 index
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS csl_fts USING fts5(
                name,
                aliases,
                content='csl',
                content_rowid='rowid'
            )
        """)

        # Create triggers to keep FTS indices in sync
        conn.executescript("""
            CREATE TRIGGER IF NOT EXISTS entity_list_ai AFTER INSERT ON entity_list BEGIN
                INSERT INTO entity_list_fts(rowid, name, aliases)
                VALUES (new.rowid, new.name, new.aliases);
            END;

            CREATE TRIGGER IF NOT EXISTS entity_list_ad AFTER DELETE ON entity_list BEGIN
                INSERT INTO entity_list_fts(entity_list_fts, rowid, name, aliases)
                VALUES('delete', old.rowid, old.name, old.aliases);
            END;

            CREATE TRIGGER IF NOT EXISTS entity_list_au AFTER UPDATE ON entity_list BEGIN
                INSERT INTO entity_list_fts(entity_list_fts, rowid, name, aliases)
                VALUES('delete', old.rowid, old.name, old.aliases);
                INSERT INTO entity_list_fts(rowid, name, aliases)
                VALUES (new.rowid, new.name, new.aliases);
            END;

            CREATE TRIGGER IF NOT EXISTS sdn_list_ai AFTER INSERT ON sdn_list BEGIN
                INSERT INTO sdn_list_fts(rowid, name, aliases)
                VALUES (new.rowid, new.name, new.aliases);
            END;

            CREATE TRIGGER IF NOT EXISTS sdn_list_ad AFTER DELETE ON sdn_list BEGIN
                INSERT INTO sdn_list_fts(sdn_list_fts, rowid, name, aliases)
                VALUES('delete', old.rowid, old.name, old.aliases);
            END;

            CREATE TRIGGER IF NOT EXISTS sdn_list_au AFTER UPDATE ON sdn_list BEGIN
                INSERT INTO sdn_list_fts(sdn_list_fts, rowid, name, aliases)
                VALUES('delete', old.rowid, old.name, old.aliases);
                INSERT INTO sdn_list_fts(rowid, name, aliases)
                VALUES (new.rowid, new.name, new.aliases);
            END;

            CREATE TRIGGER IF NOT EXISTS denied_persons_ai AFTER INSERT ON denied_persons BEGIN
                INSERT INTO denied_persons_fts(rowid, name)
                VALUES (new.rowid, new.name);
            END;

            CREATE TRIGGER IF NOT EXISTS denied_persons_ad AFTER DELETE ON denied_persons BEGIN
                INSERT INTO denied_persons_fts(denied_persons_fts, rowid, name)
                VALUES('delete', old.rowid, old.name);
            END;

            CREATE TRIGGER IF NOT EXISTS denied_persons_au AFTER UPDATE ON denied_persons BEGIN
                INSERT INTO denied_persons_fts(denied_persons_fts, rowid, name)
                VALUES('delete', old.rowid, old.name);
                INSERT INTO denied_persons_fts(rowid, name)
                VALUES (new.rowid, new.name);
            END;

            CREATE TRIGGER IF NOT EXISTS csl_ai AFTER INSERT ON csl BEGIN
                INSERT INTO csl_fts(rowid, name, aliases)
                VALUES (new.rowid, new.name, new.aliases);
            END;

            CREATE TRIGGER IF NOT EXISTS csl_ad AFTER DELETE ON csl BEGIN
                INSERT INTO csl_fts(csl_fts, rowid, name, aliases)
                VALUES('delete', old.rowid, old.name, old.aliases);
            END;

            CREATE TRIGGER IF NOT EXISTS csl_au AFTER UPDATE ON csl BEGIN
                INSERT INTO csl_fts(csl_fts, rowid, name, aliases)
                VALUES('delete', old.rowid, old.name, old.aliases);
                INSERT INTO csl_fts(rowid, name, aliases)
                VALUES (new.rowid, new.name, new.aliases);
            END;
        """)

        conn.commit()

    # --- Entity List Operations ---

    def add_entity_list_entry(self, entry: EntityListEntry) -> None:
        """Add an entry to the Entity List."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO entity_list
            (id, name, aliases, addresses, country, license_requirement,
             license_policy, federal_register_citation, effective_date, standard_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.name,
                json.dumps(entry.aliases),
                json.dumps(entry.addresses),
                entry.country,
                entry.license_requirement,
                entry.license_policy,
                entry.federal_register_citation,
                entry.effective_date.isoformat() if entry.effective_date else None,
                entry.standard_order,
            ),
        )
        conn.commit()

    def search_entity_list(
        self,
        query: str,
        country: str | None = None,
        fuzzy_threshold: float = 0.7,
        limit: int = 20,
    ) -> list[SanctionsSearchResult]:
        """Search the BIS Entity List.

        Args:
            query: Name or partial name to search for
            country: Optional country filter
            fuzzy_threshold: Minimum fuzzy match score (0-1)
            limit: Maximum results to return

        Returns:
            List of search results with match scores
        """
        conn = self._get_connection()
        results = []

        # First try exact FTS5 match
        fts_query = query.replace('"', '""')
        sql = """
            SELECT e.*, entity_list_fts.rank
            FROM entity_list e
            JOIN entity_list_fts ON e.rowid = entity_list_fts.rowid
            WHERE entity_list_fts MATCH ?
        """
        params: list = [f'"{fts_query}"']

        if country:
            sql += " AND e.country = ?"
            params.append(country)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit * 2)  # Get extra for fuzzy filtering

        cursor = conn.execute(sql, params)
        for row in cursor:
            entry = self._row_to_entity_list_entry(row)
            # Calculate actual fuzzy score
            score = fuzz.ratio(query.lower(), entry.name.lower()) / 100.0
            results.append(
                SanctionsSearchResult(
                    entry=entry,
                    match_score=score,
                    match_type="fts_match",
                    matched_field="name",
                    matched_value=entry.name,
                )
            )

        # If not enough results, do fuzzy search on all entries
        if len(results) < limit:
            sql = "SELECT * FROM entity_list"
            params = []
            if country:
                sql += " WHERE country = ?"
                params.append(country)

            cursor = conn.execute(sql, params)
            seen_ids = {r.entry.id for r in results}

            for row in cursor:
                if row["id"] in seen_ids:
                    continue

                entry = self._row_to_entity_list_entry(row)

                # Check name
                name_score = fuzz.ratio(query.lower(), entry.name.lower()) / 100.0
                if name_score >= fuzzy_threshold:
                    results.append(
                        SanctionsSearchResult(
                            entry=entry,
                            match_score=name_score,
                            match_type="fuzzy_name",
                            matched_field="name",
                            matched_value=entry.name,
                        )
                    )
                    continue

                # Check aliases
                for alias in entry.aliases:
                    alias_score = fuzz.ratio(query.lower(), alias.lower()) / 100.0
                    if alias_score >= fuzzy_threshold:
                        results.append(
                            SanctionsSearchResult(
                                entry=entry,
                                match_score=alias_score,
                                match_type="alias",
                                matched_field="alias",
                                matched_value=alias,
                            )
                        )
                        break

        # Sort by score and limit
        results.sort(key=lambda r: r.match_score, reverse=True)
        return results[:limit]

    def _row_to_entity_list_entry(self, row: sqlite3.Row) -> EntityListEntry:
        """Convert database row to EntityListEntry."""
        return EntityListEntry(
            id=row["id"],
            name=row["name"],
            aliases=json.loads(row["aliases"]),
            addresses=json.loads(row["addresses"]),
            country=row["country"],
            license_requirement=row["license_requirement"],
            license_policy=row["license_policy"],
            federal_register_citation=row["federal_register_citation"],
            effective_date=date.fromisoformat(row["effective_date"])
            if row["effective_date"]
            else None,
            standard_order=row["standard_order"],
        )

    # --- SDN List Operations ---

    def add_sdn_entry(self, entry: SDNEntry) -> None:
        """Add an entry to the SDN List."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO sdn_list
            (id, name, sdn_type, programs, aliases, addresses, ids,
             nationalities, dates_of_birth, places_of_birth, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.name,
                entry.sdn_type.value,
                json.dumps(entry.programs),
                json.dumps(entry.aliases),
                json.dumps(entry.addresses),
                json.dumps(entry.ids),
                json.dumps(entry.nationalities),
                json.dumps(entry.dates_of_birth),
                json.dumps(entry.places_of_birth),
                entry.remarks,
            ),
        )
        conn.commit()

    def search_sdn_list(
        self,
        query: str,
        sdn_type: EntityType | None = None,
        program: str | None = None,
        fuzzy_threshold: float = 0.7,
        limit: int = 20,
    ) -> list[SanctionsSearchResult]:
        """Search the OFAC SDN List.

        Args:
            query: Name or partial name to search for
            sdn_type: Optional filter by entity type
            program: Optional filter by sanctions program
            fuzzy_threshold: Minimum fuzzy match score (0-1)
            limit: Maximum results to return

        Returns:
            List of search results with match scores
        """
        conn = self._get_connection()
        results = []

        # First try exact FTS5 match
        fts_query = query.replace('"', '""')
        sql = """
            SELECT s.*, sdn_list_fts.rank
            FROM sdn_list s
            JOIN sdn_list_fts ON s.rowid = sdn_list_fts.rowid
            WHERE sdn_list_fts MATCH ?
        """
        params: list = [f'"{fts_query}"']

        if sdn_type:
            sql += " AND s.sdn_type = ?"
            params.append(sdn_type.value)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit * 2)

        cursor = conn.execute(sql, params)
        for row in cursor:
            entry = self._row_to_sdn_entry(row)
            if program and program not in entry.programs:
                continue
            score = fuzz.ratio(query.lower(), entry.name.lower()) / 100.0
            results.append(
                SanctionsSearchResult(
                    entry=entry,
                    match_score=score,
                    match_type="fts_match",
                    matched_field="name",
                    matched_value=entry.name,
                )
            )

        # Fuzzy search if needed
        if len(results) < limit:
            sql = "SELECT * FROM sdn_list"
            conditions = []
            params = []

            if sdn_type:
                conditions.append("sdn_type = ?")
                params.append(sdn_type.value)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            cursor = conn.execute(sql, params)
            seen_ids = {r.entry.id for r in results}

            for row in cursor:
                if row["id"] in seen_ids:
                    continue

                entry = self._row_to_sdn_entry(row)
                if program and program not in entry.programs:
                    continue

                name_score = fuzz.ratio(query.lower(), entry.name.lower()) / 100.0
                if name_score >= fuzzy_threshold:
                    results.append(
                        SanctionsSearchResult(
                            entry=entry,
                            match_score=name_score,
                            match_type="fuzzy_name",
                            matched_field="name",
                            matched_value=entry.name,
                        )
                    )
                    continue

                for alias in entry.aliases:
                    alias_score = fuzz.ratio(query.lower(), alias.lower()) / 100.0
                    if alias_score >= fuzzy_threshold:
                        results.append(
                            SanctionsSearchResult(
                                entry=entry,
                                match_score=alias_score,
                                match_type="alias",
                                matched_field="alias",
                                matched_value=alias,
                            )
                        )
                        break

        results.sort(key=lambda r: r.match_score, reverse=True)
        return results[:limit]

    def _row_to_sdn_entry(self, row: sqlite3.Row) -> SDNEntry:
        """Convert database row to SDNEntry."""
        return SDNEntry(
            id=row["id"],
            name=row["name"],
            sdn_type=EntityType(row["sdn_type"]),
            programs=json.loads(row["programs"]),
            aliases=json.loads(row["aliases"]),
            addresses=json.loads(row["addresses"]),
            ids=json.loads(row["ids"]),
            nationalities=json.loads(row["nationalities"]),
            dates_of_birth=json.loads(row["dates_of_birth"]),
            places_of_birth=json.loads(row["places_of_birth"]),
            remarks=row["remarks"],
        )

    # --- Denied Persons List Operations ---

    def add_denied_person(self, entry: DeniedPersonEntry) -> None:
        """Add an entry to the Denied Persons List."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO denied_persons
            (id, name, addresses, effective_date, expiration_date,
             standard_order, federal_register_citation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.name,
                json.dumps(entry.addresses),
                entry.effective_date.isoformat() if entry.effective_date else None,
                entry.expiration_date.isoformat() if entry.expiration_date else None,
                entry.standard_order,
                entry.federal_register_citation,
            ),
        )
        conn.commit()

    def search_denied_persons(
        self,
        query: str,
        fuzzy_threshold: float = 0.7,
        limit: int = 20,
    ) -> list[SanctionsSearchResult]:
        """Search the BIS Denied Persons List.

        Args:
            query: Name or partial name to search for
            fuzzy_threshold: Minimum fuzzy match score (0-1)
            limit: Maximum results to return

        Returns:
            List of search results with match scores
        """
        conn = self._get_connection()
        results = []

        # FTS5 search
        fts_query = query.replace('"', '""')
        cursor = conn.execute(
            """
            SELECT d.*, denied_persons_fts.rank
            FROM denied_persons d
            JOIN denied_persons_fts ON d.rowid = denied_persons_fts.rowid
            WHERE denied_persons_fts MATCH ?
            ORDER BY rank LIMIT ?
            """,
            (f'"{fts_query}"', limit * 2),
        )

        for row in cursor:
            entry = self._row_to_denied_person_entry(row)
            score = fuzz.ratio(query.lower(), entry.name.lower()) / 100.0
            results.append(
                SanctionsSearchResult(
                    entry=entry,
                    match_score=score,
                    match_type="fts_match",
                    matched_field="name",
                    matched_value=entry.name,
                )
            )

        # Fuzzy search
        if len(results) < limit:
            cursor = conn.execute("SELECT * FROM denied_persons")
            seen_ids = {r.entry.id for r in results}

            for row in cursor:
                if row["id"] in seen_ids:
                    continue

                entry = self._row_to_denied_person_entry(row)
                score = fuzz.ratio(query.lower(), entry.name.lower()) / 100.0
                if score >= fuzzy_threshold:
                    results.append(
                        SanctionsSearchResult(
                            entry=entry,
                            match_score=score,
                            match_type="fuzzy_name",
                            matched_field="name",
                            matched_value=entry.name,
                        )
                    )

        results.sort(key=lambda r: r.match_score, reverse=True)
        return results[:limit]

    def _row_to_denied_person_entry(self, row: sqlite3.Row) -> DeniedPersonEntry:
        """Convert database row to DeniedPersonEntry."""
        return DeniedPersonEntry(
            id=row["id"],
            name=row["name"],
            addresses=json.loads(row["addresses"]),
            effective_date=date.fromisoformat(row["effective_date"])
            if row["effective_date"]
            else None,
            expiration_date=date.fromisoformat(row["expiration_date"])
            if row["expiration_date"]
            else None,
            standard_order=row["standard_order"],
            federal_register_citation=row["federal_register_citation"],
        )

    # --- Country Sanctions Operations ---

    def add_country_sanctions(self, sanctions: CountrySanctions) -> None:
        """Add or update country sanctions data."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO country_sanctions
            (country_code, country_name, ofac_programs, embargo_type,
             ear_country_groups, itar_restricted, arms_embargo, summary,
             key_restrictions, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sanctions.country_code,
                sanctions.country_name,
                json.dumps(sanctions.ofac_programs),
                sanctions.embargo_type,
                json.dumps(sanctions.ear_country_groups),
                1 if sanctions.itar_restricted else 0,
                1 if sanctions.arms_embargo else 0,
                sanctions.summary,
                json.dumps(sanctions.key_restrictions),
                json.dumps(sanctions.notes),
            ),
        )
        conn.commit()

    def get_country_sanctions(self, country_code: str) -> CountrySanctions | None:
        """Get sanctions information for a country.

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            CountrySanctions object or None if not found
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM country_sanctions WHERE country_code = ?",
            (country_code.upper(),),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return CountrySanctions(
            country_code=row["country_code"],
            country_name=row["country_name"],
            ofac_programs=json.loads(row["ofac_programs"]),
            embargo_type=row["embargo_type"],
            ear_country_groups=json.loads(row["ear_country_groups"]),
            itar_restricted=bool(row["itar_restricted"]),
            arms_embargo=bool(row["arms_embargo"]),
            summary=row["summary"],
            key_restrictions=json.loads(row["key_restrictions"]),
            notes=json.loads(row["notes"]),
        )

    def get_country_by_name(self, country_name: str) -> CountrySanctions | None:
        """Get sanctions information by country name.

        Args:
            country_name: Full or partial country name

        Returns:
            CountrySanctions object or None if not found
        """
        conn = self._get_connection()
        # Try exact match first
        cursor = conn.execute(
            "SELECT * FROM country_sanctions WHERE LOWER(country_name) = LOWER(?)",
            (country_name,),
        )
        row = cursor.fetchone()

        if row is None:
            # Try partial match
            cursor = conn.execute(
                "SELECT * FROM country_sanctions WHERE LOWER(country_name) LIKE LOWER(?)",
                (f"%{country_name}%",),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return CountrySanctions(
            country_code=row["country_code"],
            country_name=row["country_name"],
            ofac_programs=json.loads(row["ofac_programs"]),
            embargo_type=row["embargo_type"],
            ear_country_groups=json.loads(row["ear_country_groups"]),
            itar_restricted=bool(row["itar_restricted"]),
            arms_embargo=bool(row["arms_embargo"]),
            summary=row["summary"],
            key_restrictions=json.loads(row["key_restrictions"]),
            notes=json.loads(row["notes"]),
        )

    # --- CSL Operations ---

    def add_csl_entry(
        self,
        entry_id: str,
        name: str,
        entry_type: str,
        source_list: str,
        programs: list[str] | None = None,
        aliases: list[str] | None = None,
        addresses: list[str] | None = None,
        countries: list[str] | None = None,
        remarks: str = "",
    ) -> None:
        """Add an entry to the Consolidated Screening List."""
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO csl
            (id, name, entry_type, source_list, programs, aliases, addresses, countries, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                name,
                entry_type,
                source_list,
                json.dumps(programs or []),
                json.dumps(aliases or []),
                json.dumps(addresses or []),
                json.dumps(countries or []),
                remarks,
            ),
        )
        conn.commit()

    def search_csl(
        self,
        query: str,
        source_list: str | None = None,
        country: str | None = None,
        fuzzy_threshold: float = 0.7,
        limit: int = 20,
    ) -> list[dict]:
        """Search the Consolidated Screening List.

        Args:
            query: Name or partial name to search for
            source_list: Optional filter by source list code
            country: Optional filter by country
            fuzzy_threshold: Minimum fuzzy match score (0-1)
            limit: Maximum results to return

        Returns:
            List of matching entries with scores
        """
        conn = self._get_connection()
        results = []

        # First try FTS5 match
        fts_query = query.replace('"', '""')
        sql = """
            SELECT c.*, csl_fts.rank
            FROM csl c
            JOIN csl_fts ON c.rowid = csl_fts.rowid
            WHERE csl_fts MATCH ?
        """
        params: list = [f'"{fts_query}"']

        if source_list:
            sql += " AND c.source_list = ?"
            params.append(source_list)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit * 2)

        cursor = conn.execute(sql, params)
        seen_ids = set()

        for row in cursor:
            entry = self._row_to_csl_dict(row)
            countries_list = json.loads(row["countries"]) if row["countries"] else []

            # Apply country filter if specified
            if country and country.upper() not in [c.upper() for c in countries_list]:
                continue

            score = fuzz.ratio(query.lower(), row["name"].lower()) / 100.0
            entry["match_score"] = score
            entry["match_type"] = "fts_match"
            results.append(entry)
            seen_ids.add(row["id"])

        # Fuzzy search if needed
        if len(results) < limit:
            sql = "SELECT * FROM csl"
            conditions = []
            params = []

            if source_list:
                conditions.append("source_list = ?")
                params.append(source_list)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            cursor = conn.execute(sql, params)

            for row in cursor:
                if row["id"] in seen_ids:
                    continue

                countries_list = json.loads(row["countries"]) if row["countries"] else []
                if country and country.upper() not in [c.upper() for c in countries_list]:
                    continue

                # Check name
                name_score = fuzz.ratio(query.lower(), row["name"].lower()) / 100.0
                if name_score >= fuzzy_threshold:
                    entry = self._row_to_csl_dict(row)
                    entry["match_score"] = name_score
                    entry["match_type"] = "fuzzy_name"
                    results.append(entry)
                    seen_ids.add(row["id"])
                    continue

                # Check aliases
                aliases = json.loads(row["aliases"]) if row["aliases"] else []
                for alias in aliases:
                    alias_score = fuzz.ratio(query.lower(), alias.lower()) / 100.0
                    if alias_score >= fuzzy_threshold:
                        entry = self._row_to_csl_dict(row)
                        entry["match_score"] = alias_score
                        entry["match_type"] = "alias"
                        entry["matched_alias"] = alias
                        results.append(entry)
                        seen_ids.add(row["id"])
                        break

        # Sort by score and limit
        results.sort(key=lambda r: r.get("match_score", 0), reverse=True)
        return results[:limit]

    def _row_to_csl_dict(self, row: sqlite3.Row) -> dict:
        """Convert database row to CSL dictionary."""
        return {
            "id": row["id"],
            "name": row["name"],
            "entry_type": row["entry_type"],
            "source_list": row["source_list"],
            "programs": json.loads(row["programs"]) if row["programs"] else [],
            "aliases": json.loads(row["aliases"]) if row["aliases"] else [],
            "addresses": json.loads(row["addresses"]) if row["addresses"] else [],
            "countries": json.loads(row["countries"]) if row["countries"] else [],
            "remarks": row["remarks"],
        }

    def clear_csl(self) -> None:
        """Clear all CSL data."""
        conn = self._get_connection()
        conn.execute("DELETE FROM csl")
        conn.commit()

    def get_csl_stats(self) -> dict:
        """Get CSL statistics by source list."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT source_list, COUNT(*) as count
            FROM csl
            GROUP BY source_list
            ORDER BY count DESC
        """)
        return {row["source_list"]: row["count"] for row in cursor}

    # --- Utility Operations ---

    def clear_all(self) -> None:
        """Clear all data from all tables."""
        conn = self._get_connection()
        conn.executescript("""
            DELETE FROM entity_list;
            DELETE FROM sdn_list;
            DELETE FROM denied_persons;
            DELETE FROM country_sanctions;
            DELETE FROM csl;
        """)
        conn.commit()

    def get_stats(self) -> dict:
        """Get database statistics."""
        conn = self._get_connection()
        stats = {}

        for table in _VALID_TABLES:
            # Table name validated against allowlist - safe for SQL interpolation
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")  # nosec B608  # nosemgrep
            stats[table] = cursor.fetchone()[0]

        return stats

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
