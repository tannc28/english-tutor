# Mods cho Claude Code

`lop-hoc-bar/`: lệnh **`/lop-hoc`** in ra link lớp học + % context đã dùng (không gọi model; chỉ thêm 1 dòng nhỏ vào lịch sử). App cloud của Tân không vẽ dải trên ô chat hay panel (đã kiểm chứng 11/11), nên chỉ dùng lệnh này (+ dòng trạng thái ở nơi app có hiện).

Mod chạy trong container của phiên, nên mất khi container bị thu hồi. Để cài lại trong phiên mới: chép thư mục `lop-hoc-bar/` vào `~/.claude/dev-mods/<session-id>/` sau khi tải skill plugin-authoring, rồi bấm "Turn them on" khi được hỏi.
