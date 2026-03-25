# 本地四模式最小生成回归（阶段 0 补充）

## 执行环境

项目路径：`/root/.openclaw/workspace/quanzhen-night-journal`

本次验证使用本地 `.env`：
- `ENGINE_ROOT=/root/.openclaw/workspace/quanzhen-night-journal`
- `BLOG_OUTPUT_DIR=/root/.openclaw/workspace/quanzhen-night-journal/.tmp-output`
- `LOG_DIR=/root/.openclaw/workspace/quanzhen-night-journal/logs`

注意：
- 本次仅验证本地控制流与模式边界
- 未接入真实可用模型密钥，因此生成链路中的模型调用阶段预期失败
- 这意味着本轮验证的重点是：
  - 模式阻断是否生效
  - 本地路径隔离是否生效
  - 失败是否被记录到日志

---

## 回归用例结果

### 1. `review-first`
结果：**失败（符合当前无可用模型前提）**

现象：
- 运行退出码为 `1`
- 日志记录 `HTTP Error 401: Unauthorized`

说明：
- 流程进入了生成链路
- 失败点在模型调用，而不是路径或模式判断

### 2. `manual-only`
结果：**通过**

现象：
- 运行退出码为 `1`
- 日志明确记录：`Mode is manual-only; timer publish refused.`

说明：
- 自动发布阻断逻辑正常
- 模式判断优先于后续生成流程

### 3. `auto`
结果：**失败（符合当前无可用模型前提）**

现象：
- 运行退出码为 `1`
- 日志记录 `HTTP Error 401: Unauthorized`

说明：
- 自动模式控制流能进入生成阶段
- 当前未进入落盘/Hugo 阶段，因为模型调用未成功

### 4. `pause_publishing=true`
结果：**通过**

现象：
- 运行退出码为 `1`
- 日志明确记录：`Publishing paused by manual override.`

说明：
- 暂停发布阻断逻辑正常
- 阻断发生在发布链之前

---

## 本轮结论

### 已验证通过的内容
- `manual-only` 阻断逻辑正常
- `pause_publishing` 阻断逻辑正常
- 本地日志记录正常
- 本地输出目录隔离正常（未写入生产路径）
- 本地 override 切换与恢复流程正常

### 当前仍未完成的内容
- `review-first` 成功生成并落草稿
- `auto` 成功生成并写入本地输出目录
- Hugo 本地构建链验证

### 未完成原因
不是模式逻辑故障，而是：
- 本地未配置可用模型凭据
- 生成链路在 API 调用处即失败

---

## 阶段 0 状态判断

到目前为止，阶段 0 已经完成了：
1. 本地项目路径确认
2. 基线差异识别
3. `.env` 建立
4. runtime state bootstrap
5. `analyze_journal.py` 本地可运行
6. 四模式中的两种阻断逻辑已验证通过
7. 失败日志链路已验证通过

因此可以认为：
- **阶段 0 的“本地开发基线建立”已基本成立**
- 但严格意义上的“完整生成链回归”仍需等待可用模型凭据，或在后续加入 mock llm 客户端后完成

---

## 对后续阶段的建议

进入阶段 1 时，可先不要求真实模型可用；优先做：
- 包骨架建立
- config / models / application 收口
- 为后续引入 mock llm 留出注入点

这样能避免后续重构继续被外部 API 可用性牵制。
