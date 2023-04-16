import os
import subprocess
import argparse
import logging
import time
import netifaces
import random

# 获取当前电脑无线接口名称
wifi_interfaces = []
for interface in netifaces.interfaces():
    if "wlp" in interface:
        wifi_interfaces.append(interface)
interface_name = wifi_interfaces[0]

# 创建logs目录（如果不存在）
if not os.path.exists('logs'):
    os.makedirs('logs')

# 解析命令行参数
parser = argparse.ArgumentParser(description='Connect to Wi-Fi network specified number of times with modified MAC address')
parser.add_argument('-s', '--ssid', required=True, help='SSID of Wi-Fi network to connect to')
parser.add_argument('-t', '--security-type', default='wpa2', help='Security type (e.g. wpa2)')
parser.add_argument('-p', '--password', required=True, help='Password for Wi-Fi network')
parser.add_argument('-n', '--num-attempts', type=int, required=True, help='Number of times to attempt connection')
args = parser.parse_args()

# 设置日志记录器
log_file_name = f"logs/{interface_name}_{args.security_type}_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 创建文件处理器和终端处理器
file_handler = logging.FileHandler(log_file_name)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 定义日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

for i in range(args.num_attempts):
    try:
        # 自动生成 MAC 地址
        new_mac = f"00:11:{random.randint(0x00, 0xff):02X}:{random.randint(0x00, 0xff):02X}:{random.randint(0x00, 0xff):02X}:{random.randint(0x00, 0xff):02X}"
        logging.info(f"Generated MAC address: {new_mac}")

        # 修改 MAC 地址
        cmd = ["ifconfig", interface_name, "down"]
        logging.debug(f"Running command: {' '.join(cmd)}")
        subprocess.call(cmd)

        cmd = ["ifconfig", interface_name, "hw", "ether", new_mac]
        logging.debug(f"Running command: {' '.join(cmd)}")
        subprocess.call(cmd)

        cmd = ["ifconfig", interface_name, "up"]
        logging.debug(f"Running command: {' '.join(cmd)}")
        subprocess.call(cmd)

        # 连接到 Wi-Fi 网络
        cmd = ["nmcli", "dev", "wifi", "connect", args.ssid, "password", args.password, "ifname", interface_name]
        logging.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if "successfully activated" in result.stdout or "激活了设备" in result.stdout:
            logging.info(f"Attempt {i+1} successful!")
        else:
            logging.warning("Attempt {} failed. {}".format(i+1, result.stderr))
    except Exception as e:
        logging.error(f"An error occurred on attempt {i+1}: {e}")

print('Done.')
