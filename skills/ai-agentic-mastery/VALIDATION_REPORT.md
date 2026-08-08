# 验证报告

## 结论

- 候选 Skill：4
- 测试用例：28
- 主流程自测：28/28 通过
- 所有不应触发用例：8/8 通过
- 总通过率：100%
- 可信度：中等。测试由构建者自测，不是独立 agent 盲测；安装后仍需用真实请求抽查。

## 分项结果

| Skill | 应触发 | 不应触发 | 边界 | 执行 | 结果 |
|---|---:|---:|---:|---:|---|
| `agentic-workflow-compounding` | 3/3 | 2/2 | 1/1 | 1/1 | 7/7 |
| `context-capital-routing` | 3/3 | 2/2 | 1/1 | 1/1 | 7/7 |
| `operational-skill-audit` | 3/3 | 2/2 | 1/1 | 1/1 | 7/7 |
| `question-seed-generalism` | 3/3 | 2/2 | 1/1 | 1/1 | 7/7 |

## 兄弟 Skill 区分

- “让重复任务调用工具、写回产物” → `agentic-workflow-compounding`
- “已有许多资料，不知道不同任务加载什么” → `context-capital-routing`
- “已有 Skill，判断是否只是人设或文风” → `operational-skill-audit`
- “陌生领域连问题都问不出来” → `question-seed-generalism`

四类触发对象分别是工作流、上下文系统、Skill 质量和陌生领域探索，未发现必须合并的重叠。

## 执行动作检查

- 每个 Skill 均定义输入、输出、步骤产物和完成标准。
- 高风险动作均有判停或升级条件。
- `agentic-workflow-compounding` 保留外部写入前的授权/复核。
- `context-capital-routing` 包含敏感数据最小化、失效和删除。
- `operational-skill-audit` 发现危险执行时停止并转安全审计。
- `question-seed-generalism` 不替代医疗、法律、财务和工程安全判断。

## 结构验证

- 4 个 `SKILL.md` 的 frontmatter 仅含 `name` 和 `description`。
- 名称均为小写字母与连字符，目标目录无同名冲突。
- 4 个 `test-prompts.json` 均为有效 JSON，每个包含 7 个测试。
- 每个测试集均含 3 个正例、2 个诱饵、1 个边界场景和 1 个执行验收。

## 静态安全检查

- 风险结论：**安全，可在授权后安装。**
- 包内只有 UTF-8 Markdown 和 JSON。
- 没有脚本、二进制、符号链接或可执行文件。
- 没有下载执行、凭据读取、环境变量外传、持久化、删除或覆盖指令。
- 文本中“凭据外传、破坏性动作”仅作为必须停止的风险信号，不是执行指令。

## 安装后抽查计划

每个 Skill 安装后至少运行：

1. 一条典型正例，确认能被正确选择；
2. 一条兄弟 Skill 诱饵，确认不会抢任务；
3. 一条高风险边界，确认能停止或升级。

