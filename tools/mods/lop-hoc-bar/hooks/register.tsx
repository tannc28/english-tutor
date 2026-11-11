import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const CLASS_URL = 'https://claude.ai/artifact/LX12NEhBjqgC3qv5bvqAC2'
const ctx = atom({ plugin: 'lop-hoc-bar', key: 'ctx' } as const, null)

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const p = (await $.session.usage()).context.percent
    if (typeof p === 'number') {
      await update($, ctx, () => p)
      $.ui.status(`ctx ${p}%`)
    }
    return next(e)
  })

  on('session.measure', async ($, e, next) => {
    const p = e.context.percent
    if (typeof p === 'number') {
      await update($, ctx, () => p)
      $.ui.status(`ctx ${p}%`)
    }
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)
    const p = await read($, ctx)
    const { Box, Text, Link } = $.ui.resolve(e)
    const warn = typeof p === 'number' && p >= 80
    return (
      <Box>
        <Link href={CLASS_URL}>📚 Lớp tiếng Anh của Tân</Link>
        <Text dimColor>{'  ·  '}</Text>
        <Text color={warn ? 'yellow' : undefined} dimColor={!warn}>
          {typeof p === 'number' ? `ctx ${p}%` : 'ctx –'}
        </Text>
      </Box>
    )
  })
}
