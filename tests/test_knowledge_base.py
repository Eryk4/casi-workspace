from __future__ import annotations

import unittest
from pathlib import Path
import shutil
from io import BytesIO
import zipfile

from app.bootstrap import build_services
from app.config import KNOWLEDGE_DIR
from app.db import reset_database
from app.services.knowledge_service import KnowledgeError


class KnowledgeBaseTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        shutil.rmtree(KNOWLEDGE_DIR, ignore_errors=True)
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.organization_service = self.services["organization_service"]
        self.organization_repository = self.services["organization_repository"]
        self.knowledge_service = self.services["knowledge_service"]
        self.auth_service.ensure_default_admin()
        self.admin = self.auth_service.list_users()[0]
        self.default_org = self.organization_repository.get_by_slug("organizacja-domyslna")
        if self.default_org is None:
            self.organization_service.create_organization(
                {"name": "organizacja-domyslna", "slug": "organizacja-domyslna", "is_active": 1},
                actor_user=self.admin,
                actor_login="admin",
            )
            self.default_org = self.organization_repository.get_by_slug("organizacja-domyslna")
        assert self.default_org is not None

    def test_answers_are_scoped_to_selected_organization(self) -> None:
        beta_org = self.organization_service.create_organization(
            {"name": "Klient Beta", "slug": "klient-beta", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )

        self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Polityka urlopowa",
            actor_user=self.admin,
            actor="admin",
            file_name="urlopy.txt",
            content_text="Wniosek urlopowy trzeba wysłać minimum 7 dni przed planowanym terminem.",
        )
        self.knowledge_service.add_document(
            organization_id=int(beta_org["organization_id"]),
            title="Delegacje Beta",
            actor_user=self.admin,
            actor="admin",
            file_name="delegacje_beta.txt",
            content_text="W organizacji Beta delegację krajową zatwierdza dyrektor operacyjny.",
        )

        beta_answer = self.knowledge_service.answer_question(
            "Kto zatwierdza delegację krajową?",
            organization_id=int(beta_org["organization_id"]),
        )
        default_answer = self.knowledge_service.answer_question(
            "Kiedy wysłać wniosek urlopowy?",
            organization_id=int(self.default_org["organization_id"]),
        )

        self.assertEqual(beta_answer["organization_name"], "Klient Beta")
        self.assertTrue(beta_answer["matches"])
        self.assertEqual(beta_answer["matches"][0]["title"], "Delegacje Beta")
        self.assertIn("dyrektor operacyjny", beta_answer["answer"])
        self.assertIn("7 dni", default_answer["answer"])

    def test_sync_imports_files_from_designated_folder(self) -> None:
        beta_org = self.organization_service.create_organization(
            {"name": "Klient Beta", "slug": "klient-beta", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        org_folder = KNOWLEDGE_DIR / "organizacje" / "klient-beta"
        org_folder.mkdir(parents=True, exist_ok=True)
        source_file = org_folder / "procedura_urlopowa.txt"
        source_file.write_text(
            "W organizacji Beta urlop okolicznościowy zgłasza się bezpośrednio do lidera zespołu.",
            encoding="utf-8",
        )

        wynik = self.knowledge_service.sync_folder(
            organization_id=int(beta_org["organization_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        lista = self.knowledge_service.list_documents(int(beta_org["organization_id"]))
        odpowiedz = self.knowledge_service.answer_question(
            "Do kogo zgłosić urlop okolicznościowy?",
            organization_id=int(beta_org["organization_id"]),
        )

        self.assertEqual(wynik["imported_count"], 1)
        self.assertEqual(wynik["updated_count"], 0)
        self.assertEqual(Path(wynik["folder_path"]), org_folder)
        self.assertEqual(len(lista["documents"]), 1)
        self.assertEqual(lista["documents"][0]["file_name"], "procedura_urlopowa.txt")
        self.assertIn("lidera zespołu", odpowiedz["answer"])

    def test_documents_can_be_storage_only_and_are_grouped_by_folder(self) -> None:
        created = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Wzor aneksu",
            actor_user=self.admin,
            actor="admin",
            file_name="wzor_aneksu.txt",
            content_text="Wzor aneksu do umowy. Pola: strony, zakres zmian, data wejscia w zycie.",
            library_path="Wzory/Umowy",
            is_downloadable=True,
            use_in_assistant=False,
        )

        listing = self.knowledge_service.list_documents(int(self.default_org["organization_id"]))
        answer = self.knowledge_service.answer_question(
            "Jakie pola ma wzor aneksu?",
            organization_id=int(self.default_org["organization_id"]),
        )

        self.assertEqual(created["library_path"], "Wzory/Umowy")
        self.assertTrue(created["is_downloadable"])
        self.assertFalse(created["use_in_assistant"])
        self.assertTrue(any(item["path"] == "Wzory/Umowy" for item in listing["folder_summary"]))
        self.assertIn("nie ma jeszcze gotowych dokument", answer["answer"].lower())

    def test_sync_builds_library_path_from_nested_folder(self) -> None:
        beta_org = self.organization_service.create_organization(
            {"name": "Klient Foldery", "slug": "klient-foldery", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        nested_folder = KNOWLEDGE_DIR / "organizacje" / "klient-foldery" / "Wzory" / "HR"
        nested_folder.mkdir(parents=True, exist_ok=True)
        source_file = nested_folder / "wniosek_urlopowy.txt"
        source_file.write_text("Wzor wniosku urlopowego dla pracownikow etatowych.", encoding="utf-8")

        self.knowledge_service.sync_folder(
            organization_id=int(beta_org["organization_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        self.knowledge_service.process_pending_jobs(limit=4)
        listing = self.knowledge_service.list_documents(int(beta_org["organization_id"]))

        self.assertEqual(listing["documents"][0]["library_path"], "Wzory/HR")
        self.assertEqual(listing["documents"][0]["library_path_label"], "Wzory / HR")

    def test_pipeline_tracks_document_status_versions_and_citations(self) -> None:
        beta_org = self.organization_service.create_organization(
            {"name": "Klient Pipeline", "slug": "klient-pipeline", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        org_folder = KNOWLEDGE_DIR / "organizacje" / "klient-pipeline"
        org_folder.mkdir(parents=True, exist_ok=True)
        source_file = org_folder / "procedura_delegacji.txt"
        source_file.write_text(
            "Delegacje w organizacji Pipeline zatwierdza kierownik operacyjny.",
            encoding="utf-8",
        )

        queued = self.knowledge_service.sync_folder(
            organization_id=int(beta_org["organization_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        queued_document = self.knowledge_service.list_documents(int(beta_org["organization_id"]))["documents"][0]

        self.assertEqual(queued["imported_count"], 1)
        self.assertEqual(queued_document["processing_status"], "queued")
        self.assertEqual(queued_document["current_version_number"], 0)
        self.assertTrue(any(job["status"] == "pending" for job in queued_document["recent_jobs"]))

        processed = self.knowledge_service.process_pending_jobs(limit=2)
        ready_document = self.knowledge_service.list_documents(int(beta_org["organization_id"]))["documents"][0]
        answer = self.knowledge_service.answer_question(
            "Kto zatwierdza delegacje?",
            organization_id=int(beta_org["organization_id"]),
        )

        self.assertEqual(processed["processed_count"], 1)
        self.assertEqual(ready_document["processing_status"], "ready")
        self.assertEqual(ready_document["current_version_number"], 1)
        self.assertEqual(ready_document["versions"][0]["version_number"], 1)
        self.assertIn("kierownik operacyjny", ready_document["content_preview"])
        self.assertIn("kierownik operacyjny", ready_document["versions"][0]["snippet"])
        self.assertIn("kierownik operacyjny", answer["answer"])
        self.assertIn("| v1", answer["matches"][0]["citation_label"])

        source_file.write_text(
            "Delegacje w organizacji Pipeline zatwierdza dyrektor finansowy.",
            encoding="utf-8",
        )
        updated = self.knowledge_service.sync_folder(
            organization_id=int(beta_org["organization_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        self.knowledge_service.process_pending_jobs(limit=2)
        updated_document = self.knowledge_service.list_documents(int(beta_org["organization_id"]))["documents"][0]
        updated_answer = self.knowledge_service.answer_question(
            "Kto zatwierdza delegacje?",
            organization_id=int(beta_org["organization_id"]),
        )

        self.assertEqual(updated["updated_count"], 1)
        self.assertEqual(updated_document["processing_status"], "ready")
        self.assertEqual(updated_document["current_version_number"], 2)
        self.assertEqual(
            [version["version_number"] for version in updated_document["versions"][:2]],
            [2, 1],
        )
        self.assertIn("dyrektor finansowy", updated_document["content_preview"])
        self.assertIn("dyrektor finansowy", updated_document["versions"][0]["snippet"])
        self.assertIn("dyrektor finansowy", updated_answer["answer"])
        self.assertIn("| v2", updated_answer["matches"][0]["citation_label"])

    def test_add_document_extracts_text_from_xlsx(self) -> None:
        xlsx_bytes = self._build_xlsx_bytes(
            [
                ["Temat", "Opis"],
                ["Delegacje", "Delegacje zatwierdza kierownik operacyjny."],
            ]
        )

        created = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Macierz kompetencji",
            actor_user=self.admin,
            actor="admin",
            file_name="macierz.xlsx",
            file_bytes=xlsx_bytes,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        odpowiedz = self.knowledge_service.answer_question(
            "Kto zatwierdza delegacje?",
            organization_id=int(self.default_org["organization_id"]),
        )

        self.assertEqual(created["file_name"], "macierz.xlsx")
        self.assertIn("kierownik operacyjny", odpowiedz["answer"])

    def test_add_document_uses_ocr_for_images(self) -> None:
        class FakeOcrEngine:
            def integration_status(self) -> dict[str, object]:
                return {"enabled": True, "mode": "tesseract"}

            def extract_text(self, file_name: str, file_bytes: bytes | None = None) -> str:
                return "Instrukcja obiegu dokumentow. Wnioski akceptuje dyrektor finansowy."

        self.knowledge_service.ocr_engine = FakeOcrEngine()

        created = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Skan procedury",
            actor_user=self.admin,
            actor="admin",
            file_name="procedura.png",
            file_bytes=b"\x89PNG\r\n",
            mime_type="image/png",
        )
        odpowiedz = self.knowledge_service.answer_question(
            "Kto akceptuje wnioski?",
            organization_id=int(self.default_org["organization_id"]),
        )

        self.assertEqual(created["file_name"], "procedura.png")
        self.assertIn("dyrektor finansowy", odpowiedz["answer"])

    def test_document_lifecycle_replace_restore_and_watch_status_are_preserved(self) -> None:
        created = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Procedura obiegu",
            actor_user=self.admin,
            actor="admin",
            file_name="procedura.txt",
            content_text="Wersja pierwsza. Wnioski akceptuje kierownik operacyjny.",
            library_path="Procedury/HR",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.knowledge_service.process_pending_jobs(limit=2)

        replaced = self.knowledge_service.replace_document_file(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
            file_name="procedura_v2.txt",
            file_bytes=b"Wersja druga. Wnioski akceptuje dyrektor finansowy.",
            mime_type="text/plain",
        )
        self.assertEqual(replaced["processing_status"], "queued")
        self.knowledge_service.process_pending_jobs(limit=2)

        archived = self.knowledge_service.archive_document(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        self.assertEqual(archived["lifecycle_status"], "archived")

        deleted = self.knowledge_service.delete_document(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        self.assertEqual(deleted["lifecycle_status"], "deleted")

        restored = self.knowledge_service.restore_document(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        self.assertEqual(restored["lifecycle_status"], "active")

        restored_version = self.knowledge_service.restore_document_version(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            version_number=1,
            actor_user=self.admin,
            actor="admin",
        )
        self.assertEqual(restored_version["processing_status"], "queued")
        self.knowledge_service.process_pending_jobs(limit=2)

        listing = self.knowledge_service.list_documents(int(self.default_org["organization_id"]), include_deleted=True)
        final_document = listing["documents"][0]

        self.assertEqual(final_document["lifecycle_status"], "active")
        self.assertEqual(final_document["current_version_number"], 3)
        self.assertEqual(final_document["library_path"], "Procedury/HR")
        self.assertEqual(
            [item["version_number"] for item in final_document["versions"][:3]],
            [3, 2, 1],
        )
        self.assertEqual(listing["watch_status"]["watch_mode"], "polling")
        self.assertIn("kierownik operacyjny", final_document["content_preview"])

    def test_document_detail_includes_audit_history_and_download_summary(self) -> None:
        created = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Wzor polityki rabatowej",
            actor_user=self.admin,
            actor="admin",
            file_name="polityka_rabatowa.txt",
            content_text="Rabaty powyzej 15 procent akceptuje dyrektor handlowy.",
            library_path="Wzory/Sprzedaz",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.knowledge_service.process_pending_jobs(limit=2)
        self.knowledge_service.archive_document(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        self.knowledge_service.restore_document(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
        )
        self.knowledge_service.record_document_download(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
        )

        detail = self.knowledge_service.get_document_detail(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
        )

        self.assertIn("audit_events", detail)
        self.assertIn("audit_summary", detail)
        self.assertGreaterEqual(detail["audit_summary"]["event_count"], 5)
        self.assertEqual(detail["audit_summary"]["download_count"], 1)
        event_types = [item["event_type"] for item in detail["audit_events"]]
        self.assertIn("knowledge_document_created", event_types)
        self.assertIn("knowledge_document_updated", event_types)
        self.assertIn("knowledge_document_archived", event_types)
        self.assertIn("knowledge_document_restored", event_types)
        self.assertIn("knowledge_document_downloaded", event_types)
        self.assertTrue(any(item["action_label"] == "Pobranie pliku" for item in detail["audit_events"]))

    def test_document_can_track_official_version_and_comments_per_version(self) -> None:
        created = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Polityka obiegu umow",
            actor_user=self.admin,
            actor="admin",
            file_name="polityka_umowy.txt",
            content_text=(
                "Wersja pierwsza.\n"
                "Umowy zatwierdza dyrektor operacyjny.\n"
                "Po akceptacji dokument trafia do podpisu."
            ),
            library_path="Wzory/Umowy",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.knowledge_service.process_pending_jobs(limit=2)
        self.knowledge_service.replace_document_file(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
            file_name="polityka_umowy_v2.txt",
            file_bytes=(
                "Wersja druga.\n"
                "Umowy zatwierdza dyrektor finansowy.\n"
                "Po akceptacji dokument trafia do podpisu i rejestru wzorow."
            ).encode("utf-8"),
            mime_type="text/plain",
        )
        self.knowledge_service.process_pending_jobs(limit=2)

        detail_before_mark = self.knowledge_service.get_document_detail(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
        )

        self.assertEqual(detail_before_mark["current_version_number"], 2)
        self.assertEqual(detail_before_mark["official_version_number"], 0)
        self.assertEqual(detail_before_mark["workflow_status"], "official_missing")
        self.assertEqual(detail_before_mark["business_status"], "roboczy")
        self.assertTrue(detail_before_mark["versions"][0]["is_current"])
        self.assertFalse(detail_before_mark["versions"][0]["is_official"])
        self.assertFalse(detail_before_mark["versions"][1]["is_official"])

        marked = self.knowledge_service.mark_document_official_version(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            version_number=2,
            actor_user=self.admin,
            actor="admin",
        )
        commented = self.knowledge_service.add_document_comment(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            note_text="To jest wersja do wdrozenia od przyszlego tygodnia.",
            version_number=2,
            annotation_kind="annotation",
            anchor_label="sekcja akceptacji",
            actor_user=self.admin,
            actor="admin",
        )
        commented = self.knowledge_service.add_document_comment(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            note_text="Warto jeszcze dopisac osobe rezerwowa dla podpisu.",
            actor_user=self.admin,
            actor="admin",
        )

        self.assertEqual(marked["official_version_number"], 2)
        self.assertEqual(marked["business_status"], "obowiazujacy")
        self.assertTrue(marked["versions"][0]["is_official"])
        self.assertEqual(commented["comment_summary"]["comment_count"], 2)
        self.assertEqual(commented["comment_summary"]["version_comment_count"], 1)
        self.assertEqual(commented["comment_summary"]["document_comment_count"], 1)
        self.assertEqual(commented["comments"][0]["target_label"], "Dokument")
        self.assertEqual(commented["comments"][1]["target_label"], "Wersja v2")
        self.assertEqual(commented["comments"][1]["annotation_kind"], "annotation")
        self.assertEqual(commented["comments"][1]["anchor_label"], "sekcja akceptacji")
        self.assertEqual(commented["versions"][0]["comment_count"], 1)
        self.assertEqual(commented["official_version_number"], 2)
        event_types = [item["event_type"] for item in commented["audit_events"]]
        self.assertIn("knowledge_document_official_version_marked", event_types)
        self.assertIn("knowledge_document_comment_added", event_types)

    def test_list_documents_exposes_activity_feed_workflow_and_seen_marker(self) -> None:
        created = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Instrukcja wdrozenia",
            actor_user=self.admin,
            actor="admin",
            file_name="instrukcja_wdrozenia.txt",
            content_text="Wersja pierwsza. Akceptuje kierownik operacyjny.",
            library_path="Procedury/Wdrozenie",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.knowledge_service.process_pending_jobs(limit=2)
        self.knowledge_service.replace_document_file(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
            file_name="instrukcja_wdrozenia_v2.txt",
            file_bytes=b"Wersja druga. Akceptuje dyrektor finansowy.",
            mime_type="text/plain",
        )
        self.knowledge_service.process_pending_jobs(limit=2)
        self.knowledge_service.add_document_comment(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            note_text="To wymaga potwierdzenia przez dzial HR.",
            actor_user=self.admin,
            actor="admin",
        )

        listing = self.knowledge_service.list_documents(
            int(self.default_org["organization_id"]),
            viewer_user_id=int(self.admin["user_id"]),
        )

        self.assertEqual(listing["documents"][0]["workflow_status"], "official_missing")
        self.assertEqual(listing["documents"][0]["business_status"], "roboczy")
        self.assertEqual(listing["activity_summary"]["pending_review_count"], 1)
        self.assertGreaterEqual(listing["activity_summary"]["unread_count"], 1)
        self.assertTrue(any(item["event_type"] == "knowledge_document_comment_added" for item in listing["activity_feed"]))

        seen = self.knowledge_service.mark_activity_feed_seen(
            organization_id=int(self.default_org["organization_id"]),
            viewer_user_id=int(self.admin["user_id"]),
        )
        listing_after_seen = self.knowledge_service.list_documents(
            int(self.default_org["organization_id"]),
            viewer_user_id=int(self.admin["user_id"]),
        )

        self.assertEqual(seen["unread_count"], 0)
        self.assertEqual(listing_after_seen["activity_summary"]["unread_count"], 0)

    def test_document_business_workflow_and_responsibles_are_serialized_for_candidates_and_reviewers(self) -> None:
        organization = self.organization_service.create_organization(
            {"name": "Klient Obieg", "slug": "klient-obieg", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        reviewer = self.auth_service.create_user(
            {
                "login": "reviewer-obieg",
                "display_name": "Rita Review",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        approver = self.auth_service.create_user(
            {
                "login": "approver-obieg",
                "display_name": "Adam Akceptacja",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        document = self.knowledge_service.add_document(
            organization_id=int(organization["organization_id"]),
            title="Procedura obiegu faktur",
            actor_user=self.admin,
            actor="admin",
            file_name="procedura_obiegu_faktur.txt",
            content_text="Wersja pierwsza. Dokument ma przejsc przez review i akceptacje.",
            library_path="Procedury/Faktury",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.knowledge_service.process_pending_jobs(limit=2)

        updated = self.knowledge_service.update_document_metadata(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
            business_status="do_sprawdzenia",
            reviewer_user_id=int(reviewer["user_id"]),
            approver_user_id=int(approver["user_id"]),
        )
        candidates = self.knowledge_service.list_assignment_candidates(int(organization["organization_id"]))
        reviewer_listing = self.knowledge_service.list_documents(
            int(organization["organization_id"]),
            viewer_user_id=int(reviewer["user_id"]),
        )
        detail = self.knowledge_service.get_document_detail(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
        )

        self.assertEqual(updated["business_status"], "do_sprawdzenia")
        self.assertEqual(updated["reviewer_user_id"], int(reviewer["user_id"]))
        self.assertEqual(updated["approver_user_id"], int(approver["user_id"]))
        self.assertEqual(updated["reviewer_user_label"], "Rita Review")
        self.assertEqual(updated["approver_user_label"], "Adam Akceptacja")
        self.assertTrue(any(int(item["user_id"]) == int(reviewer["user_id"]) for item in candidates))
        self.assertTrue(any(int(item["user_id"]) == int(approver["user_id"]) for item in candidates))
        self.assertEqual(reviewer_listing["documents"][0]["business_status"], "do_sprawdzenia")
        self.assertEqual(reviewer_listing["activity_summary"]["pending_decision_count"], 1)
        self.assertEqual(reviewer_listing["activity_summary"]["awaiting_review_count"], 1)
        self.assertEqual(reviewer_listing["activity_summary"]["my_review_count"], 1)
        self.assertEqual(reviewer_listing["activity_summary"]["my_attention_count"], 1)
        self.assertTrue(
            any(item["event_type"] == "knowledge_document_workflow_updated" for item in reviewer_listing["activity_feed"])
        )
        self.assertTrue(
            any(item["event_type"] == "knowledge_document_assignments_updated" for item in detail["audit_events"])
        )

    def test_document_decision_flow_requires_reason_and_progresses_between_review_and_approval(self) -> None:
        organization = self.organization_service.create_organization(
            {"name": "Klient Decyzje", "slug": "klient-decyzje", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        owner = self.auth_service.create_user(
            {
                "login": "owner-decyzje",
                "display_name": "Olga Owner",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        reviewer = self.auth_service.create_user(
            {
                "login": "reviewer-decyzje",
                "display_name": "Rafal Review",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        approver = self.auth_service.create_user(
            {
                "login": "approver-decyzje",
                "display_name": "Ada Approval",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        document = self.knowledge_service.add_document(
            organization_id=int(organization["organization_id"]),
            title="Procedura decyzji dokumentu",
            actor_user=self.admin,
            actor="admin",
            file_name="procedura_decyzji.txt",
            content_text="Wersja pierwsza procedury. Dokument ma przejsc review i akceptacje.",
            library_path="Procedury/Operacje",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.knowledge_service.process_pending_jobs(limit=2)
        self.knowledge_service.update_document_metadata(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
            owner_user_id=int(owner["user_id"]),
            reviewer_user_id=int(reviewer["user_id"]),
            approver_user_id=int(approver["user_id"]),
        )

        owner_listing = self.knowledge_service.list_documents(
            int(organization["organization_id"]),
            viewer_user_id=int(owner["user_id"]),
        )
        owner_actions = {
            item["code"]: item for item in owner_listing["documents"][0]["decision_actions"]
        }
        self.assertEqual(owner_actions["send_for_review"]["required_assignments"], ["reviewer_user_id"])
        self.assertTrue(owner_actions["send_for_review"]["requires_reason"])
        self.assertTrue(owner_actions["send_for_review"]["hint"])

        with self.assertRaises(KnowledgeError):
            self.knowledge_service.decide_document_workflow(
                organization_id=int(organization["organization_id"]),
                knowledge_document_id=int(document["knowledge_document_id"]),
                action="send_for_review",
                reason="   ",
                actor_user=owner,
                actor="owner-decyzje",
            )

        review_step = self.knowledge_service.decide_document_workflow(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            action="send_for_review",
            reason="Dokument jest gotowy do sprawdzenia przez review.",
            actor_user=owner,
            actor="owner-decyzje",
        )
        approval_step = self.knowledge_service.decide_document_workflow(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            action="send_for_approval",
            reason="Review zakonczony, przekazuje do akceptacji.",
            actor_user=reviewer,
            actor="reviewer-decyzje",
        )
        approved = self.knowledge_service.decide_document_workflow(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            action="approve",
            reason="Wersja jest zatwierdzona do pracy operacyjnej.",
            actor_user=approver,
            actor="approver-decyzje",
        )

        self.assertEqual(review_step["business_status"], "do_sprawdzenia")
        self.assertEqual(approval_step["business_status"], "do_akceptacji")
        self.assertEqual(approved["business_status"], "obowiazujacy")
        self.assertEqual(approved["official_version_number"], 1)
        self.assertEqual(approved["workflow_status"], "stable")
        self.assertGreaterEqual(approved["comment_summary"]["comment_count"], 3)
        event_types = [item["event_type"] for item in approved["audit_events"]]
        self.assertIn("knowledge_document_decision_taken", event_types)
        self.assertIn("knowledge_document_comment_added", event_types)
        self.assertIn("knowledge_document_official_version_marked", event_types)

    def test_compare_document_versions_returns_structured_diff_summary(self) -> None:
        created = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Instrukcja obiegu umow",
            actor_user=self.admin,
            actor="admin",
            file_name="instrukcja_umowy.txt",
            content_text=(
                "Krok 1: przygotuj projekt umowy.\n"
                "Krok 2: akceptacja przez dzial prawny.\n"
                "Krok 3: wysylka do klienta."
            ),
            library_path="Procedury/Umowy",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.knowledge_service.process_pending_jobs(limit=2)
        self.knowledge_service.replace_document_file(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            actor_user=self.admin,
            actor="admin",
            file_name="instrukcja_umowy_v2.txt",
            file_bytes=(
                "Krok 1: przygotuj projekt umowy.\n"
                "Krok 2: akceptacja przez dzial prawny i dzial handlowy.\n"
                "Krok 3: wysylka do klienta.\n"
                "Krok 4: zapis do CRM."
            ).encode("utf-8"),
            mime_type="text/plain",
        )
        self.knowledge_service.process_pending_jobs(limit=2)

        comparison = self.knowledge_service.compare_document_versions(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_id=int(created["knowledge_document_id"]),
            left_version_number=2,
            right_version_number=1,
        )

        self.assertEqual(comparison["left_version"]["version_number"], 2)
        self.assertEqual(comparison["right_version"]["version_number"], 1)
        self.assertEqual(comparison["target_version"]["version_number"], 2)
        self.assertEqual(comparison["base_version"]["version_number"], 1)
        self.assertGreaterEqual(comparison["summary"]["added_line_count"], 1)
        self.assertGreaterEqual(comparison["summary"]["removed_line_count"], 1)
        self.assertGreaterEqual(comparison["summary"]["changed_block_count"], 1)
        self.assertEqual(comparison["summary"]["comparison_basis"], "older_to_newer")
        self.assertIn("v2", comparison["change_summary"]["overview"])
        self.assertTrue(comparison["change_summary"]["added_topics"])
        self.assertTrue(comparison["side_by_side_rows"])
        self.assertTrue(any(item["type"] == "changed" for item in comparison["side_by_side_rows"]))
        block_types = [item["type"] for item in comparison["blocks"]]
        self.assertIn("added", block_types)
        self.assertIn("removed", block_types)

    def test_bulk_update_documents_moves_selected_records_and_reports_failures(self) -> None:
        created_one = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Wzor NDA",
            actor_user=self.admin,
            actor="admin",
            file_name="wzor_nda.txt",
            content_text="Paragraf 1: strony umowy.\nParagraf 2: poufnosc.",
            library_path="Wzory/Prawne",
            is_downloadable=True,
            use_in_assistant=False,
        )
        created_two = self.knowledge_service.add_document(
            organization_id=int(self.default_org["organization_id"]),
            title="Wzor zamowienia",
            actor_user=self.admin,
            actor="admin",
            file_name="wzor_zamowienia.txt",
            content_text="Sekcja 1: dane klienta.\nSekcja 2: zakres prac.",
            library_path="Wzory/Sprzedaz",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.knowledge_service.process_pending_jobs(limit=4)

        result = self.knowledge_service.bulk_update_documents(
            organization_id=int(self.default_org["organization_id"]),
            knowledge_document_ids=[
                int(created_one["knowledge_document_id"]),
                int(created_two["knowledge_document_id"]),
                999999,
            ],
            action="move_folder",
            actor_user=self.admin,
            actor="admin",
            library_path="Wzory/Aktualne",
        )

        self.assertEqual(result["action"], "move_folder")
        self.assertEqual(result["succeeded_count"], 2)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(result["skipped_count"], 0)
        self.assertEqual(result["target_library_path"], "Wzory/Aktualne")
        documents = self.knowledge_service.list_documents(int(self.default_org["organization_id"]), include_deleted=True)["documents"]
        updated_paths = {
            int(item["knowledge_document_id"]): item["library_path"]
            for item in documents
            if int(item["knowledge_document_id"]) in {int(created_one["knowledge_document_id"]), int(created_two["knowledge_document_id"])}
        }
        self.assertEqual(updated_paths[int(created_one["knowledge_document_id"])], "Wzory/Aktualne")
        self.assertEqual(updated_paths[int(created_two["knowledge_document_id"])], "Wzory/Aktualne")
        self.assertIn("Nie znaleziono dokumentu", result["failed"][0]["message"])

    def _build_xlsx_bytes(self, rows: list[list[str]]) -> bytes:
        shared_strings: list[str] = []
        shared_index: dict[str, int] = {}
        sheet_rows: list[str] = []

        for row_number, values in enumerate(rows, start=1):
            cells: list[str] = []
            for column_number, value in enumerate(values, start=1):
                if value not in shared_index:
                    shared_index[value] = len(shared_strings)
                    shared_strings.append(value)
                cell_ref = f"{chr(64 + column_number)}{row_number}"
                cells.append(f'<c r="{cell_ref}" t="s"><v>{shared_index[value]}</v></c>')
            sheet_rows.append(f"<row r=\"{row_number}\">{''.join(cells)}</row>")

        shared_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<sst xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\""
            f" count=\"{len(shared_strings)}\" uniqueCount=\"{len(shared_strings)}\">"
            + "".join(f"<si><t>{value}</t></si>" for value in shared_strings)
            + "</sst>"
        )
        sheet_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            "<sheetData>"
            + "".join(sheet_rows)
            + "</sheetData></worksheet>"
        )
        workbook_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
            "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
            "<sheets><sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>"
        )
        workbook_rels_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" "
            "Target=\"worksheets/sheet1.xml\"/>"
            "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings\" "
            "Target=\"sharedStrings.xml\"/>"
            "</Relationships>"
        )
        root_rels_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" "
            "Target=\"xl/workbook.xml\"/>"
            "</Relationships>"
        )
        content_types_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
            "<Override PartName=\"/xl/workbook.xml\" "
            "ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
            "<Override PartName=\"/xl/worksheets/sheet1.xml\" "
            "ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
            "<Override PartName=\"/xl/sharedStrings.xml\" "
            "ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml\"/>"
            "</Types>"
        )

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types_xml)
            archive.writestr("_rels/.rels", root_rels_xml)
            archive.writestr("xl/workbook.xml", workbook_xml)
            archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
            archive.writestr("xl/sharedStrings.xml", shared_xml)
            archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
