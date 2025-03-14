from pathlib import Path
from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.control import Interval, Permission
from util.sendMessage import safeSendGroupMessage


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

HOME = Path(__file__).parent


@channel.use(
    ListenerSchema(listening_events=[GroupMessage], decorators=[Permission.require()])
)
async def az(group: Group, message: MessageChain):

    if (
        yaml_data["Saya"]["Message"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Message" in group_data[str(group.id)]["DisabledFunc"]:
        return

    saying = message.asDisplay()
    if saying == "草":
        await Interval.manual(5)
        await safeSendGroupMessage(group, MessageChain.create([Plain("一种植物（")]))
    if saying == "好耶":
        await Interval.manual(5)
        await safeSendGroupMessage(
            group, MessageChain.create([Image(path=HOME.joinpath("haoye.png"))])
        )
    if saying == "流汗黄豆.jpg":
        await Interval.manual(5)
        await safeSendGroupMessage(
            group, MessageChain.create([Image(path=HOME.joinpath("jpg"))])
        )
