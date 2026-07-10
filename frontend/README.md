# 管理后台前端

浅色默认、左侧栏导航的 SaaS 风格管理后台。

```bash
npm ci
npm run dev      # 开发
npm run build    # 构建
npm test         # 单测
```

生产构建由 `caddy/Dockerfile` 多阶段构建打入 `qz-caddy` 镜像，经 `http://<IP>:5210/admin/` 访问。
