# AI Process Consulting Assistant

A Streamlit-based frontend application for AI-powered process automation consulting. This application analyzes business process maps and provides intelligent recommendations for automation using Generative AI, Agentic AI, and traditional automation techniques.

## Features

🤖 **Comprehensive Process Analysis**
- Process summary with participants and steps
- Automation potential percentage calculation
- Step-by-step automation recommendations
- AI framework suggestions
- Current process pain point identification

🎯 **Intelligent Automation Recommendations**
- **Generative AI** opportunities for content creation and document processing
- **Agentic AI** suggestions for complex decision-making workflows
- **Traditional Automation** identification for repetitive tasks
- Detailed justification for each recommendation

📊 **Interactive Visualizations**
- Automation potential gauge chart
- Process step categorization pie chart
- Color-coded automation tags
- Professional dashboard layout

🔧 **Framework Recommendations**
- LangChain + CrewAI for document workflows
- Microsoft Power Platform for enterprise integration
- Custom AutoGen for multi-agent scenarios
- Implementation complexity assessment

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit application:
```bash
streamlit run process_consulting_app.py
```

2. Open your web browser and navigate to the provided local URL (typically `http://localhost:8501`)

3. Upload your process map using the sidebar file uploader

4. Configure analysis options:
   - Choose analysis depth (Quick, Detailed, or Comprehensive)
   - Select focus areas (Cost Reduction, Time Optimization, etc.)

5. View the comprehensive analysis results including:
   - Process summary and automation percentage
   - Detailed step-by-step automation recommendations
   - AI framework suggestions
   - Current process explanation and pain points

## Supported File Formats

- **Images**: PNG, JPG, JPEG
- **Documents**: PDF, TXT
- **Process Models**: BPMN, XML

## Sample Analysis

The application includes a sample analysis of a customer onboarding process to demonstrate its capabilities. Click "View Sample Analysis" on the welcome screen to explore the features.

## Application Structure

```
├── process_consulting_app.py    # Main Streamlit application
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## Key Components

### 1. Process Analysis Engine
- Analyzes uploaded process maps
- Identifies automation opportunities
- Categorizes process steps
- Calculates automation potential

### 2. Visualization Dashboard
- Interactive charts and gauges
- Color-coded automation recommendations
- Professional styling with custom CSS
- Responsive layout design

### 3. AI Framework Recommendations
- Evaluates different AI/automation frameworks
- Provides implementation complexity assessment
- Offers justification for each recommendation

## Customization

The application can be easily customized by modifying:

- **Analysis Logic**: Update the `get_sample_analysis()` function with your own analysis engine
- **Styling**: Modify the CSS in the `st.markdown()` sections
- **Visualizations**: Enhance charts using Plotly functions
- **File Processing**: Add support for additional file formats

## Future Enhancements

- Integration with actual AI analysis engines
- Real-time process map parsing
- PDF report generation
- Excel export functionality
- Multi-language support
- Advanced visualization options

## Dependencies

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **Pillow**: Image processing support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

