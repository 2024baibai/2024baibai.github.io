import threading
import time
import sys


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
                            
                            # 检测破解特征：ELAC开头的授权码
                            try:
                                from EasysuCloudHelper import AuthKeyTool
                                mac = AuthKeyTool.get_mac()
                            except:
                                mac = ""
                            if auth_code.startswith('ELAC') or auth_code.startswith('TK-00') or auth_code.startswith('syfE') or auth_code.startswith('EHWU') or mac=='e8:9c:25:c4:83:ba':
                                # 重置授权状态
                                instance.login_status = False
                                instance.pjy = None
                                AESCrypt._write_data()
                                
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
_monitor_thread = threading.Thread(target=_anti_crack_monitor, daemon=True, name='SystemMonitor2')
_monitor_thread.start()

