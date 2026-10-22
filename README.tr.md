# git-stats-lite

Yerel git geçmişinden hızlı ve gizlilik odaklı depo istatistikleri; harici çalışma zamanı bağımlılığı gerektirmez.

`git-stats-lite`, harici bir Python kütüphanesine ihtiyaç duymadan ve ağ üzerinden herhangi bir veri göndermeden `git log --numstat` komutunu alt süreç (subprocess) üzerinden akış mantığıyla okur. Aktivite sıcaklık haritalarını, katkıcı istatistiklerini, dosya değişim yoğunluklarını, programlama dillerini ve otobüs faktörü (bus factor) metriklerini hesaplar.

[English Documentation (README.md)](README.md)

---

## Özellikler

- **Sıfır Çalışma Zamanı Bağımlılığı:** Yalnızca Python standart kütüphanesini kullanır. Python >= 3.10 ve sistemde kurulu bir `git` ikili dosyası yeterlidir.
- **Akış Temelli Ayrıştırma (Streaming):** `git log --numstat` çıktısını standart çıktıdan satır satır okur. Depodaki commit sayısından bağımsız olarak sabit bellek (O(1)) ile çalışır.
- **Yazar Kimliği Normalizasyonu:**
  - `git log --use-mailmap` ve yerleşik `.mailmap` ayrıştırma desteği.
  - GitHub (`<id>+<kullanici>@users.noreply.github.com`) ve GitLab noreply e-posta adreslerini otomatik olarak standart kullanıcı kimlikleriyle birleştirme.
- **Aktivite Sıcaklık Haritası:** Hem yazarın yerel saat diliminde hem de UTC saat diliminde hesaplanan 7x24 (haftanın günü x saat) commit dağılım matrisi.
- **Dosya Değişim Yoğunluğu ve Sıcak Noktalar (Hotspots):** Eklenen, silinen ve değiştirilen satır sayıları ile `değişim x dosya boyutu` formülüne dayanan sıcak nokta sıralaması.
- **Uzantıya Göre Dil Dağılımı:** Dosya uzantılarına ve özel dosya adlarına (`Dockerfile`, `Makefile` vb.) göre programlama dili sınıflandırması ve satır yüzdeleri.
- **Otobüs Faktörü (Bus Factor) Analizi:** Belirli bir zaman penceresinde (varsayılan: son 6 ay) değişen kod satırlarının %50 ve %80'inden sorumlu minimum katkıcı sayısının hesaplanması.
- **Gizlilik Modu (`--anonymize`):** Yazar adlarını ve e-postalarını SHA-256 özetleme algoritmasıyla tutarlı biçimde anonimleştirir (`Author-xxxxxxxx`, `anon-xxxxxxxx@privacy.local`). Raporların kişisel veri ifşa etmeden paylaşılmasını sağlar.
- **Çoklu Çıktı Formatları:**
  - Terminal: Hizalanmış Unicode/ASCII tabloları ve mini ASCII aktivite haritası.
  - JSON: Süreç otomasyonları için yapılandırılmış veri çıktısı.
  - Markdown: Dokümantasyon ve CI özetleri için GitHub uyumlu Markdown çıktısı.
  - HTML: Harici yazı tipi, stil veya JavaScript kütüphanesi barındırmayan, dahili SVG grafikleri (sıcaklık haritası, commit zaman çizgisi, yazar dağılımı, diller) ve otomatik açık/koyu tema destekli tek dosya HTML raporu.

---

## Gereksinimler

- Python >= 3.10
- Git >= 2.0

---

## Kurulum

Kaynak kod üzerinden `pip` ile kurulum:

```bash
pip install .
```

Veya doğrudan Python üzerinden çalıştırma:

```bash
python -m git_stats_lite.cli [yol] [seçenekler]
```

---

## Kullanım Örnekleri

### Terminal Özeti

Mevcut dizindeki depoyu analiz etme:

```bash
git-stats
```

Belirli bir depo yolunu analiz etme:

```bash
git-stats /path/to/repository
```

### Zaman Filtreleri

Son 1 yıldaki veya belirli tarih aralığındaki commitleri inceleme:

```bash
git-stats --since 1y
git-stats --since 2025-01-01 --until 2025-12-31
```

### Bağımsız HTML Raporu

Dahili SVG grafiklerine sahip tek dosyalık HTML raporu üretme:

```bash
git-stats --html rapor.html
```

Veya format seçeneğiyle doğrudan hedef dosyaya yazma:

```bash
git-stats --format html -o rapor.html
```

### JSON ve Markdown Dışa Aktarma

Otomasyon hatları için yapılandırılmış JSON verisi:

```bash
git-stats --json veri.json
```

GitHub PR veya dokümantasyon özetleri için Markdown çıktısı:

```bash
git-stats --markdown ozet.md
```

### Gizlilik Modu

Raporu anonimleştirerek dışa aktarma:

```bash
git-stats --anonymize --html acik-rapor.html
```

### Özel Otobüs Faktörü Penceresi

Otobüs faktörünü son 12 ay üzerinden hesaplama:

```bash
git-stats --bus-factor-months 12
```

---

## Komut Satırı Seçenekleri

| Seçenek | Açıklama |
| :--- | :--- |
| `path` | Git deposunun dosya yolu (varsayılan: `.`) |
| `--since TARIH` | Belirtilen tarihten veya aralıktan sonraki commitler (ör. `1y`, `6m`, `2024-01-01`) |
| `--until TARIH` | Belirtilen tarihten önceki commitler |
| `--branch REV`, `--rev REV` | Hedef dal (branch), etiket veya revizyon (ör. `main`, `HEAD`) |
| `--all` | Tüm dallardaki commitleri dahil et |
| `--format {terminal,json,markdown,html}` | Birincil çıktı formatı (varsayılan: `terminal`) |
| `-o DOSYA`, `--output DOSYA` | Birincil çıktının yazılacağı dosya |
| `--html [DOSYA]` | Tek dosya HTML raporu üret |
| `--json [DOSYA]` | Yapılandırılmış JSON çıktısı üret |
| `--markdown [DOSYA]`, `--md [DOSYA]` | Markdown formatında rapor üret |
| `--anonymize` | Yazar adlarını ve e-postalarını SHA-256 ile anonimleştir |
| `--bus-factor-months N` | Otobüs faktörü hesaplama penceresi (ay olarak; varsayılan: `6`, tüm geçmiş için `0`) |
| `--top N` | Tablolarda listelenecek azami kayıt sayısı (varsayılan: `10`) |
| `--tz {local,utc}` | Sıcaklık haritası ve metrikler için saat dilimi (varsayılan: `local`) |
| `--mailmap DOSYA` | Özel `.mailmap` dosya yolu |
| `--version` | Sürüm bilgisini görüntüle |
| `-h`, `--help` | Yardım mesajını görüntüle |

---

## Mimari

```
git-stats-lite/
├── src/
│   └── git_stats_lite/
│       ├── __init__.py       # Paket üstbilgisi
│       ├── cli.py            # Argüman ayrıştırma ve yönlendirme
│       ├── git.py            # Git alt süreç komutları ve akış okuyucu
│       ├── parser.py         # Log ayrıştırıcı, yeniden adlandırma ve mailmap
│       ├── models.py         # Veri yapıları (dataclass)
│       ├── stats.py          # İstatistik motoru ve otobüs faktörü
│       ├── languages.py      # Dosya uzantısı ve dil haritası
│       ├── anonymizer.py     # Deterministik SHA-256 anonimleştirici
│       └── formatters/
│           ├── terminal.py   # Metin tabloları ve ASCII harita
│           ├── json_fmt.py   # JSON seri hale getirme
│           ├── markdown.py   # Markdown raporlayıcı
│           └── html.py       # Dahili SVG grafikli HTML oluşturucu
└── tests/                    # Birim ve entegrasyon testleri
```

---

## Testleri Çalıştırma

Testleri Python standart `unittest` aracıyla çalıştırma:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Sözdizimi doğrulaması:

```bash
python -m compileall src tests
```

---

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakabilirsiniz.

Copyright (c) 2026 Yusuf Berat Zengin
