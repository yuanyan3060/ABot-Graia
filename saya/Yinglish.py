import random

import jieba
import jieba.posseg as pseg

from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.message.element import Source
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest

jieba.setLogLevel(20)

saya = Saya.current()
channel = Channel.current()


def _词转换(x, y, 淫乱度):
    if random.random() > 淫乱度:
        return x
    if x in {"，", "。"}:
        return "……"
    if x in {"!", "！"}:
        return "❤"
    if len(x) > 1 and random.random() < 0.5:
        return f"{x[0]}……{x}"
    else:
        if y == "n" and random.random() < 0.5:
            x = "〇" * len(x)
        return f"……{x}"


def chs2yin(s, 淫乱度=0.5):
    return "".join([_词转换(x, y, 淫乱度) for x, y in pseg.cut(s)])


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight({"head": FullMatch("淫语"), "anythings": WildcardMatch()})
        ],
        decorators=[Rest.rest_control(), Permission.require(), Interval.require()],
    )
)
async def main(group: Group, anythings: WildcardMatch, source: Source):

    if (
        yaml_data["Saya"]["Yinglish"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Yinglish" in group_data[str(group.id)]["DisabledFunc"]:
        return

    if anythings.matched:
        saying = anythings.result.asDisplay()
        if len(saying) < 200:
            await safeSendGroupMessage(
                group, MessageChain.create(chs2yin(saying)), quote=source.id
            )
        else:
            await safeSendGroupMessage(group, MessageChain.create("文字过长"))
    else:
        await safeSendGroupMessage(group, MessageChain.create("未输入文字"))
