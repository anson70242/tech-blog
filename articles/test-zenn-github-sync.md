---
title: "GitHub連携によるZenn記事の自動デプロイテスト"
emoji: "🚀"
type: "tech"
topics: ["github", "zenn", "markdown"]
published: true
---

> 🌐 **English version is available here:** [Testing Automated Blogging with Hashnode and GitHub](#)

## はじめに

GitHubリポジトリとZennの連携テスト用の記事です。
ローカルのMarkdownファイルをプッシュして、正しく反映されるか確認しています。

## 動作確認項目

- マークダウンの基本記法（見出し・リスト・引用）
- コードブロックのシンタックスハイライト
- 数式（KaTeX）のレンダリング

```python
def greet(platform: str) -> str:
    return f"Hello, {platform}!"

print(greet("Zenn"))
```

インライン数式 $E = mc^2$ とブロック数式の表示テスト：

$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$

## おわりに

表示に問題がなければ、このテスト記事は削除するか、内容を書き換えて最初の記事として公開します。