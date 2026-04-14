from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.config_store import ConfigStore
from backend.models import Memory, MemoryVector, Persona, Post, PostVector
from backend.utils.serde import json_loads
from backend.utils.time import utcnow_iso


class GhostManager:
    GHOST_VERSION = "2.0"

    def __init__(self, db: AsyncSession, config_store: ConfigStore, ghost_dir: Path):
        self.db = db
        self.config_store = config_store
        self.ghost_dir = ghost_dir

    async def export(self, include_api_keys: bool = False) -> Path:
        self.ghost_dir.mkdir(parents=True, exist_ok=True)
        filename = self.ghost_dir / f"quanzhen-{utcnow_iso().replace(':', '-')}.ghost"
        personas = [self._persona_payload(item) for item in await self.db.scalars(select(Persona))]
        memories = [self._memory_payload(item) for item in await self.db.scalars(select(Memory))]
        posts = [self._post_payload(item) for item in await self.db.scalars(select(Post))]
        memory_vectors = [
            {"memory_id": item.memory_id, "embedding": json_loads(item.embedding, [])}
            for item in await self.db.scalars(select(MemoryVector))
        ]
        post_vectors = [
            {"post_id": item.post_id, "embedding": json_loads(item.embedding, [])}
            for item in await self.db.scalars(select(PostVector))
        ]
        config = await self.config_store.as_public_dict()
        if include_api_keys:
            for key in ["llm.api_key", "embedding.api_key", "webhook.auth_token"]:
                config[key] = {
                    "value": await self.config_store.get(key, ""),
                    "category": config.get(key, {}).get("category", "general"),
                    "encrypted": True,
                }
        manifest = {
            "ghost_version": self.GHOST_VERSION,
            "created_at": utcnow_iso(),
            "counts": {
                "personas": len(personas),
                "memories": len(memories),
                "posts": len(posts),
                "memory_vectors": len(memory_vectors),
                "post_vectors": len(post_vectors),
            },
        }
        with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            archive.writestr("personas.json", json.dumps(personas, ensure_ascii=False, indent=2))
            archive.writestr("memories.json", json.dumps(memories, ensure_ascii=False, indent=2))
            archive.writestr("memory_vectors.json", json.dumps(memory_vectors, ensure_ascii=False, indent=2))
            archive.writestr("post_vectors.json", json.dumps(post_vectors, ensure_ascii=False, indent=2))
            archive.writestr("vectors.bin", json.dumps(memory_vectors, ensure_ascii=False).encode("utf-8"))
            archive.writestr("posts_meta.json", json.dumps(posts, ensure_ascii=False, indent=2))
            archive.writestr("config.json", json.dumps(config, ensure_ascii=False, indent=2))
            archive.writestr("health.json", json.dumps({"generated_at": utcnow_iso()}, ensure_ascii=False, indent=2))
        return filename

    async def preview(self, filename: str, payload: bytes) -> dict:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            manifest = json.loads(archive.read("manifest.json"))
            personas = json.loads(archive.read("personas.json"))
            posts = json.loads(archive.read("posts_meta.json"))
        existing_personas = {item.name for item in await self.db.scalars(select(Persona))}
        existing_slugs = {item.slug for item in await self.db.scalars(select(Post))}
        conflicts = [f"persona:{item['name']}" for item in personas if item["name"] in existing_personas]
        conflicts.extend(f"post:{item['slug']}" for item in posts if item.get("slug") in existing_slugs)
        return {"filename": filename, "manifest": manifest, "conflicts": conflicts}

    async def import_ghost(self, filename: str, payload: bytes, confirm: bool = False) -> dict:
        preview = await self.preview(filename, payload)
        if not confirm:
            return preview

        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            personas = json.loads(archive.read("personas.json"))
            memories = json.loads(archive.read("memories.json"))
            posts = json.loads(archive.read("posts_meta.json"))
            config = json.loads(archive.read("config.json"))
            memory_vectors = self._read_json_file(archive, "memory_vectors.json", fallback="vectors.bin")
            post_vectors = self._read_json_file(archive, "post_vectors.json", fallback=None)

        existing_personas = {item.name: item.id for item in await self.db.scalars(select(Persona))}
        existing_slugs = {item.slug for item in await self.db.scalars(select(Post))}
        persona_id_map: dict[int, int] = {}
        memory_id_map: dict[int, int] = {}
        post_id_map: dict[int, int] = {}

        for item in personas:
            source_id = item.get("id")
            if item["name"] in existing_personas:
                if source_id is not None:
                    persona_id_map[source_id] = existing_personas[item["name"]]
                continue
            data = dict(item)
            data.pop("id", None)
            persona = Persona(**data)
            self.db.add(persona)
            await self.db.flush()
            if source_id is not None:
                persona_id_map[source_id] = persona.id
        for item in memories:
            data = dict(item)
            source_id = data.pop("id", None)
            source_persona_id = data.get("persona_id")
            if source_persona_id in persona_id_map:
                data["persona_id"] = persona_id_map[source_persona_id]
            memory = Memory(**data)
            self.db.add(memory)
            await self.db.flush()
            if source_id is not None:
                memory_id_map[source_id] = memory.id
        for item in posts:
            source_id = item.get("id")
            if item["slug"] in existing_slugs:
                continue
            data = dict(item)
            data.pop("id", None)
            source_persona_id = data.get("persona_id")
            if source_persona_id in persona_id_map:
                data["persona_id"] = persona_id_map[source_persona_id]
            post = Post(**data)
            self.db.add(post)
            await self.db.flush()
            if source_id is not None:
                post_id_map[source_id] = post.id
        for item in memory_vectors:
            source_memory_id = item.get("memory_id")
            target_memory_id = memory_id_map.get(source_memory_id)
            if target_memory_id is None:
                continue
            existing = await self.db.get(MemoryVector, target_memory_id)
            if existing is None:
                self.db.add(MemoryVector(memory_id=target_memory_id, embedding=json.dumps(item.get("embedding", []), ensure_ascii=False)))
            else:
                existing.embedding = json.dumps(item.get("embedding", []), ensure_ascii=False)
        for item in post_vectors:
            source_post_id = item.get("post_id")
            target_post_id = post_id_map.get(source_post_id)
            if target_post_id is None:
                continue
            existing = await self.db.get(PostVector, target_post_id)
            if existing is None:
                self.db.add(PostVector(post_id=target_post_id, embedding=json.dumps(item.get("embedding", []), ensure_ascii=False)))
            else:
                existing.embedding = json.dumps(item.get("embedding", []), ensure_ascii=False)
        for key, entry in config.items():
            value = entry.get("value")
            if value == "******":
                continue
            await self.config_store.set(
                key,
                value,
                category=entry.get("category"),
                encrypted=entry.get("encrypted"),
            )
        await self.db.flush()
        return preview

    async def list_exports(self) -> list[dict]:
        self.ghost_dir.mkdir(parents=True, exist_ok=True)
        return [
            {"filename": file.name, "path": str(file), "size": file.stat().st_size}
            for file in sorted(self.ghost_dir.glob("*.ghost"), reverse=True)
        ]

    def _persona_payload(self, persona: Persona) -> dict:
        return {
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "is_active": persona.is_active,
            "is_default": 0,
            "identity_setting": persona.identity_setting,
            "worldview_setting": persona.worldview_setting,
            "language_style": persona.language_style,
            "taboos": persona.taboos,
            "sensory_lexicon": persona.sensory_lexicon,
            "structure_preference": persona.structure_preference,
            "expression_intensity": persona.expression_intensity,
            "stability_params": persona.stability_params,
            "created_at": persona.created_at,
            "updated_at": persona.updated_at,
        }

    def _memory_payload(self, memory: Memory) -> dict:
        return {
            "id": memory.id,
            "persona_id": memory.persona_id,
            "level": memory.level,
            "content": memory.content,
            "summary": memory.summary,
            "tags": memory.tags,
            "source": memory.source,
            "weight": memory.weight,
            "time_range_start": memory.time_range_start,
            "time_range_end": memory.time_range_end,
            "review_status": memory.review_status,
            "decay_strategy": memory.decay_strategy,
            "is_core": memory.is_core,
            "created_at": memory.created_at,
            "last_accessed_at": memory.last_accessed_at,
        }

    def _post_payload(self, post: Post) -> dict:
        return {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "front_matter": post.front_matter,
            "content_markdown": post.content_markdown,
            "summary": post.summary,
            "status": post.status,
            "persona_id": post.persona_id,
            "task_id": None,
            "published_at": post.published_at,
            "revision": post.revision,
            "publish_target": post.publish_target,
            "digital_stamp": post.digital_stamp,
            "review_info": post.review_info,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
        }

    def _read_json_file(self, archive: zipfile.ZipFile, filename: str, fallback: str | None) -> list[dict]:
        try:
            return json.loads(archive.read(filename))
        except KeyError:
            if fallback is None:
                return []
            try:
                return json.loads(archive.read(fallback))
            except KeyError:
                return []
