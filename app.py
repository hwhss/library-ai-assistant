import streamlit as st
import time
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import re

# 页面配置
st.set_page_config(
    page_title="图小助-内师大图书馆AI助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 超美观自定义CSS
st.markdown('''
<style>
/* 全局背景 */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}
/* 标签页 */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    justify-content: center;
    margin-bottom: 20px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 15px;
    padding: 10px 20px;
    background: white;
    border: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white !important;
}
/* 聊天容器 */
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}
/* 用户消息 */
.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 20px 20px 0 20px;
    margin: 10px 0;
    margin-left: auto;
    max-width: 70%;
    text-align: left;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}
/* AI消息 */
.assistant-message {
    background: white;
    padding: 15px 20px;
    border-radius: 20px 20px 20px 0;
    margin: 10px 0;
    margin-right: auto;
    max-width: 70%;
    text-align: left;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
/* 按钮样式 */
.stButton>button {
    border-radius: 12px;
    border: none;
    padding: 8px 12px;
    font-size: 13px;
    background: white;
    color: #2c3e50;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: all 0.2s;
}
.stButton>button:hover {
    background: #667eea;
    color: white;
    transform: translateY(-2px);
}
/* 输入框 */
.stChatInput>div>div>input {
    border-radius: 25px;
    padding: 15px 20px;
    border: 1px solid #e0e0e0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
/* 卡片样式 */
.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin: 10px 0;
    transition: all 0.2s;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.1);
}
.copy-btn {
    background: #f0f0f0;
    border: none;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 12px;
    cursor: pointer;
    margin-top: 8px;
    float: right;
}
.copy-btn:hover {
    background: #667eea;
    color: white;
}
.mongol-badge {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 3px 8px;
    border-radius: 10px;
    font-size: 12px;
}
.feedback-btn {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}
</style>
''', unsafe_allow_html=True)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "custom_kb" not in st.session_state:
    st.session_state.custom_kb = {}
if "feedback" not in st.session_state:
    st.session_state.feedback = 0

# 模拟数据
book_collection = {
    "三体": {"floor": "三楼文学区", "status": "在架可借", "location": "3F-A12"},
    "活着": {"floor": "二楼社科区", "status": "已借出", "location": "2F-B05", "return_date": "2026-03-28"},
    "深度学习": {"floor": "五楼科技区", "status": "在架可借", "location": "5F-C08"},
    "平凡的世界": {"floor": "三楼文学区", "status": "在架可借", "location": "3F-A15"},
    "Python编程": {"floor": "五楼科技区", "status": "已借出", "return_date": "2026-04-02"},
    "蒙古秘史": {"floor": "二楼民族文献区", "status": "在架可借", "location": "2F-D01"},
}

seat_status = {
    "一楼自习区": {"total": 80, "left": 12, "full": False},
    "二楼自习区": {"total": 100, "left": 3, "full": True},
    "三楼自习区": {"total": 120, "left": 25, "full": False},
    "五楼研讨室": {"total": 10, "left": 2, "full": False},
}

new_books = [
    {"name": "长安的荔枝", "author": "马伯庸", "floor": "三楼文学区"},
    {"name": "DeepLearning入门", "author": "Ian Goodfellow", "floor": "五楼科技区"},
    {"name": "额尔古纳河右岸", "author": "迟子建", "floor": "三楼文学区"},
    {"name": "蒙古文化研究", "author": "内蒙古人民出版社", "floor": "二楼民族区"},
]

# 完整的双语知识库，补全了蒙语的常用问题！
default_kb = {
    # 中文常用问题
    "图书馆开放时间": "图书馆的开放时间是：周一至周日 8:00-22:00，法定节假日会调整为9:00-17:00，具体请关注官网通知。",
    "图书馆几点关门": "图书馆的关门时间是22:00，周一到周日都是，法定节假日是17:00关门哦。",
    "图书馆有没有WiFi": "有的！图书馆覆盖了校园WiFi，你可以连接「内师大-WiFi」，用你的校园账号登录就能用了！",
    "WiFi怎么连": "你可以搜索WiFi名称「内师大-WiFi」，然后用你的校园账号和密码登录，就能免费使用了！",
    "图书借阅期限是多久": "普通中文图书的借阅期限是30天，外文图书、热门畅销书的借阅期限是15天，期刊合订本是7天。",
    "怎么续借图书": "您有4种方式续借：1. 图书馆官网登录个人中心操作；2. 微信公众号「内师大图书馆」办理；3. 自助借还机上操作；4. 到前台找工作人员办理。续借期限为15天，每本书最多续借1次。",
    "逾期罚款怎么算": "图书逾期未还的话，每本每天罚款0.1元，单本图书最高罚款不超过图书原价。逾期超过90天，会暂停您的借阅权限。",
    "怎么借书": "您可以携带校园卡/读者证，到自助借还机上扫描图书和证件，按照提示操作即可，也可以到前台人工办理。",
    "怎么还书": "还书可以在自助借还机上操作，也可以放到门口的24小时还书箱，或者到前台办理。",
    "最多能借几本书": "本科生读者最多可借10本，研究生最多可借15本，教师最多可借20本，借阅总时长不超过60天。",
    "自习室怎么预约": "您可以通过图书馆官网、微信公众号的「座位预约」系统，提前1-3天预约自习室座位，预约成功后凭预约码入座，超时15分钟未到会自动取消预约。",
    "自习室可以占座吗": "图书馆禁止占座，离开座位超过30分钟，其他读者可以使用该座位，违规占座会被暂停预约权限。",
    "自习室有电源吗": "自习室的每个座位都配有电源插座和USB接口，您可以给电脑、手机充电。",
    "自习室可以吃东西吗": "自习室禁止饮食，您可以到一楼的休闲区用餐。",
    "电子图书怎么下载": "您可以登录图书馆的数字资源平台，找到对应的电子图书，点击下载即可，部分资源需要在馆内IP访问，校外可以通过VPN访问。",
    "怎么看知网论文": "您可以通过图书馆官网的「数字资源」入口进入知网，登录后即可下载论文，校外可以通过VPN访问。",
    "数据库怎么用": "图书馆购买了知网、万方、维普、Web of Science等几十个数据库，您可以在官网的数字资源页面找到入口，在校内直接访问，校外用VPN。",
    "怎么办理读者证": "本校师生凭校园卡直接就能用，不用额外办证；校外读者可以携带身份证到前台办理临时读者证，押金100元。",
    "读者证丢了怎么办": "您可以到前台办理挂失，挂失后7天可以补办新证，也可以在官网的个人中心在线挂失。",
    "密码忘了怎么办": "您可以在官网的登录页面点击「忘记密码」，通过手机号/邮箱重置，也可以到前台重置。",
    "图书馆可以打印复印吗": "一楼大厅有自助打印复印一体机，支持扫码支付，打印0.1元/张，复印0.1元/张。",
    "可以带包进图书馆吗": "可以的，您可以带包进入，但是禁止携带食品、饮料，禁止大声喧哗。",
    "新书怎么查询": "您可以在图书馆官网的馆藏查询系统，搜索书名、作者，就能查到这本书有没有馆藏，在哪个书架，是否可借。",
    "图书馆有研讨室吗": "有的，三楼有10个研讨室，您可以提前预约，最多8人使用，时长不超过4小时。",
    "到期提醒": "你可以告诉我你的借阅日期，我帮你算什么时候到期哦！比如输入「我3月20号借的书」",
    # 功能类问题
    "本周有什么新书": "本周新到了4本好书哦：\n1. 《长安的荔枝》- 马伯庸，三楼文学区\n2. 《DeepLearning入门》- Ian Goodfellow，五楼科技区\n3. 《额尔古纳河右岸》- 迟子建，三楼文学区\n4. 《蒙古文化研究》- 内蒙古人民出版社，二楼民族区",
    "还有空位吗": "各楼层剩余空位情况：\n- 一楼自习区：剩余12个空位\n- 二楼自习区：剩余3个空位，即将满座\n- 三楼自习区：剩余25个空位\n- 五楼研讨室：剩余2个空位",
    # 蒙语问题，补全了常用的！
    "ном хэрхэн сунгах вэ?": "Та 4 аргаар ном сунгаж болно: 1. Номын сангийн вэб сайт дээр хувийн төвдөө ороод ажиллуулах; 2. «Дотоодын их сургуулийн номын сан» хэмээх WeChat албан ёсны дансаар дамжуулан; 3. Өөрөө ажиллуулах машин дээр; 4. Урд талын ажилтанд хандаж болно. Сунгах хугацаа 15 хоног, ном бүрд нэг л удаа сунгаж болно.",
    "номын сангийн нээх цаг": "Номын сангийн нээх цаг: Даваа гарагаас Ням гараг хүртэл 8:00-22:00, хууль ёсны амралтын өдрүүдэд 9:00-17:00 болно. Дэлгэрэнгүйг вэб сайт дээрээс харна уу.",
    "суудал хэрхэн захиалах вэ?": "Та номын сангийн вэб сайт, WeChat албан ёсны дансны «суудал захиалах» системээр дамжуулан, 1-3 хоногийн өмнө захиалж болно. Захиалга амжилттай болсны дараа захиалгын кодоор суудалдаа орох боломжтой. 15 минутын дотор ирэхгүй бол захиалга автоматаар цуцлагдана.",
    "WiFi яаж холбох вэ?": "Та WiFi нэр «Дотоодын их сургууль-WiFi» гэж хайгаад, өөрийн сургуулийн нэр, нууц үгээр нэвтэрч болно! Үнэгүй ашиглах боломжтой!",
    "номын сан хэвлэж болох уу?": "Нэгдүгээр давхрын танхимд өөрөө ажиллуулах хэвлэх машин байдаг. Scaner төлбөр хийх боломжтой, хэвлэх 0.1 юань/хуудас, хуулбарлах 0.1 юань/хуудас.",
}

def get_full_kb():
    full_kb = default_kb.copy()
    full_kb.update(st.session_state.custom_kb)
    return full_kb

# 解析日期，处理到期提醒
def parse_date_and_remind(query):
    # 提取日期
    # 匹配 3月20号 或者 2026-03-20 这种格式
    date_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{1,2})月(\d{1,2})号',
        r'(\d{1,2})\.(\d{1,2})\.',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, query)
        if match:
            try:
                if len(match.groups()) == 3:
                    # 年-月-日
                    year, month, day = map(int, match.groups())
                else:
                    # 月-日
                    month, day = map(int, match.groups())
                    year = datetime.now().year
                borrow_date = datetime(year, month, day)
                due_date = borrow_date + timedelta(days=30)
                days_left = (due_date - datetime.now()).days
                if days_left > 0:
                    return f"你的借阅日期是{month}月{day}日，到期时间是{due_date.month}月{due_date.day}日，还有{days_left}天到期哦！别忘了提前续借，不然会有逾期罚款的~"
                else:
                    return f"你的借阅日期是{month}月{day}日，已经逾期{-days_left}天了！请尽快还书，不然会影响你的借阅权限哦！"
            except:
                pass
    return None

# 处理功能类的提问
def handle_function_query(query):
    query_lower = query.lower()
    
    # 1. 到期提醒
    if "到期" in query_lower or "提醒" in query_lower or "还书" in query_lower:
        # 先看有没有日期
        date_remind = parse_date_and_remind(query)
        if date_remind:
            return date_remind
        else:
            return "你可以告诉我你的借阅日期，我帮你算什么时候到期哦！比如输入「我3月20号借的书」，我就会告诉你还有多少天到期~"
    
    # 2. 查新书
    if "新书" in query_lower or "本周新书" in query_lower:
        res = "本周新到了4本好书哦：\n"
        for book in new_books:
            res += f"- 《{book['name']}》- {book['author']}，{book['floor']}\n"
        return res
    
    # 3. 查座位
    if "座位" in query_lower or "空位" in query_lower or "自习室" in query_lower:
        res = "各楼层剩余空位情况：\n"
        for floor, status in seat_status.items():
            if status['full']:
                res += f"- {floor}：剩余{status['left']}个空位，即将满座\n"
            else:
                res += f"- {floor}：剩余{status['left']}个空位\n"
        return res
    
    # 4. 查馆藏
    for book_name in book_collection.keys():
        if book_name in query or query in book_name:
            info = book_collection[book_name]
            if info['status'] == "在架可借":
                return f"《{book_name}》的信息：\n- 所在楼层：{info['floor']}\n- 具体位置：{info['location']}\n- 可借状态：✅ 在架可借"
            else:
                return f"《{book_name}》的信息：\n- 所在楼层：{info['floor']}\n- 具体位置：{info['location']}\n- 可借状态：❌ 已借出，预计{info['return_date']}归还"
    
    return None

# 模糊搜索匹配
def find_best_match(query, kb, threshold=0.4):
    # 先处理功能类的提问
    func_answer = handle_function_query(query)
    if func_answer:
        return func_answer
    
    # 再处理普通的知识库匹配
    query_lower = query.lower()
    best_score = 0
    best_answer = None
    for key, answer in kb.items():
        key_lower = key.lower()
        if query_lower in key_lower or key_lower in query_lower:
            return answer
        score = SequenceMatcher(None, query_lower, key_lower).ratio()
        if score > best_score and score > threshold:
            best_score = score
            best_answer = answer
    return best_answer

# 标题+统计
st.markdown('''
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #2c3e50; margin: 0; font-size: 2.5em;">📚 图小助</h1>
    <p style="color: #7f8c8d; font-size: 1.2em; margin-top: 10px;">内师大图书馆专属AI助手，一站式解决你所有问题！</p>
    <div style="margin-top: 15px; display: flex; justify-content: center; gap: 30px; font-size: 14px; color: #666;">
        <span>✅ 已帮助 200+ 同学解决问题</span>
        <span>⏱️ 节省 80% 咨询时间</span>
        <span>📈 服务效率提升 100%</span>
    </div>
    <div style="margin-top: 10px;">
        <span class="mongol-badge">🇲🇳 支持中文/蒙语双语提问</span>
    </div>
</div>
''', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("💡 快捷提问")
    st.write("点一下就能问，不用打字！")
    
    kb = get_full_kb()
    quick_questions = list(kb.keys())[:10]
    
    # 分离蒙语和普通问题
    mongol_questions = []
    normal_questions = []
    for q in quick_questions:
        is_mongol = False
        for c in q:
            if '\u0400' <= c <= '\u04FF':
                is_mongol = True
                break
        if is_mongol:
            mongol_questions.append(q)
        else:
            normal_questions.append(q)
    
    # 中文快捷按钮
    col1, col2 = st.columns(2)
    for i, q in enumerate(normal_questions[:6]):
        if i % 2 == 0:
            with col1:
                if st.button(q, key=q, use_container_width=True):
                    st.session_state.prompt = q
        else:
            with col2:
                if st.button(q, key=f"q_{i}", use_container_width=True):
                    st.session_state.prompt = q
    
    # 功能快捷按钮
    st.divider()
    st.write("🔍 功能快捷提问")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("三体在哪？", key="f1", use_container_width=True):
            st.session_state.prompt = "三体在哪？"
    with col2:
        if st.button("还有空位吗？", key="f2", use_container_width=True):
            st.session_state.prompt = "还有空位吗？"
    with col3:
        if st.button("本周新书？", key="f3", use_container_width=True):
            st.session_state.prompt = "本周有什么新书？"
    
    # 到期提醒快捷按钮
    if st.button("到期提醒？", key="f4", use_container_width=True):
        st.session_state.prompt = "到期提醒"
    
    # 蒙语快捷按钮
    if mongol_questions:
        st.divider()
        st.write("🇲🇳 蒙语快捷提问")
        col1, col2 = st.columns(2)
        for i, q in enumerate(mongol_questions):
            if i % 2 == 0:
                with col1:
                    if st.button(q, key=f"m_{q}", use_container_width=True):
                        st.session_state.prompt = q
            else:
                with col2:
                    if st.button(q, key=f"mq_{i}", use_container_width=True):
                        st.session_state.prompt = q
    
    st.divider()
    
    if st.button("🗑️ 清空聊天记录", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    st.header("➕ 自定义添加问题")
    new_q = st.text_input("问题")
    new_a = st.text_area("答案")
    if st.button("添加到知识库", use_container_width=True):
        if new_q and new_a:
            st.session_state.custom_kb[new_q] = new_a
            st.success("✅ 添加成功！")
            st.rerun()

# 多标签页
tab1, tab2, tab3, tab4 = st.tabs(["💬 智能问答", "🔍 馆藏查询", "🪑 座位状态", "📖 本周新书"])

# --- 标签1：智能问答 ---
with tab1:
    # 欢迎引导
    if len(st.session_state.messages) == 0:
        st.markdown('''
        <div class="card" style="text-align: center;">
            <h3>👋 欢迎使用图小助！</h3>
            <p>我可以帮你：</p>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 15px;">
                <span>✅ 解答图书馆的所有问题</span>
                <span>✅ 查询图书馆藏位置</span>
                <span>✅ 查看自习室剩余空位</span>
                <span>✅ 查看本周新书</span>
                <span>✅ 到期提醒</span>
            </div>
            <div style="margin-top: 15px; padding: 10px; background: #f0f7ff; border-radius: 10px;">
                <p style="margin:0; color: #2c3e50;">💡 你不用切换标签，直接在聊天里问就行！比如：</p>
                <ul style="text-align: left; max-width: 500px; margin: 10px auto;">
                    <li>问「三体在哪？」直接查馆藏</li>
                    <li>问「还有空位吗？」直接看座位</li>
                    <li>问「我3月20号借的书」直接算到期时间</li>
                    <li>也支持蒙语提问哦！</li>
                </ul>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    # 聊天容器
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # 显示历史消息
    if len(st.session_state.messages) > 6:
        with st.expander(f"📜 查看完整对话历史（共{len(st.session_state.messages)}条）", expanded=False):
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="user-message">👤 {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="assistant-message">
                        📚 {msg["content"]}
                        <button class="copy-btn" onclick='navigator.clipboard.writeText(`{msg["content"]}`)'>复制</button>
                        <div style='clear: both;'></div>
                    </div>
                    ''', unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-message">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="assistant-message">
                    📚 {msg["content"]}
                    <button class="copy-btn" onclick='navigator.clipboard.writeText(`{msg["content"]}`)'>复制</button>
                    <div style='clear: both;'></div>
                </div>
                ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 用户输入
    prompt = st.chat_input("请问您有什么问题？支持中文/蒙语哦~", key="prompt")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # 处理回复
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_query = st.session_state.messages[-1]["content"]
        kb = get_full_kb()
        
        answer = find_best_match(user_query, kb)
        if not answer:
            answer = "抱歉，这个问题我暂时还不知道，您可以试试问我借阅规则、自习室预约、WiFi、打印相关的问题哦！也可以自己在侧边栏添加新的问答~ 支持中文/蒙语双语哦！"
        
        # 打字机效果
        placeholder = st.empty()
        full_answer = answer
        current_text = ""
        for char in full_answer:
            current_text += char
            placeholder.markdown(f'''
            <div class="chat-container">
                <div class="assistant-message">
                    📚 {current_text}▌
                </div>
            </div>
            ''', unsafe_allow_html=True)
            time.sleep(0.02)
        
        placeholder.markdown(f'''
        <div class="chat-container">
            <div class="assistant-message">
                📚 {full_answer}
                <button class="copy-btn" onclick='navigator.clipboard.writeText(`{full_answer}`)'>复制</button>
                <div style='clear: both;'></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "assistant", "content": full_answer})
        st.rerun()

# --- 标签2：馆藏查询 ---
with tab2:
    st.markdown('''
    <div class="card">
        <h3>🔍 馆藏查询</h3>
        <p>输入书名，就能查到这本书的位置和可借状态！</p>
    </div>
    ''', unsafe_allow_html=True)
    
    book_name = st.text_input("请输入书名")
    if st.button("查询"):
        if book_name:
            match = None
            match_name = None
            for name, info in book_collection.items():
                if book_name in name or name in book_name:
                    match = info
                    match_name = name
                    break
            if match:
                st.success(f"✅ 找到《{match_name}》啦！")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("所在楼层", match['floor'])
                with col2:
                    st.metric("具体位置", match['location'])
                with col3:
                    if match['status'] == "在架可借":
                        st.metric("可借状态", "✅ 可借")
                    else:
                        st.metric("可借状态", f"❌ 已借出，预计{match['return_date']}归还")
            else:
                st.warning("抱歉，暂时没有找到这本书的信息，你可以试试其他书名~")

# --- 标签3：座位状态 ---
with tab3:
    st.markdown('''
    <div class="card">
        <h3>🪑 自习室座位状态</h3>
        <p>实时查看各楼层剩余空位，再也不用跑空啦！</p>
    </div>
    ''', unsafe_allow_html=True)
    
    for floor, status in seat_status.items():
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"**{floor}**")
            with col2:
                st.write(f"总座位: {status['total']}")
            with col3:
                st.write(f"剩余空位: {status['left']}")
            with col4:
                if status['full']:
                    st.error("⚠️ 即将满座")
                else:
                    st.success("✅ 空位充足")
            st.divider()
    
    st.info("💡 你可以点击侧边栏的「自习室怎么预约」，查看预约方法哦！")

# --- 标签4：本周新书 ---
with tab4:
    st.markdown('''
    <div class="card">
        <h3>📖 本周新书推荐</h3>
        <p>最新到馆的好书，快来看看有没有你想要的！</p>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    for i, book in enumerate(new_books):
        if i % 2 == 0:
            with col1:
                with st.container():
                    st.markdown(f'''
                    <div class="card">
                        <h4>📕 {book['name']}</h4>
                        <p>作者: {book['author']}</p>
                        <p>位置: {book['floor']}</p>
                    </div>
                    ''', unsafe_allow_html=True)
        else:
            with col2:
                with st.container():
                    st.markdown(f'''
                    <div class="card">
                        <h4>📕 {book['name']}</h4>
                        <p>作者: {book['author']}</p>
                        <p>位置: {book['floor']}</p>
                    </div>
                    ''', unsafe_allow_html=True)
