"""
Streamlit demo UI — full 4-agent dashboard.
Run with: streamlit run ui/app.py
"""

import json
import httpx
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Team Platform", page_icon="🤖", layout="wide")
st.title("AI Team Platform")
st.caption("4 AI agents — content, email, support, SEO")

# ── Sidebar ──
with st.sidebar:
    st.header("Select agent")
    agent_type = st.selectbox(
        "Agent",
        ["content-writer", "email-marketer", "seo-optimizer", "support-chatbot"],
        format_func=lambda x: x.replace("-", " ").title(),
    )
    st.divider()

    if agent_type == "content-writer":
        st.subheader("Content settings")
        format_type = st.selectbox("Format", ["blog_post", "social_media", "email_newsletter", "product_description"], format_func=lambda x: x.replace("_", " ").title())
        tone = st.selectbox("Tone", ["professional", "casual", "friendly", "authoritative", "witty", "empathetic"])
        audience = st.text_input("Target audience", value="general audience")
        word_count = st.slider("Word count", 200, 2000, 800, step=100)

    elif agent_type == "email-marketer":
        st.subheader("Campaign settings")
        goal = st.selectbox("Campaign goal", ["welcome_series", "trial_to_paid_conversion", "product_launch", "re_engagement", "upsell_cross_sell", "nurture_leads", "onboarding", "abandoned_cart", "event_promotion"], format_func=lambda x: x.replace("_", " ").title())
        segment = st.text_input("Target segment", value="all subscribers")
        email_count = st.slider("Number of emails", 2, 10, 5)
        brand_voice = st.text_input("Brand voice", value="professional, friendly")

    elif agent_type == "seo-optimizer":
        st.subheader("SEO settings")
        seo_mode = st.selectbox("Analysis mode", ["content_audit", "keyword_analysis", "meta_generator", "optimize_content", "full_audit"], format_func=lambda x: x.replace("_", " ").title())
        keywords = st.text_input("Target keywords", placeholder="python performance, optimize python")
        seo_audience = st.text_input("Target audience", value="general audience")

    elif agent_type == "support-chatbot":
        st.subheader("Chatbot settings")
        workspace_id = st.text_input("Workspace ID", value="default")
        st.divider()
        st.caption("Knowledge base")
        uploaded_file = st.file_uploader("Upload docs (PDF, DOCX, TXT)", type=["pdf", "docx", "txt", "md", "html"])
        if uploaded_file and st.button("Ingest document"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            resp = httpx.post(f"{API_URL}/api/chat/ingest/file", files=files, params={"workspace_id": workspace_id}, timeout=60)
            if resp.status_code == 200:
                r = resp.json()
                st.success(f"Ingested: {r['chunks_created']} chunks from {r['source']}")
            else:
                st.error(f"Error: {resp.text}")

        paste_text = st.text_area("Or paste text directly", height=100, key="paste_kb")
        paste_name = st.text_input("Source name", value="pasted content", key="paste_name")
        if paste_text and st.button("Ingest text"):
            resp = httpx.post(f"{API_URL}/api/chat/ingest/text", json={"text": paste_text, "source_name": paste_name, "workspace_id": workspace_id}, timeout=60)
            if resp.status_code == 200:
                r = resp.json()
                st.success(f"Ingested: {r['chunks_created']} chunks")
            else:
                st.error(f"Error: {resp.text}")

    st.divider()
    stream_mode = st.checkbox("Stream output", value=True)


# ── Main area ──
if agent_type == "content-writer":
    topic = st.text_area("What should I write about?", placeholder="e.g., 10 Python tips every dev should know", height=100)
    run_label = "Generate content"
    payload_fn = lambda: {"topic": topic, "format": format_type, "tone": tone, "audience": audience, "word_count": word_count}
    ready = bool(topic)

elif agent_type == "email-marketer":
    product = st.text_area("Describe your product/service", placeholder="e.g., SaaS project management tool, $29/month", height=100)
    run_label = "Generate email sequence"
    payload_fn = lambda: {"product": product, "goal": goal, "segment": segment, "email_count": email_count, "brand_voice": brand_voice}
    ready = bool(product)

elif agent_type == "seo-optimizer":
    if seo_mode == "keyword_analysis":
        seo_topic = st.text_area("Topic to research", placeholder="e.g., Python performance optimization", height=100)
        run_label = "Analyze keywords"
        payload_fn = lambda: {"mode": seo_mode, "keywords": keywords or seo_topic, "topic": seo_topic, "audience": seo_audience}
        ready = bool(seo_topic or keywords)
    else:
        seo_content = st.text_area("Paste content to analyze / optimize", height=200)
        run_label = f"Run {seo_mode.replace('_', ' ')}"
        payload_fn = lambda: {"mode": seo_mode, "keywords": keywords, "content": seo_content, "audience": seo_audience}
        ready = bool(keywords) and (bool(seo_content) or seo_mode == "keyword_analysis")

elif agent_type == "support-chatbot":
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ask a question...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    resp = httpx.post(f"{API_URL}/api/chat/message", json={
                        "question": question,
                        "workspace_id": workspace_id,
                        "conversation_history": st.session_state.chat_history[-10:],
                    }, timeout=120)
                    result = resp.json()
                    answer = result["answer"]
                    st.markdown(answer)

                    conf = result.get("confidence", 0)
                    sources = result.get("sources", [])
                    esc = result.get("escalation", {})

                    col1, col2 = st.columns(2)
                    with col1:
                        color = "green" if conf > 0.7 else "orange" if conf > 0.4 else "red"
                        st.caption(f"Confidence: :{color}[{conf:.0%}]")
                    with col2:
                        if sources:
                            st.caption(f"Sources: {', '.join(s['source'] for s in sources)}")

                    if esc.get("should_escalate"):
                        st.warning(f"Escalation recommended: {esc['reason']} (urgency: {esc['urgency']})")

                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    ready = False  # Chat uses its own input
    run_label = ""

# ── Run button (for non-chat agents) ──
if agent_type != "support-chatbot":
    run_btn = st.button(run_label, type="primary")

    if run_btn and ready:
        payload = payload_fn()

        if stream_mode:
            st.subheader("Output")
            container = st.empty()
            full_text = ""
            with httpx.Client(timeout=180) as client:
                with client.stream("POST", f"{API_URL}/api/agents/{agent_type}/stream", json=payload) as resp:
                    for line in resp.iter_lines():
                        if line.startswith("data:"):
                            try:
                                data = json.loads(line[5:].strip())
                                if "text" in data and not data.get("done"):
                                    full_text += data["text"]
                                    container.markdown(full_text)
                            except json.JSONDecodeError:
                                pass
            if full_text:
                st.divider()
                st.download_button("Download", full_text, file_name=f"{agent_type}-output.txt")
        else:
            with st.spinner("Generating..."):
                try:
                    resp = httpx.post(f"{API_URL}/api/agents/{agent_type}/run", json=payload, timeout=180)
                    result = resp.json()
                    st.subheader("Output")
                    st.markdown(result["content"])
                    st.divider()
                    cols = st.columns(3)
                    with cols[0]:
                        score_label = "SEO score" if agent_type == "seo-optimizer" else "Quality score"
                        st.metric(score_label, f"{result['quality_score']}/100")
                    with cols[1]:
                        st.metric("Words", result["metadata"].get("word_count", "N/A"))
                    with cols[2]:
                        st.metric("Model", result["model"])
                    if result["metadata"].get("qa_issues"):
                        with st.expander("QA issues"):
                            for issue in result["metadata"]["qa_issues"]:
                                st.warning(issue)
                    st.download_button("Download", result["content"], file_name=f"{agent_type}-output.txt")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    elif run_btn and not ready:
        st.warning("Please fill in the required fields.")
