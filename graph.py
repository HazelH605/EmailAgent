from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any
import nodes
import utils


class AgentState(TypedDict):
    email_data: Dict[str, Any]
    classification: Optional[str]
    process_result: Optional[str]
    config: Dict[str, Any]
    logger: Any


def create_workflow():
    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("classify", classify_node)
    workflow.add_node("process_code", process_code_node)
    workflow.add_node("answer_question", answer_question_node)
    workflow.add_node("handle_spam", handle_spam_node)
    workflow.add_node("log_result", log_node)
    workflow.add_node("send_reply", send_reply_node)

    # 设置入口点
    workflow.set_entry_point("classify")

    # 条件分支
    workflow.add_conditional_edges(
        "classify",
        classify_router,
        {
            "code": "process_code",
            "question": "answer_question",
            "spam": "handle_spam"
        }
    )

    # 连接处理节点到日志
    workflow.add_edge("process_code", "log_result")
    workflow.add_edge("answer_question", "log_result")
    workflow.add_edge("handle_spam", "log_result")

    # 日志节点到发送回复
    workflow.add_edge("log_result", "send_reply")

    # 发送回复到结束
    workflow.add_edge("send_reply", END)

    return workflow.compile()


def classify_node(state: AgentState) -> dict:
    """分类邮件节点"""
    classification = nodes.classify_email(state["email_data"], state["config"])
    state["logger"].info(f"邮件分类结果: {classification}")
    return {"classification": classification}


def process_code_node(state: AgentState) -> dict:
    """处理代码邮件节点"""
    result = nodes.process_code_email(state["email_data"], state["config"], state["logger"])
    return {"process_result": result}


def answer_question_node(state: AgentState) -> dict:
    """回答问题邮件节点"""
    result = nodes.answer_question_email(state["email_data"], state["config"], state["logger"])
    return {"process_result": result}


def handle_spam_node(state: AgentState) -> dict:
    """处理垃圾邮件节点"""
    result = nodes.handle_spam_email(state["email_data"], state["logger"])
    return {"process_result": result}


def log_node(state: AgentState) -> dict:
    """记录日志节点"""
    nodes.log_processing_result(
        state["logger"],
        state["email_data"],
        state["classification"],
        state["process_result"]
    )
    return {"logs": "Logged"}


def send_reply_node(state: AgentState) -> dict:
    """发送回复节点"""
    # 只有非垃圾邮件需要回复
    if state["classification"] != "spam":
        utils.send_reply(
            state["config"],
            state["email_data"]["from"],
            state["email_data"]["subject"],
            state["process_result"],
            state["logger"]
        )
    return {"reply_sent": True}


def classify_router(state: AgentState) -> str:
    """分类路由函数"""
    return state["classification"]