import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const CLASS_URL = 'https://claude.ai/artifact/LX12NEhBjqgC3qv5bvqAC2'
const PANE = 'lop-hoc'
const ctx = atom({ plugin: 'lop-hoc-bar', key: 'ctx' } as const, null)

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'lop-hoc', description: 'Mở panel Lớp tiếng Anh (link lớp học + % context)' })
    const p = (await $.session.usage()).context.percent
    if (typeof p === 'number') await update($, ctx, () => p)
    $.ui.status(`📚 Lớp học: ${CLASS_URL} · ctx ${typeof p === 'number' ? p + '%' : '–'}`)
    const placed = await $.ui.open({ id: PANE, title: '📚 Lớp tiếng Anh' })
    await $.fs.write('/tmp/lop-hoc-bar.pane.log', `open isPlaced=${placed.isPlaced} at=${await $.clock.now()}\n`)
    $.ui.toast(`📚 Lớp học: ${CLASS_URL}`)
    return next(e)
  })

  on('command.run', { command: 'lop-hoc' }, async $ => {
    const placed = await $.ui.open({ id: PANE, title: '📚 Lớp tiếng Anh' })
    const p = await read($, ctx)
    return { text: `📚 Lớp học: ${CLASS_URL}\nContext đã dùng: ${typeof p === 'number' ? p + '%' : 'chưa đo'}${placed.isPlaced ? '' : '\n(App này không hiển thị panel.)'}` }
  })

  on('session.measure', async ($, e, next) => {
    const p = e.context.percent
    if (typeof p === 'number') {
      await update($, ctx, () => p)
      $.ui.status(`📚 Lớp học: ${CLASS_URL} · ctx ${p}%`)
    }
    return next(e)
  })


  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    await $.fs.write('/tmp/lop-hoc-bar.log', `pane render surface=${e.surface} at=${await $.clock.now()}\n`)
    const p = await read($, ctx)
    const { Box, Text, Link } = $.ui.resolve(e)
    const warn = typeof p === 'number' && p >= 80
    return (
      <Box flexDirection="column">
        <Link href={CLASS_URL}>📚 Mở lớp tiếng Anh của Tân</Link>
        <Text color={warn ? 'yellow' : undefined}>
          {typeof p === 'number' ? `Context đã dùng: ${p}%` : 'Context: chưa đo'}{warn ? ' – sắp đầy' : ''}
        </Text>
      </Box>
    )
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)
    const p = await read($, ctx)
    const { Box, Text, Link } = $.ui.resolve(e)
    return (
      <Box>
        <Link href={CLASS_URL}>📚 Lớp tiếng Anh của Tân</Link>
        <Text dimColor>{typeof p === 'number' ? `  ·  ctx ${p}%` : '  ·  ctx –'}</Text>
      </Box>
    )
  })
}
