from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import aiofiles

from backend.adapters.caddy_adapter import CaddyAdapter
from backend.config import Settings, get_settings
from backend.engine.config_store import ConfigStore
from backend.utils.time import utcnow_iso


CLOUDFLARE_NETWORKS = (
    ipaddress.ip_network("103.21.244.0/22"),
    ipaddress.ip_network("103.22.200.0/22"),
    ipaddress.ip_network("103.31.4.0/22"),
    ipaddress.ip_network("104.16.0.0/12"),
    ipaddress.ip_network("108.162.192.0/18"),
    ipaddress.ip_network("131.0.72.0/22"),
    ipaddress.ip_network("141.101.64.0/18"),
    ipaddress.ip_network("162.158.0.0/15"),
    ipaddress.ip_network("172.64.0.0/13"),
    ipaddress.ip_network("173.245.48.0/20"),
    ipaddress.ip_network("188.114.96.0/20"),
    ipaddress.ip_network("190.93.240.0/20"),
    ipaddress.ip_network("197.234.240.0/22"),
    ipaddress.ip_network("198.41.128.0/17"),
    ipaddress.ip_network("2400:cb00::/32"),
    ipaddress.ip_network("2405:8100::/32"),
    ipaddress.ip_network("2405:b500::/32"),
    ipaddress.ip_network("2606:4700::/32"),
    ipaddress.ip_network("2803:f800::/32"),
    ipaddress.ip_network("2a06:98c0::/29"),
    ipaddress.ip_network("2c0f:f248::/32"),
)


@dataclass(slots=True)
class DomainInspection:
    normalized_domain: str
    enabled: bool
    reason: str
    resolved_ips: list[str]


class SiteRuntimeManager:
    def __init__(
        self,
        config_store: ConfigStore,
        settings: Settings | None = None,
        caddy_adapter: CaddyAdapter | None = None,
    ):
        self.config_store = config_store
        self.settings = settings or get_settings()
        self.caddy_adapter = caddy_adapter or CaddyAdapter()

    async def apply(self) -> dict[str, object]:
        site_title = (await self.config_store.get("site.title", "全真夜记")) or "全真夜记"
        site_subtitle = (await self.config_store.get("site.subtitle", "")) or ""
        theme = (await self.config_store.get("hugo.theme", "PaperMod")) or "PaperMod"
        domain = (await self.config_store.get("site.domain", "")) or ""
        inspection = await self.inspect_domain(domain)

        base_url = f"https://{inspection.normalized_domain}/" if inspection.enabled else "/"
        caddyfile = self._render_caddyfile(inspection.normalized_domain if inspection.enabled else "")
        hugo_config = self._render_hugo_config(
            site_title=site_title,
            site_subtitle=site_subtitle,
            theme=theme,
            base_url=base_url,
        )
        support_pages_changed = await self._sync_support_pages(site_title=site_title, site_subtitle=site_subtitle)

        await self._write_if_changed(self.settings.runtime_caddyfile_path, caddyfile)
        hugo_changed = await self._write_if_changed(self.settings.runtime_hugo_config_path, hugo_config)
        if hugo_changed or support_pages_changed:
            await self._trigger_hugo_rebuild()

        await self.config_store.set("site.domain", inspection.normalized_domain, category="site")
        await self.config_store.set("site.domain_enabled", "1" if inspection.enabled else "0", category="site")
        await self.config_store.set("site.domain_status", "enabled" if inspection.enabled else "disabled", category="site")
        await self.config_store.set("site.domain_reason", inspection.reason, category="site")
        await self.config_store.set("site.domain_checked_at", utcnow_iso(), category="site")
        await self.config_store.set("hugo.base_url", base_url, category="hugo")

        caddy_reload = False
        caddy_reload_error = ""
        try:
            caddy_reload = await self.caddy_adapter.reload(caddyfile)
        except Exception as exc:  # pragma: no cover - depends on runtime network/container state
            caddy_reload_error = str(exc)

        return {
            "domain": inspection.normalized_domain,
            "enabled": inspection.enabled,
            "reason": inspection.reason,
            "resolved_ips": inspection.resolved_ips,
            "base_url": base_url,
            "caddy_reloaded": caddy_reload,
            "caddy_reload_error": caddy_reload_error,
        }

    async def _sync_support_pages(self, *, site_title: str, site_subtitle: str) -> bool:
        description = site_subtitle.strip() or "记录深夜写作、自动生成与人工修订后的夜记。"
        pages = {
            "about.md": self._render_about_page(site_title=site_title, description=description),
            "archives.md": self._render_archives_page(),
            "search.md": self._render_search_page(),
        }
        changed = False
        for name, content in pages.items():
            if await self._write_if_changed(self.settings.hugo_content_path / name, content):
                changed = True
        return changed

    async def inspect_domain(self, raw_domain: str) -> DomainInspection:
        domain = self._normalize_domain(raw_domain)
        if not domain:
            return DomainInspection("", False, "未配置域名，系统当前运行于 IP 模式。", [])
        if self._looks_like_ip(domain):
            return DomainInspection(domain, False, "检测到填写的是 IP 地址而非域名，HTTPS 自动接入不会启用。", [])

        resolved_ips = await self._resolve_domain_ips(domain)
        if not resolved_ips:
            return DomainInspection(domain, False, "域名当前没有可用的 A/AAAA 解析记录。", [])

        server_ips = self._candidate_server_ips()
        if not server_ips:
            return DomainInspection(
                domain,
                False,
                "无法确认当前服务器公网 IP，请设置 PUBLIC_SERVER_IP 后重试。",
                resolved_ips,
            )
        if not set(resolved_ips).intersection(server_ips):
            if self.settings.allow_cloudflare_proxy_domain and self._all_cloudflare_ips(resolved_ips):
                return DomainInspection(
                    domain,
                    True,
                    "检测到 Cloudflare 代理，已按代理模式启用 HTTPS 申请。",
                    resolved_ips,
                )
            return DomainInspection(
                domain,
                False,
                f"DNS 解析未直连当前服务器。当前解析: {', '.join(resolved_ips)}；服务器期望: {', '.join(sorted(server_ips))}",
                resolved_ips,
            )
        return DomainInspection(domain, True, "域名解析已对准当前服务器，可启用 HTTPS。", resolved_ips)

    async def _resolve_domain_ips(self, domain: str) -> list[str]:
        def _lookup() -> list[str]:
            try:
                records = socket.getaddrinfo(domain, None, proto=socket.IPPROTO_TCP)
            except socket.gaierror:
                return []
            results = sorted({item[4][0] for item in records if item and item[4]})
            return results

        return await asyncio.to_thread(_lookup)

    def _candidate_server_ips(self) -> set[str]:
        results: set[str] = set()
        raw_public = (self.settings.public_server_ip or "").strip()
        for part in raw_public.split(","):
            value = part.strip()
            if value:
                results.add(value)
        try:
            hostname = socket.gethostname()
            for item in socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP):
                if item and item[4]:
                    ip = item[4][0]
                    if not ip.startswith("127.") and ip != "::1":
                        results.add(ip)
        except socket.gaierror:
            pass
        return results

    async def _write_if_changed(self, path: Path, content: str) -> bool:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text(encoding="utf-8") == content:
            return False
        async with aiofiles.open(path, "w", encoding="utf-8") as handle:
            await handle.write(content)
        return True

    async def _trigger_hugo_rebuild(self) -> None:
        self.settings.build_signal_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(self.settings.build_signal_path, "w", encoding="utf-8") as handle:
            await handle.write(utcnow_iso())

    def _normalize_domain(self, raw_domain: str) -> str:
        value = raw_domain.strip()
        if not value:
            return ""
        if "://" not in value:
            value = f"https://{value}"
        parsed = urlparse(value)
        domain = parsed.netloc or parsed.path
        return domain.strip().strip("/")

    def _looks_like_ip(self, value: str) -> bool:
        try:
            socket.inet_aton(value)
            return True
        except OSError:
            return False

    def _all_cloudflare_ips(self, values: list[str]) -> bool:
        if not values:
            return False
        try:
            return all(
                any(ipaddress.ip_address(value) in network for network in CLOUDFLARE_NETWORKS)
                for value in values
            )
        except ValueError:
            return False

    def _render_caddyfile(self, domain: str) -> str:
        email_line = f"    email {self.settings.acme_email}\n" if self.settings.acme_email else ""
        admin_block = "{\n    admin 0.0.0.0:2019\n" + email_line + "}\n\n"
        console = (
            "(qz_console) {\n"
            "    redir /admin /admin/ 308\n\n"
            "    handle_path /admin/* {\n"
            "        root * /srv/webui\n"
            "        header Cache-Control \"no-store\"\n"
            "        try_files {path} /index.html\n"
            "        file_server\n"
            "    }\n\n"
            "    @api path /api /api/*\n"
            "    handle @api {\n"
            "        reverse_proxy core:8000\n"
            "    }\n\n"
            "    @console_root path /\n"
            "    redir @console_root /admin/ 308\n\n"
            "    respond 404\n"
            "}\n\n"
        )
        blog = (
            "(qz_blog) {\n"
            "    @blocked path /admin /admin/* /api /api/*\n"
            "    respond @blocked 404\n\n"
            "    root * /srv/hugo\n"
            "    file_server\n"
            "}\n\n"
        )
        site_5210 = (
            ":5210 {\n"
            "    import qz_console\n"
            "}\n"
        )
        if not domain:
            return admin_block + console + blog + site_5210
        return admin_block + console + blog + site_5210 + f"\n{domain} {{\n    import qz_blog\n}}\n"

    def _render_hugo_config(
        self,
        *,
        site_title: str,
        site_subtitle: str,
        theme: str,
        base_url: str,
    ) -> str:
        description = site_subtitle.strip() or "记录深夜写作、自动生成与人工修订后的夜记。"
        return (
            f'baseURL = {self._toml_string(base_url)}\n'
            'languageCode = "zh-cn"\n'
            f"title = {self._toml_string(site_title)}\n"
            f"theme = {self._toml_string(theme)}\n\n"
            "[params]\n"
            "ShowReadingTime = true\n"
            "ShowShareButtons = false\n"
            "ShowCodeCopyButtons = false\n"
            "ShowBreadCrumbs = true\n"
            "ShowPostNavLinks = true\n"
            "ShowRssButtonInSectionTermList = true\n"
            'defaultTheme = "light"\n'
            "disableThemeToggle = true\n"
            f"description = {self._toml_string(description)}\n\n"
            "[params.label]\n"
            f"text = {self._toml_string(site_title)}\n\n"
            "[params.homeInfoParams]\n"
            'Title = "这个博客是什么"\n'
            f'Content = {self._toml_string(description)}\n\n'
            "[markup]\n"
            "[markup.goldmark]\n"
            "[markup.goldmark.renderer]\n"
            "unsafe = false\n\n"
            "[outputs]\n"
            'home = ["HTML", "RSS", "JSON"]\n\n'
            "[[menu.main]]\n"
            'identifier = "home"\n'
            'name = "首页"\n'
            'url = "/"\n'
            "weight = 10\n\n"
            "[[menu.main]]\n"
            'identifier = "archives"\n'
            'name = "归档"\n'
            'url = "/archives/"\n'
            "weight = 20\n\n"
            "[[menu.main]]\n"
            'identifier = "search"\n'
            'name = "搜索"\n'
            'url = "/search/"\n'
            "weight = 30\n\n"
            "[[menu.main]]\n"
            'identifier = "about"\n'
            'name = "关于"\n'
            'url = "/about/"\n'
            "weight = 40\n"
        )

    def _render_about_page(self, *, site_title: str, description: str) -> str:
        return (
            "---\n"
            'title: "关于"\n'
            f'description: "{description}"\n'
            "---\n\n"
            f"{site_title} 是一个持续写作的夜间博客。\n\n"
            "这里会发布自动生成后的稿件，也会保留人工修订与审核后的版本。\n\n"
            "如果你是第一次来到这里，可以先看首页最新文章，也可以去归档页按时间翻阅，或直接用搜索查找关键词。\n"
        )

    def _render_archives_page(self) -> str:
        return (
            "---\n"
            'title: "归档"\n'
            'layout: "archives"\n'
            'description: "按时间回看已经发布的夜记。"\n'
            'summary: "按时间回看已经发布的夜记。"\n'
            "---\n"
        )

    def _render_search_page(self) -> str:
        return (
            "---\n"
            'title: "搜索"\n'
            'layout: "search"\n'
            'description: "搜索已经发布的文章、摘要和正文内容。"\n'
            'summary: "搜索已经发布的文章、摘要和正文内容。"\n'
            'placeholder: "输入标题、摘要或正文关键词后回车"\n'
            "---\n"
        )

    def _toml_string(self, value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
