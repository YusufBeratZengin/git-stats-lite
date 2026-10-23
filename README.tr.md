# git-stats-lite

[![CI](https://github.com/YusufBeratZengin/git-stats-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/YusufBeratZengin/git-stats-lite/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/git-stats-lite.svg)](https://pypi.org/project/git-stats-lite/)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.10-3776ab.svg?logo=python&logoColor=white)](https://pypi.org/project/git-stats-lite/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](pyproject.toml)

> Yerel Git geçmişinden hızlı, gizlilik odaklı istatistikler ve bus factor risk analizleri.

[English](README.md) | [Türkçe](README.tr.md)

<p align="center">
  <img src="docs/demo.svg" alt="git-stats-lite terminal demosu" width="720">
</p>

## Neden git-stats-lite?

- **Sıfır çalışma zamanı bağımlılığı ve %100 çevrimdışı**: Tamamen yerel Git kopyanız üzerinde alt süreç akışıyla (subprocess streaming) çalışır. Ağ çağrısı, bulut servisi, izleme kodu veya harici kütüphane gerektirmez.
- **Eyleme dönüştürülebilir sağlık ve bus factor metrikleri**: %50 ve %80 bus factor risk pencerelerini hesaplar, kod değişim yoğunluğunu (`değişim * boyut`) tespit eder ve yazarın yerel saatine veya UTC'ye göre 7x24 haftalık aktivite haritası sunar.
- **Farklı formatlarda taşınabilir dışa aktarma**: Terminal tabloları, makine tarafından okunabilir JSON, GitHub uyumlu Markdown ve harici JavaScript/CSS gerektirmeyen gömülü SVG grafikli bağımsız tek dosya HTML raporları üretir.

## Hızlı Başlangıç

Python 3.10+ yüklü ortamda paketi kurmadan doğrudan kaynak koddan çalıştırabilirsiniz:

```sh
# Depoyu klonlayıp hemen analiz edin
git clone https://github.com/YusufBeratZengin/git-stats-lite.git
cd git-stats-lite
python src/git_stats_lite/cli.py . --top 5
```

Veya pip ile yerel olarak kurun:

```sh
python -m pip install .
git-stats . --top 5
```

## Kullanım

### Komut Satırı Arayüzü (CLI)

```sh
# Son 1 yılı yazar kimliklerini anonimleştirerek analiz et
git-stats . --since 1y --anonymize

# Bağımsız tek dosya HTML raporu oluştur (etkileşimli SVG grafiklerle)
git-stats . --html report.html

# Markdown özeti ve ham JSON veri çıktısı al
git-stats . --markdown summary.md --json stats.json

# Aktivite haritasını UTC saat diliminde görüntüle
git-stats . --tz utc --top 5

# Belirli bir dalı veya revizyonu analiz et
git-stats . --branch main --since 6m
```

> **İpucu:** Kurulum yapmadan önce `python src/git_stats_lite/cli.py` veya `python -m git_stats_lite` komutunu doğrudan kullanabilirsiniz.

### Python API

```python
from git_stats_lite.git import stream_git_log
from git_stats_lite.parser import parse_git_log_stream
from git_stats_lite.stats import StatsAggregator

# Git log akışını okuyup metrikleri biriktir
stats = StatsAggregator(repo_path=".", timezone_mode="utc")
stats.process_all(parse_git_log_stream(stream_git_log(".", since="1y")))
report = stats.generate_report()

print(f"Toplam Commit: {report.total_commits}")
print(f"Bus Factor (%50): {report.bus_factor.bus_factor_50}")
```

## Yapılandırma ve Seçenekler

| Seçenek | Açıklama | Varsayılan |
| --- | --- | --- |
| `path` | Depo veya alt dizin yolu | `.` |
| `--since DATE`, `--until DATE` | Git tarihleri veya göreli aralıklar (`1y`, `6m`, `30d` vb.) | `None` |
| `--branch REV`, `--rev REV` | İncelenecek dal, etiket veya revizyon | Aktif dal |
| `--all` | Tüm Git ref'lerini analize dahil et | `false` |
| `--format {terminal,json,markdown,html}` | Birincil çıktı formatı | `terminal` |
| `-o FILE`, `--output FILE` | Birincil çıktıyı hedef dosyaya yaz | stdout |
| `--html [FILE]` | Bağımsız HTML raporu üret (dosyaya veya stdout'a) | `None` |
| `--json [FILE]` | Yapılandırılmış JSON verisi üret (dosyaya veya stdout'a) | `None` |
| `--markdown [FILE]`, `--md [FILE]` | GitHub uyumlu Markdown özeti üret | `None` |
| `--anonymize` | Yazar adı ve e-postasını SHA-256 ile anonimleştir | `false` |
| `--bus-factor-months N` | Bus factor penceresi (ay cinsinden; `0` = tüm geçmiş) | `6` |
| `--top N` | Tablolarda gösterilecek satır sınırı | `10` |
| `--tz {local,utc}` | 7x24 aktivite haritası için saat dilimi modu | `local` |
| `--mailmap FILE` | Ek özel mailmap eşleme dosyasının yolu | `None` |
| `--version`, `-h`, `--help` | Sürüm veya yardım metnini göster | |

## SSS ve Sınırlamalar

- **Bus Factor nasıl hesaplanır?**
  Bus factor penceresi varsayılan olarak incelenen en yeni commit'ten geriye doğru 6 aydır. Katkıcılar değişen satır toplamına (eklenen + silinen) göre sıralanır. Satır değişiminin %50 ve %80'ini karşılayan en az yazar sayısı hesaplanır. Bütün diff'ler sıfırsa otomatik olarak commit sayılarına geçilir.
- **`--anonymize` seçeneği ne yapar ve sınırları nelerdir?**
  Yazar adları ve e-postaları deterministik ve tuzlu SHA-256 hash'leri ile (`Author-xxxxxxxx`) gizlenir. Kişi adları maskelenirken depo adı, dosya yolları ve commit zaman damgaları raporda görünmeye devam eder.
- **Aktivite haritasında hangi saat dilimi kullanılır?**
  `--tz local` modunda her commit'in yazıldığı anda Git'e kaydedilen yerel saat dilimi kullanılır. `--tz utc` modunda ise tüm zamanlar küresel ekip karşılaştırması için UTC'ye dönüştürülür.
- **Sığ klonlarda (shallow clone) çalışır mı?**
  Evet, ancak metrikler yalnızca çekilen geçmiş derinliğini yansıtır. Tüm depo geçmişi için önce `git fetch --unshallow` çalıştırılmalıdır.

## Katkıda Bulunma

Hata bildirimleri, özellik önerileri ve katkılar memnuniyetle karşılanır!
Lütfen [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) ve [SECURITY.md](SECURITY.md) belgelerini inceleyin.

Geliştirme adımları:

```sh
# Depoyu klonlayıp geliştirme bağımlılıklarını kurun
python -m pip install -e ".[dev]"

# Linter, tip kontrolü ve testleri coverage ile çalıştırın
python -m ruff check .
python -m mypy src
python -m pytest
```

## Lisans

[MIT](LICENSE). Telif Hakkı (c) 2026 Yusuf Berat Zengin.
