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
    locals = ("上海", "青海", "陕西", "贵州", "西藏", "河南", "河北", "新疆", "广西", "山西", "宁夏", "吉林", "厦门", "内蒙古", "云南", "兰州", "甘肃",
              "黑龙江", "重庆", "辽宁", "湖南", "湖北", "深圳", "海南", "浙江", "江西", "江苏", "广东", "山东", "安徽", "天津", "四川", "北京", "东南", "东方")
    hk = ("凤凰", "香港", "TVB", "tvb", "星空")
    taiwan = ("大爱", "亚洲")
    aomen = ("澳门", "澳视", "澳亚")

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
        """对频道进行分组"""
        if channelName.find("cctv") != -1 or channelName.find("CCTV") != -1:
            channelGroups[ChannelGroup.CCTV].append((channelName, uri))
        elif any((channelName.find(localChannel) != -1 for localChannel in self.__class__.locals)):
            channelGroups[ChannelGroup.LOCAL].append((channelName, uri))
        elif any((channelName.find(hkChannel) != -1 for hkChannel in self.__class__.hk)):
            channelGroups[ChannelGroup.HK].append((channelName, uri))
        elif any((channelName.find(aomenChannel) != -1 for aomenChannel in self.__class__.aomen)):
            channelGroups[ChannelGroup.AM].append((channelName, uri))
        elif any((channelName.find(taiwanChannel) != -1 for taiwanChannel in self.__class__.taiwan)):
            channelGroups[ChannelGroup.TAI_WAN].append((channelName, uri))
        else:
            channelGroups[ChannelGroup.OTHER].append((channelName, uri))

    def __formatGroupedChannels(self, channelGroups: Dict[ChannelGroup, List], destinyPath: str) -> None:
        """将分组好的频道格式化为m3u文件
        channelGroups: 分组好的频道信息
        destinyPath: 存储的目标m3u文件路径
        """
        channels: list
        if self.doOrder:
            self.__consolePrint("对频道进行排序")
            for channelGroup, channels in channelGroups.items():
                channels.sort(key=lambda x: x[0])
        if self.checkConnect:
            uris = []
            for channelGroup, channels in channelGroups.items():
                for channelName, uri in channels:
                    uris.append(uri)
            self.__consolePrint("开始检查链接的有效性")
            checkResults = ConnectChecker.checkURIs(uris)
        self.__consolePrint("生成格式化后的m3u文件{}".format(destinyPath))
        with open(file=destinyPath, encoding="UTF-8", mode="w") as fopen:
            print("#EXTM3U", file=fopen)
            channelGroup: ChannelGroup
            channels: list
            for channelGroup, channels in channelGroups.items():
                for channelName, uri in channels:
                    if (not self.checkConnect) or checkResults[uri]:
                        print("#EXTINF:-1 group-title=\"{}\",{}".format(
                            channelGroup.getName(), channelName), file=fopen)
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
            ChannelGroup.HK: [],
            ChannelGroup.AM: [],
            ChannelGroup.TAI_WAN: [],
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
            ChannelGroup.HK: [],
            ChannelGroup.AM: [],
            ChannelGroup.TAI_WAN: [],
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
