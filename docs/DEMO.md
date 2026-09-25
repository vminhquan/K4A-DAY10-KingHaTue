# Kịch bản demo CP6

## Mục tiêu

Trình diễn bằng artifacts thật rằng dữ liệu bẩn tạo silent failure, Quality Gate
phát hiện lỗi và repair từ raw snapshot phục hồi lại chỉ số RAG.

## Chuẩn bị

```bash
source .venv/bin/activate
python script/verify_artifacts.py
```

Kết quả mong đợi: `CP1–CP6 artifact verification passed (GX + MiniLM + 3 Chroma collections).`

## Demo 3–5 phút

1. Mở `data/reports/phase1_report.md`: chỉ ra 24 raw/clean records, 10 benchmark
   questions, GX baseline pass và baseline Hit Rate/Token F1.
2. Mở `data/results/corruption_log.json`: chỉ ra sáu lỗi được tiêm có chủ đích.
3. Mở `data/quality/corrupted_quality_report.json`: chứng minh GX phát hiện
   duplicate và summary quá ngắn; Freshness SLA báo `is_fresh: false`.
4. Mở `data/reports/corruption_report.md`: trình bày bảng Baseline → Corrupted →
   Repaired. Lần chạy hiện tại có Hit Rate `1.000 → 0.700 → 1.000` và Token F1
   `1.000 → 0.800 → 1.000`.
5. Chạy lại repair để chứng minh idempotency:

   ```bash
   ALLOW_EMBEDDING_DOWNLOAD=1 python script/run_corruption_flow.py
   python script/verify_artifacts.py
   ```
6. Smoke-test QA Agent (LLM provider lấy từ `.env`, hiện là OpenAI):

   ```bash
   ALLOW_EMBEDDING_DOWNLOAD=1 python -c 'from core.config import load_settings; from retrieval.agent import build_agent, run_agent_question; from retrieval.index import LocalEmbeddingIndex; s=load_settings(); print(run_agent_question(build_agent(s, LocalEmbeddingIndex.load(s)), "Which paper discusses Great Expectations quality gates for production RAG systems?"))'
   ```

## Câu hỏi phản biện ngắn

| Câu hỏi | Trả lời dựa trên implementation |
| --- | --- |
| Vì sao giữ raw response và raw records? | Repair chỉ đọc raw artifact, không sửa lại dữ liệu corrupted; đây là data lineage và idempotency. |
| GX check khác Freshness SLA thế nào? | GX kiểm tra schema/completeness/uniqueness/summary length; Freshness đo tỷ lệ `age_days > 180` và so với ngưỡng 25%. |
| Vì sao phải dùng cùng test set? | Để metric thay đổi chỉ do dữ liệu/index, không do câu hỏi hoặc ground truth khác nhau. |
| Vì sao có ba collection Chroma? | Baseline, corrupted và repaired được cô lập, giúp đối chiếu không làm lẫn index. |
| Embedding nào đang dùng? | Cả ba manifests ghi `sentence-transformers/all-MiniLM-L6-v2`, backend `sentence-transformers`, vector 384 chiều. |

## Việc nhóm cần hoàn tất trước nộp LMS

- Điền tên, MSSV, vai trò và tự khai đóng góp thật vào `docs/TEAM.md`.
- Hoàn thiện thông tin thành viên trong `report/group_report.md` và báo cáo cá nhân.
- Mỗi thành viên tự commit/push phần việc của mình lên `main` và tự nộp URL repo lên LMS.
- Không commit `.env` hoặc API key.
