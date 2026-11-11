/** % context window đã dùng (0–100); null khi chưa có số đo */
export type CtxPercent = number | null

declare module 'claude-code' {
  interface PluginState {
    'lop-hoc-bar': { ctx: CtxPercent }
  }
}
