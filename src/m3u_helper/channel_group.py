import enum
class ChannelGroup(enum.Enum):
    CCTV = 1
    LOCAL = 2 #省级频道
    HKMOTW = 3 #港澳台频道
    WEI_SHI = 7 #卫视频道
    CITY = 8 #市级频道
    OTHER = 6
    def getName(self):
        if self is ChannelGroup.CCTV:
            return "央视频道"
        elif self is ChannelGroup.LOCAL:
            return "省级频道"
        elif self is ChannelGroup.HKMOTW:
            return "港澳台频道"
        elif self is ChannelGroup.WEI_SHI:
            return "卫视频道"
        elif self is ChannelGroup.CITY:
            return "市级频道"
        elif self is ChannelGroup.OTHER:
            return "其它频道"
        else:
            return ""
