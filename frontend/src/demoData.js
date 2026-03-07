export const DEMO_SESSIONS = [
    { user_id: '【大四】林同学', platform: 'wechat', message_count: 9, updated_at: '2026-03-06 15:30:22', is_demo: true },
    { user_id: '王总(找融资)', platform: 'wechat', message_count: 11, updated_at: '2026-03-06 15:28:15', is_demo: true, needs_intervention: true },
    { user_id: 'HR-Amanda', platform: 'pdd', message_count: 7, updated_at: '2026-03-06 15:25:01', is_demo: true },
    { user_id: '🔥急单-李先生', platform: 'taobao', message_count: 8, updated_at: '2026-03-06 15:20:10', is_demo: true },
    { user_id: '愤怒的甲方(售后)', platform: 'pdd', message_count: 9, updated_at: '2026-03-06 15:15:33', is_demo: true, needs_intervention: true },
    { user_id: '智创科技-陈总监', platform: 'wechat', message_count: 6, updated_at: '2026-03-06 15:10:05', is_demo: true },
    { user_id: '补开发票-张三', platform: 'pdd', message_count: 4, updated_at: '2026-03-06 14:00:00', is_demo: true },
];

export const DEMO_CHATS = {
    '【大四】林同学': [
        { role: 'user', content: '你好，我是大四学生，下周要答辩了，想做一个毕业答辩的PPT，大概多少钱呀？', created_at: '15:20:10' },
        { role: 'assistant', platform: 'bot', content: '同学你好！恭喜即将毕业🎉\n毕业答辩PPT通常包含学术风格排版和清晰的逻辑梳理。我们对学生有专属的【校园特惠价】：\n基础排版版：15元/页\n精美学术版（含定制图表和微动画）：30元/页\n请问你的PPT大概有多少页内容呢？', created_at: '15:20:12' },
        { role: 'user', content: '大概有25页，我的预算不是很多，只有300块钱左右...能不能便宜点呀？主要是导师说我原来那个太丑了，让我重做😭', created_at: '15:22:00' },
        { role: 'assistant', platform: 'bot', content: '非常理解你的情况！🎓\n如果是25页的话，基础排版特惠价是375元。为了支持你的答辩，我可以帮你申请一个【学生专属9折优惠】，折后大概337元。\n这个价格能接受吗？我可以让设计师重点帮你优化封面和核心数据页，保证答辩效果！', created_at: '15:22:05' },
        { role: 'user', content: '337可以的！谢谢你！那我应该怎么发资料给你们？', created_at: '15:25:10' },
        { role: 'assistant', platform: 'bot', content: '太好了！你可以直接把目前的PPT原文件，以及导师的具体修改意见（截图或者文档）发在这个聊天框里。然后点击这个链接支付定金（50%）：[学生特惠专属定金链接]。', created_at: '15:25:12' },
        { role: 'user', content: '好的，我已经付了。资料发过去了 [文件：林xx_毕业答辩_v2.pptx]', created_at: '15:28:20' },
        { role: 'assistant', platform: 'bot', content: '收到啦！定金已核销，文件已安全接收存档。\n已为你生成工单 #STU-20260306。\n设计师小周会在5分钟内来加你微信，答辩加油鸭！💪', created_at: '15:28:22' },
        { role: 'user', content: '好的，麻烦让他快点加我，我有点焦虑', created_at: '15:30:22' },
    ],
    '王总(找融资)': [
        { role: 'user', content: '[语音 20s] 小伙子啊，我这边有个大健康的项目，马上要见几个投资人，需要搞个牛逼一点的商业计划书，你们能不能搞？', created_at: '15:10:00' },
        { role: 'assistant', platform: 'bot', content: '您好王总！商业计划书（BP）融资路演是我们非常核心的业务。\n我们有专门的【投融创投设计组】，能够为您提供从商业逻辑梳理到高端视觉定制的完整服务。\n请问您的项目目前有基础的商业计划文档或大纲吗？大概什么时候需要用到呢？', created_at: '15:10:03' },
        { role: 'user', content: '[语音 15s] 资料嘛，我有个大概的Word，但是不全。主要是我脑子里有完整的想法，能不能我直接口述，你们帮我整理出来做成PPT？', created_at: '15:12:00' },
        { role: 'assistant', platform: 'bot', content: '完全没问题！我们提供【策划+设计一站式服务】。\n流程是这样的：\n1. 安排资深商业策划师与您电话深度沟通（约1小时），梳理商业模式、盈利模式和核心壁垒。\n2. 策划师出具PPT大纲供您确认。\n3. 大纲确认后，设计总监介入进行高端视觉定制。\n\n这类全案定制的起步价是 5000元，具体根据沟通深度和最终页数评估。您觉得这个流程OK吗？', created_at: '15:12:05' },
        { role: 'user', content: '价格好说，关键是东西要干！下周二我就要飞北京见薛总，能赶出来吗？时间很紧啊！', created_at: '15:15:00' },
        { role: 'assistant', platform: 'bot', content: '下周二交付时间确实非常紧凑，但我们可以为您开启【特急全案通道】！\n如果今天能完成电话沟通和定金支付，我们周末无休为您赶工，确保下周一晚上把终稿交到您手上，绝对不耽误您周二的行程。\n\n特急服务需要加收30%的加急费，可以接受吗？', created_at: '15:15:03' },
        { role: 'user', content: '行！只要东西好，加急费我出。现在怎么弄？', created_at: '15:18:00' },
        { role: 'assistant', platform: 'bot', content: '爽快！请您点击下方链接支付全案意向定金 2000元：\n[大客户全案意向定金链接]\n\n支付完成后，我立刻拉群，我们的主策划和设计总监现在就可以和您开个语音会议对接细节！', created_at: '15:18:05' },
        { role: 'user', content: '付了！你赶紧拉群，我马上上车了，路上可以说。', created_at: '15:20:00' },
        { role: 'assistant', platform: 'bot', content: '收到您的定金！财务已确认。\n专属服务群已建好，群名【王总-大健康融资BP专案组】，主策划老李和设计总监Amy已经就位，请您在微信确认通过入群邀请。祝您一路顺风，我们群里见！', created_at: '15:20:03' },
        { role: 'user', content: '🤝👍🌹', created_at: '15:28:15' }
    ],
    'HR-Amanda': [
        { role: 'user', content: '你好，我们需要做一份季度总结的PPT，能发点你们的案例看看吗？', created_at: '15:15:00' },
        { role: 'assistant', platform: 'bot', content: '您好，Amanda！季度总结PPT是我们做过最多的类型之一。\n这里为您准备了几套不同风格的精选案例：\n1. 📊 [稳重商务风-适合国企/传统行业]\n2. 🚀 [现代科技风-适合互联网/科技公司]\n3. ✨ [极简扁平风-适合外企/创意团队]\n\n您看贵公司偏好哪种风格呢？如果方便，可以发一下贵公司的Logo，我们可以为您免费做一个封面Demo。', created_at: '15:15:02' },
        { role: 'user', content: '我们是做SaaS的，现代科技风比较合适。这次大概有30页，主要是很多数据图表，你们能把数据图表做的好看点吗？不想用系统自带的。', created_at: '15:18:00' },
        { role: 'assistant', platform: 'bot', content: '绝对没问题！针对SaaS行业和大量数据图表的需求，我们建议采用【定制级数据可视化排版】（单价约60元/页）。\n我们会废弃系统自带图表，使用矢量图形重新绘制，确保数据清晰的同时，极具高级感和科技感。\n\n这是我们做过的数据可视化案例截图：[图片:数据图表对比.png]\n30页的话，总价预计在 1800元左右。您觉得合适吗？', created_at: '15:18:05' },
        { role: 'user', content: '看着不错。那怎么开发票？我们公司报销需要增值税专用发票。', created_at: '15:22:00' },
        { role: 'assistant', platform: 'bot', content: '我们可以开具【增值税专用发票】的！\n流程上，您可以在确认收稿并付清尾款后，提供公司的开票信息（抬头、税号、地址电话、开户行及账号），我们会在3个工作日内为您开具并寄出纸质专票。\n\n如果确认制作，请拍下定金链接：[PPT定制通用定金50%]', created_at: '15:22:03' },
        { role: 'user', content: 'ok，我走一下审批流程，晚点拍。', created_at: '15:25:01' }
    ],
    '🔥急单-李先生': [
        { role: 'user', content: '在不在？！十万火急！明早9点要投标！！！', created_at: '15:00:00' },
        { role: 'assistant', platform: 'bot', content: '在的在的！深呼吸，我们来帮您解决！🚑\n明早9点投标完全来得及，我们有通宵突击团队！\n请问这份投标PPT目前是什么状态？是需要纯美化排版，还是内容也需要调整？大概多少页？', created_at: '15:00:02' },
        { role: 'user', content: '内容都写好了，一共45页，但是非常乱，完全拿不出手！你们今晚能给我美化完吗？钱不是问题！', created_at: '15:02:00' },
        { role: 'assistant', platform: 'bot', content: '了解！45页的纯美化排版，要求明早9点前交付，属于【特级夜间突击单】。\n为了保证质量和速度，我们会安排2位资深设计师拆分页面协同作业，明早8点前一定把定稿发给您！\n\n特级夜间加急的费用是 80元/页，45页合计 3600元。\n时间紧迫，如果您同意，请立即发送文件给我，并拍下全款链接，我们立刻开工！', created_at: '15:02:05' },
        { role: 'user', content: '没问题，文件发你了。 [文件：市政工程投标方案_终版_千万别改错.pptx]', created_at: '15:05:00' },
        { role: 'assistant', platform: 'bot', content: '收到文件！设计师已经在分析文件字体和母版了。\n请您花1分钟拍下链接：[夜间突击全款专用通道_3600元]\n拍下后我马上建群。', created_at: '15:05:03' },
        { role: 'user', content: '付完了！兄弟们靠你们了，这个标对我们公司很重要！', created_at: '15:08:00' },
        { role: 'assistant', platform: 'bot', content: '感谢信任！款项已收到。\n🚀 工单已启动！今夜无眠，保证完成任务。\n设计师A和设计师B已入群，稍后会在群里发2页的风格Demo给您确认，确认后我们就火力全开。请留意微信群消息！', created_at: '15:08:03' }
    ],
    '愤怒的甲方(售后)': [
        { role: 'user', content: '你们怎么搞的？这做的是什么垃圾玩意？！根本和我给的参考图不一样！', created_at: '15:00:00' },
        { role: 'assistant', platform: 'bot', content: '在此向您致以最诚挚的歉意🙇！非常抱歉没能达到您的期望。为了尽快给您一个满意的答复，能具体说说哪里觉得不合适吗？是色彩、排版还是整体风格的问题？我们承诺修改到您满意为止！', created_at: '15:00:02' },
        { role: 'user', content: '你是不是机器人啊？我昨天跟你们设计师说了三遍！要极简！要高端！结果今天给我发过来的全是花里胡哨的渐变色和俗气的3D小人，你们能听懂人话吗？', created_at: '15:05:00' },
        { role: 'assistant', platform: 'bot', content: '非常理解您的愤怒。设计师没有准确把握“极简高端”的需求并使用了错误的设计元素，这是我们的严重失误。\n我已经把您的情况紧急升级。为了不耽误您的时间，我立刻为您申请更换一位擅长极简留白风格的【设计总监】亲自为您重做，且不收任何额外费用。\n\n⚠️ （系统提示：识别到用户强烈不满，已呼叫主管介入）', created_at: '15:05:05' },
        { role: 'user', content: '换总监？你们总监能行吗？我明天下午就要用了，现在重做来得及？要是不行赶紧给我退款，我去找别人！', created_at: '15:08:00' },
        { role: 'assistant', platform: 'manual', content: '您好，我是设计部的主管老赵。刚看了您的聊天记录和原稿，确实是我们设计师对“极简”的理解出了偏差，太急于展示技巧了，实在抱歉。\n您放心，这单我亲自接手。我已经把那些渐变和3D元素全部删掉了。极简风格讲究的是排版版式、字体层级和高级留白。我今天晚上带人通宵给您重排，明早10点前给您看一版真正对标苹果发布会级别的初稿。\n如果不满意，我个人做主全额退款。您看能再给我们一次机会吗？', created_at: '15:10:00' },
        { role: 'user', content: '行，赵主管，既然你这么说了，我就等明早10点。要是还不行，别怪我不客气，我是要直接去平台投诉的。', created_at: '15:12:00' },
        { role: 'assistant', platform: 'manual', content: '没问题，一言为定！您早点休息，剩下的交给我。明早10点我准时在微信群里发您初稿。', created_at: '15:14:00' },
        { role: 'user', content: '嗯。', created_at: '15:15:33' }
    ],
    '智创科技-陈总监': [
        { role: 'user', content: '哈喽，我们下个月有个大型行业展会，除了主会场的宣讲PPT，我们还需要配套的展会海报、宣传册和H5长图。你们这边能做全套的外包吗？', created_at: '15:00:00' },
        { role: 'assistant', platform: 'bot', content: '您好陈总监！我们完全可以承接！我们不仅是PPT专家，背后还有完整的【全案视觉设计团队】。\n像展会这种需要统一视觉识别系统（VI）的场景，打包交给我们是最高效、视觉最统一的选择。\n我们可以为您提供：\n1. 主会场级宽屏PPT定制\n2. 展会线下物料（海报、易拉宝、三折页宣传册）\n3. 线上宣发物料（H5长图、朋友圈首图）\n请问这次展会的主题定了吗？', created_at: '15:00:03' },
        { role: 'user', content: '主题是“智领未来·云端共生”，主要是推我们最新的AI智算平台。预算大概3万左右。', created_at: '15:05:00' },
        { role: 'assistant', platform: 'bot', content: '非常棒的主题！3万元的预算非常充足，足够我们为您配置【顶级全案专属团队】（含1名主视觉KV设计师，2名物料设计师，1名PPT动效师，1名项目经理）。\n\n为了给您更精准的报价和排期，我们需要拉个会对齐一下各项物料的具体数量和尺寸。您看今天下午或明天上午方便安排一个简短的腾讯会议吗？', created_at: '15:05:05' },
        { role: 'user', content: '明天上午10点吧。我把会议链接发在群里，你让你们项目经理准时上线。', created_at: '15:08:00' },
        { role: 'assistant', platform: 'bot', content: '好的，已为您预约明天上午10点的需求对接会。\n我们的资深大客户经理（Tony）和主视觉总监（Leo）会准时参会。期待与智创科技的深度合作！', created_at: '15:08:05' }
    ],
    '补开发票-张三': [
        { role: 'user', content: '上个月做的一个PPT，现在可以补开发票吗？', created_at: '13:50:00' },
        { role: 'assistant', platform: 'bot', content: '您好！合作愉快，可以补开发票的。\n请问您需要开具增值税普通发票还是专用发票呢？\n另外，请直接在对话框回复您的：\n1. 企业全称抬头\n2. 纳税人识别号(税号)\n3. 接收电子发票的有效邮箱地址（专票需提供详细地址和开户行）', created_at: '13:50:02' },
        { role: 'user', content: '普票就行。\n抬头：杭州三叶草网络科技有限公司\n税号：91330100XXXXXX456T\n邮箱：zhangsan@sanyecao.com', created_at: '13:55:00' },
        { role: 'assistant', platform: 'bot', content: '✅ 已经顺利接收您的开票资料，验证无误！\n\n🎉 发票申请已提交，序列号：INV-2026-0089222。\n电子发票文档最迟会在第二个工作日下午发送至您的邮箱 zhangsan@sanyecao.com，请留意查收。如果没收到可以随时联系我！', created_at: '13:55:05' }
    ]
};

// 优先级映射（用于干预池排序和颜色展示）
// priority: 'urgent' | 'high' | 'normal'
export const DEMO_ESCALATIONS = [
    // ── 售后冲突 ───────────────────────────────────────────────
    { id: 1, user_id: '愤怒的甲方(售后)', reason_label: '售后冲突/高压维权', priority: 'urgent', trigger_message: '你是不是机器人啊？我昨天跟你们设计师说了三遍！要极简！要高端！结果今天给我发过来的全是花里胡哨的渐变色和俗气的3D小人，你们能听懂人话吗？！' },
    { id: 2, user_id: '赵老板(退款纠纷)', reason_label: '售后冲突/高压维权', priority: 'urgent', trigger_message: '我明天就去拼多多官方投诉！你们这是欺诈消费者，发给我的稿子根本不是我要的风格，我要退全款！' },
    { id: 3, user_id: '匿名买家1038', reason_label: '售后冲突/一般不满', priority: 'high', trigger_message: '质量太差了，而且还没有按时交货，跟之前说好的完全不一样 😡😡😡' },

    // ── 大客户 / 高价值 / 加急 ─────────────────────────────────
    { id: 4, user_id: '王总(找融资)', reason_label: '大客户加急/复杂需求', priority: 'urgent', trigger_message: '价格好说，关键是东西要干！下周二我就要飞北京见薛总，能赶出来吗？时间很紧啊！' },
    { id: 5, user_id: '🔥急单-李先生', reason_label: '限时加急/夜间突击单', priority: 'urgent', trigger_message: '明早9点投标！！文件刚发你了，今晚必须搞完！！钱不是问题！！！' },
    { id: 6, user_id: 'CEO-David(外企)', reason_label: '大客户/语言障碍', priority: 'high', trigger_message: 'I need bilingual PPT slides for our board meeting. English + Chinese. The budget is flexible, but quality must be top-tier. Can your team handle this?' },

    // ── 规则触发自动接管 ──────────────────────────────────────
    { id: 7, user_id: '张工程师(定制插件需求)', reason_label: '规则触发/超出服务范围', priority: 'normal', trigger_message: '我需要一个可以自动运行的PPT宏脚本，当某个数据超过阈值的时候图表颜色自动变红，这个你们能写代码实现吗？' },
    { id: 8, user_id: '小王(砍价达人)', reason_label: '规则触发/连续低价骚扰', priority: 'normal', trigger_message: '便宜点啊！100块钱20页行不行？上次我朋友在你们这里做也是这个价！不然我去找别人了，反正网上多的是' },

    // ── 边缘测试数据 ──────────────────────────────────────────
    { id: 9, user_id: 'Emoji用户🎯🔥💯', reason_label: '规则触发/语义检测', priority: 'normal', trigger_message: '🙏🙏 求求你了！！！！帮帮忙吧！老板明天要！！！😭😭😭😭 我已经催了好多次了 这次再做不好我真的要被开除了！！！我求求你们！！！！！！！！😭😭' },
    { id: 10, user_id: '测试用户-超长触发词', reason_label: '售后冲突/投诉升级', priority: 'high', trigger_message: '我已经和你们的客服沟通了三次了，每次都说会改，每次我拿到的稿件还是同样的问题，颜色搭配完全是错的，字体也太小，我给你们的参考图你们压根没看，这种服务态度让我非常失望，我决定去消费者协会反映，并且在所有社交平台给你们差评，告诉所有人不要来这里做PPT，你们的服务真的太差了！！！' },
    { id: 11, user_id: '匿名买家5577', reason_label: '开票/合规问题', priority: 'normal', trigger_message: '我要开增值税专用发票，金额2万。对方财务说你们开的普票不合规，我要退款重新走公对公打款流程，你们能配合吗？' },
    { id: 12, user_id: '已回复待关闭_陈同学', reason_label: '大客户加急/已人工处理', priority: 'high', trigger_message: '客服已经帮我解决了，但系统提示还没消失，请关闭这条干预记录。（此条目用于测试"已回复但干预状态未消"边缘场景）' },
];

export const DEMO_ORDERS = [
    { id: '1001', order_sn: 'PPT-20260306-0982', status: 'req_fixed', requirement: JSON.stringify({ topic: '市政工程投标方案', pages: '45页', style: '严肃正规', deadline: '明早9点前', details: '特级夜间加急，需要2个设计师同时开工，绝对不能出错。' }), user_id: '🔥急单-李先生', created_at: '2026-03-06 15:05:00' },
    { id: '1002', order_sn: 'PPT-20260306-0981', status: 'processing', requirement: JSON.stringify({ topic: '大健康项目商业计划书', pages: '约20页', style: '高端科技', details: '创始人全案定制，有语音沟通记录。' }), user_id: '王总(找融资)', created_at: '2026-03-06 15:20:00' },
    { id: '1003', order_sn: 'PPT-20260306-0980', status: 'awaiting_review', requirement: JSON.stringify({ topic: '大四毕业答辩', pages: '25页', style: '学术严谨', details: '学生特惠，需要改封面。' }), user_id: '【大四】林同学', created_at: '2026-03-06 15:28:20' },
    { id: '1004', order_sn: 'PPT-20260306-0970', status: 'shipped', requirement: JSON.stringify({ topic: '智创科技企业介绍', pages: '18页', style: '现代科技' }), user_id: '智创科技-陈总监', created_at: '2026-03-05 10:00:00' }
];

export const DEMO_STATS = {
    active_sessions: 124,
    pending_escalations: 2,
    active_orders: 8,
    conversion_rate: '8.4%',
    avg_response_time: '1.2s',
    total_revenue: '¥ 12,840',
    satisfaction_rate: '98.5%'
};

// 24 小时时间轴标签
const HOURS_24 = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'];

// 多天小时数据 — 左→右 = 最早→今日
export const DEMO_MULTI_DAY = [
    {
        label: '3月3日', date: '2026-03-03', color: '#8B5CF6', hours: HOURS_24,
        conversations: [6, 3, 1, 1, 0, 4, 12, 35, 65, 100, 140, 165, 150, 125, 175, 230, 215, 180, 140, 110, 80, 55, 30, 14],
        aiRate: [0, 0, 0, 0, 0, 75, 80, 82, 78, 74, 70, 68, 72, 76, 71, 65, 67, 73, 78, 80, 82, 85, 88, 90],
        responseTime: [0, 0, 0, 0, 0, 1.1, 1.3, 1.5, 2.0, 2.4, 2.8, 3.1, 2.6, 2.2, 2.9, 3.5, 3.2, 2.7, 2.1, 1.8, 1.5, 1.2, 1.0, 0.8],
        conversions: [0, 0, 0, 0, 0, 0, 1, 2, 4, 6, 9, 11, 10, 8, 12, 15, 14, 11, 8, 6, 4, 3, 2, 1],
        escalations: [0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 5, 6, 5, 4, 6, 8, 7, 5, 4, 3, 2, 1, 1, 0]
    },
    {
        label: '3月4日', date: '2026-03-04', color: '#EC4899', hours: HOURS_24,
        conversations: [2, 1, 0, 0, 0, 1, 6, 18, 42, 78, 110, 135, 120, 90, 155, 200, 185, 160, 125, 95, 68, 42, 20, 8],
        aiRate: [0, 0, 0, 0, 0, 80, 78, 76, 72, 70, 66, 64, 68, 72, 65, 60, 63, 70, 75, 78, 80, 84, 87, 92],
        responseTime: [0, 0, 0, 0, 0, 0.9, 1.2, 1.8, 2.2, 2.6, 3.0, 3.4, 2.8, 2.3, 3.2, 3.8, 3.5, 2.9, 2.3, 1.9, 1.4, 1.1, 0.9, 0.7],
        conversions: [0, 0, 0, 0, 0, 0, 0, 1, 3, 5, 7, 9, 8, 6, 10, 13, 12, 10, 8, 5, 4, 2, 1, 0],
        escalations: [0, 0, 0, 0, 0, 0, 1, 1, 2, 4, 5, 7, 5, 3, 6, 9, 8, 6, 4, 3, 2, 1, 0, 0]
    },
    {
        label: '前日', date: '2026-03-05', color: '#10B981', hours: HOURS_24,
        conversations: [8, 4, 2, 1, 0, 5, 15, 40, 85, 130, 180, 210, 195, 160, 220, 285, 260, 200, 150, 105, 75, 50, 28, 15],
        aiRate: [0, 0, 0, 0, 0, 82, 79, 75, 71, 68, 64, 62, 66, 70, 63, 58, 61, 68, 73, 77, 81, 84, 86, 91],
        responseTime: [0, 0, 0, 0, 0, 1.0, 1.4, 1.9, 2.5, 2.9, 3.3, 3.6, 3.0, 2.5, 3.4, 4.0, 3.7, 3.0, 2.4, 1.9, 1.5, 1.2, 1.0, 0.8],
        conversions: [0, 0, 0, 0, 0, 1, 1, 3, 5, 8, 12, 14, 13, 10, 15, 19, 17, 13, 10, 7, 5, 3, 2, 1],
        escalations: [0, 0, 0, 0, 0, 0, 1, 2, 3, 5, 7, 9, 7, 5, 8, 12, 10, 8, 5, 3, 2, 1, 1, 0]
    },
    {
        label: '昨日', date: '2026-03-06', color: '#F59E0B', hours: HOURS_24,
        conversations: [5, 2, 1, 0, 0, 3, 10, 30, 70, 112, 125, 140, 118, 95, 140, 162, 155, 130, 110, 88, 65, 45, 22, 10],
        aiRate: [0, 0, 0, 0, 0, 85, 81, 77, 73, 71, 67, 65, 69, 74, 66, 62, 64, 71, 76, 79, 83, 86, 89, 93],
        responseTime: [0, 0, 0, 0, 0, 0.8, 1.1, 1.6, 2.1, 2.5, 2.9, 3.2, 2.7, 2.1, 3.0, 3.6, 3.3, 2.8, 2.2, 1.7, 1.3, 1.0, 0.8, 0.6],
        conversions: [0, 0, 0, 0, 0, 0, 1, 2, 4, 7, 8, 9, 8, 6, 9, 11, 10, 8, 7, 5, 3, 2, 1, 1],
        escalations: [0, 0, 0, 0, 0, 0, 0, 1, 3, 4, 5, 6, 4, 3, 5, 7, 6, 4, 3, 2, 2, 1, 0, 0]
    },
    {
        label: '今日', date: '2026-03-07', color: '#6366F1', hours: HOURS_24,
        conversations: [3, 1, 0, 0, 1, 2, 8, 22, 55, 98, 145, 178, 132, 110, 188, 340, 310, 265, 190, 145, 92, 60, 35, 12],
        aiRate: [0, 0, 0, 0, 100, 90, 85, 80, 76, 72, 69, 66, 70, 75, 68, 61, 63, 69, 74, 78, 82, 85, 88, 92],
        responseTime: [0, 0, 0, 0, 0.5, 0.7, 1.0, 1.4, 1.8, 2.3, 2.7, 3.0, 2.5, 2.0, 2.8, 3.5, 3.2, 2.6, 2.0, 1.6, 1.2, 0.9, 0.7, 0.5],
        conversions: [0, 0, 0, 0, 0, 0, 1, 1, 3, 6, 9, 12, 9, 7, 12, 22, 20, 17, 12, 9, 6, 4, 2, 1],
        escalations: [0, 0, 0, 0, 0, 0, 0, 1, 2, 4, 6, 8, 5, 4, 7, 14, 12, 9, 6, 4, 3, 1, 1, 0]
    },
];

// 指标元数据
export const METRIC_OPTIONS = [
    { key: 'conversations', label: '对话量', unit: '条', icon: '💬' },
    { key: 'aiRate', label: 'AI解决率', unit: '%', icon: '🤖' },
    { key: 'responseTime', label: '响应耗时', unit: 's', icon: '⏱️' },
    { key: 'conversions', label: '成单转化', unit: '单', icon: '🛒' },
    { key: 'escalations', label: '人工干预', unit: '次', icon: '🚨' },
];

// 保留兼容旧引用
export const DEMO_HOURLY = { hours: HOURS_24, counts: DEMO_MULTI_DAY[4].conversations };
export const DEMO_HOURLY_YESTERDAY = { hours: HOURS_24, counts: DEMO_MULTI_DAY[3].conversations };

export const DEMO_KNOWLEDGE = [
    { id: '1a2b3c4d-5e6f-7g8h-9i0j', content: '### 定价策略\n- 基础排版：15-30元/页，适合内部汇报、学生答辩，主要做对齐和简单配色。\n- 商务精装：50-80元/页，适合外部宣讲、招商路演，包含定制图表、重绘和微动画。\n- 高端全定制：100-200元/页，对标发布会级别，包含3D建模、复杂动画和原画级插图。' },
    { id: '9f8e7d6c-5b4a-3z2y-1x0w', content: '### 交付与售后政策\n- 初稿交付时间：日常单 24-48小时，加急单 6-12小时。\n- 修改次数：定稿前提供【无限次】细节修改，直到客户满意。\n- 退款政策：初稿若严重偏离客户原需求且拒绝修改，可全额退款；修改超过3次后提出退款，仅退换尾款，定金不退。' },
    { id: '5h6g7f8e-9d0c-1b2a-3z4y', content: '### 发票开具说明\n本店支持开具【增值税普通发票】和【增值税专用发票】。\n- 普票需提供：抬头、税号、邮箱。\n- 专票需额外提供：注册地址、企业电话、开户行及账号。\n- 开具时间：订单确认收货且尾款结清后的 1-3 个工作日内，电子发票发送至邮箱，纸质专票顺丰到付。' }
];
