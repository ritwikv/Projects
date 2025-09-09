import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import json

# Configure page
st.set_page_config(
    page_title="AI Process Consulting Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
    }
    
    .automation-high {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    
    .automation-medium {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    
    .automation-low {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
    
    .step-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .genai-tag {
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .agentic-tag {
        background-color: #f3e5f5;
        color: #7b1fa2;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .automation-tag {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .manual-tag {
        background-color: #ffebee;
        color: #c62828;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

def create_automation_gauge(percentage):
    """Create a gauge chart for automation percentage"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = percentage,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Automation Potential"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "lightgray"},
                {'range': [25, 50], 'color': "gray"},
                {'range': [50, 75], 'color': "lightblue"},
                {'range': [75, 100], 'color': "blue"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_step_categorization_chart(categories):
    """Create a pie chart for step categorization"""
    fig = px.pie(
        values=list(categories.values()),
        names=list(categories.keys()),
        title="Process Step Categorization",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def display_process_analysis(analysis_data):
    """Display the complete process analysis"""
    
    # Header
    st.markdown('<div class="main-header">🤖 AI Process Analysis Results</div>', unsafe_allow_html=True)
    
    # Summary Section
    st.markdown('<div class="section-header">📋 Process Summary</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Process Overview</h4>
            <p><strong>What it achieves:</strong> {analysis_data['summary']['achievement']}</p>
            <p><strong>Key Participants:</strong> {', '.join(analysis_data['summary']['participants'])}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Process Steps:**")
        for i, step in enumerate(analysis_data['summary']['process_steps'], 1):
            st.markdown(f"{i}. {step}")
    
    with col2:
        # Automation Percentage Gauge
        fig_gauge = create_automation_gauge(analysis_data['automation_percentage'])
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Automation Analysis Section
    st.markdown('<div class="section-header">🔧 Automation Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Steps That Can Be Automated")
        
        for step in analysis_data['automatable_steps']:
            automation_type = step['type'].lower()
            if 'genai' in automation_type or 'generative' in automation_type:
                tag_class = 'genai-tag'
                icon = '🧠'
            elif 'agentic' in automation_type:
                tag_class = 'agentic-tag'
                icon = '🤖'
            else:
                tag_class = 'automation-tag'
                icon = '⚙️'
            
            st.markdown(f"""
            <div class="step-card">
                <h5>{icon} {step['step_name']}</h5>
                <span class="{tag_class}">{step['type']}</span>
                <p><strong>How:</strong> {step['how']}</p>
                <p><strong>Why:</strong> {step['justification']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ❌ Steps That Cannot Be Automated")
        
        for step in analysis_data['non_automatable_steps']:
            st.markdown(f"""
            <div class="step-card">
                <h5>👤 {step['step_name']}</h5>
                <span class="manual-tag">Manual Required</span>
                <p><strong>Reason:</strong> {step['reason']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Step Categorization
    st.markdown('<div class="section-header">📊 Step Categorization</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        fig_pie = create_step_categorization_chart(analysis_data['step_categories'])
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("### Category Breakdown")
        for category, count in analysis_data['step_categories'].items():
            percentage = (count / sum(analysis_data['step_categories'].values())) * 100
            st.markdown(f"""
            <div class="metric-card">
                <strong>{category}:</strong> {count} steps ({percentage:.1f}%)
            </div>
            """, unsafe_allow_html=True)
    
    # AI Framework Recommendations
    st.markdown('<div class="section-header">🚀 Agentic AI Framework Recommendations</div>', unsafe_allow_html=True)
    
    for framework in analysis_data['framework_recommendations']:
        st.markdown(f"""
        <div class="step-card">
            <h4>🔧 {framework['name']}</h4>
            <p><strong>Best For:</strong> {framework['best_for']}</p>
            <p><strong>Why Recommended:</strong> {framework['justification']}</p>
            <p><strong>Implementation Complexity:</strong> {framework['complexity']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Current Process Explanation
    st.markdown('<div class="section-header">📖 Current Process Explanation</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>Process Flow Analysis</h4>
        <p>{analysis_data['current_process_explanation']['overview']}</p>
        
        <h5>Key Characteristics:</h5>
        <ul>
    """, unsafe_allow_html=True)
    
    for characteristic in analysis_data['current_process_explanation']['characteristics']:
        st.markdown(f"<li>{characteristic}</li>", unsafe_allow_html=True)
    
    st.markdown(f"""
        </ul>
        
        <h5>Pain Points:</h5>
        <ul>
    """, unsafe_allow_html=True)
    
    for pain_point in analysis_data['current_process_explanation']['pain_points']:
        st.markdown(f"<li>{pain_point}</li>", unsafe_allow_html=True)
    
    st.markdown("</ul></div>", unsafe_allow_html=True)

def get_sample_analysis():
    """Return sample analysis data for demonstration"""
    return {
        "summary": {
            "achievement": "Customer onboarding process that transforms new customer applications into active accounts through verification, documentation, and system setup",
            "participants": ["Customer Service Rep", "Compliance Officer", "IT Administrator", "Account Manager"],
            "process_steps": [
                "Customer submits application form with personal and business information",
                "Initial document verification and completeness check",
                "Compliance screening against regulatory databases",
                "Credit check and risk assessment",
                "Account setup in core banking system",
                "Welcome package generation and delivery",
                "First customer contact and relationship establishment"
            ]
        },
        "automation_percentage": 75,
        "automatable_steps": [
            {
                "step_name": "Document Verification",
                "type": "Generative AI + OCR",
                "how": "AI can extract and validate information from documents using OCR and NLP",
                "justification": "GenAI excels at document understanding and can cross-reference information across multiple documents automatically"
            },
            {
                "step_name": "Compliance Screening",
                "type": "Agentic AI",
                "how": "AI agents can query multiple databases and apply complex compliance rules",
                "justification": "Agentic AI can orchestrate multiple API calls and decision trees based on regulatory requirements"
            },
            {
                "step_name": "Account Setup",
                "type": "Traditional Automation",
                "how": "RPA can automate system entries and configurations",
                "justification": "Repetitive system interactions are ideal for robotic process automation"
            },
            {
                "step_name": "Welcome Package Generation",
                "type": "Generative AI",
                "how": "AI can personalize content based on customer profile and preferences",
                "justification": "GenAI can create tailored communications and documentation at scale"
            }
        ],
        "non_automatable_steps": [
            {
                "step_name": "Relationship Establishment Call",
                "reason": "Requires human empathy, relationship building, and complex problem-solving"
            },
            {
                "step_name": "Complex Exception Handling",
                "reason": "Edge cases and unusual situations require human judgment and creativity"
            },
            {
                "step_name": "Final Approval for High-Risk Cases",
                "reason": "Regulatory requirements mandate human oversight for certain risk categories"
            }
        ],
        "step_categories": {
            "Data Processing": 3,
            "Decision Making": 2,
            "Communication": 2,
            "System Integration": 2,
            "Human Interaction": 1
        },
        "framework_recommendations": [
            {
                "name": "LangChain + CrewAI",
                "best_for": "Document processing and multi-step workflows",
                "justification": "Excellent for chaining LLM operations and managing complex document workflows",
                "complexity": "Medium"
            },
            {
                "name": "Microsoft Power Platform + AI Builder",
                "best_for": "Enterprise integration and form processing",
                "justification": "Seamless integration with existing Microsoft ecosystem and strong OCR capabilities",
                "complexity": "Low"
            },
            {
                "name": "Custom AutoGen Framework",
                "best_for": "Multi-agent collaboration scenarios",
                "justification": "Perfect for scenarios requiring multiple AI agents to collaborate on complex tasks",
                "complexity": "High"
            }
        ],
        "current_process_explanation": {
            "overview": "The current customer onboarding process is a hybrid manual-digital workflow that takes 3-5 business days to complete. It involves multiple handoffs between departments and relies heavily on manual document review and data entry.",
            "characteristics": [
                "High manual effort in document verification (2-3 hours per application)",
                "Multiple system touchpoints requiring separate logins and data entry",
                "Sequential processing with potential bottlenecks at compliance review",
                "Paper-based documentation requiring physical storage and retrieval"
            ],
            "pain_points": [
                "Inconsistent processing times due to manual variations",
                "High error rates in data transcription (approximately 5-8%)",
                "Customer frustration with lengthy onboarding times",
                "Compliance risks due to manual oversight gaps",
                "High operational costs due to labor-intensive processes"
            ]
        }
    }

def main():
    # Sidebar
    st.sidebar.title("🤖 AI Process Consultant")
    st.sidebar.markdown("Upload your process map to get AI-powered automation insights")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload Process Map",
        type=['pdf', 'png', 'jpg', 'jpeg', 'bpmn', 'xml', 'txt'],
        help="Upload your process map in any supported format"
    )
    
    # Analysis options
    st.sidebar.markdown("### Analysis Options")
    analysis_depth = st.sidebar.selectbox(
        "Analysis Depth",
        ["Quick Analysis", "Detailed Analysis", "Comprehensive Report"]
    )
    
    focus_areas = st.sidebar.multiselect(
        "Focus Areas",
        ["Cost Reduction", "Time Optimization", "Quality Improvement", "Compliance", "Customer Experience"],
        default=["Cost Reduction", "Time Optimization"]
    )
    
    # Main content
    if uploaded_file is None:
        # Welcome screen
        st.markdown('<div class="main-header">🤖 AI Process Consulting Assistant</div>', unsafe_allow_html=True)
        
        st.markdown("""
        ## Welcome to your AI-powered Process Automation Consultant! 
        
        This application analyzes your business processes and provides intelligent recommendations for automation using:
        
        - 🧠 **Generative AI** for content creation and document processing
        - 🤖 **Agentic AI** for complex decision-making and orchestration  
        - ⚙️ **Traditional Automation** for repetitive tasks
        
        ### What you'll get:
        
        ✅ **Process Summary** - Clear overview of your process and participants  
        ✅ **Automation Potential** - Percentage of steps that can be automated  
        ✅ **Step-by-Step Analysis** - Detailed breakdown of automation opportunities  
        ✅ **AI Framework Recommendations** - Best tools and platforms for your needs  
        ✅ **Implementation Roadmap** - Prioritized approach to automation  
        
        ### Get Started:
        👈 Upload your process map using the sidebar to begin the analysis!
        """)
        
        # Show sample analysis
        if st.button("🎯 View Sample Analysis", type="primary"):
            st.session_state.show_sample = True
        
        if st.session_state.get('show_sample', False):
            st.markdown("---")
            st.info("📋 Below is a sample analysis of a customer onboarding process:")
            sample_data = get_sample_analysis()
            display_process_analysis(sample_data)
    
    else:
        # File uploaded - show analysis
        st.success(f"✅ Process map '{uploaded_file.name}' uploaded successfully!")
        
        # Simulate processing
        with st.spinner("🔍 Analyzing your process map with AI..."):
            import time
            time.sleep(2)  # Simulate processing time
        
        # In a real implementation, you would process the uploaded file here
        # For now, we'll show the sample analysis
        analysis_data = get_sample_analysis()
        
        # Customize analysis based on uploaded file
        st.info(f"📊 Analysis complete for {uploaded_file.name} | Depth: {analysis_depth} | Focus: {', '.join(focus_areas)}")
        
        display_process_analysis(analysis_data)
        
        # Download report option
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("📥 Download PDF Report"):
                st.info("PDF report generation would be implemented here")
        
        with col2:
            if st.button("📊 Export to Excel"):
                st.info("Excel export would be implemented here")
        
        with col3:
            if st.button("🔄 Analyze Another Process"):
                st.session_state.clear()
                st.rerun()

if __name__ == "__main__":
    main()

