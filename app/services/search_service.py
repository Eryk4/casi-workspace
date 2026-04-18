from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable

from app.domain.constants import (
    KNOWLEDGE_READ_CAPABILITY,
    MANAGER_ASSISTANT_MANAGER_ROLES,
    MANAGER_ASSISTANT_MODULE,
    MANAGER_ASSISTANT_WORKSPACE_ROLES,
    ORGANIZATION_SETTINGS_ROLES,
    USER_MANAGEMENT_ROLES,
)
from app.repositories.billing_repository import BillingRepository
from app.repositories.contractor_repository import ContractorRepository
from app.repositories.event_repository import EventRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


@dataclass(slots=True)
class QueryAnalysis:
    raw_query: str
    normalized_query: str
    tokens: list[str]
    expanded_tokens: list[str]
    search_terms: list[str]
    preferred_group_keys: set[str]
    preferred_module_keys: set[str]
    month_numbers: set[str]
    question_like: bool


@dataclass(slots=True)
class SearchCandidate:
    group_key: str
    raw_item: dict[str, Any]
    serialized_item: dict[str, Any]
    score: float


class SearchService:
    MAX_RESULTS_PER_GROUP = 6
    MAX_REPOSITORY_FETCH = 12
    MAX_SEARCH_TERMS = 6

    STOPWORDS = {
        "a",
        "aby",
        "albo",
        "bez",
        "bo",
        "co",
        "czy",
        "dla",
        "do",
        "i",
        "ich",
        "jak",
        "jako",
        "jest",
        "jesli",
        "jeśli",
        "lub",
        "na",
        "nad",
        "o",
        "od",
        "oraz",
        "po",
        "pod",
        "przez",
        "sie",
        "się",
        "ta",
        "te",
        "ten",
        "to",
        "tych",
        "tym",
        "u",
        "w",
        "we",
        "z",
        "za",
        "ze",
    }

    MONTH_KEYWORDS = {
        "styczen": "01",
        "stycznia": "01",
        "luty": "02",
        "lutego": "02",
        "marzec": "03",
        "marca": "03",
        "kwiecien": "04",
        "kwietnia": "04",
        "maj": "05",
        "maja": "05",
        "czerwiec": "06",
        "czerwca": "06",
        "lipiec": "07",
        "lipca": "07",
        "sierpien": "08",
        "sierpnia": "08",
        "wrzesien": "09",
        "wrzesnia": "09",
        "pazdziernik": "10",
        "pazdziernika": "10",
        "listopad": "11",
        "listopada": "11",
        "grudzien": "12",
        "grudnia": "12",
    }

    TERM_EXPANSIONS = {
        "fakture": ("faktura",),
        "fakturze": ("faktura",),
        "faktury": ("faktura",),
        "faktur": ("faktura",),
        "kontrahenta": ("kontrahent",),
        "kontrahentow": ("kontrahent",),
        "zadanie": ("zadania",),
        "zadaniu": ("zadania",),
        "zadan": ("zadania",),
        "rozliczen": ("rozliczenia",),
        "platnosc": ("platnosci", "wplata"),
        "platnosci": ("wplata",),
        "przelew": ("transakcja", "wplata"),
        "przelewy": ("transakcje", "wplata"),
        "rachunek": ("rachunki", "iban"),
        "rachunku": ("rachunki", "iban"),
        "rachunki": ("iban",),
        "wyciag": ("transakcja", "csv"),
        "wyciagu": ("transakcja", "csv"),
        "wyciagi": ("transakcje", "csv"),
        "onboardingu": ("onboarding",),
        "delegacje": ("delegacja",),
        "delegacji": ("delegacja",),
        "dokument": ("plik", "dokumenty"),
        "dokumentow": ("dokumenty", "plik"),
        "plikow": ("pliki",),
        "uzytkownika": ("uzytkownik",),
        "uzytkownikow": ("uzytkownicy",),
        "organizacji": ("organizacja",),
        "logow": ("logi",),
    }

    GROUP_HINTS = {
        "invoices": {
            "faktura",
            "faktury",
            "invoice",
            "invoices",
            "ksef",
            "nip",
            "duplikat",
            "duplikaty",
            "ocr",
        },
        "tasks": {
            "zadanie",
            "zadania",
            "task",
            "tasks",
            "termin",
            "przypomnienie",
            "spotkanie",
            "onboarding",
            "planner",
            "asystent",
        },
        "contractors": {
            "kontrahent",
            "kontrahenci",
            "contractor",
            "contractors",
            "firma",
            "firmy",
            "dostawca",
            "klient",
        },
        "knowledge_documents": {
            "wiedza",
            "procedura",
            "procedury",
            "instrukcja",
            "instrukcje",
            "dokument",
            "dokumenty",
            "plik",
            "pliki",
            "regulamin",
            "asystent",
        },
        "billing_bank_accounts": {
            "rachunek",
            "rachunki",
            "iban",
            "konto",
            "bank",
            "bankowe",
        },
        "billing_transactions": {
            "transakcja",
            "transakcje",
            "wyciag",
            "wyciagi",
            "przelew",
            "przelewy",
            "platnosc",
            "platnosci",
            "wplata",
            "wplaty",
            "csv",
        },
        "logs": {
            "log",
            "logi",
            "historia",
            "zmiana",
            "zdarzenie",
            "zdarzenia",
        },
        "users": {
            "uzytkownik",
            "uzytkownicy",
            "konto",
            "konta",
            "login",
            "rola",
        },
        "organizations": {
            "organizacja",
            "organizacje",
            "slug",
            "klient",
            "firma",
        },
    }

    MODULE_TO_GROUPS = {
        "dashboard": {"dashboard"},
        "invoices": {"invoices"},
        "tasks": {"tasks"},
        "contractors": {"contractors"},
        "billing": {"billing_bank_accounts", "billing_transactions"},
        "billing_bank_accounts": {"billing_bank_accounts"},
        "billing_transactions": {"billing_transactions"},
        "knowledge": {"knowledge_documents"},
        "logs": {"logs"},
        "organizations": {"organizations"},
        "users": {"users"},
    }

    DATE_KEYS = (
        "incoming_date",
        "issue_date",
        "sale_date",
        "due_at",
        "remind_at",
        "booking_date",
        "event_time",
        "updated_at",
        "last_processed_at",
        "last_login_at",
    )

    MODULES = (
        {
            "key": "dashboard",
            "title": "Pulpit",
            "subtitle": "Szybki podglad wskaznikow, przypomnien i ostatnich zdarzen.",
            "view": "dashboard",
            "aliases": ("pulpit", "dashboard", "home", "start"),
        },
        {
            "key": "invoices",
            "title": "Faktury",
            "subtitle": "Dokumenty, statusy, duplikaty i filtry faktur.",
            "view": "invoices",
            "aliases": ("faktura", "faktury", "invoice", "invoices", "tabela faktur", "tabela invoices"),
        },
        {
            "key": "tasks",
            "title": "Asystent Szefa",
            "subtitle": "Zadania, wydarzenia, przypomnienia i plan dnia.",
            "view": "tasks",
            "aliases": ("zadanie", "zadania", "task", "tasks", "asystent szefa", "planner"),
            "allowed_roles": MANAGER_ASSISTANT_MANAGER_ROLES,
            "requires_org_module": MANAGER_ASSISTANT_MODULE,
        },
        {
            "key": "contractors",
            "title": "Kontrahenci",
            "subtitle": "Kartoteka firm, NIP-y i powiazane faktury.",
            "view": "contractors",
            "aliases": ("kontrahent", "kontrahenci", "contractor", "contractors"),
        },
        {
            "key": "billing",
            "title": "Rozliczenia",
            "subtitle": "Rachunki bankowe, transakcje i roadmapa rozliczen.",
            "view": "billing",
            "aliases": ("rozliczenia", "billing", "platnosci", "wplaty"),
        },
        {
            "key": "billing_bank_accounts",
            "title": "Rozliczenia: rachunki bankowe",
            "subtitle": "Rachunki organizacji, banki i numery IBAN.",
            "view": "billing",
            "section": "billing-bank-account-table-body",
            "aliases": ("rachunki bankowe", "rachunek bankowy", "bank account", "iban", "billing_bank_accounts"),
        },
        {
            "key": "billing_transactions",
            "title": "Rozliczenia: transakcje",
            "subtitle": "Wyciagi CSV, referencje i historia wplat.",
            "view": "billing",
            "section": "billing-transaction-table-body",
            "aliases": ("transakcja", "transakcje", "wyciag", "wyciagi", "billing_transactions"),
        },
        {
            "key": "knowledge",
            "title": "Asystent Firmowy i Dokumenty",
            "subtitle": "Baza wiedzy organizacji, biblioteka plikow i dokumenty referencyjne.",
            "view": "knowledge",
            "aliases": ("asystent firmowy", "baza wiedzy", "dokumenty", "pliki firmowe", "knowledge", "knowledge_documents"),
            "requires_capability": KNOWLEDGE_READ_CAPABILITY,
        },
        {
            "key": "logs",
            "title": "Historia systemu",
            "subtitle": "Logi operacji, decyzji i zmian w systemie.",
            "view": "logs",
            "aliases": ("log", "logi", "historia", "event logs", "event_logs"),
        },
        {
            "key": "organizations",
            "title": "Organizacje",
            "subtitle": "Zakres danych, integracje i konfiguracja organizacji.",
            "view": "organizations",
            "aliases": ("organizacja", "organizacje", "organization", "organizations"),
            "allowed_roles": ORGANIZATION_SETTINGS_ROLES,
        },
        {
            "key": "users",
            "title": "Uzytkownicy",
            "subtitle": "Konta, role i uprawnienia zespolu.",
            "view": "users",
            "aliases": ("uzytkownik", "uzytkownicy", "user", "users", "konta"),
            "allowed_roles": USER_MANAGEMENT_ROLES,
        },
    )

    def __init__(
        self,
        *,
        auth_service: AuthService,
        invoice_repository: InvoiceRepository,
        contractor_repository: ContractorRepository,
        task_repository: TaskRepository,
        knowledge_repository: KnowledgeRepository,
        billing_repository: BillingRepository,
        event_repository: EventRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self.auth_service = auth_service
        self.invoice_repository = invoice_repository
        self.contractor_repository = contractor_repository
        self.task_repository = task_repository
        self.knowledge_repository = knowledge_repository
        self.billing_repository = billing_repository
        self.event_repository = event_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository

    def search(
        self,
        query_text: str,
        *,
        actor_user: dict[str, Any],
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        query = str(query_text or "").strip()
        analysis = self._analyze_query(query, actor_user, organization_id)
        if not analysis.normalized_query:
            return {
                "query": "",
                "scope_label": self._build_scope_label(actor_user, organization_id),
                "modules": [],
                "groups": [],
            }

        groups: list[dict[str, Any]] = []

        invoice_group = self._build_group(
            group_key="invoices",
            label="Faktury",
            analysis=analysis,
            fetcher=lambda term, limit: self.invoice_repository.search_invoices(
                term,
                organization_id=organization_id,
                limit=limit,
            ),
            serializer=self._serialize_invoice,
        )
        if invoice_group:
            groups.append(invoice_group)

        if self._can_access_manager_assistant_workspace(actor_user, organization_id):
            task_group = self._build_group(
                group_key="tasks",
                label="Zadania i wydarzenia",
                analysis=analysis,
                fetcher=lambda term, limit: self.task_repository.search_tasks(
                    term,
                    organization_id=organization_id,
                    viewer_user_id=int(actor_user["user_id"]),
                    limit=limit,
                ),
                serializer=self._serialize_task,
            )
            if task_group:
                groups.append(task_group)

        contractor_group = self._build_group(
            group_key="contractors",
            label="Kontrahenci",
            analysis=analysis,
            fetcher=lambda term, limit: self.contractor_repository.search_contractors(
                term,
                organization_id=organization_id,
                limit=limit,
            ),
            serializer=self._serialize_contractor,
        )
        if contractor_group:
            groups.append(contractor_group)

        if self.auth_service.has_capability(actor_user, KNOWLEDGE_READ_CAPABILITY):
            knowledge_group = self._build_group(
                group_key="knowledge_documents",
                label="Asystent Firmowy i Dokumenty",
                analysis=analysis,
                fetcher=lambda term, limit: self.knowledge_repository.search_documents(
                    term,
                    organization_id=organization_id,
                    limit=limit,
                ),
                serializer=self._serialize_knowledge_document,
            )
            if knowledge_group:
                groups.append(knowledge_group)

        bank_account_group = self._build_group(
            group_key="billing_bank_accounts",
            label="Rozliczenia: rachunki bankowe",
            analysis=analysis,
            fetcher=lambda term, limit: self.billing_repository.search_bank_accounts(
                term,
                organization_id=organization_id,
                limit=limit,
            ),
            serializer=self._serialize_bank_account,
        )
        if bank_account_group:
            groups.append(bank_account_group)

        transaction_group = self._build_group(
            group_key="billing_transactions",
            label="Rozliczenia: transakcje",
            analysis=analysis,
            fetcher=lambda term, limit: self.billing_repository.search_transactions(
                term,
                organization_id=organization_id,
                limit=limit,
            ),
            serializer=self._serialize_transaction,
        )
        if transaction_group:
            groups.append(transaction_group)

        log_group = self._build_group(
            group_key="logs",
            label="Historia systemu",
            analysis=analysis,
            fetcher=lambda term, limit: self.event_repository.search_logs(
                term,
                organization_id=organization_id,
                limit=limit,
            ),
            serializer=self._serialize_log,
        )
        if log_group:
            groups.append(log_group)

        if actor_user.get("role") in USER_MANAGEMENT_ROLES:
            users_group = self._build_group(
                group_key="users",
                label="Uzytkownicy",
                analysis=analysis,
                fetcher=lambda term, limit: self.user_repository.search_users(
                    term,
                    organization_id=organization_id,
                    limit=limit,
                ),
                serializer=self._serialize_user,
            )
            if users_group:
                groups.append(users_group)

        if actor_user.get("role") in ORGANIZATION_SETTINGS_ROLES:
            organization_scope = None if actor_user.get("is_global_admin") else int(actor_user.get("organization_id") or 0)
            organizations_group = self._build_group(
                group_key="organizations",
                label="Organizacje",
                analysis=analysis,
                fetcher=lambda term, limit: self.organization_repository.search_organizations(
                    term,
                    organization_id=organization_scope or None,
                    limit=limit,
                ),
                serializer=self._serialize_organization,
            )
            if organizations_group:
                groups.append(organizations_group)

        return {
            "query": query,
            "scope_label": self._build_scope_label(actor_user, organization_id),
            "modules": self._search_modules(analysis, actor_user, organization_id),
            "groups": groups,
        }

    def _build_group(
        self,
        *,
        group_key: str,
        label: str,
        analysis: QueryAnalysis,
        fetcher: Callable[[str, int], list[dict[str, Any]]],
        serializer: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any] | None:
        candidates = self._collect_candidates(
            group_key=group_key,
            analysis=analysis,
            fetcher=fetcher,
            serializer=serializer,
        )
        if not candidates:
            return None

        minimum_score = 1.25 if len(analysis.search_terms) <= 1 else 2.4
        if group_key in analysis.preferred_group_keys:
            minimum_score -= 0.35
        if analysis.question_like and group_key == "knowledge_documents":
            minimum_score -= 0.25

        visible_candidates = [candidate for candidate in candidates if candidate.score >= minimum_score]
        if not visible_candidates and candidates and candidates[0].score >= (minimum_score - 0.45):
            visible_candidates = candidates[:1]
        if not visible_candidates:
            return None

        return {
            "key": group_key,
            "label": label,
            "items": [candidate.serialized_item for candidate in visible_candidates[: self.MAX_RESULTS_PER_GROUP]],
        }

    def _collect_candidates(
        self,
        *,
        group_key: str,
        analysis: QueryAnalysis,
        fetcher: Callable[[str, int], list[dict[str, Any]]],
        serializer: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> list[SearchCandidate]:
        candidate_map: dict[tuple[str, str, str], SearchCandidate] = {}
        seen_terms: set[str] = set()
        search_terms = list(analysis.search_terms)
        if analysis.preferred_group_keys and group_key not in analysis.preferred_group_keys:
            search_terms = search_terms[:2]
        else:
            search_terms = search_terms[:4]

        for index, term in enumerate(search_terms):
            if not term or term in seen_terms:
                continue
            seen_terms.add(term)
            limit = self.MAX_REPOSITORY_FETCH if index == 0 else max(self.MAX_RESULTS_PER_GROUP + 1, 8)
            for raw_item in fetcher(term, limit):
                serialized_item = serializer(raw_item)
                candidate_key = (
                    str(serialized_item.get("entity_type") or ""),
                    str(serialized_item.get("entity_id") or ""),
                    str(serialized_item.get("organization_id") or ""),
                )
                score = self._score_item(
                    group_key=group_key,
                    raw_item=raw_item,
                    serialized_item=serialized_item,
                    analysis=analysis,
                )
                existing = candidate_map.get(candidate_key)
                if existing is None or score > existing.score:
                    candidate_map[candidate_key] = SearchCandidate(
                        group_key=group_key,
                        raw_item=raw_item,
                        serialized_item=serialized_item,
                        score=score,
                    )

        return sorted(
            candidate_map.values(),
            key=lambda candidate: (-candidate.score, str(candidate.serialized_item.get("title") or "")),
        )

    def _score_item(
        self,
        *,
        group_key: str,
        raw_item: dict[str, Any],
        serialized_item: dict[str, Any],
        analysis: QueryAnalysis,
    ) -> float:
        title = self._normalize_search_text(serialized_item.get("title"))
        subtitle = self._normalize_search_text(serialized_item.get("subtitle"))
        meta = self._normalize_search_text(serialized_item.get("meta"))
        search_blob = self._build_search_blob(raw_item, serialized_item)

        score = 0.0
        matched_terms: set[str] = set()

        if analysis.normalized_query:
            if analysis.normalized_query in title:
                score += 8.0
            elif analysis.normalized_query in subtitle:
                score += 6.0
            elif analysis.normalized_query in meta:
                score += 4.5
            elif analysis.normalized_query in search_blob:
                score += 4.0

        for term in analysis.search_terms:
            if not term or term == analysis.normalized_query:
                continue

            term_score = 0.0
            if term in title:
                term_score = max(term_score, 4.0)
            elif self._token_has_fuzzy_match(term, title):
                term_score = max(term_score, 2.4)

            if term in subtitle:
                term_score = max(term_score, 2.8)
            elif self._token_has_fuzzy_match(term, subtitle):
                term_score = max(term_score, 1.8)

            if term in meta:
                term_score = max(term_score, 2.2)
            elif self._token_has_fuzzy_match(term, meta):
                term_score = max(term_score, 1.3)

            if term in search_blob:
                term_score = max(term_score, 1.9)
            elif self._token_has_fuzzy_match(term, search_blob):
                term_score = max(term_score, 1.0)

            if term_score > 0:
                matched_terms.add(term)
                score += term_score

        if group_key in analysis.preferred_group_keys:
            score += 2.3
        elif analysis.preferred_group_keys:
            score -= 0.45

        if any(group_key in self.MODULE_TO_GROUPS.get(module_key, set()) for module_key in analysis.preferred_module_keys):
            score += 1.1

        if analysis.question_like and group_key == "knowledge_documents":
            score += 1.5

        month_hits = self._count_month_hits(raw_item, analysis.month_numbers)
        if month_hits:
            score += min(month_hits, 2) * 1.25

        expected_terms = [term for term in analysis.search_terms if len(term) >= 3 or term.isdigit()]
        coverage_base = max(1, min(len(expected_terms), 4))
        score += (len(matched_terms) / coverage_base) * 2.0

        if len(expected_terms) >= 2 and not matched_terms:
            score -= 2.0
        elif len(expected_terms) >= 3 and len(matched_terms) == 1:
            score -= 1.0

        return score

    def _build_search_blob(self, raw_item: dict[str, Any], serialized_item: dict[str, Any]) -> str:
        parts: list[str] = [
            str(serialized_item.get("title") or ""),
            str(serialized_item.get("subtitle") or ""),
            str(serialized_item.get("meta") or ""),
            str(serialized_item.get("category") or ""),
            str(serialized_item.get("badge") or ""),
        ]
        for key, value in raw_item.items():
            if value is None or isinstance(value, bool):
                continue
            if not isinstance(value, (str, int, float)):
                continue
            text_value = str(value).strip()
            if not text_value:
                continue
            if key in {"content_text", "details", "ocr_raw_text", "source_metadata"} and len(text_value) > 1200:
                text_value = text_value[:1200]
            parts.append(text_value)
        return self._normalize_search_text(" ".join(parts))

    def _count_month_hits(self, raw_item: dict[str, Any], month_numbers: set[str]) -> int:
        if not month_numbers:
            return 0
        hits = 0
        for key in self.DATE_KEYS:
            value = str(raw_item.get(key) or "").strip()
            if len(value) >= 7 and value[5:7] in month_numbers:
                hits += 1
        return hits

    def _token_has_fuzzy_match(self, token: str, text: str) -> bool:
        normalized_token = self._normalize_search_text(token)
        normalized_text = self._normalize_search_text(text)
        if not normalized_token or not normalized_text:
            return False
        if normalized_token in normalized_text:
            return True

        token_stem = self._stem_token(normalized_token)
        for word in normalized_text.split():
            if word == normalized_token:
                return True
            if len(normalized_token) >= 4 and (word.startswith(normalized_token) or normalized_token.startswith(word)):
                return True
            if token_stem and len(token_stem) >= 4 and self._stem_token(word) == token_stem:
                return True
        return False

    def _analyze_query(
        self,
        query_text: str,
        actor_user: dict[str, Any],
        organization_id: int | None,
    ) -> QueryAnalysis:
        normalized_query = self._normalize_search_text(query_text)
        tokens = self._unique_tokens(normalized_query.split())
        content_tokens = [token for token in tokens if token.isdigit() or token not in self.STOPWORDS]
        month_numbers = {self.MONTH_KEYWORDS[token] for token in content_tokens if token in self.MONTH_KEYWORDS}

        expanded_tokens = list(content_tokens)
        for token in content_tokens:
            expanded_tokens.extend(self.TERM_EXPANSIONS.get(token, ()))
            stem = self._stem_token(token)
            if stem and stem != token:
                expanded_tokens.append(stem)
        expanded_tokens = self._unique_tokens(expanded_tokens)

        preferred_group_keys: set[str] = set()
        for token in expanded_tokens:
            for group_key, hints in self.GROUP_HINTS.items():
                if token in hints:
                    preferred_group_keys.add(group_key)

        preferred_module_keys: set[str] = set()
        for definition in self.MODULES:
            if not self._module_is_accessible(definition, actor_user, organization_id):
                continue
            for alias in definition.get("aliases") or ():
                normalized_alias = self._normalize_search_text(alias)
                alias_tokens = normalized_alias.split()
                if not normalized_alias:
                    continue
                if normalized_alias in normalized_query or normalized_query in normalized_alias:
                    preferred_module_keys.add(str(definition["key"]))
                    break
                if any(token in alias_tokens for token in expanded_tokens):
                    preferred_module_keys.add(str(definition["key"]))
                    break

        return QueryAnalysis(
            raw_query=query_text,
            normalized_query=normalized_query,
            tokens=tokens,
            expanded_tokens=expanded_tokens,
            search_terms=self._unique_search_terms(normalized_query, content_tokens, expanded_tokens),
            preferred_group_keys=preferred_group_keys,
            preferred_module_keys=preferred_module_keys,
            month_numbers=month_numbers,
            question_like=self._looks_like_question(query_text),
        )

    def _looks_like_question(self, query_text: str) -> bool:
        normalized_query = self._normalize_search_text(query_text)
        if not normalized_query:
            return False
        if "?" in str(query_text or ""):
            return True
        question_prefixes = (
            "co",
            "czy",
            "gdzie",
            "jak",
            "jaka",
            "jaki",
            "jakie",
            "kiedy",
            "kto",
            "kto",
            "ktora",
            "ktore",
            "ktory",
            "po co",
        )
        return any(normalized_query.startswith(prefix) for prefix in question_prefixes)

    def _unique_tokens(self, values: list[str]) -> list[str]:
        unique_values: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized_value = self._normalize_search_text(value)
            if not normalized_value or normalized_value in seen:
                continue
            seen.add(normalized_value)
            unique_values.append(normalized_value)
        return unique_values

    def _unique_search_terms(
        self,
        normalized_query: str,
        content_tokens: list[str],
        expanded_tokens: list[str],
    ) -> list[str]:
        candidates: list[str] = []
        if normalized_query:
            candidates.append(normalized_query)
        compact_phrase = " ".join(content_tokens)
        if compact_phrase and compact_phrase != normalized_query:
            candidates.append(compact_phrase)
        candidates.extend(content_tokens)
        candidates.extend(expanded_tokens)
        if len(content_tokens) >= 2:
            candidates.extend(" ".join(content_tokens[index : index + 2]) for index in range(len(content_tokens) - 1))
        return self._unique_tokens(candidates)[: self.MAX_SEARCH_TERMS]

    def _stem_token(self, token: str) -> str:
        normalized_token = self._normalize_search_text(token)
        if len(normalized_token) <= 4:
            return normalized_token
        for suffix in (
            "ami",
            "ach",
            "ego",
            "owa",
            "owe",
            "owy",
            "enie",
            "ania",
            "anie",
            "enia",
            "niu",
            "cia",
            "cie",
            "ciu",
            "owa",
            "owe",
            "ach",
            "owi",
            "ego",
            "emu",
            "ami",
            "om",
            "ow",
            "ie",
            "ia",
            "iu",
            "ym",
            "em",
            "ej",
            "y",
            "a",
            "e",
            "i",
            "u",
        ):
            if normalized_token.endswith(suffix) and len(normalized_token) - len(suffix) >= 4:
                return normalized_token[: -len(suffix)]
        return normalized_token

    def _search_modules(
        self,
        analysis: QueryAnalysis,
        actor_user: dict[str, Any],
        organization_id: int | None,
    ) -> list[dict[str, Any]]:
        modules: list[tuple[float, dict[str, Any]]] = []
        for definition in self.MODULES:
            if not self._module_is_accessible(definition, actor_user, organization_id):
                continue

            aliases = [self._normalize_search_text(alias) for alias in definition.get("aliases") or ()]
            score = 0.0
            for alias in aliases:
                if not alias:
                    continue
                if analysis.normalized_query and analysis.normalized_query in alias:
                    score = max(score, 8.0)
                elif analysis.normalized_query and alias in analysis.normalized_query:
                    score = max(score, 7.0)
                elif any(token == alias or token in alias.split() for token in analysis.expanded_tokens):
                    score = max(score, 4.5)
                elif any(self._token_has_fuzzy_match(token, alias) for token in analysis.expanded_tokens):
                    score = max(score, 2.4)

            module_key = str(definition["key"])
            if module_key in analysis.preferred_module_keys:
                score += 1.8
            if any(group_key in analysis.preferred_group_keys for group_key in self.MODULE_TO_GROUPS.get(module_key, set())):
                score += 1.2

            if score < 3.5:
                continue

            modules.append(
                (
                    score,
                    {
                        "entity_type": "module",
                        "entity_id": definition["key"],
                        "organization_id": None,
                        "view": definition["view"],
                        "section": definition.get("section"),
                        "category": "Modul",
                        "badge": "Modul",
                        "title": definition["title"],
                        "subtitle": definition["subtitle"],
                        "meta": f"Widok: {definition['view']}",
                    },
                )
            )

        modules.sort(key=lambda item: (-item[0], item[1]["title"]))
        return [module for _, module in modules[: self.MAX_RESULTS_PER_GROUP]]

    def _module_is_accessible(
        self,
        definition: dict[str, Any],
        actor_user: dict[str, Any],
        organization_id: int | None,
    ) -> bool:
        allowed_roles = definition.get("allowed_roles")
        if allowed_roles and actor_user.get("role") not in allowed_roles:
            return False
        required_capability = definition.get("requires_capability")
        if required_capability and not self.auth_service.has_capability(actor_user, required_capability):
            return False
        required_org_module = definition.get("requires_org_module")
        if required_org_module and not self._organization_has_module(organization_id, str(required_org_module)):
            return False
        return True

    def _can_access_manager_assistant_workspace(
        self,
        actor_user: dict[str, Any],
        organization_id: int | None,
    ) -> bool:
        if actor_user.get("role") not in MANAGER_ASSISTANT_WORKSPACE_ROLES:
            return False
        return self._organization_has_module(organization_id, MANAGER_ASSISTANT_MODULE)

    def _organization_has_module(self, organization_id: int | None, module_code: str) -> bool:
        if organization_id is None:
            return False
        try:
            return self.organization_repository.organization_has_module(int(organization_id), module_code)
        except (TypeError, ValueError):
            return False

    def _serialize_invoice(self, item: dict[str, Any]) -> dict[str, Any]:
        title = item.get("invoice_number") or item.get("ksef_number") or item.get("file_name") or f"Faktura #{item['id']}"
        subtitle = self._join_parts(item.get("issuer_name"), item.get("issuer_nip"))
        amount = f"{item.get('gross_amount')} {item.get('currency')}" if item.get("gross_amount") is not None else None
        meta = self._join_parts(
            item.get("organization_name"),
            item.get("source"),
            item.get("status"),
            item.get("incoming_date") or item.get("issue_date"),
            amount,
        )
        return self._result_item(
            entity_type="invoice",
            entity_id=item["id"],
            organization_id=item.get("organization_id"),
            view="invoices",
            category="Faktury",
            badge=f"#{item['id']}",
            title=title,
            subtitle=subtitle,
            meta=meta,
        )

    def _serialize_task(self, item: dict[str, Any]) -> dict[str, Any]:
        subtitle = self._join_parts(item.get("assigned_user_name"), item.get("calendar_name"))
        meta = self._join_parts(
            item.get("organization_name"),
            item.get("task_type"),
            item.get("status"),
            item.get("priority"),
            item.get("due_at"),
        )
        return self._result_item(
            entity_type="task",
            entity_id=item["task_id"],
            organization_id=item.get("organization_id"),
            view="tasks",
            category="Zadania i wydarzenia",
            badge=f"#{item['task_id']}",
            title=item.get("title") or f"Zadanie #{item['task_id']}",
            subtitle=subtitle,
            meta=meta,
        )

    def _serialize_contractor(self, item: dict[str, Any]) -> dict[str, Any]:
        subtitle = self._join_parts(item.get("nip"), item.get("email"), item.get("phone"))
        meta = self._join_parts(
            item.get("organization_name"),
            "nowy" if item.get("is_new") else None,
            f"faktur: {item.get('invoice_count')}" if item.get("invoice_count") is not None else None,
        )
        return self._result_item(
            entity_type="contractor",
            entity_id=item["contractor_id"],
            organization_id=item.get("organization_id"),
            view="contractors",
            category="Kontrahenci",
            badge=f"#{item['contractor_id']}",
            title=item.get("name") or f"Kontrahent #{item['contractor_id']}",
            subtitle=subtitle,
            meta=meta,
        )

    def _serialize_knowledge_document(self, item: dict[str, Any]) -> dict[str, Any]:
        usage_bits = []
        if item.get("is_downloadable", 1):
            usage_bits.append("do pobrania")
        if item.get("use_in_assistant", 1):
            usage_bits.append("w asystencie")
        meta = self._join_parts(
            item.get("organization_name"),
            item.get("library_path") or "bez folderu",
            item.get("source_type"),
            item.get("processing_status"),
            ", ".join(usage_bits) if usage_bits else None,
            f"znaki: {item.get('char_count')}" if item.get("char_count") is not None else None,
        )
        return self._result_item(
            entity_type="knowledge_document",
            entity_id=item["knowledge_document_id"],
            organization_id=item.get("organization_id"),
            view="knowledge",
            category="Dokumenty firmowe",
            badge=f"v{item.get('current_version_number') or 0}",
            title=item.get("title") or item.get("file_name") or f"Dokument #{item['knowledge_document_id']}",
            subtitle=item.get("file_name"),
            meta=meta,
        )

    def _serialize_bank_account(self, item: dict[str, Any]) -> dict[str, Any]:
        subtitle = self._join_parts(item.get("bank_name"), item.get("iban"))
        meta = self._join_parts(
            item.get("organization_name"),
            item.get("currency"),
            "aktywny" if item.get("is_active") else "nieaktywny",
        )
        return self._result_item(
            entity_type="billing_bank_account",
            entity_id=item["billing_bank_account_id"],
            organization_id=item.get("organization_id"),
            view="billing",
            section="billing-bank-account-table-body",
            category="Rozliczenia: rachunki bankowe",
            badge=f"#{item['billing_bank_account_id']}",
            title=item.get("account_name") or f"Rachunek #{item['billing_bank_account_id']}",
            subtitle=subtitle,
            meta=meta,
        )

    def _serialize_transaction(self, item: dict[str, Any]) -> dict[str, Any]:
        title = item.get("reference") or item.get("counterparty_name") or item.get("title") or f"Transakcja #{item['billing_transaction_id']}"
        subtitle = self._join_parts(item.get("counterparty_name"), item.get("title"))
        amount = f"{item.get('amount')} {item.get('currency')}" if item.get("amount") is not None else None
        meta = self._join_parts(
            item.get("organization_name"),
            item.get("account_name"),
            amount,
            item.get("matched_status"),
            item.get("booking_date"),
        )
        return self._result_item(
            entity_type="billing_transaction",
            entity_id=item["billing_transaction_id"],
            organization_id=item.get("organization_id"),
            view="billing",
            section="billing-transaction-table-body",
            category="Rozliczenia: transakcje",
            badge=f"#{item['billing_transaction_id']}",
            title=title,
            subtitle=subtitle,
            meta=meta,
        )

    def _serialize_log(self, item: dict[str, Any]) -> dict[str, Any]:
        subtitle = self._join_parts(item.get("actor"), item.get("decision_reason"))
        meta = self._join_parts(item.get("organization_name"), item.get("event_type"), item.get("event_time"))
        return self._result_item(
            entity_type="log",
            entity_id=item["id"],
            organization_id=item.get("organization_id"),
            view="logs",
            section="log-table-body",
            category="Historia systemu",
            badge=f"#{item['id']}",
            title=item.get("event_type") or f"Log #{item['id']}",
            subtitle=subtitle,
            meta=meta,
        )

    def _serialize_user(self, item: dict[str, Any]) -> dict[str, Any]:
        subtitle = self._join_parts(item.get("display_name"), item.get("organization_name"))
        meta = self._join_parts(item.get("role"), "aktywne" if item.get("is_active") else "nieaktywne", item.get("last_login_at"))
        return self._result_item(
            entity_type="user",
            entity_id=item["user_id"],
            organization_id=item.get("organization_id"),
            view="users",
            category="Uzytkownicy",
            badge=f"#{item['user_id']}",
            title=item.get("login") or f"Uzytkownik #{item['user_id']}",
            subtitle=subtitle,
            meta=meta,
        )

    def _serialize_organization(self, item: dict[str, Any]) -> dict[str, Any]:
        meta = self._join_parts(
            item.get("slug"),
            item.get("email_inbox_address"),
            "aktywna" if item.get("is_active") else "nieaktywna",
        )
        return self._result_item(
            entity_type="organization",
            entity_id=item["organization_id"],
            organization_id=item.get("organization_id"),
            view="organizations",
            category="Organizacje",
            badge=f"#{item['organization_id']}",
            title=item.get("name") or f"Organizacja #{item['organization_id']}",
            subtitle=f"uzytkownicy: {item.get('user_count', 0)} | faktury: {item.get('invoice_count', 0)}",
            meta=meta,
        )

    def _result_item(
        self,
        *,
        entity_type: str,
        entity_id: Any,
        organization_id: Any,
        view: str,
        category: str,
        badge: str,
        title: str,
        subtitle: str | None,
        meta: str | None,
        section: str | None = None,
    ) -> dict[str, Any]:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "organization_id": organization_id,
            "view": view,
            "section": section,
            "category": category,
            "badge": badge,
            "title": title,
            "subtitle": subtitle or "",
            "meta": meta or "",
        }

    def _build_scope_label(self, actor_user: dict[str, Any], organization_id: int | None) -> str:
        if actor_user.get("is_global_admin"):
            if organization_id is None:
                return "Wszystkie organizacje"
            organization = self.organization_repository.get_by_id(int(organization_id))
            return organization["name"] if organization else "Wybrana organizacja"
        return str(actor_user.get("organization_name") or "Twoja organizacja")

    def _alias_matches(self, normalized_query: str, alias: str) -> bool:
        normalized_alias = self._normalize_search_text(alias)
        return bool(normalized_alias) and (
            normalized_query in normalized_alias or normalized_alias in normalized_query
        )

    def _normalize_search_text(self, value: Any) -> str:
        ascii_value = (
            unicodedata.normalize("NFKD", str(value or ""))
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )
        return re.sub(r"[^a-z0-9]+", " ", ascii_value).strip()

    def _join_parts(self, *values: Any) -> str:
        parts = [str(value).strip() for value in values if str(value or "").strip()]
        return " | ".join(parts)
