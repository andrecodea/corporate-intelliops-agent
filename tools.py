""""""
import logging
from langchain_core.tools import InjectedToolArg, tool 
from tavily import TavilyClient
from typing_extensions import Annotated, Literal
from pydantic import Field

_client: TavilyClient | None = None 

def _get_tavily_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient()
    return _client

log = logging.getLogger(__name__)

@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, Field(default=3, ge=1, le=5)] = 3,
    topic: Annotated[
        Literal["general", "news", "finance"],
    ] = "general",
    search_depth: Annotated[
        Literal["advanced", "basic", "fast", "ultra-fast"],
    ] = "fast",
    ) -> str:
    """Search the web for information on a given query.

    Use this tool to gather general context, facts, or news on a topic.
    Prefer 'fast' for most queries. Use 'advanced' only for high-precision research (costs 2 credits).

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return. Default 3, max 5.
        topic: Category of the search. 'news' for real-time updates and current events. 'finance' for financial data. 'general' for broad searches.
        search_depth: Controls latency vs. relevance tradeoff. 'fast' returns multiple snippets with low latency (1 credit). 'ultra-fast' minimizes latency above all (1 credit). 'basic' is balanced (1 credit). 'advanced' returns highest relevance (2 credits).

    Returns:
        Formatted search results with title, URL, and content snippets
    """

    try:
        log.info(f"[RESEARCH AGENT] Executing tavily_search tool for {query}")

        sep = "\n"

        search_results = _get_tavily_client().search(
            query=query,
            max_results=max_results,
            topic=topic,
            search_depth=search_depth
        )

        results_texts = []

        for result in search_results.get("results", []):
            url = result["url"]
            title = result["title"]
            content = result.get("content", "")

            result_text = (
                f"{title}\n"
                f"**URL:** {url}\n"
                f"{content}\n\n"
                "---\n"
            )

            results_texts.append(result_text)
        
        response = f"""Found {len(results_texts)} result(s) for '{query}'\n\n {sep.join(results_texts)}"""

        return response
    except Exception as e:
        log.error(f"Failed to conduct a search on {query}: {e}", exc_info=True)
        raise

@tool(parse_docstring=True)
def tavily_extract(
    urls: list[str],
    query: str,
    extract_depth: Annotated[
        Literal["basic", "advanced"]
    ] = "basic",
    ) -> str:
    """Extract the full content from one or more web pages given their URLs.

    Use this tool when search snippets are insufficient and you need the complete content
    of a specific article, paper, blog post, or page. Always provide URLs obtained from
    a prior tavily_search call — do not guess URLs.

    Args:
        urls: List of URLs to extract content from
        query: Optional search intent used to rerank extracted content chunks by relevance
        extract_depth: Extraction depth. 'basic' costs 1 credit per 5 URLs. 'advanced' retrieves tables and embedded content at higher latency, costs 2 credits per 5 URLs.

    Returns:
        Full extracted content per URL, formatted as markdown
    """
    try:
        extraction_results = _get_tavily_client().extract(
            urls=urls,
            query=query,
            extract_depth=extract_depth,
        )

        results_texts = []

        for result in extraction_results["results"]:
            result_url = result["url"]
            title = result.get("title", result_url)
            content = result.get("raw_content", "")

            result_text = (
                f"{title}\n"
                f"**URL:** {result_url}\n"
                f"{content}\n\n"
                "---\n"
            )

            results_texts.append(result_text)
        
        response = f"""Extracted content from {len(urls)} URLs for '{query}'\n{"".join(results_texts)}"""

        return response
    except Exception as e:
        log.error(f"Failed to extract from {urls}: {e}", exc_info=True)
        raise

@tool(parse_docstring=True)
def tavily_crawl(
    url: str,
    instructions: str,
    max_depth: int = 3,
    limit: int  = 20,
    extract_depth: Annotated[
        Literal["basic", "advanced"],
        InjectedToolArg
    ] = "basic",
    ) -> str:
    """Crawl a website starting from a root URL, traversing multiple linked pages.

    Use this tool ONLY for multi-page sources such as official documentation, wikis, or
    structured knowledge bases. For single pages, use tavily_extract instead.
    Always provide a root URL obtained from a prior tavily_search call — do not guess URLs.

    Args:
        url: Root URL to begin the crawl from
        instructions: Natural language instructions to guide the crawler (e.g. 'Find all pages about checkpointing'). Increases cost to 2 credits per 10 pages.
        max_depth: How many link levels deep to crawl from the root URL. Default 3, max 5.
        limit: Total number of pages to process before stopping. Default 20.

    Returns:
        Crawled content per page, formatted as markdown
    """
    search_results = _get_tavily_client().crawl(
        url=url,
        instructions=instructions,
        max_depth=max_depth,
        limit=limit,
        extract_depth=extract_depth
    )

    results_texts = []

    for result in search_results.get("results", []):
        result_url = result["url"]
        title = result.get("title", result_url)
        content = result.get("raw_content", "")

        result_text = (
            f"{title}\n"
            f"**URL:** {result_url}\n"
            f"{content}\n\n"
            "---\n"
        )

        results_texts.append(result_text)
    
    response = f"""Crawled through {url} and got {len(results_texts)} results\n{"".join(results_texts)}"""

    return response

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each tool use to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving tool results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing gaps: What specific information am I still missing?
    - Before concluding: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"