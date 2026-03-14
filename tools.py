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
        InjectedToolArg
    ] = "general",
    search_depth: Annotated[
        Literal["advanced", "basic", "fast", "ultra-fast"],
    ] = "fast",
    ) -> str:
    """Search the web for information on a given query.

    Uses Tavily to discover relevant URLs, then fetches and returns full webpage content as markdown.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 3, max: 5)
        topic: Topic filter - 'general', 'news', or 'finance' (default: 'general')
        search_depth: Depth filter - 'advanced', 'basic', 'fast', 'ultra-fast' (default: 'fast')

    Returns:
        Formatted search results with full webpage content
    """
    tavily_client = _get_tavily_client()

    try:
        log.info(f"[RESEARCH AGENT] Executing tavily_search tool for {query}")

        sep = "\n"

        search_results = tavily_client.search(
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

            result_texts.append(result_text)
        
        response = f"""Found {len(result_texts)} result(s) for '{query}'\n\n {sep.join(result_texts)}"""

        return response
    except Exception as e:
        log.error(f"Failed to conduct a search on {query}: {e}", exc_info=True)
        raise

@tool(parse_docstring=True)
def tavily_extract(
    urls: List[str],
    query: str,
    extract_depth: Annotated[
        Literal["basic", "advanced"]
    ] = "basic",
    max_retries = 3,
    ) -> str:
    """Extract content from a single web page based on a given URL or list of URLs.

    Uses Tavily to extract relevant content 
    
    """
    try:
        extraction_results = tavily_client.extract(
            urls=urls,
            query=topic,
            extract_depth=extract_depth,
            max_retries=max_retries
        )

        title = extraction_results["title"]
        content = extraction_results.get("raw_content", "")

        result_text = f"""{title}
            **URL:** {urls}

            {content}

            ---
            """
        
        response = f"""Extracted content from {len(urls)} URLs for '{query}'

        {result_text}"""

        return response
    except Exception as e:
        log.error(f"Failed to extract from {url}: {e}", exc_info=True)
        raise



@tool(parse_docstring=True)
def tavily_crawl(
    query: str,
    max_retries = 3,
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[
        Literal["general", "news", "finance"],
        InjectedToolArg
    ] = "general",
    ) -> str:
    """"""
    search_results = tavily_client.search(
        query=query,
        max_results=max_results,
        topic=topic,
        max_retries=max_retries
    )

    results_texts = []

    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]
        content = search_results.get("content", "")

        result_text = f"""{title}
        **URL:** {url}

        {content}

        ---
        """

        result_texts.append(result_text)
    
    response = f"""Found {len(result_texts)} result(s) for '{query}'

    {result_text}"""

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