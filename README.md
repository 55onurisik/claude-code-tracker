# claude-code-tracker

Claude Code plugin — her prompt'u ve gerçek token kullanımını SQLite'a kaydeder.

---

## Kurulum (Mac / Linux / Windows)

### Adım 1 — Gereksinimleri kur

- [Python 3.8+](https://www.python.org/downloads/) ✓
- [Git](https://git-scm.com/downloads) ✓
- [Claude Code](https://claude.ai/code) ✓

### Adım 2 — Tek komutla kur

**Mac / Linux (Terminal):**
```bash
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/55onurisik/claude-code-tracker/main/install.py').read())"
```

**Windows (CMD veya PowerShell):**
```
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/55onurisik/claude-code-tracker/main/install.py').read())"
```

Bu komut repoyu otomatik olarak doğru yere indirir ve yapılandırır.

### Adım 3 — Claude Code'u yeniden başlat

Tamamen kapat, tekrar aç.

### Adım 4 — Test et

Claude Code'da çalıştır:
```
/token-tracker:stats
```

---

## Komutlar

| Komut | Ne yapar |
|---|---|
| `/token-tracker:stats` | Genel dashboard: toplam token, maliyet, model dağılımı |
| `/token-tracker:today` | Bugünkü prompt'lar ve token kullanımı |
| `/token-tracker:cost` | Günlük/haftalık/aylık maliyet raporu |
| `/token-tracker:search <kelime>` | Geçmiş prompt'larda arama |
| `/token-tracker:export [csv\|json]` | Tüm veriyi dışa aktar |
| `/token-tracker:reset` | Veritabanını sıfırla (onay ister) |

---

## Nasıl çalışır

```
Prompt yazarsın
    ↓
UserPromptSubmit hook → prompt veritabanına kaydedilir
    ↓
Claude yanıt verir
    ↓
Stop hook (async) → transcript JSONL okunur
    → Gerçek token sayıları çekilir (input, output, cache)
    → Maliyet hesaplanır
    → responses tablosuna kaydedilir
```

Token verileri Claude'un kendi transcript dosyalarından (`~/.claude/projects/`) okunur — tahmin değil, gerçek API değerleri.

---

## Veritabanı

| Platform | Konum |
|---|---|
| Mac / Linux | `~/.claude-tracker/tracker.db` |
| Windows | `C:\Users\<kullanici>\.claude-tracker\tracker.db` |

---

## Güncelleme

Aynı kurulum komutunu tekrar çalıştır, mevcut veriyi silmez.

---

## Lisans

MIT
