import sys
import json
import os
import re
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv  # 新增

# 自动从 .env 文件加载环境变量 (本地开发环境生效)
load_dotenv()

NOTION_TOKEN = os.getenv("notion_token")
PAGE_ID = os.getenv("page_id")

def get_today_data(notion, page_id, today_str):
    """读取当天已有的数据并解析成字典"""
    data = {}
    block_ids = []
    try:
        response = notion.blocks.children.list(block_id=page_id)
        blocks = response.get("results", [])
        found_today = False
        for block in blocks:
            if block["type"] == "heading_2":
                text = block["heading_2"]["rich_text"][0]["plain_text"]
                if text == today_str:
                    found_today = True
                    block_ids.append(block["id"])
                    continue
                elif found_today:
                    break
            if found_today:
                block_ids.append(block["id"])
                if block["type"] == "bulleted_list_item":
                    content = block["bulleted_list_item"]["rich_text"][0]["plain_text"]
                    # 匹配 "项目: 数字" 格式
                    match = re.match(r"(.+?):\s*([\d\.-]+)", content)
                    if match:
                        key, val = match.groups()
                        data[key.strip()] = float(val)
                    elif "备注:" in content:
                        data["备注"] = content.replace("备注:", "").strip()
        return data, block_ids
    except:
        return {}, []


def main(args):
    if not NOTION_TOKEN or not PAGE_ID:
        return {"status": "error", "message": "环境变量配置缺失"}

    notion = Client(auth=NOTION_TOKEN)
    today_str = datetime.now().strftime("%Y.%m.%d")

    # 1. 获取已存数据
    existing_data, old_block_ids = get_today_data(notion, PAGE_ID, today_str)

    # 2. 定义映射
    mapping = {
        "alipay": "支付宝",
        "webank": "微众",
        "cmb": "招商",
        "housing_fund": "公积金",
        "boc_hk": "中银",
        "longbridge": "长桥",
        "remark": "备注",
    }

    # 3. 合并新老数据 (新数据覆盖老数据，老数据若没提到则保留)
    for eng_key, chn_key in mapping.items():
        if args.get(eng_key) is not None:
            existing_data[chn_key] = args.get(eng_key)

    # 4. 计算总额
    total_rmb = sum(
        [float(existing_data.get(k, 0)) for k in ["支付宝", "微众", "招商", "公积金"]]
    )
    total_hkd = sum([float(existing_data.get(k, 0)) for k in ["中银", "长桥"]])

    # 5. 清理旧 Block
    for bid in old_block_ids:
        try:
            notion.blocks.delete(bid)
        except:
            pass

    # 6. 构造新 Block
    def bullet(c):
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": str(c)}}]},
        }

    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": today_str}}]},
        },
        bullet(f"支付宝: {existing_data.get('支付宝', 0)}"),
        bullet(f"微众: {existing_data.get('微众', 0)}"),
        bullet(f"中银: {existing_data.get('中银', 0)} (港币)"),
        bullet(f"招商: {existing_data.get('招商', 0)}"),
        bullet(f"公积金: {existing_data.get('公积金', 0)}"),
        bullet(f"长桥: {existing_data.get('长桥', 0)} (港币)"),
        bullet(f"人民币总资产: {round(total_rmb, 2)}"),
        bullet(f"港币总资产: {round(total_hkd, 2)}"),
        bullet(f"备注: {existing_data.get('备注', '无')}"),
    ]

    try:
        notion.blocks.children.append(block_id=PAGE_ID, children=children)
        return {"status": "success", "message": f"记录已整合更新：{today_str}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(main(json.loads(sys.argv[1])), ensure_ascii=False))
