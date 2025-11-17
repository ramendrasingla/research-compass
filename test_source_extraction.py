"""Test script to verify source extraction from tool outputs."""

import sys
sys.path.insert(0, 'research_compass_core/src')

from research_compass_core.utils import _parse_arxiv_sources, _parse_semantic_scholar_sources

# Sample ArXiv output (matches the format from arxiv_tools.py)
arxiv_sample = """Found 2 arXiv papers:

--- PAPER 1: Attention Is All You Need ---
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar
Published: 2017-06-12 (Updated: 2017-06-12)
Category: cs.CL
URL: http://arxiv.org/abs/1706.03762v5
PDF: http://arxiv.org/pdf/1706.03762v5

ABSTRACT:
The dominant sequence transduction models are based on complex recurrent or
convolutional neural networks in an encoder-decoder configuration.

SEARCH QUERY: transformers deep learning
--------------------------------------------------------------------------------

--- PAPER 2: BERT: Pre-training of Deep Bidirectional Transformers ---
Authors: Jacob Devlin, Ming-Wei Chang, Kenton Lee
Published: 2018-10-11 (Updated: 2019-05-24)
Category: cs.CL
URL: http://arxiv.org/abs/1810.04805v2
PDF: http://arxiv.org/pdf/1810.04805v2

ABSTRACT:
We introduce a new language representation model called BERT, which stands for
Bidirectional Encoder Representations from Transformers.

SEARCH QUERY: transformers deep learning
--------------------------------------------------------------------------------
"""

# Sample Semantic Scholar output (matches the format from semantic_scholar_tools.py)
semantic_scholar_sample = """Found 2 papers on Semantic Scholar:

--- PAPER 1: Deep Residual Learning for Image Recognition ---
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren
Year: 2016 | Venue: CVPR
Citations: 95842
Fields: Computer Vision, Deep Learning
URL: https://www.semanticscholar.org/paper/2c03df8b48bf3fa39054345bafabfeff15bfd11d
PDF: https://arxiv.org/pdf/1512.03385.pdf

ABSTRACT:
Deeper neural networks are more difficult to train. We present a residual learning
framework to ease the training of networks that are substantially deeper.

SEARCH QUERY: deep learning computer vision
PAPER ID: 2c03df8b48bf3fa39054345bafabfeff15bfd11d
--------------------------------------------------------------------------------

--- PAPER 2: ImageNet Classification with Deep Convolutional Neural Networks ---
Authors: Alex Krizhevsky, Ilya Sutskever, Geoffrey E. Hinton
Year: 2012 | Venue: NIPS
Citations: 78542
URL: https://www.semanticscholar.org/paper/abd1c342495432171beb7ca8fd9551ef13cbd0ff

ABSTRACT:
We trained a large, deep convolutional neural network to classify the 1.2 million
high-resolution images in the ImageNet LSVRC-2010 contest.

SEARCH QUERY: deep learning computer vision
PAPER ID: abd1c342495432171beb7ca8fd9551ef13cbd0ff
--------------------------------------------------------------------------------
"""

def test_arxiv_parsing():
    """Test ArXiv source parsing."""
    print("=" * 80)
    print("Testing ArXiv Parsing")
    print("=" * 80)

    seen_urls = set()
    sources = _parse_arxiv_sources(arxiv_sample, seen_urls)

    print(f"\nExtracted {len(sources)} ArXiv sources")
    for i, source in enumerate(sources, 1):
        print(f"\nSource {i}:")
        print(f"  Title: {source.title}")
        print(f"  Authors: {', '.join(source.authors)}")
        print(f"  URL: {source.url}")
        print(f"  PDF: {source.pdf_url}")
        print(f"  Published: {source.published_date}")
        print(f"  API: {source.search_api}")

    return len(sources) == 2

def test_semantic_scholar_parsing():
    """Test Semantic Scholar source parsing."""
    print("\n" + "=" * 80)
    print("Testing Semantic Scholar Parsing")
    print("=" * 80)

    seen_urls = set()
    sources = _parse_semantic_scholar_sources(semantic_scholar_sample, seen_urls)

    print(f"\nExtracted {len(sources)} Semantic Scholar sources")
    for i, source in enumerate(sources, 1):
        print(f"\nSource {i}:")
        print(f"  Title: {source.title}")
        print(f"  Authors: {', '.join(source.authors)}")
        print(f"  URL: {source.url}")
        print(f"  PDF: {source.pdf_url}")
        print(f"  Year: {source.published_date}")
        print(f"  Citations: {source.citation_count}")
        print(f"  Venue: {source.venue}")
        print(f"  API: {source.search_api}")

    return len(sources) == 2

if __name__ == "__main__":
    print("Testing Source Extraction Parsers\n")

    arxiv_pass = test_arxiv_parsing()
    ss_pass = test_semantic_scholar_parsing()

    print("\n" + "=" * 80)
    print("Test Results")
    print("=" * 80)
    print(f"ArXiv Parsing: {'✅ PASS' if arxiv_pass else '❌ FAIL'}")
    print(f"Semantic Scholar Parsing: {'✅ PASS' if ss_pass else '❌ FAIL'}")

    if arxiv_pass and ss_pass:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
