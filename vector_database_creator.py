import os
from langchain.embeddings.ollama import OllamaEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma



def create_vector_database(persist_directory,collection_name,pdf_path):
    

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"    # use the ollama run nomic-embed-text the first time you run this code
    )

    #pdf_path = r"include_path"

    # Ensure the PDF file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pdf_loader = PyPDFLoader(pdf_path) # This loads the PDF

    try:
        pages = pdf_loader.load()
        print(f"PDF has been loaded and has {len(pages)} pages")
    except Exception as e:
        print(f"Error loading PDF: {e}")
        raise


    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )


    pages_split = text_splitter.split_documents(pages) 

    pages_split = text_splitter.split_documents(pages) # We now apply this to our pages

    #persist_directory = r"include path"  # Update this path accordingly
    #collection_name = "name_of_your_collection"  # Update this accordingly

    # If our collection does not exist in the directory, we create using the os command
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)

    try:
        # Here, we actually create the chroma database using our embeddigns model
        vectorstore = Chroma.from_documents(
            documents=pages_split,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        print(f"Created ChromaDB vector store!")
        
    except Exception as e:
        print(f"Error setting up ChromaDB: {str(e)}")
        raise

    return vectorstore