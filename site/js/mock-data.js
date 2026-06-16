// Mock data for AI Daily Pulse demo

const MOCK_FEATURED = [
  {
    quote: '"We are beginning to see the emergence of truly autonomous AI systems. GPT-5 represents not just an incremental improvement, but a fundamental shift in what\'s possible."',
    author: 'Sam Altman',
    source: 'X (Twitter)',
    time: '今日 09:32',
    tag: '新模型发布',
    category: 'model'
  },
  {
    quote: '"We\'ve identified the root cause of the service degradation. Our V5 inference cluster experienced cascading failures under peak load. Full postmortem coming in 24h."',
    author: '梁文锋',
    source: 'X (Twitter)',
    time: '今日 11:45',
    tag: '事故声明',
    category: 'incident'
  },
  {
    quote: '"Auto-regressive LLMs are a dead end for achieving real intelligence. We need world models that understand physics, causality, and can plan."',
    author: 'Yann LeCun',
    source: 'X (Twitter)',
    time: '今日 08:17',
    tag: 'CEO发言',
    category: 'statement'
  }
];

const MOCK_TIMELINE = [
  {
    time: '10:30',
    title: 'OpenAI 正式发布 GPT-5 Turbo',
    source: '来源: OpenAI Blog, TechCrunch 等 12 处提及',
    mentionCount: 12,
    trendScore: 92,
    summary: '推理能力提升40%，支持100万token上下文',
    category: 'model'
  },
  {
    time: '09:15',
    title: 'DeepSeek-V5 API 出现间歇性超时',
    source: '来源: 机器之心, 用户社媒反馈 等 8 处提及',
    mentionCount: 8,
    trendScore: 76,
    summary: '亚太区用户大面积反馈推理延迟超过30秒',
    category: 'incident'
  },
  {
    time: '08:00',
    title: 'Yann LeCun 发文质疑 AGI 路线',
    source: '来源: X (Twitter), The Verge 等 6 处提及',
    mentionCount: 6,
    trendScore: 68,
    summary: '再次强调世界模型路线，引发社区激烈讨论',
    category: 'statement'
  }
];

const MOCK_NEWS = [
  {
    category: '新模型',
    categoryKey: 'model',
    time: '10:30',
    title: 'OpenAI 正式发布 GPT-5 Turbo，推理性能大幅提升',
    summary: '新模型在数学推理、代码生成和长文本理解上均有显著提升，上下文窗口扩展至100万token，API定价维持GPT-4 Turbo水平。',
    mentions: 12,
    score: 92
  },
  {
    category: '事故',
    categoryKey: 'incident',
    time: '09:15',
    title: 'DeepSeek-V5 亚太区服务出现大面积超时',
    summary: 'API响应时间从平均2秒飙升至30秒以上，影响数千开发者。官方已确认问题源于推理集群负载均衡故障。',
    mentions: 8,
    score: 76
  },
  {
    category: '发言',
    categoryKey: 'statement',
    time: '08:00',
    title: 'Yann LeCun 再批自回归路线：这不是通往智能的路',
    summary: '在长推文中详细阐述了为什么他认为当前的LLM架构无法实现AGI，提出联合嵌入预测架构(JEPA)才是正确方向。',
    mentions: 6,
    score: 68
  },
  {
    category: '商业',
    categoryKey: 'business',
    time: '07:30',
    title: '豆包大模型宣布企业版API全面涨价35%',
    summary: '字节跳动旗下豆包大模型企业API价格上调，128K上下文版本涨幅最大。市场分析认为此举反映算力成本压力。',
    mentions: 9,
    score: 71
  },
  {
    category: '新模型',
    categoryKey: 'model',
    time: '06:45',
    title: 'Anthropic 发布 Claude 4 Sonnet 预览版',
    summary: '新版本在复杂工具使用和多步推理方面有明显改进，率先开放给API付费用户测试。',
    mentions: 7,
    score: 65
  },
  {
    category: '发言',
    categoryKey: 'statement',
    time: '06:00',
    title: 'Dario Amodei：AI安全投入需要指数级增长',
    summary: 'Anthropic CEO在博文中呼吁行业将安全研究预算提升至模型训练成本的20%以上。',
    mentions: 5,
    score: 55
  },
  {
    category: '事故',
    categoryKey: 'incident',
    time: '05:30',
    title: 'Google Gemini 图像生成再现偏差问题',
    summary: '用户发现Gemini在生成历史人物图像时再次出现不准确的种族多样性表现，Google暂时下线该功能。',
    mentions: 4,
    score: 48
  },
  {
    category: '商业',
    categoryKey: 'business',
    time: '04:00',
    title: 'Mistral 完成新一轮6亿欧元融资',
    summary: '估值达到60亿欧元，资金将用于扩建欧洲本土GPU集群和多模态模型研发。',
    mentions: 6,
    score: 58
  }
];
