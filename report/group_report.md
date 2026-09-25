# Group Report — Day 10: Data Pipeline & Data Observability

> Báo cáo cá nhân sử dụng số liệu từ artifacts đã nghiệm thu.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4 — K4-L3-DAY10              |
| Tên nhóm/bài làm | KingHaTue — cá nhân |
| Repository | `https://github.com/vminhquan/K4-L3-DAY10-KingHaTue` |
| Ngày hoàn thành | 2026-09-25               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Võ Minh Quân | 2A202602429 | End-to-end pipeline owner | Toàn bộ `src/`, `script/`, `data/` và report artifacts |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

Pipeline đã hoàn thiện chuỗi Crossref → raw records → cleaning → Quality Gate/Freshness → MiniLM/ChromaDB → evaluation. Lần nghiệm thu dùng 24 raw/clean records, tạo 10 câu benchmark thuộc bốn nhóm nghiệp vụ, và index bằng `sentence-transformers/all-MiniLM-L6-v2` (384 chiều). Baseline đạt retrieval hit rate 1.000, Token F1 1.000, judge accuracy 1.000 và mean judge score 5.000. LLM Judge và smoke-test QA Agent dùng OpenAI `gpt-4o-mini` qua biến môi trường; report không chứa API key.

Pipeline tiêm sáu dạng corruption. Trạng thái corrupted còn 23 rows; GX phát hiện 8 duplicate `paper_id`, 5 summary ngắn, đồng thời Freshness SLA ghi 6/23 stale (26.09%), vượt ngưỡng 25%. Hit rate giảm còn 0.700, Token F1 còn 0.800, judge accuracy còn 0.800 và mean judge score 4.400. Repair tái dựng clean data/index từ raw records thay vì vá dataframe lỗi; trạng thái repaired trở về 24 rows, GX/Freshness pass và các metric về baseline.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion | Crossref/snapshot | Parse, retry, fallback | `data/raw/` | Võ Minh Quân |
| Cleaning | Raw records | Deduplicate, `age_days`, embedding text | `data/clean/` | Võ Minh Quân |
| Embedding/index | Clean data | MiniLM 384D, 3 Chroma collections | `data/embeddings/`, `data/chroma/` | Võ Minh Quân |
| Evaluation | Fixed test set/index | Hit rate, Token F1, LLM Judge | `data/results/` | Võ Minh Quân |
| Observability | Three dataframes | GX 1.23.1 + Freshness SLA | `data/quality/` | Võ Minh Quân |
| Corruption/repair | Clean/raw artifacts | 6 faults; rebuild from raw | `data/results/`, `data/clean/` | Võ Minh Quân |
| Orchestration | Pipeline artifacts | Baseline then corruption/repair | `data/reports/` | Võ Minh Quân |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER` | `openai` |
| `LLM_MODEL` | `gpt-4o-mini` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày; stale ratio tối đa 25% |
| Random seed, nếu có | Test set và corruption deterministic |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-09-25 | `baseline_metrics.json`, `phase1_report.md` |
| Corruption flow | Thành công | 2026-09-25 | `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source | Crossref REST API; offline snapshot `data/raw/crossref_response.json` |
| Query/filter | `agentic retrieval augmented generation large language model` |
| Thời điểm lấy dữ liệu | Snapshot tái lập, nghiệm thu 2026-09-25 |
| Số record nhận được | 24 |
| Cơ chế retry/backoff | Retry live API; fallback snapshot khi offline/lỗi 429 |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | string | Có | DOI chuẩn hóa | Loại record thiếu/trùng |
| `title` | string | Có | Tiêu đề | Chuẩn hóa whitespace; loại thiếu |
| `summary` | string | Có | Abstract đã bỏ JATS/HTML | Bắt buộc ≥30 ký tự ở GX |
| `published` | ISO date | Có | Ngày xuất bản | Parse ISO, dùng tính `age_days` |
| `text_for_embedding` | string | Có | 5 trường retrieval | GX non-null trước index |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Normalize JATS/HTML và whitespace | Validity | 24 | `papers_clean.json` |
| Deduplicate theo DOI/paper_id | Uniqueness | 0 duplicate còn lại | GX `paper_id_unique` pass |
| Dựng age_days và embedding text | Freshness/completeness | 24 | clean JSON + GX non-null pass |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

`text_for_embedding` ghép Title, Authors, Published, Categories và Summary. `paper_id` là DOI chuẩn hóa; `age_days = (run_date - published).days`. Các quy tắc này giúp document identity ổn định khi index, corruption và repair.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi | 10 |
| Các `question_type` | summary, authors, date, categories |
| Ground-truth document ID | `paper_id` sinh từ cleaned data |
| Embedding model | `all-MiniLM-L6-v2`, 384D |
| Vector store/collection | Chroma: `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | 4 |
| LLM provider/model | OpenAI `gpt-4o-mini` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Giữ nguyên test set loại trừ biến nhiễu do câu hỏi/ground truth; thay đổi metric chỉ phản ánh dữ liệu và index.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records | `data/raw/` | Có | 24 parsed records, snapshot fallback |
| Cleaned dataset | `data/clean/` | Có | 24 rows, deduplicated |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/` | Có | MiniLM thật, 3 collections |
| Evaluation set | `data/eval/` | Có | 10 fixed questions |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Hit/F1/Judge metrics |
| Quality/freshness | `data/quality/` | Có | GX 1.23.1 và SLA |
| Baseline report | `data/reports/phase1_report.md` | Có | Baseline evidence |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` | 1.000 | Ground-truth document được retrieve |
| `mean_token_f1` | 1.000 | Câu trả lời khớp ground truth |
| `judge_accuracy` | 1.000 | LLM Judge xác nhận 10/10 |
| `mean_judge_score` | 5.000 | Chất lượng judge cao nhất thang 1–5 |
| Ragas | Không dùng làm score gate | Các metric chính ở trên dùng để so sánh 3 trạng thái |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| Row count | Completeness | 5–5000 | Pass: 24 | `baseline_quality_report.json` |
| paper_id/title/embedding text non-null | Completeness | 0 null | Pass | `baseline_quality_report.json` |
| paper_id unique | Uniqueness | 0 duplicate | Pass | `baseline_quality_report.json` |
| Summary length | Validity | ≥30 chars | Pass | `baseline_quality_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Clean dataframe trước index |
| Timestamp mới nhất | 2026-07-22 |
| Ngưỡng freshness | `age_days > 180`; stale ratio ≤25% |
| Trạng thái baseline | Fresh |
| Lý do | 1/24 stale = 4.17%, dưới ngưỡng 25% |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop newest | Bỏ 20% records mới nhất | 5 | Retrieval thiếu thông tin mới | Hit rate giảm | Rebuild raw |
| Blank summary | Xóa summary | 4 | Summary length fail | GX fail | Rebuild raw |
| Inject noise | Chèn token nhiễu | 4 | Semantic retrieval giảm | Token F1 giảm | Rebuild raw |
| Truncate title | Title <8 ký tự | 4 | Metadata yếu đi | Retrieval suy giảm | Rebuild raw |
| Stale date | Backdate published | 4 | Freshness stale | 6/23 stale = 26.09% | Rebuild raw |
| Duplicate rows | Nhân bản row | 4 | Uniqueness fail | 8 duplicate paper_id | Rebuild raw |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có.
- Nhận xét: Log ghi đủ sáu operation, `paper_id` bị tác động, count và mô tả; input 24 rows, output 23 rows.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair đọc lại `data/raw/crossref_records.json`, chạy cleaning, GX/Freshness, re-index và evaluate. Vì không dùng corrupted dataframe làm nguồn repair, thao tác có tính idempotent và duy trì lineage.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate` | 1.000 | 0.700 | 1.000 | -0.300 | +0.300 | Phục hồi hoàn toàn |
| `mean_token_f1` | 1.000 | 0.800 | 1.000 | -0.200 | +0.200 | Phục hồi hoàn toàn |
| `judge_accuracy` | 1.000 | 0.800 | 1.000 | -0.200 | +0.200 | LLM Judge xác nhận |
| `mean_judge_score` | 5.000 | 4.400 | 5.000 | -0.600 | +0.600 | Phục hồi hoàn toàn |
| Quality checks pass/fail | Pass | Fail | Pass | Duplicate/summary fail | Pass | Gate phát hiện lỗi |
| Freshness status | Fresh 4.17% | Stale 26.09% | Fresh 4.17% | Vượt SLA | Fresh | Backdate bị loại qua repair |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. Sáu corruption → GX uniqueness/summary fail và Freshness stale → hit rate 1.000 xuống 0.700, Token F1 1.000 xuống 0.800.
2. Rebuild từ raw records → GX/Freshness pass → tất cả retrieval và Judge metrics trở về baseline.

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Cache MiniLM ban đầu không có trọng số đầy đủ, có nguy cơ dùng hashing fallback.
- **Nguyên nhân:** `all-MiniLM-L6-v2` chưa tải hoàn chỉnh trong Hugging Face cache.
- **Cách xử lý:** Tải/xác minh MiniLM và re-index với `ALLOW_EMBEDDING_DOWNLOAD=1`.
- **Cách xác minh:** Manifests ghi backend `sentence-transformers`; Chroma có 24/23/24 documents; `script/verify_artifacts.py` pass.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Snapshot 24 papers | Phủ kiến thức hẹp | Refresh source có versioning rồi chạy lại benchmark |
| Crossref/network có thể lỗi | Không luôn lấy data mới | Retry, fallback, scheduled refresh và alert |
| Benchmark 10 câu | Bao phủ còn nhỏ | Mở rộng versioned regression test set |

## 13. Checklist trước khi nộp

- [x] Thông tin cá nhân và repository đã được điền.
- [ ] Commit thật khớp với phạm vi công việc cá nhân.
- [x] Lệnh tái hiện đã chạy trên phiên bản artifacts hiện tại.
- [x] Ba trạng thái dùng chung evaluation set.
- [x] Metrics/quality/freshness khớp artifacts.
- [x] Các đường dẫn artifact truy cập được và verification pass.
- [x] Báo cáo vai trò cá nhân đã được tạo.
- [x] Không có `.env`, API key, token hoặc secret trong report.
