-- ============================================================
-- 全真夜记 (Quanzhen Night Journal) — 完整数据库 Schema
-- 版本: v2.0 (终局形态)
-- 数据库: SQLite (WAL 模式)
-- 向量扩展: sqlite-vec
-- ============================================================

-- 启用 WAL 模式
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

-- ============================================================
-- 1. 用户与认证
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    is_initialized  INTEGER NOT NULL DEFAULT 0,  -- 0=未完成初始化, 1=已完成
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 默认管理员 (密码在首次登录后强制修改)
-- password_hash 为 'quanzhen' 的 bcrypt hash，实际部署时由启动脚本生成
INSERT OR IGNORE INTO users (id, username, password_hash, is_initialized)
VALUES (1, 'admin', '$PLACEHOLDER_HASH$', 0);

-- ============================================================
-- 2. 系统配置 (KV 存储)
-- ============================================================

CREATE TABLE IF NOT EXISTS system_config (
    key         TEXT    PRIMARY KEY,
    value       TEXT,                       -- JSON 或纯文本
    encrypted   INTEGER NOT NULL DEFAULT 0, -- 1=值已加密 (API Key 等)
    category    TEXT    NOT NULL DEFAULT 'general',
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 预置配置项
INSERT OR IGNORE INTO system_config (key, value, category) VALUES
    ('site.title',           '全真夜记',           'site'),
    ('site.subtitle',        '',                   'site'),
    ('site.domain',          '',                   'site'),
    ('site.domain_enabled',  '0',                  'site'),
    ('site.domain_status',   'disabled',           'site'),
    ('site.domain_reason',   '',                   'site'),
    ('site.domain_checked_at', '',                 'site'),
    ('llm.base_url',         '',                   'llm'),
    ('llm.api_key',          '',                   'llm'),
    ('llm.model_id',         '',                   'llm'),
    ('embedding.base_url',   '',                   'embedding'),
    ('embedding.api_key',    '',                   'embedding'),
    ('embedding.model_id',   '',                   'embedding'),
    ('embedding.dimensions', '1536',               'embedding'),
    ('schedule.days_per_cycle',   '1',             'schedule'),
    ('schedule.posts_per_cycle',  '1',             'schedule'),
    ('schedule.publish_time',     '21:02',         'schedule'),
    ('schedule.cycle_anchor_date', '',             'schedule'),
    ('schedule.review_cron',      '0 3 * * 0',     'schedule'),
    ('schedule.decay_cron',       '0 4 * * *',     'schedule'),
    ('schedule.sample_interval_minutes', '5',      'schedule'),
    ('budget.daily_limit_usd',    '1.00',          'budget'),
    ('budget.monthly_limit_usd',  '20.00',         'budget'),
    ('budget.is_hibernating',     '0',             'budget'),
    ('qa.max_retries',            '3',             'qa'),
    ('qa.min_length',             '200',           'qa'),
    ('qa.max_length',             '5000',          'qa'),
    ('qa.duplicate_threshold',    '0.85',          'qa'),
    ('qa.forbidden_words',        '[]',            'qa'),
    ('qa.template_phrases',       '["首先","其次","总之","综上所述","值得注意的是"]', 'qa'),
    ('anti_perfection.enabled',          '1',      'anti_perfection'),
    ('anti_perfection.consecutive_max',  '3',      'anti_perfection'),
    ('anti_perfection.cooldown_hours',   '24',     'anti_perfection'),
    ('sensory.blind_zone_minutes',       '30',     'sensory'),
    ('sensory.cpu_high_threshold',       '80',     'sensory'),
    ('sensory.mem_high_threshold',       '85',     'sensory'),
    ('sensory.io_high_threshold',        '70',     'sensory'),
    ('sensory.source_mode',              'container', 'sensory'),  -- container | host
    ('webhook.auth_mode',         'bearer',        'webhook'),     -- bearer | hmac
    ('webhook.auth_token',        '',              'webhook'),
    ('webhook.cooldown_seconds',  '1800',          'webhook'),
    ('system.initialized',        '0',             'system'),
    ('system.encryption_key',     '',              'system'),
    ('hugo.theme',                'PaperMod',      'hugo'),
    ('hugo.base_url',             '/',             'hugo');

-- ============================================================
-- 3. 人格 (Persona)
-- ============================================================

CREATE TABLE IF NOT EXISTS personas (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT    NOT NULL,
    description             TEXT    NOT NULL DEFAULT '',
    is_active               INTEGER NOT NULL DEFAULT 1,
    is_default              INTEGER NOT NULL DEFAULT 0,
    identity_setting        TEXT    NOT NULL DEFAULT '',  -- 核心身份设定
    worldview_setting       TEXT    NOT NULL DEFAULT '',  -- 世界观设定
    language_style          TEXT    NOT NULL DEFAULT '',  -- 语言风格规则
    taboos                  TEXT    NOT NULL DEFAULT '[]', -- JSON array: 禁忌
    sensory_lexicon         TEXT    NOT NULL DEFAULT '{}', -- JSON object: 感知→意象映射
    structure_preference    TEXT    NOT NULL DEFAULT 'medium', -- short/medium/long
    expression_intensity    TEXT    NOT NULL DEFAULT 'moderate', -- calm/moderate/intense
    stability_params        TEXT    NOT NULL DEFAULT '{"temperature_base": 0.7, "temperature_range": [0.3, 1.2]}',
    created_at              TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at              TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 确保最多只有一个默认人格
CREATE UNIQUE INDEX IF NOT EXISTS idx_personas_default
    ON personas (is_default) WHERE is_default = 1;

-- ============================================================
-- 4. 记忆 (Memory)
-- ============================================================

CREATE TABLE IF NOT EXISTS memories (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_id          INTEGER NOT NULL,
    level               TEXT    NOT NULL CHECK (level IN ('L0', 'L1', 'L2', 'L3')),
    content             TEXT    NOT NULL,
    summary             TEXT    NOT NULL DEFAULT '',
    tags                TEXT    NOT NULL DEFAULT '[]',   -- JSON array
    source              TEXT    NOT NULL DEFAULT 'auto_summary'
                        CHECK (source IN ('hand_written', 'auto_summary', 'article', 'reflection', 'import')),
    weight              REAL    NOT NULL DEFAULT 1.0,
    time_range_start    TEXT,
    time_range_end      TEXT,
    review_status       TEXT    NOT NULL DEFAULT 'unreviewed'
                        CHECK (review_status IN ('unreviewed', 'reviewed', 'promoted')),
    decay_strategy      TEXT    NOT NULL DEFAULT 'standard',
    is_core             INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    last_accessed_at    TEXT,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memories_persona_level ON memories (persona_id, level);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories (created_at);
CREATE INDEX IF NOT EXISTS idx_memories_weight ON memories (weight DESC);

-- 记忆向量表 (sqlite-vec 虚拟表, 维度在运行时根据配置创建)
-- 注意: 此表由应用层在启动时根据 embedding.dimensions 配置动态创建
-- 示例: CREATE VIRTUAL TABLE memory_vectors USING vec0(
--     memory_id INTEGER PRIMARY KEY,
--     embedding FLOAT[1536]
-- );

-- ============================================================
-- 5. 感知快照 (Sensory Snapshot)
-- ============================================================

CREATE TABLE IF NOT EXISTS sensory_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    source              TEXT    NOT NULL DEFAULT 'container'
                        CHECK (source IN ('container', 'host')),
    sampled_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    cpu_percent         REAL,
    memory_percent      REAL,
    io_read_bytes       INTEGER,
    io_write_bytes      INTEGER,
    disk_usage_percent  REAL,
    network_rx_bytes    INTEGER,
    network_tx_bytes    INTEGER,
    load_average        REAL,
    api_latency_ms      INTEGER,
    tags                TEXT    NOT NULL DEFAULT '[]',       -- JSON array: ["high_cpu", "io_spike"]
    translated_text     TEXT    NOT NULL DEFAULT '',         -- 人格化翻译结果
    persona_id          INTEGER,                            -- 翻译时使用的人格
    is_in_blind_zone    INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_sampled ON sensory_snapshots (sampled_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_blind ON sensory_snapshots (is_in_blind_zone);

-- ============================================================
-- 6. 事件 (Event)
-- ============================================================

CREATE TABLE IF NOT EXISTS events (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type              TEXT    NOT NULL
                            CHECK (event_type IN ('scheduler', 'manual', 'webhook', 'folder_monitor', 'system_exception', 'review', 'publish')),
    source                  TEXT    NOT NULL DEFAULT '',
    raw_payload             TEXT    NOT NULL DEFAULT '{}',   -- JSON
    normalized_semantic     TEXT    NOT NULL DEFAULT '',
    auth_status             TEXT    NOT NULL DEFAULT 'not_required'
                            CHECK (auth_status IN ('passed', 'failed', 'not_required')),
    dedup_key               TEXT,
    cooldown_status         TEXT    NOT NULL DEFAULT 'ready'
                            CHECK (cooldown_status IN ('ready', 'cooling')),
    created_at              TEXT    NOT NULL DEFAULT (datetime('now')),
    task_id                 INTEGER,
    FOREIGN KEY (task_id) REFERENCES generation_tasks(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_dedup ON events (dedup_key);
CREATE INDEX IF NOT EXISTS idx_events_created ON events (created_at);

-- ============================================================
-- 6.1 公开访问统计 (Public Page Views)
-- ============================================================

CREATE TABLE IF NOT EXISTS public_page_views (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path            TEXT    NOT NULL DEFAULT '/',
    page_title      TEXT    NOT NULL DEFAULT '',
    referrer        TEXT    NOT NULL DEFAULT '',
    ip_address      TEXT    NOT NULL DEFAULT '',
    user_agent      TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_public_page_views_created ON public_page_views (created_at);
CREATE INDEX IF NOT EXISTS idx_public_page_views_path_created ON public_page_views (path, created_at);

-- ============================================================
-- 7. 生成任务 (Generation Task)
-- ============================================================

CREATE TABLE IF NOT EXISTS generation_tasks (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_source      TEXT    NOT NULL
                        CHECK (trigger_source IN ('scheduler', 'manual', 'webhook', 'folder_monitor', 'system_exception', 'review')),
    event_id            INTEGER,
    persona_id          INTEGER NOT NULL,
    context_snapshot    TEXT    NOT NULL DEFAULT '{}',   -- JSON: 组装时的完整上下文
    memory_hits         TEXT    NOT NULL DEFAULT '[]',   -- JSON: [{id, similarity, level}]
    sensory_snapshot_id INTEGER,
    prompt_summary      TEXT    NOT NULL DEFAULT '{}',   -- JSON: 各 Prompt 片段来源摘要
    generated_content   TEXT,
    qa_result           TEXT    NOT NULL DEFAULT '{}',   -- JSON: {length_ok, forbidden_ok, template_ok, duplicate_ok, risk_level}
    retry_count         INTEGER NOT NULL DEFAULT 0,
    max_retries         INTEGER NOT NULL DEFAULT 3,
    token_input         INTEGER NOT NULL DEFAULT 0,
    token_output        INTEGER NOT NULL DEFAULT 0,
    cost_estimate       REAL    NOT NULL DEFAULT 0.0,
    status              TEXT    NOT NULL DEFAULT 'queued'
                        CHECK (status IN (
                            'queued', 'preparing_context', 'generating', 'qa_checking',
                            'rewrite_pending', 'waiting_human_signoff', 'ready_to_publish',
                            'publishing', 'published', 'draft_saved', 'failed',
                            'circuit_open', 'aborted'
                        )),
    cold_start          INTEGER NOT NULL DEFAULT 0,
    anti_perfection     INTEGER NOT NULL DEFAULT 0,     -- 是否走火入魔模式
    queue_wait_ms       INTEGER NOT NULL DEFAULT 0,
    trace_json          TEXT    NOT NULL DEFAULT '[]',
    error_code          TEXT,
    error_message       TEXT,
    started_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    finished_at         TEXT,
    post_id             INTEGER,
    FOREIGN KEY (event_id)            REFERENCES events(id)            ON DELETE SET NULL,
    FOREIGN KEY (persona_id)          REFERENCES personas(id)          ON DELETE RESTRICT,
    FOREIGN KEY (sensory_snapshot_id) REFERENCES sensory_snapshots(id) ON DELETE SET NULL,
    FOREIGN KEY (post_id)             REFERENCES posts(id)             ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON generation_tasks (status);
CREATE INDEX IF NOT EXISTS idx_tasks_persona ON generation_tasks (persona_id);
CREATE INDEX IF NOT EXISTS idx_tasks_started ON generation_tasks (started_at);

-- ============================================================
-- 8. 文章 (Post / Draft)
-- ============================================================

CREATE TABLE IF NOT EXISTS posts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    title               TEXT    NOT NULL DEFAULT '',
    slug                TEXT    NOT NULL DEFAULT '',
    front_matter        TEXT    NOT NULL DEFAULT '{}',   -- JSON
    content_markdown    TEXT    NOT NULL DEFAULT '',
    summary             TEXT    NOT NULL DEFAULT '',
    status              TEXT    NOT NULL DEFAULT 'draft'
                        CHECK (status IN (
                            'draft', 'pending_review', 'approved', 'publishing',
                            'published', 'publish_failed', 'archived', 'aborted'
                        )),
    persona_id          INTEGER,
    task_id             INTEGER,
    published_at        TEXT,
    revision            INTEGER NOT NULL DEFAULT 1,
    publish_target      TEXT    NOT NULL DEFAULT 'hugo',
    digital_stamp       TEXT,                           -- ASCII art / SVG 签名
    review_info         TEXT    NOT NULL DEFAULT '{}',   -- JSON: {reviewer, time, note}
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE SET NULL,
    FOREIGN KEY (task_id)    REFERENCES generation_tasks(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_slug ON posts (slug) WHERE slug != '';
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts (status);
CREATE INDEX IF NOT EXISTS idx_posts_published ON posts (published_at);

-- ============================================================
-- 9. 文章修订历史 (Post Revisions)
-- ============================================================

CREATE TABLE IF NOT EXISTS post_revisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id         INTEGER NOT NULL,
    revision        INTEGER NOT NULL,
    title           TEXT    NOT NULL,
    content_markdown TEXT   NOT NULL,
    front_matter    TEXT    NOT NULL DEFAULT '{}',
    change_reason   TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_revisions_post ON post_revisions (post_id, revision);

-- ============================================================
-- 10. 审计日志 (Audit Log) — append-only
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL DEFAULT (datetime('now')),
    actor       TEXT    NOT NULL DEFAULT 'system'
                CHECK (actor IN ('system', 'user', 'scheduler', 'webhook')),
    action      TEXT    NOT NULL,                        -- e.g. 'persona.create', 'task.status_change'
    target_type TEXT,                                    -- persona / task / post / memory / config / ghost
    target_id   TEXT,                                    -- 字符串以兼容各类 ID
    detail      TEXT    NOT NULL DEFAULT '{}',           -- JSON: 变更详情
    ip_address  TEXT,
    severity    TEXT    NOT NULL DEFAULT 'info'
                CHECK (severity IN ('info', 'warning', 'critical'))
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs (severity);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs (target_type, target_id);

-- ============================================================
-- 11. 成本记录 (Cost Record) — append-only
-- ============================================================

CREATE TABLE IF NOT EXISTS cost_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id             INTEGER,
    call_type           TEXT    NOT NULL
                        CHECK (call_type IN ('generation', 'embedding', 'reflection', 'qa_enhanced')),
    model_id            TEXT    NOT NULL DEFAULT '',
    token_input         INTEGER NOT NULL DEFAULT 0,
    token_output        INTEGER NOT NULL DEFAULT 0,
    token_total         INTEGER NOT NULL DEFAULT 0,
    cost_estimate       REAL    NOT NULL DEFAULT 0.0,
    currency            TEXT    NOT NULL DEFAULT 'USD',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    response_latency_ms INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES generation_tasks(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_costs_created ON cost_records (created_at);
CREATE INDEX IF NOT EXISTS idx_costs_task ON cost_records (task_id);
CREATE INDEX IF NOT EXISTS idx_costs_type ON cost_records (call_type);

-- ============================================================
-- 12. 文件夹监控配置
-- ============================================================

CREATE TABLE IF NOT EXISTS folder_monitors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT    NOT NULL UNIQUE,
    is_active   INTEGER NOT NULL DEFAULT 1,
    file_types  TEXT    NOT NULL DEFAULT '["txt", "md"]',  -- JSON array
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- 触发器: 自动更新 updated_at
-- ============================================================

CREATE TRIGGER IF NOT EXISTS trg_users_updated
AFTER UPDATE ON users
BEGIN UPDATE users SET updated_at = datetime('now') WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS trg_personas_updated
AFTER UPDATE ON personas
BEGIN UPDATE personas SET updated_at = datetime('now') WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS trg_posts_updated
AFTER UPDATE ON posts
BEGIN UPDATE posts SET updated_at = datetime('now') WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS trg_config_updated
AFTER UPDATE ON system_config
BEGIN UPDATE system_config SET updated_at = datetime('now') WHERE key = NEW.key; END;
