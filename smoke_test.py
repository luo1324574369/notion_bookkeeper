import json
from main import main


def run_smoke_test():
    """
    冒烟测试：模拟一次真实的 Notion 写入
    """
    print("--- 正在启动冒烟测试 ---")

    # 模拟 AI 提取的输入参数
    test_input = {
        "alipay": 1000.5,
        "webank": 2000.75,
        "remark": "这是通过 .env 配置进行的冒烟测试",
        "longbridge": 1500.25,
    }

    # 执行主逻辑
    result = main(test_input)

    if result["status"] == "success":
        print("✅ 测试成功！内容已同步至 Notion。")
    else:
        print(f"❌ 测试失败！错误信息: {result['message']}")

    print(f"返回结果: {json.dumps(result, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    # 首先检查环境变量是否读取成功
    from main import NOTION_TOKEN, PAGE_ID

    if not NOTION_TOKEN or not PAGE_ID:
        print("⚠️ 错误：无法从环境变量或 .env 文件读取到配置！")
        print("请确认 .env 文件存在且内容格式正确。")
    else:
        run_smoke_test()
