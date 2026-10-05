# AI Bill of Materials: local-AI 800-171A assessment

Generated 2026-10-05T18:33:00Z. Machine-readable twin: `aibom.cdx.json` (CycloneDX 1.6). Regenerate for your own setup with `aibom/make_aibom.py`.

## Model

| | |
|---|---|
| Name | Gemma 4 26B A4B QAT |
| Catalog id | `google/gemma-4-26b-a4b-qat` |
| Publisher | google |
| Parameters | 26B |
| Architecture | gemma4 |
| Quantization | 4bit |
| Format | safetensors |
| Maximum context | 262144 tokens |
| Files obtained from | https://huggingface.co/lmstudio-community/gemma-4-26B-A4B-it-QAT-MLX-4bit (revision aa5e2e50376f54254d503276ca2222ea8569b95e; license Apache-2.0) |

SHA-256 of every model file (compare yours to confirm you have the same weights):

| File | Bytes | SHA-256 |
|---|---|---|
| chat_template.jinja | 18245 | `29af862bccabb14b90a4ff951bcd14c33fe74b651c5f07fc7f2e9aa46a59fe7c` |
| config.json | 33376 | `29910322dd085f45c8f95c6c0f1611b20f722d6f6c8394321b34817e98a972fa` |
| generation_config.json | 203 | `b69207f9be617e982d13cc273cce6fd88c98dda99a4bdc5e2d52ffe0a0d9f0a9` |
| model-00001-of-00003.safetensors | 5275612587 | `898863f0d5eba7153a9c9b9443aac1969809f2149e88481c725b6da40783f129` |
| model-00002-of-00003.safetensors | 5296718232 | `2abdca76ed4a647cfe8af680908894e2709b4e1221ddbbbef1b1edb14f60e303` |
| model-00003-of-00003.safetensors | 5036507755 | `a554f0fdb61bc9e510a5318e723a780c31434fd3e3dcdd3c16c700f835ade7b7` |
| model.safetensors.index.json | 176940 | `5455e83705bbdd4e3702c7d4f9d49d4900e84533036628f74500538075dd5c80` |
| processor_config.json | 902 | `1bd0d00776284f369c1eff5fb631e865dfcdca861e0b7d60dbef27fcf37436a8` |
| tokenizer.json | 32169626 | `cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f` |
| tokenizer_config.json | 21874 | `91fe431216b0e1ce89d685b47ff0dbf69175c2f962d396edc97844b077bdfab3` |

## Settings used

| Setting | Value |
|---|---|
| temperature | 0.2 |
| max_tokens per reply | 8192 |
| context window loaded | 65536 tokens |
| base step limit per requirement | 24 (+1 per objective beyond six) |
| conversation budget | 120000 characters, older tool output trimmed |
| tool output cap | 6000 characters |

## Prompts

SHA-256 of the instruction text the model receives (a change to either changes the result):

| Prompt | SHA-256 |
|---|---|
| RULES | `1af62da74f1f10b52c3fb076bef228d6f27252cc5f232567e329e18fff3e3abf` |
| REV3_RULE | `3c8ea35a129319234ec63875b6590d729ed9624ad38e83037a62abb9f74e277a` |

## Software

| Component | Version | Role |
|---|---|---|
| LM Studio | 0.4.25+1 | serves the model locally (OpenAI-style API on localhost:1234) |
| Python | 3.9.6 | runs the assessor, graders and tests |
| OpenSSH | 10.3p1 | the one read-only connection to the target |
| macOS sandbox-exec | 26.7 | limits what the AI can read and reach |
| Assessor (this repository) | commit 4287148 | the runner, command list, graders |

## Hardware and operating system

- Apple M4 Pro, 64 GB memory
- macOS 26.7

## Data given to the AI

| Item | Version | SHA-256 |
|---|---|---|
| NIST SP 800-171 Rev 3 OSCAL catalog | 1.1.0 | `21b6f3b118b6e5b305aaed3a0e4b70fa5d1d9aa388a0b92e7d6ddfed69e93ac3` |
| Rev 3 objective kit | generated; see kit header | `270b0966b11400886ce176ca43cd078496ce5dad3718a0c2ff2d70d051875428` |
| Rev 2 objective kit | generated; see kit header | `a5d77033eb8d134b6ff694e8151ee47b78c5d7345603d228d734f4b7f4228ecd` |

Target: a Linux server (read-only commands over SSH) plus a read-only copy of the organization's documents.

## What is not in this list

- The organization's own documents and the answer keys (private by design).
- Anything the model learned in training: the publisher's model card is the source for that.
