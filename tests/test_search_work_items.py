from __future__ import annotations

import unittest

from tests.search_test_support import SearchServiceTestCase


class SearchWorkItemsTests(SearchServiceTestCase):
    def test_search_returns_work_items_group_for_sla_queries(self) -> None:
        casi = self.organization_repository.get_by_slug("casi")
        self.assertIsNotNone(casi)
        assert casi is not None
        organization_id = int(casi["organization_id"])
        actor_user = self.users_by_login["casi_admin"]

        self.services["work_item_service"].create_work_item(
            {
                "title": "Pilna eskalacja SLA dla klienta CASI",
                "source_type": "support",
                "status": "w_toku",
                "priority_level": "wysoki",
                "sla_deadline_at": "2099-04-10T09:00",
            },
            actor_user=actor_user,
            actor="CASI Admin",
            organization_id=organization_id,
        )

        result = self.search_service.search(
            "eskalacja sla casi",
            actor_user=actor_user,
            organization_id=organization_id,
        )
        work_item_items = [
            item
            for group in result["groups"]
            if group["key"] == "work_items"
            for item in group["items"]
        ]
        self.assertTrue(work_item_items)
        self.assertTrue(any("Pilna eskalacja SLA dla klienta CASI" in item["title"] for item in work_item_items))


if __name__ == "__main__":
    unittest.main()
