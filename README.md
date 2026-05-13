# X Intel Monitor

用 Hermes Agent 自动监控 X/Twitter 大佬推文的完整方案。数据采集 → AI 选题过滤 → 文案生成 → Discord 推送，全自动运行。

## 核心定位

帮人省掉「刷 timeline」这件苦力活，把精力留给真正需要判断的内容。

## 架构

```
BestBlogs OPML (160个AI圈账号)
        ↓
xgo.ing RSS 订阅服务（免费，无需 API Key）
        ↓
scripts/x_rss_fetcher.py    ← 并发抓取，48h窗口，ID去重
        ↓
Hermes Agent（配置 principles/writing_principles.md）
        ↓
Discord 频道                ← 推送格式化好的文案
```

## 目录结构

```
x-intel-monitor/
├── README.md
├── requirements.txt
├── .gitignore
│
├── scripts/
│   ├── x_rss_fetcher.py          # 免费方案：xgo.ing RSS，无需 API Key
│   └── twitter_fetch_tikhub.py    # 付费方案：TikHub SDK，需要 API Key
│
├── config/
│   ├── monitored_accounts.py      # TikHub 版本监控账号列表
│   └── cron_prompt.md             # 完整 cron prompt（可直接内联进 cron 配置）
│
└── principles/
    └── writing_principles.md       # 文案写作原则全文（旁观者腔根治方案）
```

## 数据源致谢

- **BestBlogs OPML**：by [@ginobefun](https://github.com/ginobefun/BestBlogs) — 160 个 AI 研究者/Lab/Builder/VC 的 Twitter 账号，已按语言（中英文）分类
- **xgo.ing**：将 Twitter 账号转 RSS 输出的免费服务

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

### 3. 采集数据

```bash
# 免费方案（xgo.ing RSS，无需配置）
python3 scripts/x_rss_fetcher.py

# 付费方案（TikHub SDK，需要 API Key）
# 1. 获取 API Key：https://tikhub.io
# 2. 设置环境变量：export TIKHUB_API_KEY=你的key
# 3. 运行：
python3 scripts/twitter_fetch_tikhub.py
```

### 4. 配置 Hermes Agent

把 `config/cron_prompt.md` 的完整内容复制进 Hermes Agent cron job 的 prompt 字段，
把 `principles/writing_principles.md` 作为写作原则 skill 加载。

### 5. 配置 Discord 推送

在 cron job 的 `deliver` 字段填入你的 Discord channel ID。

## 可选：Hermes Tweet 原生 X/Twitter 路线

现有 RSS 抓取流程可以继续作为默认数据源。如果你希望让 Hermes Agent 直接调用
X/Twitter 插件做后续搜索、监控和人工确认后的发布动作，可以安装
[Hermes Tweet](https://github.com/Xquik-dev/hermes-tweet)：

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
```

在 Hermes Agent 环境里设置 `XQUIK_API_KEY` 后，Hermes Tweet 会提供
`tweet_explore`、`tweet_read` 和 `tweet_action` 工具：

- 搜索 tweets 和 search Twitter/X，用关键词跟进 AI 话题
- 读取 tweet replies、look up users，并在发布后 monitor tweets
- 导出 followers，辅助判断账号来源和扩散质量
- 经过人工确认后 post tweets、post replies 或 send DMs

建议无人值守 cron 只调用搜索、读取、监控和导出类动作，把发推、回复和 DM 留给
人工确认流程。

## 核心依赖

| 依赖 | 说明 |
|------|------|
| [BestBlogs OPML](https://github.com/ginobefun/BestBlogs) | 账号来源，160个AI圈账号 |
| [xgo.ing](https://xgo.ing) | RSS 转换服务，零配置 |
| [TikHub SDK](https://tikhub.io) | 付费 API 备选方案 |

## 文案写作原则

详见 `principles/writing_principles.md`，核心要点：

- **不写标题**：开口即内容
- **旁观者腔是死罪**：禁止"有意思的是"、"他说的"、"言下之意"等句式
- **英文账号转发 400 字门槛**：写不够直接跳过
- **中文账号只写回复**：100字左右，不写转发
- **术语要消化**：英文名词翻译成人话说，不能直接贴

完整规范见 `principles/writing_principles.md`。

## 好文案锚点

参考 `references/good-fansi-examples.md` 和 `references/claude-managed-agents-example.md`
中的范本，出结果前对照自查。

## License

MIT
