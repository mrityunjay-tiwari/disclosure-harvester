from __future__ import annotations

from harvester.load.database import Database
from harvester.models import ValidatedHolding
from harvester.utils import new_id


class Publisher:
    def __init__(self, db: Database):
        self.db = db

    def publish(self, holdings: list[ValidatedHolding]) -> int:
        published = 0
        for holding in holdings:
            existing = self.db.fetchone(
                """
                select holding_id, quantity, market_value, percentage_to_nav, source_file_id
                from published_holdings
                where amc_name = ?
                  and scheme_name = ?
                  and period = ?
                  and document_type = ?
                  and holding_business_key = ?
                  and is_current = true
                """,
                [
                    holding.amc_name,
                    holding.scheme_name,
                    holding.period,
                    holding.document_type,
                    holding.holding_business_key,
                ],
            )
            if existing:
                existing_values = tuple(existing[1:4])
                incoming_values = (holding.quantity, holding.market_value, holding.percentage_to_nav)
                if existing_values == incoming_values:
                    continue
                self.db.execute(
                    """
                    update published_holdings
                    set is_current = false,
                        superseded_by_file_id = ?
                    where holding_id = ?
                    """,
                    [holding.source_file_id, existing[0]],
                )
            self.db.execute(
                """
                insert into published_holdings
                (holding_id, amc_name, scheme_name, period, document_type, holding_business_key,
                 isin, security_name, asset_type, quantity, market_value, percentage_to_nav,
                 source_file_id, source_sha256, is_current)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, true)
                """,
                [
                    new_id("holding"),
                    holding.amc_name,
                    holding.scheme_name,
                    holding.period,
                    holding.document_type,
                    holding.holding_business_key,
                    holding.isin,
                    holding.security_name,
                    holding.asset_type,
                    holding.quantity,
                    holding.market_value,
                    holding.percentage_to_nav,
                    holding.source_file_id,
                    holding.source_sha256,
                ],
            )
            published += 1
        return published
