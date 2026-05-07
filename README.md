# X Intel Monitor

用 Hermes Agent 自动监控 X/Twitter 大佬推文的完整方案。数据采集 → AI 选题过滤 → 文案生成 → Discord 推送，全自动运行。

**核心定位**：帮人省掉「刷 timeline」这件苦力活，把精力留给真正需要判断的内容。

## 架构

```
BestBlogs OPML (160个AI圈账号)
        ↓
xgo.ing RSS 订阅服务（免费，无需 API Key）
        ↓
x_rss_fetcher.py   ← 并发抓取，48h窗口，ID去重
        ↓
Hermes Agent（配置 ljg 写作原则）  ← 选题判断 + 文案生成
        ↓
Discord 频道       ← 推送格式化好的文案
```

## 数据源致谢

- **账号列表**：[BestBlogs RSS Twitters OPML](https://github.com/ginobefun/BestBlogs) by [@ginobefun](https://x.com/ginobefun) — 160 个 AI 研究者/Lab/Builder/VC 的 Twitter 账号，已按语言（中英文）分类
- **RSS 服务**：xgo.ing — 将 Twitter 账号转 RSS 输出的免费服务

## 核心依赖

| 依赖 | 说明 |
|------|------|
| [BestBlogs OPML](https://github.com/ginobefun/BestBlogs) | 账号来源，160个AI圈账号 |
| [xgo.ing](https://xgo.ing) | RSS 转换服务，零配置 |
| [ljg 写作原则](https://hermes-agent.nousresearch.com) | 文案写作标准，踩坑者视角，非旁观者腔 |

## 快速开始

### 1. 克隆

```bash
git clone https://github.com/SIXIANGGUO/x-intel-monitor.git
cd x-intel-monitor
```

### 2. 安装依赖

```bash
pip3 install feedparser
```

### 3. 运行采集

```bash
python x_rss_fetcher.py
```

输出：`fetched-tweets.json`，包含最近48小时内所有账号的新推文（已去重）。

## 开源内容说明

本 repo 仅开源 `x_rss_fetcher.py`（xgo.ing RSS 采集方案），完全免费，零配置。

**未开源的部分**：
- TikHub SDK 采集脚本（`twitter_fetch_concurrent.py`）— 含 API Key，不适合公开
- Hermes cron prompt 和文案写作规则 — 是自己的迭代成果，未整理开源
- 监控账号列表 — 含特定账号选择逻辑，是自己的整理结果

如需 TikHub SDK 版本，需自行注册 tikhub.io 获取 API Key 后参考 `x_rss_fetcher.py` 的逻辑自行实现。

## 文件说明

| 文件 | 说明 |
|------|------|
| `x_rss_fetcher.py` | 采集脚本，xgo.ing RSS 并发抓取，48h窗口，ID去重 |
| `requirements.txt` | Python 依赖（仅 feedparser） |

## 两套抓取方案对比

| | xgo.ing RSS（开源这套） | TikHub SDK（需单独配置） |
|--|----------------------|------------------------|
| 费用 | 免费 | 有（~¥0.001/请求） |
| 覆盖 | 原文推文，漏转发/QT | 全覆盖（原文+转发+引用） |
| 配置 | `pip3 install feedparser` 即可 | 需注册 tikhub.io + API Key |
| 推荐场景 | 日常监控首选 | 想抓全量时补充 |

## 完整自动监控配置

本项目只包含数据采集层。要跑完整流水线（采集 → 写作 → 推送），需要配合 Hermes Agent：

1. 把 `x_rss_fetcher.py` 的输出路径改为绝对路径（默认是脚本同目录下 `fetched-tweets.json`）
2. 在 Hermes 中配置 cron job，定时运行采集 + AI 文案生成
3. 文案写作标准参考 [ljg 写作原则](https://hermes-agent.nousresearch.com)，核心是：踩坑者视角、不当翻译/旁观者、文案按账号语言分流

详细配置方法见完整文章：*如何利用 Hermes 快速获取 X 上的大佬推文*

## 开源协议

MIT License。

## 相关项目

- [BestBlogs](https://github.com/ginobefun/BestBlogs) — AI/Startup/VC Twitter 账号 OPML 维护者
- [ljg 写作原则](https://hermes-agent.nousresearch.com) — 本系统文案写作标准来源，踩坑者视角，非旁观者腔
- [Hermes Agent](https://hermes-agent.nousresearch.com) — 本系统运行的 AI Agent 框架
