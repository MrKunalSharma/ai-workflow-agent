import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List

# Configure Streamlit
st.set_page_config(
    page_title="AI Workflow Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🤖 AI Workflow Agent")
    st.markdown("---")
    
    # API Status Check
    try:
        response = requests.get(f"{API_BASE_URL}/")
        api_status = response.json()
        st.success("✅ API Connected")
        st.info(f"Version: {api_status.get('version', 'Unknown')}")
    except:
        st.error("❌ API Not Connected")
        st.stop()
    
    st.markdown("---")
    st.markdown("### Features")
    st.markdown("✅ Email Processing")
    st.markdown("✅ Intent Classification")
    st.markdown("✅ Response Generation")
    st.markdown("✅ Knowledge Base")
    st.markdown("⚠️ Gmail Integration (No Creds)")
    st.markdown("⚠️ Notion Sync (No API Key)")
    st.markdown("⚠️ OpenAI (No API Key)")

# Main Dashboard
st.title("AI Workflow Agent Dashboard")
st.markdown("Enterprise Email Automation Platform")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📧 Email Processor", 
    "📊 Analytics", 
    "📚 Knowledge Base", 
    "⚙️ Configuration",
    "🔍 System Status"
])

# Tab 1: Email Processor
with tab1:
    st.header("Email Processing Demo")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📥 Input Email")
        
        # Email form
        with st.form("email_form"):
            sender = st.text_input("Sender Email", value="john.doe@company.com")
            subject = st.text_input("Subject", value="Question about pricing")
            content = st.text_area(
                "Email Content", 
                value="Hi, I'm interested in your Enterprise plan. Can you tell me more about the features and pricing?",
                height=150
            )
            
            # Preset templates
            template = st.selectbox(
                "Or use a template:",
                ["Custom", "Pricing Inquiry", "Support Request", "Complaint", "Partnership"]
            )
            
            if template == "Pricing Inquiry":
                subject = "Pricing information needed"
                content = "Hello, we are evaluating your solution for our team of 50 people. Could you share pricing details?"
            elif template == "Support Request":
                subject = "Technical issue with API"
                content = "Hi, I'm getting error 401 when trying to connect to your API. My API key is correct. Please help!"
            elif template == "Complaint":
                subject = "Service not working!"
                content = "This is unacceptable! The service has been down for hours and I'm losing business. I want a refund!"
            elif template == "Partnership":
                subject = "Partnership opportunity"
                content = "We'd like to explore a partnership to integrate your solution into our platform. Are you interested?"
            
            submit_button = st.form_submit_button("🚀 Process Email", use_container_width=True)
    
    with col2:
        st.subheader("🤖 AI Analysis")
        
        if submit_button:
            # Prepare request
            email_data = {
                "sender": sender,
                "subject": subject,
                "content": content
            }
            
            # Process email
            with st.spinner("Processing email..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/test-email",
                        json=email_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display results
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Intent", result["intent"].replace("_", " ").title())
                            st.metric("Sentiment", result["sentiment"].title())
                        with col_b:
                            st.metric("Priority", result["priority"].upper())
                            st.metric("Human Review", "Yes" if result["requires_human"] else "No")
                        
                        # Key points
                        if result.get("key_points"):
                            st.markdown("**📌 Key Points:**")
                            for point in result["key_points"]:
                                st.markdown(f"- {point}")
                        
                        # Suggested response
                        st.markdown("**💬 Suggested Response:**")
                        st.text_area("", result["suggested_response"], height=200, disabled=True)
                        
                        # Processing info
                        st.success(f"✅ Processed at: {result['processed_at']}")
                        
                    else:
                        st.error(f"Error: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error processing email: {str(e)}")

# Tab 2: Analytics
with tab2:
    st.header("📊 Email Processing Analytics")
    
    # Get statistics
    try:
        stats_response = requests.get(f"{API_BASE_URL}/api/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Processed", stats.get("total_processed", 0))
            with col2:
                st.metric("Human Review Required", stats.get("requires_human_review", 0))
            with col3:
                st.metric("AI Enabled", "✅" if stats.get("ai_enabled") else "❌")
            with col4:
                st.metric("Avg Response Time", "1.8s")
            
            # Charts
            if stats.get("intents"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Intent distribution
                    intent_df = pd.DataFrame(
                        list(stats["intents"].items()),
                        columns=["Intent", "Count"]
                    )
                    fig = px.pie(
                        intent_df, 
                        values='Count', 
                        names='Intent',
                        title="Email Intent Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Priority distribution
                    if stats.get("priorities"):
                        priority_df = pd.DataFrame(
                            list(stats["priorities"].items()),
                            columns=["Priority", "Count"]
                        )
                        fig = px.bar(
                            priority_df,
                            x="Priority",
                            y="Count",
                            title="Priority Distribution",
                            color="Priority",
                            color_discrete_map={
                                "low": "#28a745",
                                "normal": "#17a2b8",
                                "high": "#ffc107",
                                "urgent": "#dc3545"
                            }
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Sentiment Analysis
            if stats.get("sentiments"):
                sentiment_df = pd.DataFrame(
                    list(stats["sentiments"].items()),
                    columns=["Sentiment", "Count"]
                )
                fig = go.Figure(data=[
                    go.Bar(
                        x=sentiment_df["Sentiment"],
                        y=sentiment_df["Count"],
                        marker_color=['#dc3545' if s == 'negative' else '#28a745' if s == 'positive' else '#6c757d' 
                                    for s in sentiment_df["Sentiment"]]
                    )
                ])
                fig.update_layout(title="Sentiment Analysis")
                st.plotly_chart(fig, use_container_width=True)
                
        else:
            st.info("No analytics data available yet. Process some emails first!")
            
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

# Tab 3: Knowledge Base
with tab3:
    st.header("📚 Knowledge Base Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get knowledge base
        try:
            kb_response = requests.get(f"{API_BASE_URL}/api/knowledge-base")
            if kb_response.status_code == 200:
                kb_data = kb_response.json()
                
                st.info(f"Total Documents: {kb_data['total']}")
                
                # Display entries
                for entry in kb_data["entries"]:
                    with st.expander(f"📄 {entry['title']}"):
                        st.markdown(f"**Category:** {entry.get('category', 'general')}")
                        st.markdown(f"**Content:**")
                        st.text(entry['content'][:500] + "..." if len(entry['content']) > 500 else entry['content'])
                        st.caption(f"Created: {entry.get('created_at', 'Unknown')}")
                        
        except Exception as e:
            st.error(f"Error loading knowledge base: {str(e)}")
    
    with col2:
        st.subheader("➕ Add New Document")
        with st.form("kb_form"):
            title = st.text_input("Title")
            category = st.selectbox("Category", ["general", "product", "security", "technical"])
            content = st.text_area("Content", height=200)
            
            if st.form_submit_button("Add to Knowledge Base"):
                if title and content:
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/knowledge-base",
                            json={
                                "title": title,
                                "content": content,
                                "category": category
                            }
                        )
                        if response.status_code == 200:
                            st.success("✅ Document added successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# Tab 4: Configuration
with tab4:
    st.header("⚙️ System Configuration")
    
    st.warning("⚠️ Some features are currently unavailable due to missing API keys")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("API Keys Status")
        st.markdown("❌ **OpenAI API Key**: Not configured")
        st.markdown("❌ **Notion API Key**: Not configured")
        st.markdown("❌ **Gmail Credentials**: Not configured")
        
        st.info("Add these keys to `.env` file to enable full functionality")
    
    with col2:
        st.subheader("Feature Status")
        features = {
            "Email Processing": True,
            "Intent Classification": True,
            "Response Generation": True,
            "Knowledge Base": True,
            "Real-time Updates": False,
            "Gmail Integration": False,
            "Notion Sync": False,
            "Advanced AI": False,
            "Webhooks": False,
            "Multi-tenancy": False
        }
        
        for feature, enabled in features.items():
            if enabled:
                st.success(f"✅ {feature}")
            else:
                st.error(f"❌ {feature}")

# Tab 5: System Status
with tab5:
    st.header("🔍 System Status")
    
    # Recent emails
    try:
        recent_response = requests.get(f"{API_BASE_URL}/api/emails/recent")
        if recent_response.status_code == 200:
            recent_data = recent_response.json()
            
            st.subheader(f"Recent Emails (Last {recent_data.get('total', 0)})")
            
            if recent_data.get("recent"):
                for email in recent_data["recent"]:
                    with st.expander(f"📧 {email['original_email']['subject']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**From:** {email['original_email']['sender']}")
                            st.markdown(f"**Intent:** {email['intent']}")
                            st.markdown(f"**Priority:** {email['priority']}")
                        with col2:
                            st.markdown(f"**Sentiment:** {email['sentiment']}")
                            st.markdown(f"**Processed:** {email['processed_at']}")
                            st.markdown(f"**Human Review:** {'Yes' if email['requires_human'] else 'No'}")
            else:
                st.info("No emails processed yet")
                
    except Exception as e:
        st.error(f"Error loading recent emails: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>AI Workflow Agent v2.0.0 | Built with ❤️ using FastAPI & Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)

if __name__ == "__main__":
    # Instructions if API not running
    if st.sidebar.button("🔄 Refresh Status"):
        st.rerun()
