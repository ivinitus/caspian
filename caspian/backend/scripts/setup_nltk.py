"""
Setup script for downloading required NLTK data.
"""
import nltk

def download_nltk_data():
    """Download required NLTK data packages."""
    required_packages = [
        'punkt',  # For sentence tokenization
        'averaged_perceptron_tagger',  # For POS tagging
        'stopwords',  # Common stopwords
    ]
    
    for package in required_packages:
        print(f"Downloading {package}...")
        nltk.download(package)
        print(f"Successfully downloaded {package}")

if __name__ == "__main__":
    print("Downloading required NLTK data...")
    download_nltk_data()
    print("NLTK setup complete!")
