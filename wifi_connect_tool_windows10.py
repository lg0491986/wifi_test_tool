# coding=gbk
import datetime
import time
import random
import ctypes, sys, os
import traceback
from string import Template
import psutil
import pywifi
from pywifi import const
import re

connect_status = {
    0: 'DISCONNECTED',
    1: 'SCANNING',
    2: 'INACTIVE',
    3: 'CONNECTING',
    4: 'CONNECTED',
}

    
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def random_mac_connect(ssid, passwd, interface_name, secType):
    path = ""
    """以829b20固定开头生成随机mac,默认为WPA2PSK加密,interface_name为无线网卡的名称,times为次数，默认1000"""
    down = 'netsh interface set interface "{}" disabled'.format(interface_name)
    up = 'netsh interface set interface "{}" enabled'.format(interface_name)
    # 每次运行程序前都判断网卡接口是否存在，防止死循环
    # print(psutil.net_if_addrs().keys())
    # print(interface_name)
    if interface_name in psutil.net_if_addrs().keys():
        print("网卡接口存在")
    else:
        print("网卡未找到")
        return False
        # os.system(up)
        # time.sleep(3)
    # 抓取接口
    itf0 = pywifi.PyWiFi()
    network_adapter = itf0.interfaces()[0]
    network_adapter_name = network_adapter.name()
    adapter_list = network_adapter_name.split("#")
    adapter_count = len(adapter_list)
    adapter_index = 0
    if adapter_count > 1:
        adapter_index = int(adapter_list[1])
        network_adapter_name = network_adapter_name.split("Adapter")[0]
    print("无线网卡名称为：{} index: {}".format(network_adapter_name, adapter_index))

    X = 'ABCDEF1234567890'
    list_X = list(X)
    list_mac = []
    mac_A = "829B20"
    for i in range(6):
        data = random.choice(list_X)
        list_mac.append(data)
    mac_B = "".join(list_mac)
    mac = (mac_A + mac_B)
    print("本次生成的mac为：{}".format(mac))
    if is_admin():
        print("已经以管理员权限运行")
        # 遍历所有项
        query_file = os.popen(
            'reg query HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}')
        result_file = query_file.read()
        list_file = re.findall('08002BE10318}(.+?)\n', result_file)
        # print("result_file: {} list_file:{}".format(result_file, list_file))
        # 执行查询所有项
        for i in list_file:
            query_cmd = Template(
                r'reg query HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\class\{4D36E972-E325-11CE-BFC1-08002BE10318}${path}')
            path = i
            # print("path: {}".format(path))
            query_cmd = query_cmd.safe_substitute(path=i)
            query_desc = os.popen(query_cmd)
            result_device = query_desc.read()
            # print("result_device: {}".format(result_device))
            # 寻找符合条件的interface_name所在的项名
            if network_adapter_name in result_device:
                if adapter_index > 1:
                    adapter_index = adapter_index - 1
                else:    
                    print("成功在注册表中匹配到网卡-{}的配置信息:{}".format(network_adapter_name, i))
                    path = i
                    break
        # 含{}字符串无法用format拼接
        ch_regedit_add = Template(
            r'reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\class\{4D36E972-E325-11CE-BFC1-08002BE10318}${path} /t REG_SZ /v NetworkAddress /d ${mac} /f')
        # print(path)
        ch_regedit_add = ch_regedit_add.safe_substitute(path=path, mac=mac)
        print(os.popen(ch_regedit_add).read())
        print("禁用无线网卡")
        os.system(down)
        time.sleep(3)
        print("启用无线网卡")
        os.system(up)
        time.sleep(3)
    else:
        if sys.version_info[0] == 3:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    mac_dict = dict()
    dic = psutil.net_if_addrs()
    for adapter in dic:
        sniclist = dic[adapter]
        for snic in sniclist:
            if '-' in snic.address and len(snic.address) == 17:
                mac_dict[adapter] = snic.address
    print("所有网卡mac信息如下：", mac_dict)
    mac_generate = mac[0:2] + "-" + mac[2:4] + "-" + mac[4:6] + "-" + mac[6:8] + "-" + mac[8:10] + "-" + mac[10:12]
    assert mac_generate in mac_dict.values()
    print("网卡mac符合要求并且修改成功")
    # 抓取网卡接口
    itf = pywifi.PyWiFi()
    Realtek = itf.interfaces()[0]
    print("无线网卡名称为：" + Realtek.name())
    Realtek.disconnect()
    time.sleep(3)
    # 获取wifi的连接状态
    assert Realtek.status() == 0
    print("网卡已断开无线连接")
    if secType == 'WPA-PSK':
        """
        WPA-PSK
        """
        ##所有连接前的配置信息写入到profile文件内
        profile_wpapsk = pywifi.Profile()
        profile_wpapsk.ssid = ssid
        # 认证方式,OPEN/SHARED
        profile_wpapsk.auth = const.AUTH_ALG_OPEN
        # 加密方式，不支持WPA3-SAE
        profile_wpapsk.akm.append(const.AKM_TYPE_WPAPSK)
        ##加密规则：CCMP,TKIP,WEP,NONE,UNKNOW
        profile_wpapsk.cipher = const.CIPHER_TYPE_CCMP
        profile_wpapsk.key = "12345678"
        # 添加所有AP配置文件(所连接WiFi的信息)
        Realtek_profile = Realtek.add_network_profile(profile_wpapsk)
    elif secType == 'WPA2-PSK':
        """
        WPA2-PSK
        """
        profile_wpa2psk = pywifi.Profile()
        profile_wpa2psk.ssid = ssid
        profile_wpa2psk.auth = const.AUTH_ALG_OPEN
        profile_wpa2psk.akm.append(const.AKM_TYPE_WPA2PSK)
        profile_wpa2psk.cipher = const.CIPHER_TYPE_CCMP
        profile_wpa2psk.key = passwd
        Realtek_profile = Realtek.add_network_profile(profile_wpa2psk)

    elif secType == 'NONE':
        """
        不加密
        """
        profile_none = pywifi.Profile()
        profile_none.ssid = ssid
        profile_none.auth = const.AUTH_ALG_OPEN
        profile_none.akm.append(const.AKM_TYPE_NONE)
        profile_none.cipher = const.CIPHER_TYPE_NONE
        Realtek_profile = Realtek.add_network_profile(profile_none)
    else:
        raise Exception("请输入正确的加密方式：WPA-PSK、WPA2-PSK、NONE中的一种")
    # 添加profile开始连接
    Realtek.connect(Realtek_profile)
    time.sleep(10)
    for i in range(3):
        if Realtek.status() != 4:
            Realtek.connect(Realtek_profile)
            time.sleep(5)
        else:
            break
    print("无线连接状态：", Realtek.status())
    assert Realtek.status() == 4
    print("Realtek已连接至:{}".format(ssid))
    ip_dict = dict()
    dic2 = psutil.net_if_addrs()
    for adapter in dic2:
        sniclist = dic2[adapter]
        for snic in sniclist:
            if '.' in snic.address:
                ip_dict[adapter] = snic.address
    wl_ip = ip_dict.get(interface_name)
    cmd = 'ping -S {} 61.139.2.69'.format(wl_ip)
    res = os.popen(cmd)
    output = res.read()
    print("无线网卡{} ping 外网:".format(wl_ip), output)
    print(str(datetime.datetime.now())[0:19])
    return True


def run(ssid, secType, passwd, interface_name, run_times):
    x = y = 0
    for i in range(1, run_times + 1):
        # 是否开启打印重定向
        # f = open('C://test.log', 'a+')
        # sys.stdout = f
        try:
            ##函数入口
            ret = random_mac_connect(ssid=ssid, secType=secType, passwd=passwd, interface_name=interface_name)
            if not ret:
                break
            print("***********************第{}次无线反复重连操作已完成****************************".format(i))
            x += 1
        except Exception as e:
            # print(e.__class__.__name__,e)
            print(repr(e))
            print(traceback.format_exc())
            print("***********************第{}次无线反复重连操作失败*****************************".format(i))
            y += 1
        finally:
            print("成功总次数：{}".format(x))
            print("失败总次数：{}".format(y))


if __name__ == '__main__':
    """若不加密则不必传passwd参数"""
    run(ssid='CMCC-pkfg', secType="NONE", passwd=None, interface_name='WLAN 4', run_times=1)
    # run(ssid='00V6-2.4', secType="NONE", passwd=None, interface_name='WLAN 4', run_times=10000)
    # run(ssid='000hyk2-HUAWEI-AX3-Pro', secType="NONE", passwd=None, interface_name='WLAN 4', run_times=10000)
    # run(ssid='000hyk2-TL-XDR3010', secType='WPA2-PSK', passwd='12345678', interface_name='WLAN 4', run_times=10000)
    #run(ssid='000hyk2-1803', secType='WPA2-PSK', passwd='12345678', interface_name='WLAN 4', run_times=10000)
    # run(ssid='33333333333333', passwd='12345678', interface_name='WLAN 4', run_times=3, secType='WPA2-PSK')
