# Individual Report — Day 10: Data Pipeline & Data Observability

> Báo cáo cá nhân của Võ Minh Quân. Toàn bộ số liệu được đối chiếu từ artifacts đã nghiệm thu.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên | Võ Minh Quân |
| MSSV | 2A202602429 |
| Khóa/Lớp | K4 — K4-L3A-DAY10 |
| Tên bài làm | KingHaTue — cá nhân |
| Vai trò chính | End-to-end Data Pipeline owner |
| Repository | `https://github.com/vminhquan/K4A-DAY10-KingHaTue` |
| Ngày hoàn thành | 25-09-2026 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Ingestion & cleaning | `crossref.py`, `cleaning.py` | Crossref/snapshot | Raw + clean 24 records | Hoàn thành |
| Index & agent | `retrieval/` | `text_for_embedding` | MiniLM + Chroma 3 collections + OpenAI agent | Hoàn thành |
| Observability/evaluation | `quality.py`, `metrics.py`, `testset.py` | Dataframe/index/test set | GX/Freshness + metrics/reports | Hoàn thành |
| Corruption/repair | `corruption.py`, pipelines | Clean/raw artifacts | Corrupted/repaired artifacts | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tích hợp end-to-end và demo | Toàn bộ modules | `script/verify_artifacts.py` pass GX + MiniLM + 3 Chroma collections |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Baseline pipeline | `script/run_phase1.py` | 24 docs, baseline Hit/F1/Judge = 1.000/1.000/1.000 | `baseline_metrics.json` |
| Corruption/repair | `script/run_corruption_flow.py` | Hit rate 1.000 → 0.700 → 1.000 | `corruption_report.md` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Output then chốt là `data/reports/corruption_report.md`: cùng benchmark test set chứng minh corruption làm giảm metric và repair từ raw data phục hồi metric về baseline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Thiết kế pipeline có khả năng phát hiện silent failure của dữ liệu RAG trước serving layer, định lượng tác động và tự phục hồi từ nguồn raw đáng tin cậy.

### Cách triển khai

Dữ liệu Crossref được parse, chuẩn hóa và deduplicate theo DOI. Cleaning tính `age_days` và ghép năm thành phần thành `text_for_embedding`. GX 1.23.1 chạy ephemeral context để kiểm tra row count, non-null, uniqueness và summary length; Freshness SLA kiểm tra stale ratio. Dữ liệu qua gate được embed bằng MiniLM 384 chiều và nạp vào ba Chroma collection độc lập. Corruption flow làm hỏng dữ liệu theo sáu cách, sau đó repair tái dựng từ raw records, re-index và re-evaluate bằng cùng test set.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input | Crossref payload/raw records, clean dataframe, test set |
| Output | Clean/quality/index/metrics/report artifacts |
| Module phụ thuộc | `core/config.py`, ingestion, retrieval, evaluation, observability |
| Module sử dụng output | Pipelines, QA Agent và CP6 demo |
| Điều kiện lỗi cần xử lý | API 429/offline, null/duplicate/short summary, stale data, incomplete MiniLM cache |

### Cách xác minh

```bash
ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_phase1.py
ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_corruption_flow.py
python script/verify_artifacts.py
```

- **Kết quả mong đợi:** Baseline pass, corrupted fail quality/degrade metrics, repaired restore baseline.
- **Kết quả thực tế:** `CP1–CP6 artifact verification passed (GX + MiniLM + 3 Chroma collections).`
- **Artifact/log:** `data/quality/`, `data/results/`, `data/reports/`; không chứa secret.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Chọn embedding có thể tái lập và bám rubric CP2.
- **Các phương án đã cân nhắc:** Hashing fallback offline hoặc MiniLM thật.
- **Phương án đã chọn:** `sentence-transformers/all-MiniLM-L6-v2` thật, 384 chiều.
- **Lý do:** MiniLM đáp ứng đúng yêu cầu rubric; manifest ghi backend để provenance minh bạch.
- **Bằng chứng quyết định phù hợp:** Ba manifests ghi `embedding_backend=sentence-transformers`; Chroma có 24/23/24 documents.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** MiniLM cache thiếu `model.safetensors`/`pytorch_model.bin` nên có nguy cơ fallback.
- **Lệnh hoặc bước tái hiện:** Nạp MiniLM local-only trước khi tải trọng số hoàn chỉnh.
- **Nguyên nhân gốc:** Hugging Face cache chưa chứa đủ weights của model.
- **Cách xử lý:** Tải/xác minh model và re-index với `ALLOW_EMBEDDING_DOWNLOAD=1`.
- **Cách xác minh sau khi sửa:** Wrapper báo `sentence-transformers`, dimension 384; verification pass.
- **Điều học được:** Manifest cần ghi rõ embedding backend, không chỉ model name.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Crossref được parse thành raw records; cleaning tạo clean schema, GX/Freshness gate kiểm tra rồi MiniLM embed vào ChromaDB.
2. Mỗi câu test có ground-truth `paper_id`; retrieval hit kiểm tra ID xuất hiện trong kết quả, Token F1/LLM Judge đo answer quality.
3. GX đo schema/completeness/uniqueness/summary length; Freshness đo tỷ lệ `age_days > 180` so với SLA 25%.
4. Cùng test set loại trừ thay đổi do câu hỏi, nên metric change phản ánh data/index.
5. Repair thành công khi raw rebuild đưa GX/Freshness pass và metric về baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.000 | 0.700 | 1.000 | Mất 0.300 rồi phục hồi |
| `mean_token_f1` | 1.000 | 0.800 | 1.000 | Nội dung lỗi làm answer giảm khớp |
| `judge_accuracy` | 1.000 | 0.800 | 1.000 | OpenAI Judge xác nhận suy giảm |
| `mean_judge_score` | 5.000 | 4.400 | 5.000 | Phục hồi hoàn toàn |
| Quality checks | Pass | Fail | Pass | 8 duplicate, 5 summary ngắn ở corrupted |
| Freshness status | Fresh 4.17% | Stale 26.09% | Fresh 4.17% | Backdate vượt SLA rồi được rebuild |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Sáu corruption → GX fail/Freshness stale → Hit rate 1.000 xuống 0.700 và Token F1 1.000 xuống 0.800.
2. Repair từ raw records → GX/Freshness pass → tất cả metric phục hồi về baseline.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Tác động rõ nhất là tổ hợp blank summary, duplicate rows và stale date: chúng tạo signal trực tiếp ở GX/Freshness, đồng thời các mutation nội dung/mất records làm retrieval kém đi.

Kết quả nào khác với kỳ vọng ban đầu?

Corrupted Token F1 vẫn 0.800 thay vì giảm sâu hơn do một phần ground-truth passages chưa bị mutation. Điều này được kiểm tra bằng cùng 10 câu test và corruption log xác định record bị tác động.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw snapshot và stable document ID là nền tảng repair idempotent.
2. Quality Gate phải chặn schema/data lỗi trước embedding layer; Freshness cần SLA riêng.
3. Agent vẫn trả lời khi data lỗi, nên phải dùng metrics/artifacts để phát hiện silent failure.

### Nếu có thêm thời gian

Mở rộng test set theo domain và chạy scheduled Crossref refresh; đo improvement bằng coverage tăng và regression thresholds cho Hit/F1/Judge.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh phạm vi công việc đã khai báo.
- [x] Có thể giải thích luồng end-to-end.
- [x] Mọi kết luận có artifact hoặc metric đối chiếu.
- [x] Chỉ nêu các lệnh/artifacts đã kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Võ Minh Quân
**Ngày xác nhận:** 2026-09-25
