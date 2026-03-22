# 🎵 CLAC Codec

**Cole's Lossless Audio Codec Library** - A pure Python lossless audio compression engine

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)
![Pure Python](https://img.shields.io/badge/Pure_Python-Yes-brightgreen.svg)

---

## 🌟 Overview

**CLAC** (Cole's Lossless Audio Codec) is a pure Python implementation of a lossless audio compression algorithm. It's designed to be:

- **Simple** - Easy to understand and modify
- **Educational** - Demonstrates compression principles
- **Functional** - Actually works for real audio files
- **Extensible** - Can be ported to other languages

This is the **codec library only**. For a full GUI application, see [CLAC Studio](https://github.com/clacstudios/clac-studio).

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 🎯 **Lossless** | Bit-perfect audio reconstruction |
| 🔄 **Streaming** | Decode while playing (no full decompression) |
| 📦 **Block-Based** | Processes audio in 4096-sample blocks |
| 🔍 **Verification** | Built-in file integrity checking |
| 📊 **Progress** | Callback support for progress tracking |
| 💾 **Memory Efficient** | Optional byte-stream output |

### Technical Specs

| Specification | Value |
|--------------|-------|
| **Input Format** | WAV (16-bit PCM) |
| **Output Format** | CLAC (custom binary) |
| **Sample Rates** | Any (8kHz - 192kHz) |
| **Channels** | Any (Mono, Stereo, Multi) |
| **Bit Depth** | 16-bit |
| **Compression** | Lossless (typically 30-60%) |

---

## 📥 Installation

### Quick Install

```bash
# Clone or download
git clone https://github.com/clacstudios/clac.git
cd clac

# Copy to your project
cp source.py /your/project/
