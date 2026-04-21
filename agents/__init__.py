from agents.content_writer import ContentWriterAgent
from agents.email_marketer import EmailMarketerAgent
from agents.support_chatbot import SupportChatbotAgent
from agents.seo_optimizer import SEOOptimizerAgent

AGENT_REGISTRY = {
    "content-writer": ContentWriterAgent,
    "email-marketer": EmailMarketerAgent,
    "support-chatbot": SupportChatbotAgent,
    "seo-optimizer": SEOOptimizerAgent,
}


def get_agent(agent_type: str):
    cls = AGENT_REGISTRY.get(agent_type)
    if not cls:
        raise ValueError(
            f"Unknown agent: '{agent_type}'. Available: {list(AGENT_REGISTRY.keys())}"
        )
    return cls()
