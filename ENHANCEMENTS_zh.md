# ENHANCEMENTS — voice-clone-video-dub

每个版本号背后的完整故事。面向用户的 CHANGELOG 见
[`CHANGELOG.md`](CHANGELOG.md)。

## v0.1.0 — 2026-06-10（首次发布）

Pipeline 在一次工作会话里经历了 5 轮迭代。每轮都是完整重跑；最终
落到 `voice-clone-video-dub/scripts/` 里的脚本是蒸馏结果。

### 每轮加了什么

| 轮 | 触发 | 改动 | 为什么 |
|---|---|---|---|
| **v1** | 第一次端到端 | XTTS v2 + Claude Code 翻译 | 证明跨语种克隆本地可行 |
| **v2** | `>>` 标记漏到字幕里 | 从 `zh.srt` 和 `zh.ass` 清掉说话人切换标记 | 字幕文本不该含元数据 |
| **v3** | 渲染输出少一段（62 段） | 加缺失段检查 + SRT 序号同步 | 138 段里少 1 段肉眼难发现 |
| **v4** | 参考音频残留 BGM | Demucs 分离源 30s 的人声 | 背景音乐污染克隆音色 |
| **v5** | 同 v4 但要全 10min | Demucs 全分离，从中间抽 30s 参考 | 更好的参考 = 更好的克隆，5min Demucs 划算 |

### 学到什么（已写进 SKILL.md）

1. **YouTube 增量字幕是 10ms "稳定"快照 + 2s "增长"快照穿插。** 稳定的是真值。`scripts/clean-subs.js` 合并它们。
2. **XTTS v2 + PyTorch 2.6+ 需要 `weights_only=False` patch。** TTS 0.22 + transformers 4.46 + torchcodec 是 macOS 14 + Apple Silicon 上唯一测过的组合。
3. **跨语种说话人分配需要 3 票。** 文本（Claude）~95% 准，语音（Resemblyzer）~95% 男 / ~85% 女，融合后 ~98%。
4. **对全 10min 跑 Demucs 值的。** 参考音频降噪 ~15dB，克隆明显更干净。
5. **参考段必须从 BGM 之后开始。** 0-15s 即使过了 Demucs 还有 BGM 残留。主持人 20-50s，嘉宾 90-120s。

### 最终一轮的质量数据

- 138 段字幕翻译，0 缺失
- 0 XTTS 合成失败
- Apple Silicon CPU 上 12 分钟
- 输出：93 MB MP4, 192 kbps AAC, h264 CRF 22
- 跨语种克隆质量：~70-80% 达云端 API（ElevenLabs/CosyVoice）水平。明显听得出是同一个人，但底下有 AI 韵律。

### 已知问题（v0.2 待办）

- 测试视频里 Anthropic 模型名被 ASR 听成 "Mythos"（应为 Opus）
- 约 3-5% 段有 200-500ms 口型失配（文本偏长，atempo 没完美对齐）
- 不支持 3+ 说话人
- 跨语种质量上限：XTTS v2 两年老模型，下一档得换 OpenVoice v3 / CosyVoice 2 / F5-TTS 或上云
