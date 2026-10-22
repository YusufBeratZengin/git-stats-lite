# git-stats-lite
[![CI](https://github.com/YusufBeratZengin/git-stats-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/YusufBeratZengin/git-stats-lite/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/git-stats-lite)](https://pypi.org/project/git-stats-lite/) [![MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Dependencies](https://img.shields.io/badge/runtime_dependencies-0-green)

Yerel Git geçmişinden aktivite, katkıcı, dosya değişimi, dil ve bus factor istatistikleri çıkarır.
Çevrimdışı çalışır, runtime bağımlılığı yoktur; tek dosyalık HTML raporu üretir.
Kaynak kod dizininde kurulum: `python -m pip install .`
Denemek için: `python src/git_stats_lite/cli.py . --since 1y --anonymize`

[English](README.md) | [Türkçe](README.tr.md)

## Özellikler

- `git log --numstat` çıktısını akış halinde ayrıştırma; `.mailmap` ve noreply takma adlarını birleştirme.
- Günlük/haftalık commit sayıları, yazarın yerel saatinde veya UTC'de 7x24 aktivite haritası, ilk/son commit tarihleri.
- Katkıcı toplamları, dosya değişim yoğunluğu ve hotspot sıralaması, uzantı ve özel dosya adına göre dil dağılımı.
- Seçilen bus factor penceresinde değişen satırların %50/%80'ini karşılayan en az katkıcı sayısı.
- Terminal, JSON, Markdown ve dahili SVG grafikleriyle otomatik açık/koyu temalı tek dosya HTML çıktısı.
- `--anonymize` ile yazar adları ve e-postaları yerine tutarlı SHA-256 takma kimlikler.

## Demo

Sentetik verilerle çalışan çevrimdışı örneğin gerçek çıktısı:

```sh
python examples/demo.py
```

```text
Commits: 2; authors: 2
Lines: +12 / -3
Language: Python
Bus factor: 50%=1, 80%=2
UTC activity: Monday 10:00=1, Tuesday 12:00=1
```

## Kurulum

Python 3.10+ ve PATH üzerinde Git gerekir. Kaynak kod dizininde:

```sh
python -m pip install .
```

Bu komut kaynak koddan kurulum yapar; PyPI rozeti yayımlanmış sürüm varsa onu gösterir.
Kurulumdan sonra `git-stats` ve `git-stats-lite` komutları kullanılabilir.
Kaynak kod dizininde `python src/git_stats_lite/cli.py` ile doğrudan da çalıştırabilirsiniz.

## Kullanım

```sh
python src/git_stats_lite/cli.py . --since 1y --anonymize
python src/git_stats_lite/cli.py . --tz utc --format json --anonymize
python src/git_stats_lite/cli.py . --anonymize --html is/report.html
python src/git_stats_lite/cli.py . --anonymize --markdown is/summary.md
```

Dışa aktarmadan önce hedef klasörü oluşturun. Kurulumdan sonra
`python src/git_stats_lite/cli.py` yerine `git-stats` veya `python -m git_stats_lite` kullanılabilir.

Python API kullanımı (kurulumdan sonra):

```python
from git_stats_lite.git import stream_git_log
from git_stats_lite.parser import parse_git_log_stream
from git_stats_lite.stats import StatsAggregator

stats = StatsAggregator(repo_path=".", timezone_mode="utc")
stats.process_all(parse_git_log_stream(stream_git_log(".", since="1y")))
report = stats.generate_report()
print(report.total_commits)
```

## Örnekler

[examples/demo.py](examples/demo.py), sentetik log kayıtlarını gerçek parser ve
istatistik motorundan geçirir. Kurulum, ağ erişimi veya Git geçmişinde değişiklik gerektirmez.

## Yapılandırma / seçenekler

| Seçenek | Açıklama |
| --- | --- |
| `path` | Depo veya alt dizin; varsayılan `.` |
| `--since DATE`, `--until DATE` | Git tarihleri veya `1y`, `6m` gibi aralıklar; `m` ay demektir |
| `--branch REV`, `--rev REV` | Dal, etiket veya revizyon |
| `--all` | Tüm ref'leri dahil et |
| `--format {terminal,json,markdown,html}` | Birincil format; varsayılan terminal (tek değer seçilir) |
| `-o FILE`, `--output FILE` | Birincil çıktıyı dosyaya yaz |
| `--html [FILE]`, `--json [FILE]` | Dosyaya aktar; FILE yoksa stdout'a yaz |
| `--markdown [FILE]`, `--md [FILE]` | Markdown çıktısı |
| `--anonymize` | Yazar adı ve e-postasını hash ile değiştir |
| `--bus-factor-months N` | Ay cinsinden pencere; varsayılan 6, tüm geçmiş için 0 |
| `--top N` | Tablo satır sınırı; varsayılan 10 |
| `--tz {local,utc}` | Aktivite saat dilimi; varsayılan local (tek değer seçilir) |
| `--mailmap FILE` | Ek özel mailmap dosyası |
| `--version`, `-h`, `--help` | Sürüm veya yardım |

## Nasıl çalışır?

Git önce deponun mailmap dosyasını uygular; parser varsa ek mailmap dosyasını işler.
Log kayıtları akış halinde okunurken metrikler biriktirilir. Bellek kullanımı katkıcı,
dosya, gün ve commit başına tutulan kısa bus factor kayıtlarıyla birlikte büyür.
Hotspot puanı değişen satır sayısı * çalışma dizinindeki güncel satır sayısıdır;
bulunamayan veya boş dosyalarda commit sayısı * değişen satır sayısı kullanılır.
Dil dağılımı güncel kaynak ağacını değil, geçmişteki satır değişimlerini gösterir.
Raporlar harici dosya veya JavaScript kütüphanesi gerektirmez.

## Sınırlamalar / gizlilik

“Local”, raporu görüntüleyenin değil yazarın commit'e kaydettiği saat dilimidir.
Bus factor penceresi incelenen en yeni commit'te biter; bir ay yaklaşık 30,4375 gündür.
Pencerede değişen satır yoksa incelenen tüm değişimler, bütün diff'ler sıfırsa commit
sayıları kullanılır. Binary diff'ler sıfır satır sayılır. Merge diff'leri Git log'un
varsayılan davranışını izler.

Depo verileri ağ üzerinden gönderilmez. Takma kimliklerde sabit salt kullanıldığı için
raporlar arasında eşleştirme yapılabilir; hash kullanımı anonimlik garantisi vermez.
`--anonymize` açıkken de depo adı, mutlak yol, dal ve dosya yolları görünür kalır.
Paylaşmadan önce her raporu inceleyin. Hata bildirimlerinde sentetik depolar kullanın.

## Geliştirme

```sh
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy src
python -m pytest -q
python -m build
python -m twine check dist/*
```

CI, Python 3.10-3.13 sürümlerini Windows ve Linux üzerinde kontrol eder.
Testler geçici depolarda kontrollü commit'ler oluşturarak çevrimdışı çalışır.
Build araçları yalnızca geliştirme bağımlılığıdır.

## Katkıda bulunma

[CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) ve
[SECURITY.md](SECURITY.md) dosyalarına bakın. Yayınlama otomasyonu PyPI trusted publishing
kullanır; bakım sorumlusu önce yayıncı kaydını ve korumalı `pypi` ortamını yapılandırmalıdır.

## Lisans

[MIT](LICENSE). Copyright (c) 2026 Yusuf Berat Zengin.
