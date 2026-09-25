# Báo cáo vai trò cá nhân — Võ Minh Quân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Võ Minh Quân |
| MSSV | 2A202602429 |
| Lớp | K4-L3-DAY10 |
| Vai trò | End-to-end Data Pipeline owner |
| Repository | `https://github.com/vminhquan/K4A-DAY10-KingHaTue` |
| Ngày hoàn thành kỹ thuật | 2026-09-25 |

## Phạm vi công việc

| Module/deliverable | Phần thực hiện | Bằng chứng |
|---|---|---|
| Ingestion | Crossref parse, retry và offline snapshot fallback | `src/ingestion/crossref.py`, `data/raw/` |
| Cleaning/test set | Schema, deduplicate DOI, `age_days`, embedding text, 10 câu benchmark | `cleaning.py`, `testset.py`, `data/clean/`, `data/eval/` |
| Retrieval | MiniLM 384D, ba Chroma collection, QA Agent OpenAI | `src/retrieval/`, manifests, smoke test |
| Observability/evaluation | GX 1.23.1, Freshness SLA, Hit/F1/LLM Judge | `data/quality/`, `data/results/` |
| Corruption/repair | Sáu lỗi, repair từ raw records, orchestration | `corruption.py`, pipelines, comparison report |

## Kết quả và phân tích

Baseline có 24 records, GX/Freshness pass, `retrieval_hit_rate=1.000`, `mean_token_f1=1.000`, `judge_accuracy=1.000` và `mean_judge_score=5.000`. Corruption làm index còn 23 rows, tạo 8 duplicate `paper_id`, 5 summary ngắn và 26.09% stale rows. Chỉ số retrieval giảm lần lượt xuống 0.700, 0.800, 0.800 và 4.400. Repair tái dựng từ `data/raw/crossref_records.json`, không vá dữ liệu corrupted; sau repair GX/Freshness pass và bốn metric phục hồi về baseline.

Vấn đề tích hợp quan trọng là MiniLM cache ban đầu thiếu trọng số. Tôi tải/xác minh `all-MiniLM-L6-v2`, re-index với `ALLOW_EMBEDDING_DOWNLOAD=1`, rồi xác minh manifests ghi `embedding_backend=sentence-transformers`. `script/verify_artifacts.py` đã pass GX, MiniLM và ba Chroma collections 24/23/24.

## Điều học được

1. Raw snapshot và document identity ổn định tạo nền tảng cho repair idempotent.
2. GX schema checks và Freshness SLA phát hiện silent failure trước serving layer.
3. Chỉ dùng cùng test set mới cho phép kết luận data corruption là nguyên nhân làm metric suy giảm.

## Cam kết

- [x] Nội dung phản ánh phạm vi công việc cá nhân đã khai báo.
- [x] Mọi số liệu đều có artifact để đối chiếu.
- [x] Report không chứa API key hoặc nội dung `.env`.

**Võ Minh Quân — 25-09-2026**
