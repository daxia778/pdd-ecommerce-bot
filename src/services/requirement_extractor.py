import json

from src.core.llm_client import get_llm_client
from src.utils.logger import logger


async def extract_requirements_intelligently(buyer_content: str, all_content: str) -> dict:
    """
    Intelligent requirement extraction using LLM instead of regex.
    """
    fields = ["topic", "pages", "style", "deadline", "budget", "audience", "outline", "assets"]
    result = {k: "" for k in fields}
    confidence = {k: 0 for k in fields}
    result["source"] = "none"

    # Fast path: JSON order token parsing
    import re

    order_match = re.search(r"\[\[CREATE_ORDER:(.*?)\]\]", all_content, re.DOTALL)
    if order_match:
        try:
            raw = order_match.group(1).strip()
            data = json.loads(raw)
            field_map = {k: k for k in fields}
            field_map["outline"] = "details"  # Alias
            for field in fields:
                val = data.get(field_map.get(field, field), "")
                if val and str(val).strip():
                    result[field] = str(val).strip()
                    confidence[field] = 95 if field in ("topic", "pages") else 88
            result["source"] = "order_token"
            result["confidence"] = confidence
            return result
        except Exception as e:
            logger.warning(f"Error parsing CREATE_ORDER JSON: {e}")
            pass

    # Intelligent LLM extraction
    if not buyer_content.strip():
        result["confidence"] = confidence
        return result

    llm = get_llm_client()
    system_prompt = """你是一个顶级的客服主管，负责从买家的对话记录中提取PPT定制需求。
请严格分析买家的真实需求，并将提取结果输出为合法的 JSON 格式。
如果某个字段没有提到，请保持为空字符串 ""。
只提取明确的、真实存在的需求信息，不要脑补。
JSON必须包含以下字段：
- topic: PPT主题或项目类型（如"商业计划书"、"年终述职"）
- pages: PPT页数（如"20页"）的详细描述
- style: 设计风格偏好（如"极简科技风"）
- deadline: 交稿截止时间（如"明晚8点前"）
- budget: 价格预算限制（如"200元以内"）
- audience: 受众或阅读对象（如"公司高管"、"投资人"）
- outline: 其他核心的大纲或痛点描述
"""
    try:
        reply = await llm.chat(
            messages=[{"role": "user", "content": f"买家对话内容如下：\n{buyer_content}\n\n请提取需求并输出 JSON："}],
            system_prompt=system_prompt,
            max_tokens=200,
            temperature=0.1,
        )

        # Parse JSON from markdown code blocks if necessary
        json_str = reply.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)

        for field in fields:
            val = data.get(field, "")
            if val and str(val).strip():
                result[field] = str(val).strip()
                confidence[field] = 75  # LLM extracted base confidence

        if any(result[k] for k in fields):
            result["source"] = "llm"

        result["confidence"] = confidence
        return result

    except Exception as e:
        logger.error(f"LLM Requirement Extraction Failed: {e}")
        # Fallback to the old heuristic if LLM fails
        return extract_requirements_heuristically(buyer_content, result, confidence)


def extract_requirements_heuristically(buyer_content, result, confidence):
    import re

    # Fallback heuristics...
    pages_m = re.search(r"(\d+)\s*[页pP]", buyer_content)
    if pages_m:
        result["pages"] = f"{pages_m.group(1)}页"
        confidence["pages"] = 90

    topic_patterns = [
        r"(?:做|要|需要|定制|制作)\s*([\u4e00-\u9fa5a-zA-Z]{2,15}(?:PPT|ppt|计划书|报告|方案|汇报|总结|答辩|展示|投标|培训|介绍|宣传))",
        r"([\u4e00-\u9fa5]{2,8}(?:计划书|报告|方案|汇报|总结|答辩|投标|培训|宣传|介绍))",
    ]
    for pat in topic_patterns:
        topic_m = re.search(pat, buyer_content)
        if topic_m:
            result["topic"] = topic_m.group(1).strip()
            confidence["topic"] = 80
            break

    style_keywords = ["商务", "学术", "简约", "科技", "高端", "创投", "正规", "现代", "简洁", "大气"]
    for kw in style_keywords:
        if kw in buyer_content:
            result["style"] = kw
            confidence["style"] = 75
            break

    deadline_keywords = ["明天", "后天", "本周", "下周", "月底", "紧急", "加急", "尽快", "马上"]
    for kw in deadline_keywords:
        if kw in buyer_content:
            result["deadline"] = kw
            confidence["deadline"] = 82
            break

    budget_m = re.search(r"(\d+)\s*[元块]", buyer_content)
    if budget_m:
        result["budget"] = f"{budget_m.group(1)}元"
        confidence["budget"] = 78

    if any(result[k] for k in ["topic", "pages", "style", "deadline", "budget"]):
        result["source"] = "heuristic"

    result["confidence"] = confidence
    return result
