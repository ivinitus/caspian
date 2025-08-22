from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List, Optional, Any
import chardet
import PyPDF2
import io
import docx
import csv
import traceback
import sys

from app.db.models import Document, SessionLocal, User
from app.rag import get_embedding

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/extract-content")
async def extract_file_content(
    file: UploadFile = File(...),
):
    """
    Extract text content from a file without processing or storing it.
    This is a diagnostic endpoint to help with file format issues.
    """
    try:
        # Read file content as bytes first
        file_bytes = await file.read()
        
        # Process different file types appropriately
        file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        # Extract content based on file type
        if file_extension == 'pdf':
            content = extract_text_from_pdf(file_bytes)
        elif file_extension in ['doc', 'docx']:
            content = extract_text_from_docx(file_bytes)
        elif file_extension == 'csv':
            content = extract_text_from_csv(file_bytes)
        else:
            # For text files, detect encoding
            encoding_result = chardet.detect(file_bytes)
            encoding = encoding_result['encoding'] or 'utf-8'
            confidence = encoding_result.get('confidence', 0)
            
            try:
                content = file_bytes.decode(encoding)
            except UnicodeDecodeError:
                content = file_bytes.decode(encoding, errors='replace')
        
        # Return the extracted content and file information
        return {
            "filename": file.filename,
            "file_type": file_extension,
            "file_size": len(file_bytes),
            "content_length": len(content) if content else 0,
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "encoding_info": chardet.detect(file_bytes)
        }
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "filename": file.filename if file else "unknown",
            "file_extension": file_extension if 'file_extension' in locals() else "unknown"
        }
        print(f"Error in extract_file_content: {error_details}")
        raise HTTPException(status_code=500, detail=str(error_details))


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    async with SessionLocal() as db:
        try:
            # Read file content as bytes first
            file_bytes = await file.read()
            
            # Process different file types appropriately
            file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
            content = ""
            
            try:
                # PDF files
                if file_extension == 'pdf':
                    content = extract_text_from_pdf(file_bytes)
                    if not content:
                        raise ValueError("Failed to extract text from PDF file")
                
                # Word documents
                elif file_extension in ['doc', 'docx']:
                    content = extract_text_from_docx(file_bytes)
                    if not content:
                        raise ValueError("Failed to extract text from Word document")
                
                # CSV files
                elif file_extension == 'csv':
                    content = extract_text_from_csv(file_bytes)
                    if not content:
                        raise ValueError("Failed to extract text from CSV file")
                
                # Plain text files
                elif file_extension in ['txt', 'md', 'text', 'markdown', 'rst', 'rtf', 'tex', 'log']:
                    # For text files, detect encoding
                    encoding_result = chardet.detect(file_bytes)
                    print(f"Detected encoding for {file_extension} file: {encoding_result}")
                    encoding = encoding_result['encoding'] or 'utf-8'
                    
                    try:
                        content = file_bytes.decode(encoding)
                    except UnicodeDecodeError as e:
                        print(f"Initial decode failed with {encoding}: {e}")
                        # If still can't decode, try with errors='replace'
                        content = file_bytes.decode(encoding, errors='replace')
                
                # JSON, XML, HTML and other structured text files
                elif file_extension in ['json', 'xml', 'html', 'htm', 'yaml', 'yml', 'toml', 'ini', 'cfg']:
                    # Try to detect encoding
                    encoding_result = chardet.detect(file_bytes)
                    print(f"Detected encoding for {file_extension} file: {encoding_result}")
                    encoding = encoding_result['encoding'] or 'utf-8'
                    
                    try:
                        content = file_bytes.decode(encoding)
                    except UnicodeDecodeError:
                        content = file_bytes.decode(encoding, errors='replace')
                
                # For other file types, attempt text extraction with encoding detection
                else:
                    print(f"Attempting to extract text from unknown file type: {file_extension}")
                    # For unknown files, detect encoding
                    encoding_result = chardet.detect(file_bytes)
                    print(f"Detected encoding for unknown file: {encoding_result}")
                    encoding = encoding_result['encoding'] or 'utf-8'
                    
                    try:
                        content = file_bytes.decode(encoding)
                    except UnicodeDecodeError as e:
                        print(f"Initial decode failed with {encoding}: {e}")
                        # If still can't decode, try with errors='replace'
                        content = file_bytes.decode(encoding, errors='replace')
                        
                    # If we still couldn't get meaningful content, let the user know
                    if not content.strip() or content.strip().count('\ufffd') > len(content.strip()) / 3:
                        print("Too many replacement characters, file is likely binary")
                        raise ValueError(f"The file type '{file_extension}' appears to be binary and cannot be processed. Please upload a text-based file.")
            except Exception as process_error:
                print(f"Error processing file {file.filename}: {process_error}")
                raise HTTPException(status_code=400, detail=f"File processing error: {str(process_error)}")

            # If no content was extracted, return an appropriate error
            if not content or not content.strip():
                raise HTTPException(status_code=400, detail="Could not extract any text from the file. Please check if the file contains readable text or try a different file format.")

            print(f"Successfully extracted {len(content)} characters from {file.filename}")
            
            # Split content into chunks
            chunks = [p.strip() for p in content.split("\n\n") if p.strip()]

            # If no chunks were created, create one with the whole content
            if not chunks and content.strip():
                chunks = [content.strip()]
                
            if not chunks:
                raise HTTPException(status_code=400, detail="No text chunks could be created from the file.")

            print(f"Created {len(chunks)} chunks from the file")
            
            for chunk in chunks:
                embedding = get_embedding(chunk)
                doc = Document(
                    content=chunk, embedding=embedding
                )
                db.add(doc)
            await db.commit()

            return {"filename": file.filename, "chunks_added": len(chunks)}
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            print(f"Error in upload_document: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e


def extract_text_from_pdf(file_bytes):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                else:
                    print(f"Warning: Empty text extracted from page {page_num+1}")
            except Exception as page_error:
                print(f"Error extracting text from page {page_num+1}: {page_error}")
        
        if not text.strip():
            print("Warning: No text could be extracted from the PDF")
        
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_docx(file_bytes):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = ""
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
        
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text:
                        row_text.append(cell.text.strip())
                if row_text:
                    text += " | ".join(row_text) + "\n"
        
        if not text.strip():
            print("Warning: No text could be extracted from the DOCX")
            
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""


def extract_text_from_csv(file_bytes):
    """Extract text from CSV file"""
    try:
        text = ""
        # Try to detect encoding
        encoding_result = chardet.detect(file_bytes)
        print(f"CSV detected encoding: {encoding_result}")
        encoding = encoding_result['encoding'] or 'utf-8'
        
        # Try multiple delimiters if needed
        delimiters = [',', ';', '\t', '|']
        csv_file = io.StringIO(file_bytes.decode(encoding, errors='replace'))
        
        # First try to sniff the dialect
        try:
            dialect = csv.Sniffer().sniff(csv_file.read(1024))
            csv_file.seek(0)
            csv_reader = csv.reader(csv_file, dialect)
            delimiter_used = dialect.delimiter
        except:
            # If sniffing fails, reset and try with comma as default
            csv_file.seek(0)
            csv_reader = csv.reader(csv_file)
            delimiter_used = ','
        
        row_count = 0
        max_columns = 0
        
        # Create a list to store rows for tabular formatting
        rows = []
        
        for row in csv_reader:
            if any(cell.strip() for cell in row):  # Skip empty rows
                rows.append(row)
                max_columns = max(max_columns, len(row))
                row_count += 1
        
        # If we found rows, format them nicely
        if rows:
            # If first row looks like headers (shorter than other rows or all non-numeric), treat it specially
            headers = rows[0] if rows else []
            has_headers = False
            
            if len(rows) > 1:
                # Check if first row might be headers
                if all(not cell.strip().replace('.', '').replace('-', '').isdigit() for cell in headers if cell.strip()):
                    has_headers = True
            
            # Format as a table with header row if appropriate
            if has_headers:
                # Add header row
                text += " | ".join(headers) + "\n"
                text += "-" * 40 + "\n"  # Separator line
                
                # Add data rows
                for row in rows[1:]:
                    # Pad row to match max columns
                    padded_row = row + [''] * (max_columns - len(row))
                    text += " | ".join(padded_row) + "\n"
            else:
                # No headers, just add all rows
                for row in rows:
                    padded_row = row + [''] * (max_columns - len(row))
                    text += " | ".join(padded_row) + "\n"
        
        print(f"Processed {row_count} rows from CSV with delimiter '{delimiter_used}'")
        
        if not text.strip():
            print("Warning: No text could be extracted from the CSV")
            
        return text
    except Exception as e:
        print(f"Error extracting text from CSV: {e}")
        return ""