import sys, random, time
from pathlib import Path
from collections import deque
from PySide6.QtCore import Qt, QPoint, QTimer, QSettings, Signal
from PySide6.QtGui import QPixmap, QColor, QWheelEvent
from PySide6.QtWidgets import (
    QApplication, QLabel, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QGraphicsDropShadowEffect, QSizeGrip
)

ROOT = Path(__file__).resolve().parent
PINK = '#F06E91'; TEXT = '#4B4145'; MUTED = '#B49AA3'; BORDER = '#F2C8D4'; HOVER = '#FFF0F4'


def shadow(w, blur=28, y=7):
    s = QGraphicsDropShadowEffect(w); s.setBlurRadius(blur); s.setOffset(0, y); s.setColor(QColor(120, 70, 85, 55)); w.setGraphicsEffect(s)


def btn(text):
    b = QPushButton(text); b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"QPushButton{{border:0;border-radius:12px;background:transparent;color:{TEXT};font:14px 'Microsoft YaHei UI';padding:8px}}QPushButton:hover{{background:{HOVER}}}")
    return b


# 用户主动从「玩耍」页选择的动作。图片名与 key 一一对应。
ACTION_DATA = [
    ('heart', '抱爱心', '💗', ['抱抱你～♡', '给你一颗小爱心！', '今天也要被爱包围呀～', 'Cherry 的爱心分你一半！']),
    ('happy', '给你点赞', '👍', ['今天表现不错嘛～', 'Cherry 给你点个大大的赞！', '做得很好，继续保持 ♡', '嘿嘿，批准你今天优秀一下！']),
    ('shy', '害羞一下', '😊', ['别一直盯着我看嘛…', '有、有一点不好意思啦', '再看 Cherry 要脸红了！', '才没有害羞呢…哼']),
    ('cry', '委屈巴巴', '🥺', ['Cherry 有一点点难过…', '要哄一下才会好', '呜…抱抱我嘛', '你是不是忘记理我了…']),
    ('dnd', '免打扰', '🤫', ['Cherry 现在不想被打扰～', '让我安静待一会儿嘛', '现在进入安静模式', '只是暂时不营业哦～']),
    ('slack', '摸鱼中', '🐟', ['Cherry 正在偷偷摸鱼～', '先休息一下下再努力', '别说话，我在认真摆烂', '嘘……摸鱼不要被发现！']),

    ('work', '工作中', '🪧', ['Cherry 工作中，请勿打扰～', '今天也要认真一下！', '等我忙完就陪你玩 ♡', '偷偷摸鱼应该不会被发现吧…']),
    ('code', '努力敲代码', '💻', ['Cherry 正在疯狂敲代码！', '这个 bug 到底藏哪了…', '马上就写完啦！', '不许催！越催 bug 越多！']),
    ('sleepy', '写困了', '🥱', ['代码怎么越看越困…', 'Cherry 快没电了 Zzz…', '再写五分钟就睡…', '这个 bug 明天再抓好不好…']),
    ('music', '听歌摇摆', '🎧', ['这首歌好好听～', '和 Cherry 一起听嘛！', '♪ 今天心情不错～', '嘿嘿，Cherry 要开始摇啦！']),
    ('fan', '吹吹小风', '🌬️', ['呼～终于凉快一点啦', 'Cherry 快被热化了！', '风再大一点嘛～', '要不要一起吹风呀？']),
    ('chips', '躺平吃薯片', '🥔', ['今天先摆烂五分钟～', '薯片真的停不下来…', '要不要来一片？', '嘘……吃完这片再努力！']),

    ('pout', '傲娇一下', '😗', ['哼～才没有在等你呢', 'Cherry 今天有一点点傲娇', '看什么看嘛～', '哄一下就不生气啦 ♡']),
    ('luck', '好运给你', '🍀', ['今天的好运分你一半！', '四叶草 buff +1！', '嘿嘿，接住 Cherry 的好运～', '今天一定会有好事发生 ♡']),
    ('rich', '一夜暴富', '💰', ['发财发财发财！', 'Cherry 的小金库装不下啦～', '今天财运 MAX！', '嘿嘿，这下可以买好多好吃的了！']),
    ('tilt', '歪头看你', '🤍', ['你在干嘛呀？', 'Cherry 正在观察你…', '让我看看你在偷偷做什么～', '怎么啦？一直看着 Cherry 干嘛 ♡']),
    ('peek', '探头偷看', '👀', ['偷偷看看你在干嘛…', '发现你啦！', 'Cherry 路过～', '嘿嘿，被我逮到啦 ♡']),
    ('chocolate', '巧克力时间', '🍫', ['再吃一块应该没关系吧？', '被你发现啦！', '巧克力分你一口～', '甜甜的，好幸福 ♡']),

    ('angry', '生气了', '😠', ['哼！Cherry 生气了！', '现在哄我还来得及', '决定三秒钟不理你！', '除非你说 Cherry 最可爱！']),
    ('flowers', '送你花花', '💐', ['这束花送给你 ♡', '今天也要有好心情呀～', '偷偷送你一点浪漫', '不许拒绝，这是 Cherry 挑的！']),
]

# 主菜单直达状态，不强塞到“玩耍”页。
DIRECT_ACTIONS = {
    'vanity': ('臭美', '💎', ['让我看看今天漂不漂亮～', '嗯～今天也很可爱 ♡', '等一下，Cherry 还没照完呢！', '今天也要精致一下～']),
    'rest': ('乖乖睡觉', '🌙', ['Cherry 要睡一小会儿啦～', 'Zzz…有点困了', '再睡五分钟嘛…', '晚安～不许偷偷吵醒我 ♡']),
}

ACTION_INFO = {k: {'name': n, 'icon': i, 'lines': lines} for k, n, i, lines in ACTION_DATA}
ACTION_INFO.update({k: {'name': n, 'icon': i, 'lines': lines} for k, (n, i, lines) in DIRECT_ACTIONS.items()})

HANG_LINES = ['可以把我放下来吗…', 'Cherry 被挂住啦！', '呜…摸鱼被抓包了', '我知道错了嘛…先放我下来啦']

IDLE_LINES = ['Cherry 在这里呀～', '怎么啦？想和 Cherry 说话吗 ♡', '嘿嘿，被你点到啦！', '今天也要开心一点哦～', 'Cherry 正在看着你 👀', '再点一下，我还有话要说～']

SECONDARY = {
    'heart': ['再抱一下嘛 ♡', '嘿嘿，不松手～'],
    'happy': ['再奖励你一个赞！', '今天确实很棒嘛～'],
    'shy': ['都说了不要一直看啦…', 'Cherry 真的要脸红了！'],
    'cry': ['还不哄我嘛…', '抱一下就原谅你 ♡', '再哄一下下就好了…'],
    'chocolate': ['真的最后一块啦…大概', '再吃一口就停！'],
    'dnd': ['嘘～现在是安静时间', '等我缓一会儿再陪你玩嘛'],
    'slack': ['今天先摆烂一下下～', '摸鱼也是一种充电！'],
    'peek': ['嘘～我只是偷偷路过', '你刚刚在做什么呀？'],
    'work': ['正在忙呢～等我一下', '认真工作模式 ON！'],
    'code': ['别催啦！马上就写完了！', '嘘——正在抓 bug！', '刚刚那个 bug 又跑掉了！'],
    'sleepy': ['让我眯一小会…', '眼睛真的睁不开啦 Zzz…'],
    'angry': ['哼，还没哄好呢！', '再哄一下也许就原谅你～'],
    'flowers': ['花花不能退货哦 ♡', '收下嘛～这是专门给你的'],
    'music': ['下一首也一起听！', '♪ Cherry 正在跟着节奏摇～'],
    'pout': ['才、才没有等你呢！', '再哄一下嘛…就一下'],
    'fan': ['呼～舒服多啦', '这个风刚刚好～'],
    'luck': ['好运已经送达！', '今天一定顺顺利利～'],
    'rich': ['分你一枚金币！', '一起暴富呀～'],
    'tilt': ['嗯？怎么不说话啦？', 'Cherry 还在看你哦～'],
    'chips': ['咔嚓咔嚓～', '最后一片！真的！'],
    'vanity': ['别催嘛，我还没照完呢！', '今天这个角度最好看～'],
    'rest': ['唔…谁在戳 Cherry…', '再睡五分钟嘛 Zzz…'],
}

# 10% 左右的“临时彩蛋”：结束后回到用户当前主状态。
TEMP_EXTENSIONS = {
    'heart': [('shy', '被抱得有点害羞啦…')],
    'pout': [('shy', '好啦好啦…其实没有真的生气 ♡')],
    'angry': [('shy', '被你哄得有一点点不好意思…')],
    'vanity': [('shy', '一直夸我会害羞的啦…')],
    'chips': [('sleepy', '吃着吃着怎么有点困了…')],
    'dnd': [('shy', '好啦…偷偷看你一眼 ♡')],
}


class Bubble(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.l = QLabel(self); self.l.setAlignment(Qt.AlignCenter)
        self.l.setStyleSheet(f"background:rgba(255,250,252,248);border:1px solid {BORDER};border-radius:15px;padding:9px 14px;color:{TEXT};font:12px 'Microsoft YaHei UI';")
        shadow(self.l, 18, 4)
        self.t = QTimer(self); self.t.setSingleShot(True); self.t.timeout.connect(self.hide)

    def say(self, text, anchor, ms=2800):
        self.l.setText(text); self.l.adjustSize(); self.resize(self.l.width()+10, self.l.height()+10); self.l.move(5, 5)
        screen=QApplication.screenAt(anchor.center()) or QApplication.primaryScreen(); g=screen.availableGeometry()
        x=anchor.x()+anchor.width()//2-self.width()//2; y=anchor.y()-self.height()+12
        x=max(g.left()+4,min(x,g.right()-self.width()-4))
        if y < g.top()+4: y=g.top()+6
        self.move(x,y); self.show(); self.raise_(); self.t.start(ms)


class CardPopup(QWidget):
    def __init__(self, size):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True); self.resize(*size); self.setMinimumSize(int(size[0]*.82), int(size[1]*.82))
        out = QVBoxLayout(self); out.setContentsMargins(12,12,12,12)
        self.card = QFrame(); self.card.setObjectName('c'); self.card.setStyleSheet(f"QFrame#c{{background:rgba(255,252,253,252);border:1px solid {BORDER};border-radius:20px;}}")
        shadow(self.card); out.addWidget(self.card)
        self.grip = QSizeGrip(self); self.grip.setFixedSize(18,18); self.grip.raise_()

    def resizeEvent(self, e):
        self.grip.move(self.width()-24, self.height()-24)
        super().resizeEvent(e)


class MainMenu(CardPopup):
    def __init__(self, c):
        super().__init__((310,410)); v = QVBoxLayout(self.card); v.setContentsMargins(20,16,20,18)
        h = QHBoxLayout(); t = QLabel('🍒  Cherry'); t.setStyleSheet(f"color:{PINK};font:700 21px 'Microsoft YaHei UI';border:0"); h.addWidget(t); h.addStretch(); h.addWidget(QLabel('♡')); v.addLayout(h)
        s = QLabel('你的桌面小伙伴 ♡'); s.setStyleSheet(f'color:{MUTED};border:0;padding:0 0 8px 38px'); v.addWidget(s)
        items = [
            ('👗','换装', c.show_wardrobe, True),
            ('✨','玩耍', c.show_actions, True),
            ('🌙','休息', lambda: c.select_action('rest'), False),
            ('💎','臭美', lambda: c.select_action('vanity'), False),
            ('ⓘ','关于 Cherry', lambda: c.bubble.say('我是 Cherry 🍒 你的桌面小伙伴 ♡', c.geometry()), False),
        ]
        for ico, name, fn, arrow in items:
            b = btn(f'{ico}    {name}' + ('        ›' if arrow else ''))
            b.clicked.connect(lambda _, f=fn: (self.close(), f())); v.addWidget(b)
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet('background:#F2AFC1;border:0'); v.addWidget(line)
        b = btn('⏻    退出 Cherry'); b.setStyleSheet(b.styleSheet()+f'QPushButton{{color:{PINK}}}'); b.clicked.connect(QApplication.quit); v.addWidget(b)


class ClickCard(QFrame):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent); self.setCursor(Qt.PointingHandCursor); self.setObjectName('tile')
        self.setStyleSheet('QFrame#tile{background:#FFF1F5;border:1px solid #F4D1DB;border-radius:14px}QFrame#tile:hover{background:#FFE8EF;border-color:#F3A9BE}')
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton: self.clicked.emit()
        super().mouseReleaseEvent(e)


class Actions(CardPopup):
    def __init__(self, c):
        super().__init__((620,520)); self.setMinimumSize(520,450); self.c = c; self.page = 0; self.pages = (len(ACTION_DATA)+5)//6
        v = QVBoxLayout(self.card); v.setContentsMargins(22,18,22,18); v.setSpacing(10)
        h = QHBoxLayout(); t = QLabel('♥  和 Cherry 玩'); t.setStyleSheet(f"color:{PINK};font:700 20px 'Microsoft YaHei UI';border:0")
        x = QPushButton('×'); x.setFixedSize(34,34); x.setStyleSheet(f'border:0;color:{PINK};font-size:24px'); x.clicked.connect(self.close)
        h.addWidget(t); h.addStretch(); h.addWidget(x); v.addLayout(h)
        s = QLabel('今天想让 Cherry 做什么？'); s.setStyleSheet(f"color:{MUTED};font:13px 'Microsoft YaHei UI';border:0;padding-left:38px"); v.addWidget(s)
        self.grid = QGridLayout(); self.grid.setHorizontalSpacing(12); self.grid.setVerticalSpacing(12); self.grid.setContentsMargins(0,4,0,4); v.addLayout(self.grid,1)
        for col in range(3): self.grid.setColumnStretch(col,1)
        for row in range(2): self.grid.setRowStretch(row,1)
        foot = QHBoxLayout(); self.l = QPushButton('‹'); self.r = QPushButton('›'); self.mid = QLabel(); self.mid.setAlignment(Qt.AlignCenter)
        for q in (self.l,self.r):
            q.setFixedSize(44,44); q.setCursor(Qt.PointingHandCursor); q.setStyleSheet('QPushButton{background:#F7B3C7;color:white;border:0;border-radius:22px;font-size:28px}QPushButton:hover{background:#F39BB6}')
        self.l.clicked.connect(lambda: self.turn(-1)); self.r.clicked.connect(lambda: self.turn(1)); self.mid.setStyleSheet(f"color:{TEXT};font:14px 'Microsoft YaHei UI';border:0")
        foot.addWidget(self.l); foot.addStretch(); foot.addWidget(self.mid); foot.addStretch(); foot.addWidget(self.r); v.addLayout(foot); self.refresh()

    def clear(self):
        while self.grid.count():
            it = self.grid.takeAt(0); w = it.widget()
            if w: w.deleteLater()

    def refresh(self):
        self.clear(); chunk = ACTION_DATA[self.page*6:self.page*6+6]
        for i, (key, name, ico, _) in enumerate(chunk):
            card = ClickCard(); card.setMinimumSize(145,145); lay = QVBoxLayout(card); lay.setContentsMargins(8,8,8,8); lay.setSpacing(4)
            pic = QLabel(); pic.setAlignment(Qt.AlignCenter); pic.setStyleSheet('border:0;background:transparent'); pic.setMinimumHeight(100)
            p = self.c.action_pixmap(key); pic.setPixmap(p.scaled(125,105,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            lab = QLabel(f'{ico}  {name}'); lab.setAlignment(Qt.AlignCenter); lab.setStyleSheet(f"color:{TEXT};font:13px 'Microsoft YaHei UI';border:0;background:transparent")
            lay.addWidget(pic,1); lay.addWidget(lab,0); card.clicked.connect(lambda k=key: (self.close(), self.c.select_action(k))); self.grid.addWidget(card,i//3,i%3)
        self.mid.setText(f'♥      {self.page+1} / {self.pages}      ♥')

    def turn(self, d): self.page = (self.page+d) % self.pages; self.refresh()


class Wardrobe(CardPopup):
    O = [('default','默认造型'),('pink','粉色造型'),('beret','蓝莓贝雷帽'),('sailor_pink','粉色水手服'),('cream_plaid','奶油格纹'),('navy_school','海军学院'),('angel','爱心天使')]
    def __init__(self, c):
        super().__init__((560,440)); self.setMinimumSize(500,400); self.c = c; self.page = 0; self.pages = (len(self.O)+1)//2
        v = QVBoxLayout(self.card); v.setContentsMargins(22,18,22,18); v.setSpacing(10)
        h = QHBoxLayout(); t = QLabel('🌸  Cherry 衣橱'); t.setStyleSheet(f"color:{PINK};font:700 20px 'Microsoft YaHei UI';border:0")
        x = QPushButton('×'); x.setFixedSize(34,34); x.clicked.connect(self.close); x.setStyleSheet(f'border:0;color:{PINK};font-size:24px'); h.addWidget(t); h.addStretch(); h.addWidget(x); v.addLayout(h)
        s = QLabel('选择你喜欢的造型 ♡'); s.setStyleSheet(f"color:{MUTED};font:13px 'Microsoft YaHei UI';border:0;padding-left:38px"); v.addWidget(s)
        self.cards = QHBoxLayout(); self.cards.setSpacing(14); self.cards.setContentsMargins(0,5,0,5); v.addLayout(self.cards,1)
        f = QHBoxLayout(); self.l = QPushButton('‹'); self.r = QPushButton('›'); self.mid = QLabel(); self.mid.setAlignment(Qt.AlignCenter)
        for q in (self.l,self.r): q.setFixedSize(44,44); q.setStyleSheet('QPushButton{background:#F7B3C7;color:white;border:0;border-radius:22px;font-size:28px}QPushButton:hover{background:#F39BB6}')
        self.l.clicked.connect(lambda: self.turn(-1)); self.r.clicked.connect(lambda: self.turn(1)); self.mid.setStyleSheet(f"color:{TEXT};font:14px 'Microsoft YaHei UI';border:0")
        f.addWidget(self.l); f.addStretch(); f.addWidget(self.mid); f.addStretch(); f.addWidget(self.r); v.addLayout(f); self.refresh()

    def clear(self):
        while self.cards.count():
            it = self.cards.takeAt(0); w = it.widget()
            if w: w.deleteLater()

    def refresh(self):
        self.clear(); items = self.O[self.page*2:self.page*2+2]
        for key, name in items:
            card = ClickCard(); card.setMinimumSize(210,235); l = QVBoxLayout(card); l.setContentsMargins(10,10,10,10); l.setSpacing(6)
            p = QLabel(); p.setAlignment(Qt.AlignCenter); p.setStyleSheet('border:0;background:transparent'); p.setMinimumHeight(180)
            pm = QPixmap(str(ROOT/'assets'/key/'idle.png')); p.setPixmap(pm.scaled(190,175,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            n = QLabel(name); n.setAlignment(Qt.AlignCenter); n.setStyleSheet(f"border:0;color:{TEXT};font:13px 'Microsoft YaHei UI';background:transparent")
            l.addWidget(p,1); l.addWidget(n,0); card.clicked.connect(lambda k=key,nm=name: (self.c.load_outfit(k), self.close(), self.c.bubble.say(f'换好啦～{nm} ♡', self.c.geometry()))); self.cards.addWidget(card,1)
        if len(items) == 1:
            spacer = QWidget(); spacer.setMinimumSize(210,235); self.cards.addWidget(spacer,1)
        self.mid.setText(f'♥      {self.page+1} / {self.pages}      ♥')

    def turn(self,d): self.page = (self.page+d) % self.pages; self.refresh()


class Cherry(QLabel):
    def __init__(self):
        super().__init__(); self.settings = QSettings('CherryPet','Cherry')
        self.outfit = self.settings.value('outfit','default'); self.pet_size = max(180,min(520,int(self.settings.value('size',300))))
        self.drag = QPoint(); self.dragging = False
        self.main_action = self.settings.value('current_action', None); self.display_action = self.main_action
        self.click_times = deque(maxlen=8); self.extension_token = 0
        self.hanging = False; self.hanging_clicks = 0; self.hang_return_pos = None
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool); self.setAttribute(Qt.WA_TranslucentBackground,True); self.setAlignment(Qt.AlignCenter); self.setCursor(Qt.OpenHandCursor)
        self.bubble = Bubble(); self.resize_pet(self.pet_size)
        if self.main_action in ACTION_INFO and not self.action_pixmap(self.main_action).isNull(): self.set_pm(self.action_pixmap(self.main_action))
        else: self.main_action = None; self.display_action = None; self.load_outfit(self.outfit)
        g = QApplication.primaryScreen().availableGeometry(); saved = self.settings.value('pos'); self.move(saved if isinstance(saved,QPoint) else QPoint(g.right()-330,g.bottom()-322))
        self.chain_timer = QTimer(self); self.chain_timer.setSingleShot(True); self.chain_timer.timeout.connect(self.chain_action)
        self.hang_timer = QTimer(self); self.hang_timer.setSingleShot(True); self.hang_timer.timeout.connect(self.exit_hanging)
        self.schedule_chain()

    def resize_pet(self,n): self.pet_size=max(180,min(520,n)); self.setFixedSize(self.pet_size,self.pet_size); self.settings.setValue('size',self.pet_size)
    def set_pm(self,pm):
        if not pm.isNull(): self.setPixmap(pm.scaled(int(self.pet_size*.95),int(self.pet_size*.95),Qt.KeepAspectRatio,Qt.SmoothTransformation))
    def load_outfit(self,k):
        if self.hanging: self.exit_hanging()
        p = ROOT/'assets'/k/'idle.png'
        if not p.exists(): k='default'; p=ROOT/'assets/default/idle.png'
        self.outfit=k; self.settings.setValue('outfit',k); self.main_action=None; self.display_action=None; self.settings.remove('current_action')
        if hasattr(self,'chain_timer'): self.chain_timer.stop()
        self.extension_token += 1; self.set_pm(QPixmap(str(p)))
    def action_pixmap(self,k): return QPixmap(str(ROOT/'assets'/'actions'/f'{k}.png'))

    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:
            if self.hanging:
                self.dragging=False
                return
            self.drag=e.globalPosition().toPoint()-self.frameGeometry().topLeft(); self.dragging=False; self.setCursor(Qt.ClosedHandCursor)
        elif e.button()==Qt.RightButton: self.show_menu(e.globalPosition().toPoint())
    def mouseMoveEvent(self,e):
        if self.hanging: return
        if e.buttons() & Qt.LeftButton: self.dragging=True; self.move(e.globalPosition().toPoint()-self.drag)
    def mouseReleaseEvent(self,e):
        if e.button()==Qt.LeftButton:
            if self.hanging:
                self.react_hanging(); return
            self.setCursor(Qt.OpenHandCursor); self.settings.setValue('pos',self.pos())
            if not self.dragging:
                if self.main_action: self.react_again()
                else: self.bubble.say(random.choice(IDLE_LINES),self.geometry(),2500)
    def wheelEvent(self,e:QWheelEvent):
        old=self.pet_size; center=self.geometry().center(); self.resize_pet(old+(20 if e.angleDelta().y()>0 else -20)); self.move(center.x()-self.width()//2,center.y()-self.height()//2)
        pm = self.action_pixmap(self.display_action) if self.display_action else QPixmap(str(ROOT/'assets'/self.outfit/'idle.png')); self.set_pm(pm)
        if self.hanging:
            screen=QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen(); g=screen.geometry()
            x=max(g.left(), min(self.x(), g.right()-self.width()+1)); self.move(x,g.top()-2)
        self.bubble.say(f'Cherry 大小：{round(self.pet_size/300*100)}%',self.geometry(),1200)

    def pos_popup(self,p,at=None):
        g=QApplication.primaryScreen().availableGeometry(); x=(at.x()+8 if at else self.x()-p.width()+55); y=(at.y()+8 if at else self.y()+20)
        return QPoint(max(g.left()+5,min(x,g.right()-p.width()-5)),max(g.top()+5,min(y,g.bottom()-p.height()-5)))
    def show_menu(self,at=None): self.menu=MainMenu(self); self.menu.move(self.pos_popup(self.menu,at)); self.menu.show()
    def show_actions(self): self.actions=Actions(self); self.actions.move(self.pos_popup(self.actions)); self.actions.show()
    def show_wardrobe(self): self.ward=Wardrobe(self); self.ward.move(self.pos_popup(self.ward)); self.ward.show()

    def select_action(self,k, announce=True):
        if self.hanging: self.exit_hanging()
        if k not in ACTION_INFO or self.action_pixmap(k).isNull(): return
        self.extension_token += 1; self.main_action=k; self.display_action=k; self.settings.setValue('current_action',k); self.set_pm(self.action_pixmap(k))
        if announce: self.bubble.say(random.choice(ACTION_INFO[k]['lines']),self.geometry(),3000)
        self.schedule_chain()

    def react_again(self):
        now=time.monotonic(); self.click_times.append(now)
        # “摸鱼中”连续快速点 5 次：必触发屏幕顶部隐藏彩蛋。
        if len(self.click_times)>=5 and self.click_times[-1]-self.click_times[-5] <= 2.6 and self.main_action=='slack':
            self.click_times.clear(); self.bubble.say('啊！摸鱼被抓包了！',self.geometry(),1800)
            QTimer.singleShot(500, self.enter_hanging)
            return
        # 其它状态快速连点 5 次：隐藏回应，不改变主状态。
        if len(self.click_times)>=5 and self.click_times[-1]-self.click_times[-5] <= 2.6:
            self.click_times.clear(); self.bubble.say(random.choice(['你干嘛一直戳我呀！','痒痒痒——不要一直点啦！','Cherry 被你戳晕啦～']),self.geometry(),2600)
            if self.main_action not in ('rest','sleepy') and not self.action_pixmap('angry').isNull(): self.temporary_extension('angry',None,1800)
            return
        # 摸鱼时还有极低概率直接被“抓包”。
        if self.main_action=='slack' and random.random()<.08:
            self.bubble.say('等等……是不是有人来了？！',self.geometry(),1700)
            QTimer.singleShot(450, self.enter_hanging)
            return
        r=random.random(); pool=SECONDARY.get(self.main_action,[])
        if r < .70:
            self.bubble.say(random.choice(ACTION_INFO[self.main_action]['lines']),self.geometry(),2500)
        elif r < .90 or self.main_action not in TEMP_EXTENSIONS:
            self.bubble.say(random.choice(pool or ACTION_INFO[self.main_action]['lines']),self.geometry(),2500)
        else:
            ext,line=random.choice(TEMP_EXTENSIONS[self.main_action]); self.temporary_extension(ext,line,2300)

    def enter_hanging(self):
        if self.hanging or self.action_pixmap('hang').isNull(): return
        self.hanging=True; self.hanging_clicks=0; self.hang_return_pos=QPoint(self.pos())
        self.extension_token += 1; self.display_action='hang'; self.set_pm(self.action_pixmap('hang'))
        screen=QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        g=screen.geometry(); x=max(g.left(), min(self.x(), g.right()-self.width()+1))
        self.move(x, g.top()-4); self.raise_(); self.setCursor(Qt.PointingHandCursor)
        self.bubble.say(random.choice(HANG_LINES),self.geometry(),2800)
        self.hang_timer.start(random.randint(9000,14000))

    def react_hanging(self):
        self.hanging_clicks += 1
        if self.hanging_clicks >= 3:
            self.bubble.say('好啦好啦，放我下来嘛！',self.geometry(),1600)
            QTimer.singleShot(800, self.exit_hanging)
        else:
            self.bubble.say(random.choice(HANG_LINES),self.geometry(),2200)

    def exit_hanging(self):
        if not self.hanging: return
        self.hang_timer.stop(); self.hanging=False; self.hanging_clicks=0; self.setCursor(Qt.OpenHandCursor)
        if self.hang_return_pos is not None: self.move(self.hang_return_pos)
        self.hang_return_pos=None
        if self.main_action and not self.action_pixmap(self.main_action).isNull():
            self.display_action=self.main_action; self.set_pm(self.action_pixmap(self.main_action))
        else:
            self.display_action=None; self.set_pm(QPixmap(str(ROOT/'assets'/self.outfit/'idle.png')))
        self.settings.setValue('pos',self.pos())
        self.schedule_chain()

    def temporary_extension(self,k,line=None,duration=2300):
        if self.action_pixmap(k).isNull(): return
        self.extension_token += 1; token=self.extension_token; self.display_action=k; self.set_pm(self.action_pixmap(k))
        if line: self.bubble.say(line,self.geometry(),duration)
        QTimer.singleShot(duration, lambda: self.return_to_main(token))

    def return_to_main(self,token):
        if token != self.extension_token: return
        if self.main_action and not self.action_pixmap(self.main_action).isNull():
            self.display_action=self.main_action; self.set_pm(self.action_pixmap(self.main_action))

    def schedule_chain(self):
        if not hasattr(self,'chain_timer'): return
        self.chain_timer.stop()
        # 有明确逻辑的“状态链”才会自动推进；其它动作只触发临时彩蛋。
        if self.main_action=='code': self.chain_timer.start(random.randint(35000,65000))
        elif self.main_action=='sleepy': self.chain_timer.start(random.randint(35000,65000))
        elif self.main_action=='chips': self.chain_timer.start(random.randint(50000,90000))
        elif self.main_action=='slack': self.chain_timer.start(random.randint(45000,80000))

    def chain_action(self):
        if self.main_action=='code' and random.random()<.62:
            self.select_action('sleepy',False); self.bubble.say('代码看着看着……真的好困 Zzz…',self.geometry(),3200)
        elif self.main_action=='sleepy' and random.random()<.48:
            self.select_action('rest',False); self.bubble.say('Cherry 先睡一小会儿啦…',self.geometry(),3200)
        elif self.main_action=='chips' and random.random()<.35:
            self.temporary_extension('sleepy','薯片吃着吃着有点困了…',3000); self.schedule_chain()
        elif self.main_action=='slack' and random.random()<.30:
            self.enter_hanging()
        else: self.schedule_chain()

    def closeEvent(self,e):
        if self.hanging and self.hang_return_pos is not None: self.settings.setValue('pos',self.hang_return_pos)
        else: self.settings.setValue('pos',self.pos())
        self.settings.setValue('size',self.pet_size)
        if self.main_action: self.settings.setValue('current_action',self.main_action)
        super().closeEvent(e)


if __name__=='__main__':
    app=QApplication(sys.argv); app.setApplicationName('Cherry'); app.setStyle('Fusion'); c=Cherry(); c.show(); sys.exit(app.exec())
