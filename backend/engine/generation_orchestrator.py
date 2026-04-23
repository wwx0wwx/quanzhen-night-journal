from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.llm_adapter import LLMAdapter
from backend.engine.config_store import ConfigStore
from backend.engine.context_builder import ContextBuilder
from backend.engine.cost_monitor import CostMonitor
from backend.engine.digital_stamp import DigitalStampGenerator
from backend.engine.memory_engine import MemoryEngine
from backend.engine.notification_manager import NotificationManager
from backend.engine.persona_engine import PersonaEngine
from backend.engine.prompt_builder import PromptBuilder
from backend.engine.qa_engine import QAEngine
from backend.engine.task_gate import TASK_GATE
from backend.models import Event, GenerationTask, Persona, Post
from backend.publisher.registry import PublisherRegistry
from backend.utils.audit import log_audit
from backend.utils.post_content import derive_summary, extract_title
from backend.utils.publish_decision import build_publish_decision
from backend.utils.serde import json_dumps, json_loads
from backend.utils.slug import slugify
from backend.utils.text_integrity import sanitize_plain_text
from backend.utils.time import utcnow_iso

logger = logging.getLogger(__name__)


class InvalidTransition(RuntimeError):
    pass


@dataclass(slots=True)
class ClassifiedError:
    code: str
    message: str
    severity: str = "warning"


class GenerationOrchestrator:
    VALID_TRANSITIONS = {
        "queued": ["preparing_context", "failed", "aborted"],
        "preparing_context": ["generating", "failed", "aborted"],
        "generating": ["qa_checking", "failed", "aborted"],
        "qa_checking": [
            "ready_to_publish",
            "waiting_human_signoff",
            "rewrite_pending",
            "circuit_open",
            "failed",
            "aborted",
        ],
        "rewrite_pending": ["generating", "failed", "aborted"],
        "waiting_human_signoff": ["ready_to_publish", "failed", "aborted"],
        "ready_to_publish": ["publishing", "failed", "aborted"],
        "publishing": ["published", "failed", "aborted"],
    }

    TERMINAL = {"published", "failed", "circuit_open", "aborted", "draft_saved"}

    def __init__(
        self,
        db: AsyncSession,
        config_store: ConfigStore,
        persona_engine: PersonaEngine,
        memory_engine: MemoryEngine,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        qa_engine: QAEngine,
        cost_monitor: CostMonitor,
        llm_adapter: LLMAdapter,
        notification_manager: NotificationManager,
        publisher_registry: PublisherRegistry,
        digital_stamp_generator: DigitalStampGenerator,
    ):
        self.db = db
        self.config_store = config_store
        self.persona_engine = persona_engine
        self.memory_engine = memory_engine
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.qa_engine = qa_engine
        self.cost_monitor = cost_monitor
        self.llm_adapter = llm_adapter
        self.notification_manager = notification_manager
        self.publisher_registry = publisher_registry
        self.digital_stamp_generator = digital_stamp_generator

    async def execute(self, event: Event, persona: Persona | None = None) -> GenerationTask:
        persona = persona or await self.persona_engine.get_active_persona()
        if persona is None:
            raise ValueError("no_active_persona")
        task = await self._create_task(event, persona)

        try:
            async with TASK_GATE.acquire(task.id) as grant:
                task.queue_wait_ms = grant.wait_ms
                self._append_trace(
                    task,
                    "queue_acquired",
                    initial_position=grant.initial_position,
                    wait_ms=grant.wait_ms,
                )
                await self.db.commit()
                await self.db.refresh(task)

                if task.status in self.TERMINAL:
                    self._append_trace(task, "queue_skipped", reason="task_already_terminal")
                    await self.db.commit()
                    return task

                budget = await self.cost_monitor.check_budget()
                if budget.is_hibernating:
                    self._append_trace(task, "budget_blocked", reason="budget_exhausted")
                    return await self._transition(
                        task,
                        "failed",
                        error="budget hibernation is active",
                        error_code="budget_exhausted",
                    )

                await self._transition(task, "preparing_context")
                context, snapshot = await self.context_builder.build(task, persona)
                task.context_snapshot = json_dumps(snapshot)
                task.memory_hits = json_dumps([item.model_dump() for item in context.memory_hits])
                task.sensory_snapshot_id = context.sensory_snapshot.id if context.sensory_snapshot else None
                task.cold_start = 1 if context.cold_start else 0
                task.anti_perfection = 1 if context.anti_perfection else 0

                prompt, prompt_summary = self.prompt_builder.build(context)
                task.prompt_summary = json_dumps(prompt_summary)
                self._append_trace(
                    task,
                    "context_prepared",
                    cold_start=bool(task.cold_start),
                    anti_perfection=bool(task.anti_perfection),
                    memory_hits=len(context.memory_hits),
                    event_id=event.id,
                )
                await self.db.commit()

                qa_result: dict = {}
                content = ""
                while True:
                    await self._transition(task, "generating")
                    content, usage, latency = await self._generate(prompt, persona, context.anti_perfection)
                    task.generated_content = content
                    task.token_input += int(usage.get("prompt_tokens", 0))
                    task.token_output += int(usage.get("completion_tokens", 0))
                    cost = await self.cost_monitor.record(
                        task.id,
                        "generation",
                        await self.config_store.get("llm.model_id", "") or "",
                        int(usage.get("prompt_tokens", 0)),
                        int(usage.get("completion_tokens", 0)),
                        latency_ms=latency,
                    )
                    task.cost_estimate += cost.cost_estimate
                    self._append_trace(
                        task,
                        "generation_completed",
                        attempt=task.retry_count + 1,
                        latency_ms=latency,
                        prompt_tokens=int(usage.get("prompt_tokens", 0)),
                        completion_tokens=int(usage.get("completion_tokens", 0)),
                        content_preview=self._preview_text(content),
                    )
                    await self.db.commit()

                    await self._transition(task, "qa_checking")
                    qa_result = await self.qa_engine.check(content, persona.id)
                    task.qa_result = json_dumps(qa_result)
                    self._append_trace(
                        task,
                        "qa_completed",
                        attempt=task.retry_count + 1,
                        passed=bool(qa_result.get("passed")),
                        risk_level=qa_result.get("risk_level", "unknown"),
                        duplicate_ok=qa_result.get("duplicate_ok"),
                        duplicate_method=qa_result.get("duplicate_method"),
                        duplicate_post_id=qa_result.get("duplicate_post_id"),
                        duplicate_score=qa_result.get("duplicate_score"),
                        duplicate_review_required=qa_result.get("duplicate_review_required", False),
                        integrity_ok=bool(qa_result.get("integrity_ok", True)),
                        integrity_reason=qa_result.get("integrity_reason", ""),
                    )
                    await self.db.commit()

                    if not qa_result.get("integrity_ok", True):
                        if task.retry_count >= task.max_retries:
                            return await self._transition(
                                task,
                                "failed",
                                error=qa_result.get("integrity_reason") or "invalid generated content",
                                error_code="invalid_model_output",
                            )
                        task.retry_count += 1
                        await self._transition(task, "rewrite_pending")
                        prompt = self._build_rewrite_prompt(prompt, content, qa_result)
                        continue

                    if qa_result["risk_level"] == "high":
                        draft = await self._save_as_draft(task, content, persona, reason="waiting_human_signoff")
                        task.post_id = draft.id
                        self._append_trace(
                            task,
                            "draft_saved",
                            post_id=draft.id,
                            reason="waiting_human_signoff",
                        )
                        await self.db.commit()
                        return await self._transition(task, "waiting_human_signoff")

                    if qa_result["passed"]:
                        break

                    if task.retry_count >= task.max_retries:
                        draft = await self._save_as_draft(task, content, persona, reason="qa_circuit_open")
                        task.post_id = draft.id
                        self._append_trace(
                            task,
                            "draft_saved",
                            post_id=draft.id,
                            reason="qa_circuit_open",
                        )
                        await self.db.commit()
                        return await self._transition(
                            task,
                            "circuit_open",
                            error="qa retries exhausted",
                            error_code="qa_circuit_open",
                        )

                    task.retry_count += 1
                    await self._transition(task, "rewrite_pending")
                    prompt = self._build_rewrite_prompt(prompt, content, qa_result)

                await self._transition(task, "ready_to_publish")
                post = await self._create_post(task, content, persona, status="approved")
                task.post_id = post.id
                self._append_trace(task, "post_created", post_id=post.id, slug=post.slug)
                await self.db.commit()

                await self._transition(task, "publishing")
                publisher = self.publisher_registry.get(post.publish_target)
                result = await publisher.publish(post)
                if not result.success:
                    return await self._transition(
                        task,
                        "failed",
                        error=result.detail or "publisher returned unsuccessful result",
                        error_code="publish_failed",
                    )

                post.status = "published"
                post.published_at = utcnow_iso()
                post.updated_at = post.published_at
                await self.qa_engine.index_post(post.id, post.content_markdown)
                self._append_trace(task, "publish_completed", post_id=post.id, publish_target=post.publish_target)
                await self.db.commit()
                await self._transition(task, "published")
                await self.memory_engine.create_from_article(post, persona.id)
                self._append_trace(task, "memory_created", post_id=post.id, persona_id=persona.id)
                await self.db.commit()
                return task

        except (InvalidTransition, httpx.HTTPError, SQLAlchemyError, ValueError, KeyError, TypeError, OSError) as exc:
            classified = self._classify_exception(exc)
            logger.exception(
                "task execution failed task_id=%s code=%s message=%s",
                task.id,
                classified.code,
                classified.message,
            )
            self._append_trace(
                task,
                "exception",
                error_code=classified.code,
                error_message=classified.message,
                exception_type=exc.__class__.__name__,
            )
            return await self._transition(
                task,
                "failed",
                error=classified.message,
                error_code=classified.code,
                severity=classified.severity,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("unexpected task execution failure task_id=%s", task.id)
            self._append_trace(
                task,
                "exception",
                error_code="unexpected_task_exception",
                error_message=str(exc).strip() or exc.__class__.__name__,
                exception_type=exc.__class__.__name__,
            )
            return await self._transition(
                task,
                "failed",
                error=str(exc).strip() or exc.__class__.__name__,
                error_code="unexpected_task_exception",
                severity="critical",
            )

    async def approve_task(self, task_id: int, publish_immediately: bool = True) -> GenerationTask | None:
        task = await self.db.get(GenerationTask, task_id)
        if task is None:
            return task
        if task.status != "waiting_human_signoff":
            raise InvalidTransition(f"task {task.id} is not waiting_human_signoff")
        qa_result = json_loads(task.qa_result, {})
        if not qa_result.get("integrity_ok", True):
            self._append_trace(
                task, "approval_blocked", reason=qa_result.get("integrity_reason", "invalid_model_output")
            )
            return await self._transition(
                task,
                "failed",
                error=qa_result.get("integrity_reason") or "invalid generated content",
                error_code="invalid_model_output",
            )
        await self._transition(task, "ready_to_publish")
        if not publish_immediately or not task.post_id:
            if task.post_id:
                post = await self.db.get(Post, task.post_id)
                if post is not None:
                    self._set_review_info(post, task, reason="waiting_human_signoff", human_approved=True)
                    self._append_trace(task, "human_approved", post_id=post.id, publish_immediately=False)
                    await self.db.commit()
            return task
        post = await self.db.get(Post, task.post_id)
        if post is None:
            return await self._transition(task, "failed", error="post not found", error_code="post_not_found")
        self._set_review_info(post, task, reason="waiting_human_signoff", human_approved=True)
        self._append_trace(task, "human_approved", post_id=post.id, publish_immediately=True)
        await self.db.commit()
        await self._transition(task, "publishing")
        publisher = self.publisher_registry.get(post.publish_target)
        result = await publisher.publish(post)
        if not result.success:
            return await self._transition(
                task,
                "failed",
                error=result.detail or "publisher returned unsuccessful result",
                error_code="publish_failed",
            )
        post.status = "published"
        post.published_at = utcnow_iso()
        post.updated_at = post.published_at
        await self.qa_engine.index_post(post.id, post.content_markdown)
        self._append_trace(task, "publish_completed", post_id=post.id, publish_target=post.publish_target)
        await self.db.commit()
        await self._transition(task, "published")
        await self.memory_engine.create_from_article(post, task.persona_id)
        self._append_trace(task, "memory_created", post_id=post.id, persona_id=task.persona_id)
        await self.db.commit()
        return task

    async def abort_task(self, task_id: int) -> GenerationTask | None:
        task = await self.db.get(GenerationTask, task_id)
        if task is None or task.status in self.TERMINAL:
            return task
        self._append_trace(task, "aborted_by_user")
        return await self._transition(task, "aborted", error="aborted by user", error_code="task_aborted")

    async def get_trace(self, task: GenerationTask) -> dict:
        post = await self.db.get(Post, task.post_id) if task.post_id else None
        return {
            "task": task.id,
            "status": task.status,
            "context_snapshot": json_loads(task.context_snapshot, {}),
            "memory_hits": json_loads(task.memory_hits, []),
            "prompt_summary": json_loads(task.prompt_summary, {}),
            "qa_result": json_loads(task.qa_result, {}),
            "trace_events": json_loads(task.trace_json, []),
            "tokens": {"input": task.token_input, "output": task.token_output},
            "cost_estimate": task.cost_estimate,
            "queue_wait_ms": task.queue_wait_ms,
            "error_code": task.error_code,
            "error_message": task.error_message,
            "publish_decision": build_publish_decision(
                qa_result=json_loads(task.qa_result, {}),
                review_info=json_loads(post.review_info, {}) if post else {},
                task_status=task.status,
                post_status=post.status if post else None,
                has_task=True,
            ),
        }

    async def _create_task(self, event: Event, persona: Persona) -> GenerationTask:
        max_retries = int(await self.config_store.get("qa.max_retries", "3") or 3)
        task = GenerationTask(
            trigger_source=event.event_type,
            event_id=event.id,
            persona_id=persona.id,
            context_snapshot="{}",
            memory_hits="[]",
            sensory_snapshot_id=None,
            prompt_summary="{}",
            generated_content=None,
            qa_result="{}",
            retry_count=0,
            max_retries=max_retries,
            token_input=0,
            token_output=0,
            cost_estimate=0.0,
            status="queued",
            cold_start=0,
            anti_perfection=0,
            queue_wait_ms=0,
            trace_json="[]",
            error_code=None,
            error_message=None,
            started_at=utcnow_iso(),
            finished_at=None,
            post_id=None,
        )
        self.db.add(task)
        await self.db.flush()
        event.task_id = task.id
        self._append_trace(
            task,
            "task_created",
            trigger_source=task.trigger_source,
            persona_id=task.persona_id,
            event_id=event.id,
        )
        await self.db.commit()
        await log_audit(
            self.db,
            "system",
            "task.create",
            "task",
            str(task.id),
            {"trigger_source": task.trigger_source, "persona_id": task.persona_id},
        )
        await self.db.commit()
        return task

    async def _transition(
        self,
        task: GenerationTask,
        new_status: str,
        error: str | None = None,
        *,
        error_code: str | None = None,
        severity: str | None = None,
    ) -> GenerationTask:
        old_status = task.status
        if old_status in self.TERMINAL and new_status != old_status:
            return task
        if new_status != old_status and new_status not in self.VALID_TRANSITIONS.get(old_status, []):
            raise InvalidTransition(f"{old_status} -> {new_status}")
        task.status = new_status
        if error is not None:
            task.error_message = error
        if error_code is not None:
            task.error_code = error_code
        if new_status in self.TERMINAL:
            task.finished_at = utcnow_iso()
        self._append_trace(
            task,
            "status_changed",
            from_status=old_status,
            to_status=new_status,
            error_code=error_code,
            error_message=error,
        )
        await log_audit(
            self.db,
            "system",
            "task.status_change",
            "task",
            str(task.id),
            {"from": old_status, "to": new_status, "error": error, "error_code": error_code},
            severity=severity or self._status_severity(new_status),
        )
        await self.db.commit()
        await self._notify_status_change(task, old_status, new_status)
        return task

    async def _generate(
        self,
        prompt: str,
        persona: Persona,
        anti_perfection: bool,
    ) -> tuple[str, dict, int]:
        base_url = await self.config_store.get("llm.base_url", "")
        api_key = await self.config_store.get("llm.api_key", "")
        model_id = await self.config_store.get("llm.model_id", "")
        temperature = 0.72
        max_tokens = 1000
        if anti_perfection:
            temperature = 1.05
            max_tokens = 420
        return await self.llm_adapter.chat(
            base_url=base_url or "",
            api_key=api_key or "",
            model_id=model_id or "",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are writing as persona {persona.name}."
                        " Stay restrained, concrete, and in character."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def _create_post(
        self,
        task: GenerationTask,
        content: str,
        persona: Persona,
        *,
        status: str,
    ) -> Post:
        now = utcnow_iso()
        site_title = (await self.config_store.get("site.title", "全真夜记") or "全真夜记").strip() or "全真夜记"
        invalid_titles = {site_title, "全真夜记", "夜记", "无题", "未命名夜记"}
        title = extract_title(
            content,
            fallback=f"夜记 {task.id}",
            invalid_titles=invalid_titles,
        )
        title = sanitize_plain_text(title, max_length=64) or f"夜记 {task.id}"
        slug = f"{task.id}-{slugify(title, fallback_prefix=f'task-{task.id}')}"
        summary = sanitize_plain_text(derive_summary(content, title=title), max_length=180) or title
        post = Post(
            title=title,
            slug=slug,
            front_matter=json_dumps(
                {"categories": ["night-journal"], "tags": [persona.name, "夜札"], "author": persona.name}
            ),
            content_markdown=content,
            summary=summary,
            status=status,
            persona_id=persona.id,
            task_id=task.id,
            published_at=None,
            revision=1,
            publish_target="hugo",
            digital_stamp=self.digital_stamp_generator.generate(content, persona.name),
            review_info=json_dumps({"task_id": task.id}),
            created_at=now,
            updated_at=now,
        )
        self.db.add(post)
        await self.db.flush()
        self._set_review_info(post, task)
        return post

    async def _save_as_draft(
        self,
        task: GenerationTask,
        content: str,
        persona: Persona,
        reason: str,
    ) -> Post:
        post = await self._create_post(task, content, persona, status="pending_review")
        self._set_review_info(post, task, reason=reason)
        await self.db.flush()
        return post

    def _build_rewrite_prompt(self, prompt: str, content: str, qa_result: dict) -> str:
        failed = [name for name, value in qa_result.items() if name.endswith("_ok") and not value]
        integrity_reason = qa_result.get("integrity_reason", "")
        if integrity_reason:
            failed.append(f"integrity:{integrity_reason}")
        issues = ", ".join(failed) if failed else "generic_quality"
        return (
            f"{prompt}\n\n"
            f"Previous draft:\n{content}\n\n"
            f"Issues to fix: {issues}.\n"
            "Keep the same persona, but shift to a new scene, new concrete action, and new narrative progression."
        )

    def _append_trace(self, task: GenerationTask, stage: str, **detail: object) -> None:
        trace = json_loads(task.trace_json, [])
        trace.append({"ts": utcnow_iso(), "stage": stage, "detail": detail})
        task.trace_json = json_dumps(trace[-120:])

    def _set_review_info(
        self,
        post: Post,
        task: GenerationTask,
        *,
        reason: str | None = None,
        human_approved: bool | None = None,
    ) -> None:
        review_info = json_loads(post.review_info, {})
        review_info["task_id"] = task.id
        if reason is not None:
            review_info["reason"] = reason
        if human_approved is True:
            review_info["human_approved"] = True
            review_info["human_approved_at"] = utcnow_iso()
        elif human_approved is False:
            review_info["human_approved"] = False
            review_info.pop("human_approved_at", None)

        decision = build_publish_decision(
            qa_result=json_loads(task.qa_result, {}),
            review_info=review_info,
            task_status=task.status,
            post_status=post.status,
            has_task=True,
        )
        review_info.update(
            {
                "qa_auto_passed": decision["qa_auto_passed"],
                "human_approved": decision["human_approved"],
                "human_approval_recorded": decision["human_approval_recorded"],
                "human_approved_at": decision["human_approved_at"],
                "final_publish_allowed": decision["final_publish_allowed"],
                "publish_decision_path": decision["publish_decision_path"],
                "publish_decision_reason": decision["publish_decision_reason"],
            }
        )
        post.review_info = json_dumps(review_info)

    async def _notify_status_change(self, task: GenerationTask, old_status: str, new_status: str) -> None:
        if new_status not in {"failed", "circuit_open", "waiting_human_signoff"}:
            return
        await self.notification_manager.send(
            event_type=f"task.{new_status}",
            title=f"任务 #{task.id} 状态变更为 {new_status}",
            severity="error" if new_status in {"failed", "circuit_open"} else "warning",
            detail={
                "task_id": task.id,
                "from_status": old_status,
                "to_status": new_status,
                "error_code": task.error_code,
                "error_message": task.error_message,
                "persona_id": task.persona_id,
                "post_id": task.post_id,
            },
        )

    def _classify_exception(self, exc: Exception) -> ClassifiedError:
        message = str(exc).strip() or exc.__class__.__name__
        if isinstance(exc, InvalidTransition):
            return ClassifiedError("invalid_transition", message, severity="critical")
        if isinstance(exc, SQLAlchemyError):
            return ClassifiedError("database_error", "database operation failed", severity="critical")
        if isinstance(exc, httpx.ConnectTimeout):
            return ClassifiedError("llm_connect_timeout", "upstream LLM connection timed out")
        if isinstance(exc, httpx.ReadTimeout):
            return ClassifiedError("llm_read_timeout", "upstream LLM response timed out")
        if isinstance(exc, httpx.WriteTimeout):
            return ClassifiedError("llm_write_timeout", "upstream LLM request upload timed out")
        if isinstance(exc, httpx.PoolTimeout):
            return ClassifiedError("llm_pool_timeout", "upstream LLM connection pool timed out")
        if isinstance(exc, httpx.TimeoutException):
            return ClassifiedError("llm_timeout", message or "upstream LLM timed out")
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            if status_code in {401, 403}:
                return ClassifiedError("llm_auth_error", f"upstream LLM authentication failed with HTTP {status_code}")
            if status_code == 429:
                return ClassifiedError("llm_rate_limited", "upstream LLM rate limited the request")
            if isinstance(status_code, int) and status_code >= 500:
                return ClassifiedError("llm_upstream_5xx", f"upstream LLM returned HTTP {status_code}")
            if status_code in {400, 404, 422}:
                return ClassifiedError("llm_bad_request", f"upstream LLM rejected the request with HTTP {status_code}")
            return ClassifiedError("llm_http_error", f"upstream LLM returned HTTP {status_code}")
        if isinstance(exc, httpx.RequestError):
            return ClassifiedError("llm_transport_error", message)
        if isinstance(exc, ValueError):
            if message == "llm_not_configured":
                return ClassifiedError("llm_not_configured", "LLM provider is not configured", severity="critical")
            if message == "no_active_persona":
                return ClassifiedError("no_active_persona", "no active persona configured", severity="critical")
        return ClassifiedError("task_exception", message)

    def _status_severity(self, status: str) -> str:
        if status in {"failed", "circuit_open", "aborted"}:
            return "warning"
        return "info"

    def _preview_text(self, content: str, limit: int = 120) -> str:
        return content.replace("\n", " ").strip()[:limit]
