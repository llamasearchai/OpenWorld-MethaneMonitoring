from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from ..core.logging import get_logger, log_error_with_context
from ..models import EmissionRecord
from ..persistence.store import Store

IngestFunc = Callable[[], Iterable[EmissionRecord]]
ProcessFunc = Callable[[Iterable[EmissionRecord]], Iterable[EmissionRecord]]


@dataclass
class Orchestrator:
    """Simple data processing orchestrator.

    Pulls from an ingestion source, applies zero or more processors, and persists to a store.
    Retries on failure with exponential backoff (bounded).
    """

    store: Store
    ingest: IngestFunc
    processors: list[ProcessFunc]
    max_retries: int = 3

    def __post_init__(self):
        self.logger = get_logger("core.orchestrator")

    def run_once(self) -> int:
        """Run one ingestion and processing cycle.
        
        Returns:
            Number of records successfully processed and stored.
            
        Raises:
            Various exceptions from ingestion, processing, or storage operations.
        """
        try:
            records = list(self.ingest())
            self.logger.info("Ingested records", extra={"record_count": len(records)})

            for i, proc in enumerate(self.processors):
                initial_count = len(records)
                records = list(proc(records))
                self.logger.debug(
                    "Applied processor",
                    extra={
                        "processor_index": i,
                        "input_count": initial_count,
                        "output_count": len(records)
                    }
                )

            count = self.store.append(records)
            self.logger.info("Stored records", extra={"stored_count": count})
            return count

        except Exception as e:
            log_error_with_context(
                self.logger,
                "Error in orchestrator run_once",
                exception=e,
                processor_count=len(self.processors)
            )
            raise

    def run_with_retries(self) -> int:
        """Run with exponential backoff retry logic.
        
        Returns:
            Number of records successfully processed and stored.
            
        Raises:
            The last exception encountered if all retries are exhausted.
        """
        attempt = 0
        delay = 1.0
        last_exception = None

        while True:
            try:
                result = self.run_once()
                if attempt > 0:
                    self.logger.info(
                        "Orchestrator succeeded after retries",
                        extra={"attempt": attempt + 1, "total_attempts": attempt + 1}
                    )
                return result

            except (ConnectionError, OSError) as e:
                # Specific exceptions that make sense to retry
                last_exception = e
                attempt += 1
                if attempt > self.max_retries:
                    log_error_with_context(
                        self.logger,
                        "Orchestrator failed after all retries",
                        exception=e,
                        max_retries=self.max_retries,
                        total_attempts=attempt
                    )
                    raise

                self.logger.warning(
                    "Orchestrator retry",
                    extra={
                        "attempt": attempt,
                        "max_retries": self.max_retries,
                        "delay": delay,
                        "error": str(e)
                    }
                )
                time.sleep(delay)
                delay = min(delay * 2, 30.0)

            except Exception as e:
                # Don't retry for unexpected exceptions
                log_error_with_context(
                    self.logger,
                    "Orchestrator failed with non-retryable error",
                    exception=e,
                    attempt=attempt + 1
                )
                raise
