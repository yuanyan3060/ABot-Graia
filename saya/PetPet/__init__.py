import httpx

from io import BytesIO
from pathlib import Path
from PIL import ImageOps
from loguru import logger
from PIL import Image as IMG
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.event.mirai import NudgeEvent
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member, MemberPerm
from graia.ariadne.message.element import At, Image, Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.control import Interval, Permission, Rest


saya = Saya.current()
channel = Channel.current()


BASE = Path(__file__).parent.joinpath("temp")
BASE.mkdir(exist_ok=True)
FRAMES_PATH = Path(__file__).parent.joinpath("PetPetFrames")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight({"head": FullMatch("摸"), "arg1": WildcardMatch()})
        ],
        decorators=[Rest.rest_control(), Permission.require(), Interval.require()],
    )
)
async def petpet_generator(message: MessageChain, group: Group):

    if (
        yaml_data["Saya"]["PetPet"]["Disabled"]
        and not yaml_data["Saya"]["PetPet"]["CanAt"]
    ):
        return
    elif "PetPet" in group_data[str(group.id)]["DisabledFunc"]:
        return

    if message.has(At):
        await safeSendGroupMessage(
            group,
            MessageChain.create(
                [Image(data_bytes=await petpet(message.getFirst(At).target))]
            ),
        )


@channel.use(
    ListenerSchema(listening_events=[NudgeEvent], decorators=[Rest.rest_control()])
)
async def get_nudge(app: Ariadne, nudge: NudgeEvent):

    if nudge.group_id:

        if (
            yaml_data["Saya"]["PetPet"]["Disabled"]
            and not yaml_data["Saya"]["PetPet"]["CanNudge"]
        ):
            return
        elif "PetPet" in group_data[str(nudge.group_id)]["DisabledFunc"]:
            return

        Permission.manual(nudge.supplicant)
        await Interval.manual(nudge.group_id, 3)

        if nudge.target == yaml_data["Basic"]["MAH"]["BotQQ"]:
            try:
                await app.sendNudge(
                    Member(
                        id=nudge.supplicant,
                        group=Group(
                            id=nudge.group_id,
                            name="",
                            permission=MemberPerm(MemberPerm.Member),
                        ),
                        memberName="",
                        permission=MemberPerm(MemberPerm.Member),
                    )
                )
            except Exception:
                pass

        else:
            logger.info(
                f"[{nudge.group_id}] 收到戳一戳事件 -> [{nudge.supplicant}] - [{nudge.target}]"
            )

            await safeSendGroupMessage(
                nudge.group_id,
                MessageChain.create(
                    [Plain("收到 "), At(nudge.supplicant), Plain(" 的戳一戳，正在制图")]
                ),
            )

            await safeSendGroupMessage(
                nudge.group_id,
                MessageChain.create([Image(data_bytes=await petpet(nudge.target))]),
            )


frame_spec = [
    (27, 31, 86, 90),
    (22, 36, 91, 90),
    (18, 41, 95, 90),
    (22, 41, 91, 91),
    (27, 28, 86, 91),
]

squish_factor = [
    (0, 0, 0, 0),
    (-7, 22, 8, 0),
    (-8, 30, 9, 6),
    (-3, 21, 5, 9),
    (0, 0, 0, 0),
]

squish_translation_factor = [0, 20, 34, 21, 0]

frames = tuple([FRAMES_PATH.joinpath(f"frame{i}.png") for i in range(5)])


# 生成函数（非数学意味）
async def make_frame(avatar, i, squish=0, flip=False):
    # 读入位置
    spec = list(frame_spec[i])
    # 将位置添加偏移量
    for j, s in enumerate(spec):
        spec[j] = int(s + squish_factor[i][j] * squish)
    # 读取手
    hand = IMG.open(frames[i])
    # 反转
    if flip:
        avatar = ImageOps.mirror(avatar)
    # 将头像放缩成所需大小
    avatar = avatar.resize(
        (int((spec[2] - spec[0]) * 1.2), int((spec[3] - spec[1]) * 1.2)), IMG.ANTIALIAS
    ).quantize()
    # 并贴到空图像上
    gif_frame = IMG.new("RGB", (112, 112), (255, 255, 255))
    gif_frame.paste(avatar, (spec[0], spec[1]))
    # 将手覆盖（包括偏移量）
    gif_frame.paste(hand, (0, int(squish * squish_translation_factor[i])), hand)
    # 返回
    return gif_frame


async def petpet(member_id, flip=False, squish=0) -> None:

    url = f"http://q1.qlogo.cn/g?b=qq&nk={str(member_id)}&s=640"
    gif_frames = []
    async with httpx.AsyncClient() as client:
        resp = await client.get(url=url)

    avatar = IMG.open(BytesIO(resp.content))

    # 生成每一帧
    for i in range(5):
        gif_frames.append(await make_frame(avatar, i, squish=squish, flip=flip))
    # 输出

    image = BytesIO()
    gif_frames[0].save(
        image,
        format="GIF",
        append_images=gif_frames[1:],
        save_all=True,
        duration=60,
        loop=0,
        optimize=False,
    )
    return image.getvalue()
