import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple
import m3u8
from m3u8.model import M3U8

from .config import Config
from .channel_group import ChannelGroup
from .connect_checker import ConnectChecker


@dataclass
class ChannelInfo:
    group: str
    name: str
    uri: str


class Main:
    FORMATED_SUFFIX = "_formated"
    locals = ("北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "内蒙", "广西", "西藏", "宁夏", "新疆", "东南", "东方")

    hkmotw = ("凤凰", "香港", "TVB", "tvb", "‌ViuTV", "翡翠", "明珠", "星河", "星空", "无线", "无线电视", "无线新闻", "无线娱乐","大爱", "亚洲", "华视", "中天", "中视", "民视", "东森", "三立", "台视", "公视", "台湾","澳门", "澳视", "澳亚", "澳广")
    wei_shi = ("卫视",)  # 修正为元组
    citys = ("石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水",
"太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁",
"呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布",
"沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛",
"长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延边朝鲜族自治州",
"哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭地区",
"南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁",
"杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水",
"合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城",
"福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德",
"南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶",
"济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽",
"郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店",
"武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施土家族苗族自治州",
"长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西土家族苗族自治州",
"广州", "韶关", "深圳", "珠海", "汕头", "佛山", "江门", "湛江", "茂名", "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮",
"南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左",
"海口", "三亚", "三沙", "儋州",
"重庆",
"成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝藏族羌族自治州", "甘孜藏族自治州", "凉山彝族自治州",
"贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔东南苗族侗族自治州", "黔南布依族苗族自治州", "黔西南布依族苗族自治州",
"昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄彝族自治州", "红河哈尼族彝族自治州", "文山壮族苗族自治州", "西双版纳傣族自治州", "大理白族自治州", "德宏傣族景颇族自治州", "怒江傈僳族自治州", "迪庆藏族自治州",
"拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里地区",
"西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛",
"兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南", "临夏回族自治州", "甘南藏族自治州",
"西宁", "海东", "海北藏族自治州", "黄南藏族自治州", "海南藏族自治州", "果洛藏族自治州", "玉树藏族自治州", "海西蒙古族藏族自治州",
"银川", "石嘴山", "吴忠", "固原", "中卫",
"乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉回族自治州", "博尔塔拉蒙古自治州", "巴音郭楞蒙古自治州", "阿克苏地区", "克孜勒苏柯尔克孜自治州", "喀什地区", "和田地区", "伊犁哈萨克自治州", "塔城地区", "阿勒泰地区")


    def __init__(self) -> None:
        self.checkConnect: bool = False  # 是否检查连接有效性
        self.doOrder: bool = False  # 是否进行排序
        self.print: bool = True  # 是否输出控制台信息

    def __isM3uFile(self, fileName: str) -> bool:
        if fileName.endswith(".m3u") or fileName.endswith(".m3u8"):
            return True
        else:
            return False

    def __isOriginalM3uFile(self, fileName: str) -> bool:
        if not self.__isM3uFile(fileName):
            return False
        baseName, _, suffixName = fileName.rpartition('.')
        if baseName.endswith(Main.FORMATED_SUFFIX):
            return False
        return True

    def __getFormatedFileName(self, fileName: str) -> bool:
        """获取格式化的m3u文件名"""
        baseName, _, suffixName = fileName.rpartition('.')
        return baseName+Main.FORMATED_SUFFIX+"."+suffixName

    def __getFormatedFilePath(self, fileName: str) -> bool:
        """获取格式化的m3u文件路径"""
        formatedFileName = self.__getFormatedFileName(fileName)
        sysConfig = Config.getInstance()
        formatedFilePath = sysConfig.getCurrentUserWorkDirPath()+sysConfig.getDirSep() + \
            formatedFileName
        return formatedFilePath

    def __isFormatedFileExist(self, fileName: str) -> bool:
        """是否存在原始m3u文件的格式化文件"""
        if not self.__isOriginalM3uFile(fileName):
            return False
        formatedFilePath = self.__getFormatedFilePath(fileName)
        return os.path.exists(formatedFilePath)

    def __groupChannel(self, channelName: str, uri: str, channelGroups: Dict[ChannelGroup, List]) -> None:
        """对频道进行分组，优先级依次为央视频道、卫视频道、省级频道、港澳台频道、市级频道、其它频道"""
        name = channelName or ""
        if "cctv" in name.lower():
            channelGroups[ChannelGroup.CCTV].append((channelName, uri))
            return
        if any(key in name for key in self.__class__.wei_shi):
            channelGroups[ChannelGroup.WEI_SHI].append((channelName, uri))
            return
        if any(key in name for key in self.__class__.locals):
            channelGroups[ChannelGroup.LOCAL].append((channelName, uri))
            return
        if any(key in name for key in self.__class__.hkmotw):
            channelGroups[ChannelGroup.HKMOTW].append((channelName, uri))
            return
        if any(key in name for key in self.__class__.citys):
            channelGroups[ChannelGroup.CITY].append((channelName, uri))
            return
        channelGroups[ChannelGroup.OTHER].append((channelName, uri))

    def __formatGroupedChannels(self, channelGroups: Dict[ChannelGroup, List], destinyPath: str) -> None:
        """将分组好的频道格式化为m3u文件，按指定顺序输出"""
        if self.doOrder:
            self.__consolePrint("对频道进行排序")
            for channels in channelGroups.values():
                channels.sort(key=lambda x: x[0])
        checkResults = None
        if self.checkConnect:
            uris = [uri for channels in channelGroups.values() for _, uri in channels]
            self.__consolePrint("开始检查链接的有效性")
            checkResults = ConnectChecker.checkURIs(uris)
        self.__consolePrint(f"生成格式化后的m3u文件{destinyPath}")
        group_order = [
            ChannelGroup.CCTV,
            ChannelGroup.WEI_SHI,
            ChannelGroup.LOCAL,
            ChannelGroup.HKMOTW,
            ChannelGroup.CITY,
            ChannelGroup.OTHER
        ]
        with open(file=destinyPath, encoding="UTF-8", mode="w") as fopen:
            print("#EXTM3U", file=fopen)
            for group in group_order:
                for channelName, uri in channelGroups.get(group, []):
                    if (not self.checkConnect) or (checkResults and checkResults.get(uri, True)):
                        print(f"#EXTINF:-1 group-title=\"{group.getName()}\",{channelName}", file=fopen)
                        print(uri, file=fopen)
        self.__consolePrint("格式化m3u文件已生成")
        self.__consolePrint("="*20)

    def __groupChannelsByM3u8Obj(self, channels: list, channelGroups: Dict[ChannelGroup, List]) -> None:
        """对频道信息列表进行分组"""
        for channel in channels:
            self.__groupChannel(channel.name, channel.uri, channelGroups)

    def __formatM3uFile(self, filePath: str) -> None:
        """格式化m3u文件"""
        self.__consolePrint("开始格式化{}".format(filePath))
        channels = self.__getChannelsFromM3uFile(filePath)
        channelGroups = {
            ChannelGroup.CCTV: [],
            ChannelGroup.LOCAL: [],
            ChannelGroup.HKMOTW: [],
            ChannelGroup.WEI_SHI: [],
            ChannelGroup.CITY: [],
            ChannelGroup.OTHER: [],
        }
        self.__groupChannelsByM3u8Obj(channels, channelGroups)
        fileName = os.path.basename(filePath)
        formatedFilePath = self.__getFormatedFilePath(fileName)
        self.__formatGroupedChannels(channelGroups, formatedFilePath)

    def __getChannelsFromM3uFile(self, filePath: str) -> list:
        """自定义解析m3u文件，支持group-title及tvg等属性，返回ChannelInfo列表"""
        channels = []
        group = None
        name = None
        with open(file=filePath, encoding="UTF-8", mode="r") as fopen:
            lines = [line.strip() for line in fopen if line.strip()]
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('#EXTINF'):
                # 解析 group-title 和频道名，兼容多属性
                m = re.match(r'#EXTINF:-?1\s+([^,]*),(.+)', line)
                if m:
                    attrs = m.group(1)
                    name = m.group(2).strip()
                    # 提取 group-title 属性
                    group_match = re.search(r'group-title="([^"]*)"', attrs)
                    group = group_match.group(1) if group_match else ''
                else:
                    group = ''
                    name = line.split(',', 1)[-1].strip()
                # 下一个非注释行为uri
                j = i + 1
                while j < len(lines) and lines[j].startswith('#'):
                    j += 1
                if j < len(lines):
                    uri = lines[j]
                    channels.append(ChannelInfo(group, name, uri))
                    i = j
            i += 1
        return channels

    def __mergeAndFormatM3U8Objs(self, channelsList: Tuple[list], distinyPath: str) -> None:
        """对给定的多个频道列表进行合并并且格式化后保存到目标路径"""
        channelGroups = {
            ChannelGroup.CCTV: [],
            ChannelGroup.LOCAL: [],
            ChannelGroup.HKMOTW: [],
            ChannelGroup.WEI_SHI: [],
            ChannelGroup.CITY: [],
            ChannelGroup.OTHER: [],
        }
        print("对多个m3u文件内容进行合并")
        for channels in channelsList:
            self.__groupChannelsByM3u8Obj(channels, channelGroups)
        self.__formatGroupedChannels(channelGroups, distinyPath)

    def __consolePrint(self, msg: str) -> None:
        if self.print:
            print(msg)

    def main(self):
        """获取用户工作目录下的所有m3u和m3u8文件，并进行格式化"""
        self.__consolePrint("="*20)
        for dir in os.listdir():
            if os.path.isfile(dir):
                fileName = os.path.basename(dir)
                if self.__isOriginalM3uFile(fileName) and (not self.__isFormatedFileExist(fileName)):
                    sysConfig = Config.getInstance()
                    filePath = sysConfig.getCurrentUserWorkDirPath()+sysConfig.getDirSep()+fileName
                    self.__formatM3uFile(filePath)

    def allInOne(self):
        """扫描工作目录下的所有m3u和m3u8文件，汇总后创建all_in_one_formated.m3u"""
        channelsList = []
        self.__consolePrint("="*20)
        self.__consolePrint("读取工作目录下的m3u文件")
        for dir in os.listdir():
            if os.path.isfile(dir):
                fileName: str = os.path.basename(dir)
                if self.__isOriginalM3uFile(fileName):
                    sysConfig = Config.getInstance()
                    filePath = sysConfig.getCurrentUserWorkDirPath()+sysConfig.getDirSep()+fileName
                    channelsList.append(self.__getChannelsFromM3uFile(filePath))
        if channelsList:
            distinyPath = sysConfig.getCurrentUserWorkDirPath()+sysConfig.getDirSep() + \
                "all_in_one_formated.m3u"
            self.__mergeAndFormatM3U8Objs(channelsList, distinyPath)

    def showHelpInfo(self):
        helpFilePath = Config.getInstance().getHelpFilePath()
        with open(file=helpFilePath, encoding="UTF-8", mode="r") as fopen:
            for line in fopen:
                print(line, end="")
