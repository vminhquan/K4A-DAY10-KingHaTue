# Hướng dẫn báo cáo & tái lập bài làm cá nhân

Thư mục `report/` ghi nhận bài làm cá nhân của **Võ Minh Quân — 2A202602429** cho repository [`K4-L3-DAY10-KingHaTue`](https://github.com/vminhquan/K4-L3-DAY10-KingHaTue). Một người thực hiện toàn bộ luồng end-to-end.

## 1. Quy định về báo cáo

Hồ sơ báo cáo gồm:

1. [`group_report.md`](group_report.md): báo cáo tổng hợp kỹ thuật của bài làm.
2. [`individual_report.md`](individual_report.md) và [`2A202602429_VoMinhQuan.md`](2A202602429_VoMinhQuan.md): báo cáo phạm vi công việc cá nhân.

Quy ước file báo cáo cá nhân là:

```text
<MSSV>_HoTen.md
```

## 2. Kết quả chung cần đạt

Mọi bài làm của nhóm cần chứng minh được toàn bộ quan hệ:

```text
Nguồn Crossref
    -> raw records
    -> cleaned dataset
    -> embedding/index
    -> evaluation baseline
    -> quality và freshness signals
    -> corrupted dataset
    -> evaluation sau corruption
    -> repair
    -> so sánh baseline/corrupted/repaired
```

Không chỉ báo cáo rằng lệnh đã chạy thành công. Kết luận cần dựa trên artifact và số liệu thực tế, đặc biệt:

- `retrieval_hit_rate`
- `mean_token_f1`
- `judge_accuracy`
- `mean_judge_score`
- kết quả data quality checks
- trạng thái freshness

Các trạng thái baseline, corrupted và repaired phải được đánh giá trên cùng evaluation set để phép so sánh có ý nghĩa.

## 3. Nguyên tắc chung khi thực hiện

### Giữ một môi trường thống nhất

Người thực hiện giữ thống nhất cấu trúc thư mục, đường dẫn artifact và chữ ký hàm giữa các module.

### Chia theo deliverable, không chia máy móc theo package

Mỗi deliverable vẫn phải nêu rõ input, output và cách xác minh. Ingestion, cleaning, evaluation, observability và pipeline phụ thuộc trực tiếp vào cùng schema/artifact contract.

### Người thực hiện phải hiểu luồng end-to-end

Người thực hiện phải giải thích được:

- dữ liệu đi qua pipeline như thế nào;
- module của mình nhận input gì và tạo output gì;
- corruption tác động đến dữ liệu và agent ra sao;
- artifact hoặc metric nào chứng minh kết luận;
- pipeline được repair và xác minh lại như thế nào.

## 4. Phạm vi công việc cá nhân

Võ Minh Quân sở hữu tất cả khối dưới đây; chi tiết và evidence nằm ở `individual_report.md`.

| Khối                      | File trọng tâm                                                      | Output cần kiểm tra                                            |
| -------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Raw ingestion              | `src/ingestion/crossref.py`                                         | Raw response và raw records trong`data/raw/`                  |
| Cleaning và data modeling | `src/ingestion/cleaning.py`                                         | Cleaned CSV/JSON, schema và`text_for_embedding`               |
| Evaluation set             | `src/evaluation/testset.py`                                         | Test set trong`data/eval/`                                     |
| Quality và freshness      | `src/observability/quality.py`                                      | Quality/freshness artifacts trong`data/quality/`               |
| Reporting                  | `src/observability/reporting.py`                                    | Báo cáo trong`data/reports/`                                 |
| Baseline orchestration     | `src/pipelines/phase1.py`                                           | Baseline metrics và đầy đủ artifact của pha 1              |
| Corruption và repair      | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | Corruption log, corrupted/repaired metrics và comparison report |

Trình tự phụ thuộc cần giữ:

1. Hoàn thành ingestion và xác minh raw records.
2. Hoàn thành cleaning và kiểm tra schema trước khi build index.
3. Tạo evaluation set từ cleaned dataset.
4. Hoàn thành baseline pipeline trước khi chạy corruption flow.
5. Dùng lại cùng evaluation set cho baseline, corrupted và repaired.
6. Đọc artifacts và metrics trước khi viết kết luận.

Trong `individual_report.md`, mỗi thành viên cần phân biệt rõ:

- phần đã hoàn thành;
- phần mới dừng ở mức thử nghiệm;
- phần chưa chạy được và blocker còn lại;
- bằng chứng thực tế tương ứng với từng kết luận.

## 5. Gợi ý phân vai nhóm (không áp dụng cho bài làm này)

Các bảng dưới đây là tài liệu tham khảo từ starter. Bài làm hiện tại là cá nhân nên không dùng phân vai nhóm.

### Nhóm 3 thành viên

| Thành viên   | Vai trò chính                  | Nhiệm vụ sở hữu                                                        | Output bàn giao                                                     |
| -------------- | -------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Thành viên 1 | Data ingestion & cleaning owner  | `crossref.py`, `cleaning.py`; thống nhất raw/clean schema            | Raw records, cleaned dataset và mô tả cleaning rules              |
| Thành viên 2 | Evaluation & observability owner | `testset.py`, `quality.py`, `reporting.py`                           | Evaluation set, quality/freshness results và report functions       |
| Thành viên 3 | Corruption & integration owner   | `corruption.py`, `phase1.py`, `corruption_flow.py`; chạy tích hợp | Baseline/corrupted/repaired artifacts, metrics và comparison report |

Với nhóm 3, khối tích hợp tương đối lớn. Thành viên 1 hỗ trợ kiểm tra dữ liệu repair; thành viên 2 hỗ trợ xác minh metrics và báo cáo cho thành viên 3.

### Nhóm 4 thành viên — khuyến nghị

| Thành viên   | Vai trò chính                   | Nhiệm vụ sở hữu                                      | Output bàn giao                                          |
| -------------- | --------------------------------- | -------------------------------------------------------- | --------------------------------------------------------- |
| Thành viên 1 | Source owner                      | `crossref.py`; fetch, retry, parse và lưu raw data   | Raw response, raw records và schema đầu vào           |
| Thành viên 2 | Data model & evaluation-set owner | `cleaning.py`, `testset.py`                          | Cleaned dataset,`text_for_embedding` và evaluation set |
| Thành viên 3 | Observability owner               | `quality.py`, `reporting.py`                         | Quality checks, freshness và báo cáo Markdown          |
| Thành viên 4 | Corruption & integration owner    | `corruption.py`, `phase1.py`, `corruption_flow.py` | Hai flow chạy end-to-end và bộ metrics so sánh        |

Đây là cấu hình cân bằng nhất cho workload hiện tại. Thành viên 4 chịu trách nhiệm điều phối tích hợp, không phải tự sửa toàn bộ lỗi của các module khác.

### Nhóm 5 thành viên

| Thành viên   | Vai trò chính                       | Nhiệm vụ sở hữu                                              | Output bàn giao                                                    |
| -------------- | ------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------- |
| Thành viên 1 | Source owner                          | `crossref.py`                                                  | Raw response, raw records và schema                                |
| Thành viên 2 | Cleaning & test-set owner             | `cleaning.py`, `testset.py`                                  | Cleaned dataset và evaluation set                                  |
| Thành viên 3 | Observability owner                   | `quality.py`, `reporting.py`                                 | Quality/freshness artifacts và report functions                    |
| Thành viên 4 | Corruption & repair owner             | `corruption.py`; kiểm tra dữ liệu corrupted/repaired        | Corruption log, corruption scenarios và dữ liệu repair hợp lệ  |
| Thành viên 5 | Pipeline integration & evidence owner | `phase1.py`, `corruption_flow.py`; tái hiện toàn bộ flow | Lệnh chạy, metrics, comparison report và bằng chứng tích hợp |

Thành viên 5 không chỉ làm tài liệu. Vai trò này chịu trách nhiệm kỹ thuật cho orchestration, reproducibility và kiểm tra sự nhất quán giữa report với artifact.

## 6. Contract tích hợp nội bộ

Các module dùng chung contract sau:

| Contract          | Nội dung cần thống nhất                                                   |
| ----------------- | ----------------------------------------------------------------------------- |
| Raw schema        | Các trường của một paper record và cách xử lý trường thiếu        |
| Clean schema      | Tên cột, kiểu dữ liệu, quy tắc loại bỏ/deduplicate                    |
| Document identity | Cách tạo và giữ ổn định`paper_id`/document ID                        |
| Evaluation set    | Schema câu hỏi, ground truth và document IDs                               |
| Artifact paths    | Sử dụng đúng đường dẫn được cấu hình trong`src/core/config.py` |
| Metrics           | Dùng cùng tên metric và cùng evaluation set                              |
| Repair            | Repair lại từ nguồn raw/baseline nào và cách xác minh                  |

Trước khi tích hợp phần việc, cần kiểm tra:

- input/output có đúng contract chung không;
- có hard-code path, model hoặc secret không;
- thay đổi có làm hỏng module kế tiếp không;
- có artifact hoặc lệnh xác minh đi kèm không.

## 7. Cách xác minh bài làm

### Chạy baseline

Với `uv`:

```bash
ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_phase1.py
```

Với môi trường `pip` đã được kích hoạt:

```bash
ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_phase1.py
```

### Chạy corruption flow

Với `uv`:

```bash
ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_corruption_flow.py
```

Với môi trường `pip` đã được kích hoạt:

```bash
ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_corruption_flow.py
```

Repo hiện không cung cấp test hoặc grader tự động làm tiêu chí pass cuối cùng. Việc xác minh dựa trên lệnh pipeline, artifacts thực tế, metrics, báo cáo và [`RUBRIC.md`](../docs/RUBRIC.md).

Tối thiểu cần kiểm tra:

- `data/raw/`
- `data/clean/`
- `data/embeddings/`
- `data/eval/`
- `data/results/baseline_metrics.json`
- `data/quality/`
- `data/reports/phase1_report.md`
- `data/results/corruption_log.json`
- `data/reports/corruption_report.md`

Không đánh dấu hoàn thành nếu report mô tả kết quả không khớp với artifact thực tế.

## 8. Definition of Done

- [x] Có một người thực hiện, phạm vi và output rõ ràng.
- [x] Mỗi deliverable có owner và output rõ ràng.
- [x] Có thể chạy lại toàn bộ pipeline từ hướng dẫn chung.
- [x] `group_report.md` khớp với code, artifacts và metrics.
- [x] Có báo cáo cá nhân `2A202602429_VoMinhQuan.md`.
- [x] Người thực hiện có thể giải thích toàn bộ luồng end-to-end.
- [x] Không có API key hoặc secret trong report/log; không commit `.env`.

## 9. Nguyên tắc báo cáo trung thực cá nhân

- Không ghi “đã chạy thành công” nếu chưa có output mới để kiểm chứng.
- Không nhận ownership cho file hoặc hàm không trực tiếp thực hiện.
- Nếu một phần chưa hoàn thành, ghi rõ trạng thái, lỗi nguyên văn đã che secret, nguyên nhân đã xác định và bước tiếp theo.
- Chỉ so sánh các trạng thái trong cùng bài làm, trên cùng test set và cấu hình.
