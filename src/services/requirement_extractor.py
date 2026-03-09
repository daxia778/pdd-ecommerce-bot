import json
import re

from src.core.llm_client import get_llm_client
from src.utils.logger import logger


async def extract_requirements_intelligently(buyer_content: str, all_content: str) -> dict:
    """
    Intelligent requirement extraction using LLM combined with JSON tokens.
    1. Parse CREATE_ORDER JSON immediately if exists.
    2. Build prompt with FULL dialog context (so LLM sees buyer request + AI answers).
    3. Instruct LLM clearly to not hallucinate and ignore AI pricing/tier pitches.
    """
    fields = ["topic", "pages", "style", "deadline", "budget", "audience", "outline", "assets"]
    result = {k: "" for k in fields}
    confidence = {k: 0 for k in fields}
    result["source"] = "none"

    # 1. Parse JSON order token (Strongest signal)
    has_token = False
    order_match = re.search(r"\[\[CREATE_ORDER:(.*?)\]\]", all_content, re.DOTALL)
    if order_match:
        try:
            raw = order_match.group(1).strip()
            data = json.loads(raw)
            field_map = {k: k for k in fields}
            field_map["outline"] = "details"  # Alias
            for field in fields:
                val = str(data.get(field_map.get(field, field), "")).strip()
                if val and val not in ("-", "无"):
                    result[field] = val
                    confidence[field] = 95 if field in ("topic", "pages") else 88
            has_token = True
            result["source"] = "order_token"
        except Exception as e:
            logger.warning(f"Error parsing CREATE_ORDER JSON: {e}")

    # 2. Intelligent LLM extraction (Fills missing fields & fixes bad context)
    # If the buyer hasn't spoken much, skip LLM
    if len(buyer_content.strip()) < 2:
        result["confidence"] = confidence
        return result

    llm = get_llm_client()
    system_prompt = """你是一个顶级的客服需求分析师。
请阅读下方客服系统中的完整对话记录（包含买家和AI客服），提取出买家的【真实诉求】并输出为严格的 JSON 格式。
规则：
1. **只提取买家本人提出的要求**！绝对不要把 AI 客服的报价、话术、服务档次描述（比如"一般制作"、"简单排版"、"基础设计"）当做买家需求提取出来！
2. 如果某个核心字段买家明确提到了（如"明天早上要" = deadline:"明早"），哪怕 AI 没记录，你也必须提取出来。
3. 如果完全没有提到某个字段，请输出空字符串 ""。千万不要脑补。
4. "outline" (核心内容纲要) 应该是买家提供的资料或大纲（如"公司业绩汇报"），绝不能填写 AI 的设计档次。如果买家没提，留空。

JSON必须包含以下结构：
{
  "topic": "PPT主题或项目类型（如'商务计划书'）",
  "pages": "页数范围（如'20页'）",
  "style": "设计风格（如'极简科技风'）",
  "deadline": "交稿时间（如'明晚8点前'）",
  "budget": "价格预算（如'200元以内'）",
  "audience": "受众（未提及留空）",
  "outline": "买家的资料大纲/痛点（绝不能是客服的报价服务项名称！未提及留空）"
}"""

    try:
        reply = await llm.chat(
            messages=[{"role": "user", "content": f"对话记录如下：\n{all_content}\n\n请输出JSON："}],
            system_prompt=system_prompt,
            max_tokens=250,
            temperature=0.1,
        )

        json_str = reply.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)

        for field in fields:
            val = str(data.get(field, "")).strip()
            # If the token didn't extract it well, or it's empty, we let LLM fill it
            if val and val not in ("-", "无"):
                # Always trust LLM over basic token for tricky fields like deadline or outline
                should_override = not result[field] or field in ("deadline", "outline")

                # Filter out leaked AI service strings explicitly
                if field == "outline" and any(bad in val for bad in ("一般制作", "高级定制", "简单排版", "尊享版")):
                    continue

                if should_override:
                    result[field] = val
                    confidence[field] = 85

        if any(result[k] for k in fields) and not has_token:
            result["source"] = "llm"
        elif has_token:
            result["source"] = "hybrid"

        result["confidence"] = confidence
        return result

    except Exception as e:
        logger.error(f"LLM Requirement Extraction Failed: {e}")
        # Only fallback if order token failed entirely
        if not has_token:
            return extract_requirements_heuristically(buyer_content, result, confidence)
        result["confidence"] = confidence
        return result


def extract_requirements_heuristically(buyer_content, result, confidence):
    import re

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
