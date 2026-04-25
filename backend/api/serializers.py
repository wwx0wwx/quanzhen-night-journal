from __future__ import annotations

from backend.models import Event, GenerationTask, Memory, Persona, Post, SensorySnapshot
from backend.utils.publish_decision import build_publish_decision
from backend.utils.serde import json_loads


def persona_to_dict(persona: Persona) -> dict:
    return {
        "id": persona.id,
        "name": persona.name,
        "description": persona.description,
        "is_active": bool(persona.is_active),
        "is_default": bool(persona.is_default),
        "identity_setting": persona.identity_setting,
        "worldview_setting": persona.worldview_setting,
        "language_style": persona.language_style,
        "taboos": json_loads(persona.taboos, []),
        "sensory_lexicon": json_loads(persona.sensory_lexicon, {}),
        "structure_preference": persona.structure_preference,
        "expression_intensity": persona.expression_intensity,
        "stability_params": json_loads(persona.stability_params, {}),
        "scene_pool": json_loads(persona.scene_pool, []),
        "created_at": persona.created_at,
        "updated_at": persona.updated_at,
    }


def memory_to_dict(memory: Memory) -> dict:
    return {
        "id": memory.id,
        "persona_id": memory.persona_id,
        "level": memory.level,
        "content": memory.content,
        "summary": memory.summary,
        "tags": json_loads(memory.tags, []),
        "source": memory.source,
        "weight": memory.weight,
        "time_range_start": memory.time_range_start,
        "time_range_end": memory.time_range_end,
        "review_status": memory.review_status,
        "decay_strategy": memory.decay_strategy,
        "is_core": bool(memory.is_core),
        "created_at": memory.created_at,
        "last_accessed_at": memory.last_accessed_at,
    }


def task_to_dict(task: GenerationTask, post: Post | None = None) -> dict:
    qa_result = json_loads(task.qa_result, {})
    review_info = json_loads(post.review_info, {}) if post else {}
    return {
        "id": task.id,
        "status": task.status,
        "persona_id": task.persona_id,
        "trigger_source": task.trigger_source,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "retry_count": task.retry_count,
        "max_retries": task.max_retries,
        "post_id": task.post_id,
        "queue_wait_ms": task.queue_wait_ms,
        "error_code": task.error_code,
        "error_message": task.error_message,
        "acknowledged_at": task.acknowledged_at,
        "duplicate_ok": qa_result.get("duplicate_ok"),
        "duplicate_score": qa_result.get("duplicate_score"),
        "duplicate_post_id": qa_result.get("duplicate_post_id"),
        "duplicate_method": qa_result.get("duplicate_method"),
        "duplicate_review_required": qa_result.get("duplicate_review_required", False),
        **build_publish_decision(
            qa_result=qa_result,
            review_info=review_info,
            task_status=task.status,
            post_status=post.status if post else None,
            has_task=True,
        ),
    }


def post_to_dict(post: Post, task: GenerationTask | None = None) -> dict:
    review_info = json_loads(post.review_info, {})
    qa_result = json_loads(task.qa_result, {}) if task else {}
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "front_matter": json_loads(post.front_matter, {}),
        "content_markdown": post.content_markdown,
        "summary": post.summary,
        "status": post.status,
        "persona_id": post.persona_id,
        "task_id": post.task_id,
        "published_at": post.published_at,
        "revision": post.revision,
        "publish_target": post.publish_target,
        "digital_stamp": post.digital_stamp,
        "review_reason": review_info.get("reason", ""),
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "duplicate_ok": qa_result.get("duplicate_ok"),
        "duplicate_score": qa_result.get("duplicate_score"),
        "duplicate_post_id": qa_result.get("duplicate_post_id"),
        "duplicate_method": qa_result.get("duplicate_method"),
        "duplicate_review_required": qa_result.get("duplicate_review_required", False),
        **build_publish_decision(
            qa_result=qa_result,
            review_info=review_info,
            task_status=task.status if task else None,
            post_status=post.status,
            has_task=task is not None,
        ),
    }


def event_to_dict(event: Event) -> dict:
    return {
        "id": event.id,
        "event_type": event.event_type,
        "source": event.source,
        "raw_payload": json_loads(event.raw_payload, {}),
        "normalized_semantic": event.normalized_semantic,
        "auth_status": event.auth_status,
        "dedup_key": event.dedup_key,
        "cooldown_status": event.cooldown_status,
        "created_at": event.created_at,
        "task_id": event.task_id,
    }


def sensory_to_dict(snapshot: SensorySnapshot) -> dict:
    return {
        "id": snapshot.id,
        "source": snapshot.source,
        "sampled_at": snapshot.sampled_at,
        "cpu_percent": snapshot.cpu_percent,
        "memory_percent": snapshot.memory_percent,
        "io_read_bytes": snapshot.io_read_bytes,
        "io_write_bytes": snapshot.io_write_bytes,
        "io_read_delta_bytes": snapshot.io_read_delta_bytes,
        "io_write_delta_bytes": snapshot.io_write_delta_bytes,
        "io_read_bytes_per_sec": snapshot.io_read_bytes_per_sec,
        "io_write_bytes_per_sec": snapshot.io_write_bytes_per_sec,
        "disk_usage_percent": snapshot.disk_usage_percent,
        "network_rx_bytes": snapshot.network_rx_bytes,
        "network_tx_bytes": snapshot.network_tx_bytes,
        "network_rx_delta_bytes": snapshot.network_rx_delta_bytes,
        "network_tx_delta_bytes": snapshot.network_tx_delta_bytes,
        "network_rx_bytes_per_sec": snapshot.network_rx_bytes_per_sec,
        "network_tx_bytes_per_sec": snapshot.network_tx_bytes_per_sec,
        "sample_interval_seconds": snapshot.sample_interval_seconds,
        "load_average": snapshot.load_average,
        "api_latency_ms": snapshot.api_latency_ms,
        "tags": json_loads(snapshot.tags, []),
        "translated_text": snapshot.translated_text,
        "persona_id": snapshot.persona_id,
        "is_in_blind_zone": bool(snapshot.is_in_blind_zone),
    }
