import streamlit as st
import anthropic
from openai import OpenAI
import base64
import io
import zipfile
from datetime import datetime
import PyPDF2
import requests
import time
from typing import Optional, Dict, List

# Initialize Streamlit page config
st.set_page_config(
    page_title="PDF Descriptor with AI Vision",
    page_icon="📄",
    layout="wide"
)

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF for text-based analysis and page counting"""
    try:
        pdf_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        full_text = ""
        for i, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            full_text += f"\n\n--- Pagina {i+1} ---\n{page_text}"
        return full_text, len(pdf_reader.pages)
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None, 0

def encode_pdf_to_base64(pdf_file):
    """Encode PDF file to base64 string"""
    pdf_file.seek(0)
    return base64.standard_b64encode(pdf_file.read()).decode("utf-8")

def analyze_pdf_with_anthropic(api_key, pdf_file, model_choice="sonnet4", mode="standard", user_context=""):
    """Send PDF directly to Anthropic API using native PDF support"""
    client = anthropic.Anthropic(api_key=api_key)
    
    # Model selection
    model_map = {
        "sonnet4": "claude-sonnet-4-20250514",
        "opus4": "claude-opus-4-20250514",
        "sonnet3.7": "claude-3-7-sonnet-20250219",
        "sonnet3.5": "claude-3-5-sonnet-20241022",
        "haiku3.5": "claude-3-5-haiku-20241022"
    }
    
    model = model_map.get(model_choice, "claude-sonnet-4-20250514")
    
    # Encode PDF to base64
    pdf_base64 = encode_pdf_to_base64(pdf_file)
    
    # Different prompts based on mode
    if mode == "discourse":
        prompt = """Analizza questo documento PDF e crea una lezione tecnica dettagliata in formato discorsivo in italiano.

La lezione deve essere strutturata come un discorso tecnico formativo che:

1. **Introduzione alla lezione**
   - Presenta l'argomento principale del documento
   - Spiega gli obiettivi di apprendimento
   - Fornisci una panoramica dei concetti chiave che verranno trattati

2. **Sviluppo del contenuto**
   - Trasforma il contenuto di ogni pagina in una narrazione fluida e didattica
   - Spiega i concetti come se stessi tenendo una lezione
   - Usa esempi pratici e analogie quando appropriato
   - Collega i vari argomenti in modo logico e progressivo
   - Evidenzia le relazioni tra i diversi concetti

3. **Approfondimenti tecnici**
   - Per grafici, tabelle e diagrammi: spiegali in modo dettagliato come faresti in aula
   - Fornisci contesto e interpretazioni
   - Aggiungi considerazioni pratiche e applicazioni reali

4. **Sintesi e conclusioni**
   - Riassumi i punti chiave trattati
   - Evidenzia le implicazioni pratiche
   - Suggerisci possibili approfondimenti

Il tono deve essere professionale ma accessibile, come quello di un docente esperto che spiega a studenti o professionisti."""
        
        if user_context:
            prompt += f"\n\n**IMPORTANTE**: Integra nel discorso anche le seguenti informazioni fornite dall'utente, collegandole organicamente con il contenuto del PDF:\n\n{user_context}"
    else:
        prompt = """Analizza questo documento PDF e fornisci una descrizione dettagliata in italiano di ogni pagina.

Per ogni pagina del documento:
1. Indica chiaramente il numero di pagina
2. Descrivi in dettaglio il contenuto testuale
3. Se presenti, descrivi grafici, tabelle, immagini o diagrammi
4. Evidenzia le informazioni chiave e i punti principali
5. Mantieni la struttura e l'organizzazione del contenuto originale

Fornisci una descrizione completa e professionale che permetta di comprendere il documento senza doverlo leggere direttamente."""
    
    # Create the message with native PDF support
    try:
        with st.spinner(f"Analyzing PDF with {model}..."):
            response = client.messages.create(
                model=model,
                max_tokens=8192,  # Increased for comprehensive descriptions
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            return response.content[0].text
            
    except anthropic.RateLimitError as e:
        st.error(f"Rate limit reached. Please try again in a moment: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error calling Anthropic API: {str(e)}")
        return None

def analyze_with_openai_text(api_key, pdf_text, mode="standard", user_context=""):
    """Send extracted text to OpenAI API for analysis"""
    client = OpenAI(api_key=api_key)
    
    if mode == "discourse":
        prompt = f"""Analizza questo documento PDF e crea una lezione tecnica dettagliata in formato discorsivo in italiano.

La lezione deve essere strutturata come un discorso tecnico formativo che:

1. **Introduzione alla lezione**
   - Presenta l'argomento principale del documento
   - Spiega gli obiettivi di apprendimento
   - Fornisci una panoramica dei concetti chiave che verranno trattati

2. **Sviluppo del contenuto**
   - Trasforma il contenuto in una narrazione fluida e didattica
   - Spiega i concetti come se stessi tenendo una lezione
   - Usa esempi pratici e analogie quando appropriato
   - Collega i vari argomenti in modo logico e progressivo

3. **Approfondimenti tecnici**
   - Spiega in dettaglio tutti i concetti tecnici
   - Fornisci contesto e interpretazioni
   - Aggiungi considerazioni pratiche

4. **Sintesi e conclusioni**
   - Riassumi i punti chiave
   - Evidenzia le implicazioni pratiche
   - Suggerisci possibili approfondimenti

Documento:
{pdf_text}"""
        
        if user_context:
            prompt += f"\n\n**IMPORTANTE**: Integra nel discorso anche le seguenti informazioni fornite dall'utente:\n\n{user_context}"
    else:
        prompt = f"""Analizza questo documento PDF e fornisci una descrizione dettagliata in italiano di ogni pagina.

Per ogni pagina del documento:
1. Indica chiaramente il numero di pagina
2. Descrivi in dettaglio il contenuto
3. Evidenzia le informazioni chiave e i punti principali
4. Mantieni la struttura e l'organizzazione del contenuto originale

Documento:
{pdf_text}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=8192
        )
        return response.choices[0].message.content
    
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return None

def create_zip_with_results(pdf_file, description_text, provider, model_name=None, mode="standard"):
    """Create a ZIP file containing the original PDF and the description"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        pdf_file.seek(0)
        zip_file.writestr(f"original_{pdf_file.name}", pdf_file.read())
        
        # Include model name and mode in the description filename
        mode_suffix = "_lezione" if mode == "discourse" else ""
        if model_name:
            description_filename = f"descrizione_{provider}_{model_name}{mode_suffix}_{pdf_file.name.replace('.pdf', '')}.txt"
        else:
            description_filename = f"descrizione_{provider}{mode_suffix}_{pdf_file.name.replace('.pdf', '')}.txt"
        
        zip_file.writestr(description_filename, description_text.encode('utf-8'))
    
    zip_buffer.seek(0)
    return zip_buffer

def calculate_tokens(num_pages):
    """Calculate token usage for native PDF processing"""
    # Base text tokens (1,500-3,000 per page)
    avg_tokens_per_page = 2250
    text_tokens = num_pages * avg_tokens_per_page
    
    # Image tokens (each page is also processed as an image)
    # Assuming ~1,600 tokens per page for image processing
    image_tokens_per_page = 1600
    image_tokens = num_pages * image_tokens_per_page
    
    # Total input tokens
    total_input_tokens = text_tokens + image_tokens
    
    # Output tokens (comprehensive description)
    output_tokens = min(8192, num_pages * 500)  # ~500 tokens per page description
    
    return {
        "input_tokens": total_input_tokens,
        "output_tokens": output_tokens,
        "text_tokens": text_tokens,
        "image_tokens": image_tokens
    }

# Streamlit UI
st.title("📄 PDF Descriptor with AI Vision")
st.markdown("Upload a PDF file to get a detailed Italian description using AI with vision")
st.markdown("Use your personal API key")

# Create tabs
tab1, tab2 = st.tabs(["📋 Standard Analysis", "🎓 Trainers assitant"])

# Shared components function
def render_analysis_ui(mode="standard"):
    # Provider selection
    provider = st.selectbox(
        "Select AI Provider",
        ["Anthropic (Native PDF)", "OpenAI"],
        help="Anthropic supports native PDF processing with vision capabilities",
        key=f"provider_{mode}"
    )

    # Model selection for Anthropic
    if provider == "Anthropic (Native PDF)":
        col1, col2 = st.columns([3, 1])
        with col1:
            model_choice = st.radio(
                "Select Claude Model",
                [
                    "Claude Sonnet 4 (Recommended)",
                    "Claude Opus 4 (Most Powerful)",
                    "Claude Sonnet 3.7",
                    "Claude 3.5 Sonnet",
                    "Claude 3.5 Haiku (Fastest & Cheapest)"
                ],
                help="All models support native PDF processing",
                key=f"model_{mode}"
            )
            
            # Model mapping
            model_map = {
                "Claude Sonnet 4 (Recommended)": "sonnet4",
                "Claude Opus 4 (Most Powerful)": "opus4",
                "Claude Sonnet 3.7": "sonnet3.7",
                "Claude 3.5 Sonnet": "sonnet3.5",
                "Claude 3.5 Haiku (Fastest & Cheapest)": "haiku3.5"
            }
            current_model = model_map[model_choice]
        
        with col2:
            st.markdown("### 💡 Model Tips")
            if "Haiku" in model_choice:
                st.success("Fastest & most economical option!")
            elif "Sonnet 4" in model_choice:
                st.info("Best balance of performance and cost")
            elif "Opus 4" in model_choice:
                st.warning("Most capable but expensive")

    # API Key input
    api_key = st.text_input(
        f"Enter your {provider.split(' ')[0]} API Key",
        type="password",
        help=f"Get your API key from {'https://console.anthropic.com' if 'Anthropic' in provider else 'https://platform.openai.com/api-keys'}",
        key=f"api_key_{mode}"
    )

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Maximum 32MB, up to 100 pages",
        key=f"file_{mode}"
    )

    # User context for discourse mode
    user_context = ""
    if mode == "discourse":
        st.markdown("### 📝 Additional Context (Optional)")
        user_context = st.text_area(
            "Add any additional information or context that should be integrated into the lesson",
            height=150,
            placeholder="Enter any additional notes, context, or information that should be incorporated into the technical lesson...",
            help="This text will be integrated organically into the lesson narrative"
        )

    # Validate and show file info
    if uploaded_file:
        # Check file size
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        pdf_text, num_pages = extract_text_from_pdf(uploaded_file)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("File Size", f"{file_size_mb:.1f} MB")
        with col2:
            st.metric("Pages", num_pages)
        
        if file_size_mb > 32:
            st.error("❌ File size exceeds 32MB limit. Please use a smaller PDF.")
        elif num_pages > 100:
            st.error("❌ PDF has more than 100 pages. Please split the document.")

    # Show token analysis
    if uploaded_file and api_key and provider == "Anthropic (Native PDF)" and file_size_mb <= 32 and num_pages <= 100:
        # Token calculation
        tokens = calculate_tokens(num_pages)
        
        st.markdown("### 📊 Token Analysis")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Input", f"{tokens['input_tokens']:,}")
        with col2:
            st.metric("Text Tokens", f"{tokens['text_tokens']:,}")
        with col3:
            st.metric("Image Tokens", f"{tokens['image_tokens']:,}")
        with col4:
            st.metric("Output Tokens", f"{tokens['output_tokens']:,}")
        
        with st.expander("📈 Detailed Token Breakdown"):
            st.write(f"**Text Processing:**")
            st.write(f"- Text tokens: {tokens['text_tokens']:,} (~{tokens['text_tokens']//num_pages:,} per page)")
            st.write(f"**Vision Processing:**")
            st.write(f"- Image tokens: {tokens['image_tokens']:,} (~{tokens['image_tokens']//num_pages:,} per page)")
            st.write(f"**Total:**")
            st.write(f"- Total input tokens: {tokens['input_tokens']:,}")
            st.write(f"- Expected output tokens: {tokens['output_tokens']:,}")

    # Process button
    button_text = "🎓 super power for trainers" if mode == "discourse" else "🚀 Analyze PDF"
    if st.button(button_text, type="primary", disabled=not (uploaded_file and api_key), key=f"analyze_{mode}"):
        if uploaded_file and api_key:
            model_name_for_file = None
            
            if provider == "Anthropic (Native PDF)":
                if file_size_mb > 32 or num_pages > 100:
                    st.error("Please upload a PDF that meets the requirements")
                else:
                    with st.spinner("Processing your PDF..."):
                        # Get description using direct base64 encoding
                        description = analyze_pdf_with_anthropic(
                            api_key, 
                            uploaded_file, 
                            model_choice=current_model,
                            mode=mode,
                            user_context=user_context
                        )
                        # Set model name for filename
                        model_name_for_file = current_model
            
            elif provider == "OpenAI":
                with st.spinner("Extracting and analyzing text..."):
                    pdf_text, num_pages = extract_text_from_pdf(uploaded_file)
                    
                    if pdf_text:
                        description = analyze_with_openai_text(
                            api_key, 
                            pdf_text,
                            mode=mode,
                            user_context=user_context
                        )
                        # Set model name for OpenAI
                        model_name_for_file = "gpt4o"
                    else:
                        st.error("Failed to extract text from PDF")
                        description = None
            
            if description:
                st.success("✅ Analysis complete!")
                
                # Show preview
                preview_title = "📚 Preview Lesson" if mode == "discourse" else "📋 Preview Description"
                with st.expander(f"{preview_title} (first 2000 characters)"):
                    st.text(description[:2000] + "..." if len(description) > 2000 else description)
                
                # Create download with model name
                uploaded_file.seek(0)
                zip_buffer = create_zip_with_results(
                    uploaded_file, 
                    description, 
                    provider.split(' ')[0],
                    model_name_for_file,
                    mode=mode
                )
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Include model name and mode in the ZIP filename
                mode_suffix = "_lesson" if mode == "discourse" else "_analysis"
                if model_name_for_file:
                    zip_filename = f"pdf_{mode_suffix}_{provider.split(' ')[0]}_{model_name_for_file}_{timestamp}.zip"
                else:
                    zip_filename = f"pdf_{mode_suffix}_{provider.split(' ')[0]}_{timestamp}.zip"
                
                st.download_button(
                    label="📥 Download Results (ZIP)",
                    data=zip_buffer,
                    file_name=zip_filename,
                    mime="application/zip"
                )

# Tab 1: Standard Analysis
with tab1:
    st.markdown("### 📋 Standard Page-by-Page Analysis")
    st.markdown("Get a detailed description of each page in your PDF document.")
    render_analysis_ui(mode="standard")

# Tab 2: Trainers assitant
with tab2:
    st.markdown("### 🎓 Trainers assitant")
    st.markdown("Transform your PDF into a comprehensive technical lesson with a discourse format, perfect for teaching or presentations.")
    st.info("💡 This mode creates a flowing narrative that explains the PDF content as a structured lesson, integrating all information into a cohesive educational discourse.")
    render_analysis_ui(mode="discourse")

# Instructions (shown at the bottom, outside tabs)
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    ### 🚀 Quick Start
    1. **Get API Key**: 
       - Anthropic: [Console](https://console.anthropic.com/settings/keys)
       - OpenAI: [Platform](https://platform.openai.com/api-keys)
    2. **Select Tab**:
       - **Standard Analysis**: Page-by-page detailed description
       - **Trainers assitant**: Discourse format for teaching
    3. **Choose Model**: 
       - Haiku 3.5: Fastest and cheapest
       - Sonnet 4: Best balance (recommended)
       - Opus 4: Most capable but expensive
    4. **Upload PDF**: Max 32MB, 100 pages
    5. **Add Context** (Lesson mode): Optional additional information to integrate
    6. **Click Analyze/Create**: Get your results
    
    ### 💡 Tips
    - **Standard Analysis** is best for documentation and reference
    - **Trainers assitant** is ideal for creating educational content
    - **Additional Context** in lesson mode helps create more comprehensive lectures
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 20px; color: #666;'>
        <p style='margin: 0;'>POC made with ❤️ - Digital Solutions and Platform</p>
    </div>
    """,
    unsafe_allow_html=True
)