# 🎙️ voice-clone-video-dub v0.1.0

<p align="center">
  <img src="https://img.shields.io/badge/Mavis-技能-blueviolet">
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/license-MIT-green">
  <img src="https://img.shields.io/badge/克隆-XTTS%20v2-orange">
  <img src="https://img.shields.io/badge/分离-Demucs%20v4-blue">
  <img src="https://img.shields.io/badge/翻译-Claude%20Code-purple">
</p>

<p align="center">
  <b>把任意 YouTube 视频变成中文克隆配音 + 烧录硬字幕的成片。</b><br>
  <sub>对比：<a href="#-vs-普通翻译流程">vs 普通翻译流程</a> · <a href="#-vs-云端克隆-api">vs 云端克隆 API</a> · <a href="#-vs-专业配音棚">vs 专业配音棚</a></sub>
</p>

<p align="center">
  <a href="README.md">🇺🇸 English</a> · <b>🇨🇳 中文</b> · <a href="README_ja.md">🇯🇵 日本語</a> · <a href="README_ko.md">🇰🇷 한국어</a> · <a href="README_es.md">🇪🇸 Español</a> · <a href="README_fr.md">🇫🇷 Français</a> · <a href="README_de.md">🇩🇪 Deutsch</a> · <a href="README_pt.md">🇵🇹 Português</a> · <a href="README_ru.md">🇷🇺 Русский</a>
</p>

<p align="center">
  <img src="screenshot-lenny.png" width="720" alt="Lenny 英文开场帧">
</p>

---

## ⚡ 一句话总结

> 别的翻译工具给你"视频 + 中文字幕"。**voice-clone-video-dub**
> 还会克隆原说话人的音色，用他们"本来的声音"念中文——同一个
> 人，不同的语言。

你给一个 YouTube 链接，它给你一个 10 分钟 MP4：Lenny 和 Cat Wu
听起来还是他们自己，只是在说中文，屏幕上有烧录的硬字幕。

---

## 📊 vs 普通翻译流程

市面上大多数"翻译视频"工具只到硬字幕就停。**声音克隆**才是差异点：

|  | 字幕版（多数工具） | 字幕 + 通用 TTS（少数） | voice-clone-video-dub（这个） |
|---|---|---|---|
| 目标语言字幕 | ✅ | ✅ | ✅ |
| 字幕烧录到视频 | ✅ | ✅ | ✅ |
| 替换原声 | ❌ | ✅ 通用 TTS 音 | ✅ **克隆自原说话人** |
| 音色匹配原说话人 | — | ❌ | ✅ 同音色，不同语言 |
| 说话人分配 | — | ❌ | ✅ 3-vote 校验 |
| 背景音乐清理 | — | ❌ | ✅ Demucs 人声分离 |
| 10 分钟视频成本 | — | 看产品 | 🆓 本地免费 |
| 隐私 | — | ☁️ 云端 | ✅ 100% 本地 |

**结论：字幕是翻译，克隆才是"配音"的另一半。**

---

## 📊 vs 云端克隆 API（ElevenLabs / Fish / CosyVoice）

|  | ElevenLabs / Fish / CosyVoice | voice-clone-video-dub（这个） |
|---|---|---|
| 音频上云 | ☁️ 是 | ✅ 不上云，全本地 |
| 10 分钟配音成本 | ~$1-5 | 🆓 免费 |
| 跨语种（EN→ZH）质量 | ✅ 业界顶 | ⚠️ XTTS v2 上限，约 70-80% |
| 安装时间 | 5 分钟（API key） | 10-15 分钟（一次性 venv） |
| 联网 | 需要 | ✅ 不用（下完模型后） |
| 可定制 | ❌ 受限于厂商 | ✅ 完整源码 |
| 隐私 | ⚠️ 看厂商 ToS | ✅ 100% 本地 |

要 **隐私 + 免费 + 够用** → 用这个。要 **录音棚级跨语种质量** + 不在乎钱 → 用 ElevenLabs。

---

## 📊 vs 专业配音棚

|  | 配音棚 | voice-clone-video-dub |
|---|---|---|
| 10 分钟视频耗时 | 1-2 周 | 30-40 分钟 |
| 10 分钟视频成本 | $500-2000 | 🆓 免费 |
| 音色匹配 | ✅ 接近 | ⚠️ 像音色，不像身份 |
| 口型对齐 | ✅ 完美 | ⚠️ 文本对齐（per-segment atempo） |
| 背景音乐 | ✅ 保留 | ⚠️ 被配音盖掉 |
| 规模化 | ❌ 成本线性 | ✅ CPU 时间线性 |

个人项目 / YouTube 教程 / 学习片段：用这个。院线发行：还得请配音棚。

---

## 🚀 快速开始

在 Mavis 里（任何加载了这个 skill 的 LLM）给它一个 YouTube 链接：

> "https://www.youtube.com/watch?v=... — 把这 10 分钟翻译成中文，加硬字幕，克隆说话人声音"

skill 会：
1. 下载并裁剪视频
2. 用 Claude Code 并行翻译字幕
3. 判定每段说话人（3-vote：文本 + 声纹 + 手动）
4. （可选）通过 XTTS v2 克隆声音
5. 烧字幕 + 渲染最终 MP4

## 📥 安装（一次性）

```bash
git clone https://github.com/KevPH2026/voice-clone-video-dub.git
cd voice-clone-video-dub
bash voice-clone-video-dub/scripts/install-deps.sh
brew install ffmpeg-full yt-dlp
claude auth login
export HF_ENDPOINT=https://hf-mirror.com  # 仅当 HuggingFace 访问不通时
```

或者照 `voice-clone-video-dub/references/xtts-setup.md` 手动装。

## 🎯 试个样本

```bash
# 装完后，在加载了 skill 的 Mavis 里说：
# "https://www.youtube.com/watch?v=PplmzlgE0kg&t=399s — 翻译成中文"
#
# skill 会：
#   - 从 t=399s 下载 10 分钟
#   - 生成 <title>_zh_dub.mp4 (~90MB)
#   - 放到 Mavis workspace
```

上面那个 YouTube 链接就是 Lenny's Podcast 跟 Cat Wu（Anthropic Claude Code 产品负责人）那期——本仓库 demo 片段的原片。

---

## 📄 协议

MIT — 见 [`LICENSE`](LICENSE)。
