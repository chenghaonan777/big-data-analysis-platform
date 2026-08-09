"""
检查Docker服务状态
"""
import requests
import time


def check_services():
    services = {
        'Hadoop NameNode': 'http://localhost:9870',
        'Hive Server2': 'http://localhost:10002'  # Hive Web UI
    }

    print("检查Docker服务状态...")
    print("=" * 50)

    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: 运行正常")
            else:
                print(f"⚠️  {service_name}: 响应异常 ({response.status_code})")
        except Exception as e:
            print(f"❌ {service_name}: 连接失败 - {str(e)}")

    print("\n" + "=" * 50)
    print("如果所有服务都正常，现在可以运行 python app.py")


if __name__ == '__main__':
    check_services()
