def merge_url_lists(file1, file2, output_file="merged_URL.txt", remove_duplicates=True):
    """
    Merge URLs from two files and save to output file.
    
    Args:
        file1: Path to the first URL file
        file2: Path to the second URL file
        output_file: Path to the output file (default: merged_URL.txt)
        remove_duplicates: Whether to remove duplicate URLs (default: True)
    """
    try:
        # Read URLs from first file
        with open(file1, encoding='utf-8') as f:
            urls1 = f.readlines()

        # Read URLs from second file
        with open(file2, encoding='utf-8') as f:
            urls2 = f.readlines()

        # Remove whitespace and empty lines
        urls1 = [url.strip() for url in urls1 if url.strip()]
        urls2 = [url.strip() for url in urls2 if url.strip()]

        # Merge the lists
        merged_urls = urls1 + urls2

        # Remove duplicates if requested
        if remove_duplicates:
            merged_urls = list(set(merged_urls))
            merged_urls.sort()  # Sort alphabetically

        # Save to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(merged_urls))

        print(f"✓ File 1: {len(urls1)} URLs")
        print(f"✓ File 2: {len(urls2)} URLs")
        print(f"✓ Total merged: {len(merged_urls)} URLs")
        if remove_duplicates:
            print(f"✓ Duplicates removed: {len(urls1) + len(urls2) - len(merged_urls)}")
        print(f"✓ Saved to: {output_file}")

        return merged_urls

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    # Change these to your desired input files
    file1 = "Firecrawl/agent_discovered_urls.txt"
    file2 = "Firecrawl/ngrok_endpoints.txt"

    # Merge URLs from both files
    merge_url_lists(file1, file2)
