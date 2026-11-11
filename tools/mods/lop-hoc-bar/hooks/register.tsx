import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const CLASS_URL = 'https://claude.ai/artifact/LX12NEhBjqgC3qv5bvqAC2'
const ctx = atom({ plugin: 'lop-hoc-bar', key: 'ctx' } as const, null)

// App cloud của Tân không vẽ dải trên ô chat hay panel → dùng lệnh /lop-hoc (+ dòng trạng thái nơi app có hiện).
export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'lop-hoc', description: 'Link lớp tiếng Anh + % context đã dùng' })
    const p = (await $.session.usage()).context.percent
    if (typeof p === 'number') await update($, ctx, () => p)
    return next(e)
  })

  on('command.run', { command: 'lop-hoc' }, async $ => {
    const p = await read($, ctx)
    const warn = typeof p === 'number' && p >= 80 ? ' – sắp đầy' : ''
    return { text: `📚 ${CLASS_URL} · context ${typeof p === 'number' ? p + '%' : 'chưa đo'}${warn}` }
  })

  on('session.measure', async ($, e, next) => {
    const p = e.context.percent
    if (typeof p === 'number') {
      await update($, ctx, () => p)
      $.ui.status(`📚 Lớp học · ctx ${p}%`)
    }
    return next(e)
  })
}
