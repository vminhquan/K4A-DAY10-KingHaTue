# Thông Tin Cá Nhân & Báo Cáo Phạm Vi Công Việc

- **Tên Nhóm / Bài làm:** `KingHaTue` — cá nhân
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `https://github.com/vminhquan/K4A-DAY10-KingHaTue`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Võ Minh Quân | 2A202602429 | vmquan44@gmail.com | Thực hiện toàn bộ: ingestion, cleaning, MiniLM/Chroma, GX/evaluation, corruption/repair và integration | `report/2A202602429_VoMinhQuan.md` |

*Vì không tìm được nhóm nên bài làm này tôi tự thực hiện toàn bộ phạm vi kỹ thuật, mong BTC tạo điều kiện và ghi nhận cho bài lab của tôi. Cảm ơn BTC rất nhiều !*

---

## # Cá nhân

### ## Võ Minh Quân-2A202602429
- **Vai trò:** Pipeline owner — thực hiện end-to-end.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng parse DOI/title/summary/authors/categories/published trong `src/ingestion/crossref.py`.
  - Thiết lập retry live API và fallback `data/raw/crossref_response.json` khi offline hoặc lỗi 429.
  - Bàn giao `data/raw/crossref_records.json` gồm 24 records.
  - Chuẩn hóa schema, tính toán trường `age_days` và `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - Khử trùng lặp theo `paper_id`, bàn giao 24 clean records ở `data/clean/`.
  - Tạo `data/eval/test_set.json` gồm 10 câu thuộc summary/authors/date/categories.
  - Quản lý mô hình embedding `sentence-transformers/all-MiniLM-L6-v2`.
  - Nạp và quản lý 3 collection riêng biệt trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
  - Xây dựng QA Agent truy vấn ngữ cảnh chính xác theo tài liệu.
  - Thiết lập Quality Gate theo chuẩn mới **Great Expectations 1.x** và giám sát Freshness SLA trong `src/observability/quality.py`.
  - Xây dựng bộ câu hỏi đánh giá chuẩn trong `src/evaluation/testset.py`.
  - Đo lường và xuất bảng đối chiếu 3 trạng thái vào `data/reports/corruption_report.md`.
  - Tiêm sáu corruption xác định trong `src/ingestion/corruption.py`: drop newest, blank summary, noise, truncate title, stale date, duplicate rows.
  - Điều phối `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`; repair tái dựng từ raw records thay vì vá dataframe lỗi.
  - Chạy nghiệm thu `script/verify_artifacts.py`: GX + MiniLM + ba Chroma collections pass.
- **Điều học được / Đóng góp chính:**
  - Hiểu data lineage, quality gate, semantic retrieval và repair idempotent như một pipeline thống nhất.
