#!/usr/bin/env python3
"""
Simple test script to debug the chunking function
"""

def chunk_text(text: str, chunk_size: int = 256, overlap: int = 25) -> list:
    """
    Split text into overlapping chunks
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        # If we're near the end, just take the remainder
        if end > text_len:
            end = text_len

        chunk = text[start:end]
        chunks.append(chunk)

        # Move start position by chunk_size minus overlap
        # If this would not advance the position (end - overlap <= start), advance by 1 to avoid infinite loop
        next_start = end - overlap
        if next_start <= start:
            start = start + 1
        else:
            start = next_start

    # Debug: print how many chunks were created
    print(f"  Chunked text of length {text_len} into {len(chunks)} chunks (chunk_size={chunk_size}, overlap={overlap})")

    return chunks

# Test with a sample text similar to what we expect
sample_text = "This is a sample text for testing the chunking function. " * 70  # About 3,500 characters
print(f"Testing with text length: {len(sample_text)}")

try:
    chunks = chunk_text(sample_text)
    print(f"Successfully created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):  # Print first 3 chunks as examples
        print(f"Chunk {i+1}: '{chunk[:50]}...' (length: {len(chunk)})")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()