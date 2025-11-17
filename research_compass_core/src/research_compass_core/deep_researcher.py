"""Main LangGraph implementation for the Deep Research agent."""

import asyncio
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    filter_messages,
    get_buffer_string,
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from research_compass_core.configuration import (
    Configuration,
)
from research_compass_core.prompts import (
    clarify_with_user_instructions,
    compress_research_simple_human_message,
    compress_research_system_prompt,
    final_report_generation_prompt,
    lead_researcher_prompt,
    research_system_prompt,
    transform_messages_into_research_topic_prompt,
)
from research_compass_core.state import (
    AgentInputState,
    AgentState,
    ClarifyWithUser,
    ConductResearch,
    ResearchComplete,
    ResearcherOutputState,
    ResearcherState,
    ResearchQuestion,
    SupervisorState,
)
from research_compass_core.utils import (
    get_all_tools,
    get_api_key_for_model,
    get_model_token_limit,
    get_notes_from_tool_calls,
    get_today_str,
    is_token_limit_exceeded,
    openai_websearch_called,
    remove_up_to_last_ai_message,
    think_tool,
)

# Initialize a configurable model that we will use throughout the agent
configurable_model = init_chat_model(
    configurable_fields=("model", "max_tokens", "api_key"),
)

async def clarify_with_user(state: AgentState, config: RunnableConfig) -> Command[Literal["write_research_brief", "__end__"]]:
    """Analyze user messages and ask clarifying questions if the research scope is unclear.
    
    This function determines whether the user's request needs clarification before proceeding
    with research. If clarification is disabled or not needed, it proceeds directly to research.
    
    Args:
        state: Current agent state containing user messages
        config: Runtime configuration with model settings and preferences
        
    Returns:
        Command to either end with a clarifying question or proceed to research brief
    """
    # Step 1: Check if clarification is enabled in configuration
    configurable = Configuration.from_runnable_config(config)
    if not configurable.allow_clarification:
        # Skip clarification step and proceed directly to research
        return Command(goto="write_research_brief")
    
    # Step 2: Prepare the model for structured clarification analysis
    messages = state["messages"]
    model_config = {
        "model": configurable.research_model,
        "max_tokens": configurable.research_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.research_model, config),
        "tags": ["langsmith:nostream"]
    }
    
    # Configure model with structured output and retry logic
    clarification_model = (
        configurable_model
        .with_structured_output(ClarifyWithUser)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        .with_config(model_config)
    )
    
    # Step 3: Analyze whether clarification is needed
    prompt_content = clarify_with_user_instructions.format(
        messages=get_buffer_string(messages), 
        date=get_today_str()
    )
    response = await clarification_model.ainvoke([HumanMessage(content=prompt_content)])
    
    # Step 4: Route based on clarification analysis
    if response.need_clarification:
        # End with clarifying question for user
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )
    else:
        # Proceed to research with verification message
        return Command(
            goto="write_research_brief", 
            update={"messages": [AIMessage(content=response.verification)]}
        )


async def write_research_brief(state: AgentState, config: RunnableConfig) -> Command[Literal["research_supervisor"]]:
    """Transform user messages into a structured research brief and initialize supervisor.
    
    This function analyzes the user's messages and generates a focused research brief
    that will guide the research supervisor. It also sets up the initial supervisor
    context with appropriate prompts and instructions.
    
    Args:
        state: Current agent state containing user messages
        config: Runtime configuration with model settings
        
    Returns:
        Command to proceed to research supervisor with initialized context
    """
    # Step 1: Set up the research model for structured output
    configurable = Configuration.from_runnable_config(config)
    research_model_config = {
        "model": configurable.research_model,
        "max_tokens": configurable.research_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.research_model, config),
        "tags": ["langsmith:nostream"]
    }
    
    # Configure model for structured research question generation
    research_model = (
        configurable_model
        .with_structured_output(ResearchQuestion)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        .with_config(research_model_config)
    )
    
    # Step 2: Generate structured research brief from user messages
    prompt_content = transform_messages_into_research_topic_prompt.format(
        messages=get_buffer_string(state.get("messages", [])),
        date=get_today_str()
    )
    response = await research_model.ainvoke([HumanMessage(content=prompt_content)])
    
    # Step 3: Initialize supervisor with research brief and instructions
    supervisor_system_prompt = lead_researcher_prompt.format(
        date=get_today_str(),
        max_concurrent_research_units=configurable.max_concurrent_research_units,
        max_researcher_iterations=configurable.max_researcher_iterations
    )
    
    return Command(
        goto="research_supervisor", 
        update={
            "research_brief": response.research_brief,
            "supervisor_messages": {
                "type": "override",
                "value": [
                    SystemMessage(content=supervisor_system_prompt),
                    HumanMessage(content=response.research_brief)
                ]
            }
        }
    )


async def supervisor(state: SupervisorState, config: RunnableConfig) -> Command[Literal["supervisor_tools"]]:
    """Lead research supervisor that plans research strategy and delegates to researchers.
    
    The supervisor analyzes the research brief and decides how to break down the research
    into manageable tasks. It can use think_tool for strategic planning, ConductResearch
    to delegate tasks to sub-researchers, or ResearchComplete when satisfied with findings.
    
    Args:
        state: Current supervisor state with messages and research context
        config: Runtime configuration with model settings
        
    Returns:
        Command to proceed to supervisor_tools for tool execution
    """
    # Step 1: Configure the supervisor model with available tools
    configurable = Configuration.from_runnable_config(config)
    research_model_config = {
        "model": configurable.research_model,
        "max_tokens": configurable.research_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.research_model, config),
        "tags": ["langsmith:nostream"]
    }
    
    # Available tools: research delegation, completion signaling, and strategic thinking
    lead_researcher_tools = [ConductResearch, ResearchComplete, think_tool]
    
    # Configure model with tools, retry logic, and model settings
    research_model = (
        configurable_model
        .bind_tools(lead_researcher_tools)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        .with_config(research_model_config)
    )
    
    # Step 2: Generate supervisor response based on current context
    supervisor_messages = state.get("supervisor_messages", [])
    response = await research_model.ainvoke(supervisor_messages)
    
    # Step 3: Update state and proceed to tool execution
    return Command(
        goto="supervisor_tools",
        update={
            "supervisor_messages": [response],
            "research_iterations": state.get("research_iterations", 0) + 1
        }
    )

async def supervisor_tools(state: SupervisorState, config: RunnableConfig) -> Command[Literal["supervisor", "__end__"]]:
    """Execute tools called by the supervisor, including research delegation and strategic thinking.
    
    This function handles three types of supervisor tool calls:
    1. think_tool - Strategic reflection that continues the conversation
    2. ConductResearch - Delegates research tasks to sub-researchers
    3. ResearchComplete - Signals completion of research phase
    
    Args:
        state: Current supervisor state with messages and iteration count
        config: Runtime configuration with research limits and model settings
        
    Returns:
        Command to either continue supervision loop or end research phase
    """
    print("\n" + "="*80)
    print("🎯 SUPERVISOR_TOOLS CALLED!")
    print("="*80)

    # Step 1: Extract current state and check exit conditions
    configurable = Configuration.from_runnable_config(config)
    supervisor_messages = state.get("supervisor_messages", [])
    research_iterations = state.get("research_iterations", 0)
    most_recent_message = supervisor_messages[-1]

    # Debug: Print tool calls
    tool_call_names = [tc["name"] for tc in most_recent_message.tool_calls] if most_recent_message.tool_calls else []
    print(f"🔍 Tool calls made: {tool_call_names}")
    print(f"🔍 Research iteration: {research_iterations}/{configurable.max_researcher_iterations}")

    # Define exit criteria for research phase
    exceeded_allowed_iterations = research_iterations > configurable.max_researcher_iterations
    no_tool_calls = not most_recent_message.tool_calls
    research_complete_tool_call = any(
        tool_call["name"] == "ResearchComplete"
        for tool_call in most_recent_message.tool_calls
    )

    print(f"🔍 Exit conditions:")
    print(f"   - exceeded_iterations: {exceeded_allowed_iterations}")
    print(f"   - no_tool_calls: {no_tool_calls}")
    print(f"   - research_complete: {research_complete_tool_call}")

    # Exit if any termination condition is met
    if exceeded_allowed_iterations or no_tool_calls or research_complete_tool_call:
        print(f"⚠️  EXITING EARLY - Research complete")
        print("="*80 + "\n")
        return Command(
            goto=END,
            update={
                "notes": get_notes_from_tool_calls(supervisor_messages),
                "research_brief": state.get("research_brief", "")
            }
        )
    
    # Step 2: Process all tool calls together (both think_tool and ConductResearch)
    all_tool_messages = []
    update_payload = {"supervisor_messages": []}
    
    # Handle think_tool calls (strategic reflection)
    think_tool_calls = [
        tool_call for tool_call in most_recent_message.tool_calls 
        if tool_call["name"] == "think_tool"
    ]
    
    for tool_call in think_tool_calls:
        reflection_content = tool_call["args"]["reflection"]
        all_tool_messages.append(ToolMessage(
            content=f"Reflection recorded: {reflection_content}",
            name="think_tool",
            tool_call_id=tool_call["id"]
        ))
    
    # Handle ConductResearch calls (research delegation)
    conduct_research_calls = [
        tool_call for tool_call in most_recent_message.tool_calls
        if tool_call["name"] == "ConductResearch"
    ]

    print(f"🔍 Found {len(conduct_research_calls)} ConductResearch calls")

    if conduct_research_calls:
        print(f"✅ EXECUTING RESEARCH DELEGATION - Creating {len(conduct_research_calls)} researchers")
        try:
            # Limit concurrent research units to prevent resource exhaustion
            allowed_conduct_research_calls = conduct_research_calls[:configurable.max_concurrent_research_units]
            overflow_conduct_research_calls = conduct_research_calls[configurable.max_concurrent_research_units:]
            
            # Execute research tasks in parallel
            research_tasks = [
                researcher_subgraph.ainvoke({
                    "researcher_messages": [
                        HumanMessage(content=tool_call["args"]["research_topic"])
                    ],
                    "research_topic": tool_call["args"]["research_topic"]
                }, config) 
                for tool_call in allowed_conduct_research_calls
            ]

            print(f"⏳ Waiting for {len(research_tasks)} researchers to complete...")
            try:
                tool_results = await asyncio.gather(*research_tasks, return_exceptions=True)
                print(f"✅ All researchers completed! Got {len(tool_results)} results")

                # Check for exceptions in results
                successful_count = 0
                failed_count = 0
                for i, result in enumerate(tool_results):
                    if isinstance(result, Exception):
                        print(f"❌ Researcher {i+1} FAILED with exception: {type(result).__name__}: {str(result)}")
                        failed_count += 1
                    else:
                        print(f"✅ Researcher {i+1} succeeded")
                        successful_count += 1

                # If ALL researchers failed, abort the research process
                if successful_count == 0 and failed_count > 0:
                    print(f"\n❌ CRITICAL: All {failed_count} researchers failed!")
                    print(f"❌ Cannot generate report without any successful research.")
                    print(f"❌ Aborting research process.\n")
                    # Store error information in state
                    error_messages = []
                    for i, result in enumerate(tool_results):
                        if isinstance(result, Exception):
                            error_messages.append(f"Researcher {i+1}: {type(result).__name__}: {str(result)}")

                    return Command(
                        goto=END,
                        update={
                            "supervisor_messages": all_tool_messages,
                            "research_failed": True,
                            "research_error": f"All researchers failed. Errors: {'; '.join(error_messages)}"
                        }
                    )
            except Exception as e:
                print(f"❌ CRITICAL ERROR waiting for researchers: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                raise

            # Debug: Check what's in the results
            for i, result in enumerate(tool_results):
                if not isinstance(result, Exception):
                    print(f"   Researcher {i+1} result keys: {list(result.keys())}")
                    print(f"   Researcher {i+1} has 'sources' key: {'sources' in result}")
                    if 'sources' in result:
                        print(f"   Researcher {i+1} sources count: {len(result.get('sources', []))}")

            # Create tool messages with research results
            for observation, tool_call in zip(tool_results, allowed_conduct_research_calls):
                if isinstance(observation, Exception):
                    content = f"Research failed with error: {type(observation).__name__}: {str(observation)}"
                else:
                    content = observation.get("compressed_research", "Error synthesizing research report: Maximum retries exceeded")

                all_tool_messages.append(ToolMessage(
                    content=content,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                ))
            
            # Handle overflow research calls with error messages
            for overflow_call in overflow_conduct_research_calls:
                all_tool_messages.append(ToolMessage(
                    content=f"Error: Did not run this research as you have already exceeded the maximum number of concurrent research units. Please try again with {configurable.max_concurrent_research_units} or fewer research units.",
                    name="ConductResearch",
                    tool_call_id=overflow_call["id"]
                ))
            
            # Aggregate raw notes from all research results (skip exceptions)
            raw_notes_concat = "\n".join([
                "\n".join(observation.get("raw_notes", []))
                for observation in tool_results
                if not isinstance(observation, Exception)
            ])

            if raw_notes_concat:
                update_payload["raw_notes"] = [raw_notes_concat]

            # Aggregate sources from all research results
            all_sources = []
            print(f"\n🔗 SUPERVISOR: Aggregating sources from {len(tool_results)} researchers")
            for i, observation in enumerate(tool_results):
                if isinstance(observation, Exception):
                    print(f"🔗 SUPERVISOR: Researcher {i+1} SKIPPED (exception)")
                    continue

                sources = observation.get("sources", [])
                print(f"🔗 SUPERVISOR: Researcher {i+1} has {len(sources)} sources")
                if sources:
                    all_sources.extend(sources)

            # Debug logging
            import logging
            print(f"🔗 SUPERVISOR: Total aggregated sources: {len(all_sources)}")
            logging.info(f"Supervisor aggregated {len(all_sources)} sources from {len(tool_results)} researchers")
            if all_sources:
                print(f"🔗 SUPERVISOR: First source: {all_sources[0].title if hasattr(all_sources[0], 'title') else all_sources[0]}")
                logging.info(f"First aggregated source: {all_sources[0].title if hasattr(all_sources[0], 'title') else all_sources[0]}")

            if all_sources:
                print(f"🔗 SUPERVISOR: Adding {len(all_sources)} sources to state update")
                update_payload["sources"] = all_sources
                
        except Exception as e:
            # Handle research execution errors
            if is_token_limit_exceeded(e, configurable.research_model) or True:
                # Token limit exceeded or other error - end research phase
                return Command(
                    goto=END,
                    update={
                        "notes": get_notes_from_tool_calls(supervisor_messages),
                        "research_brief": state.get("research_brief", "")
                    }
                )
    
    # Step 3: Return command with all tool results
    update_payload["supervisor_messages"] = all_tool_messages
    return Command(
        goto="supervisor",
        update=update_payload
    ) 

# Supervisor Subgraph Construction
# Creates the supervisor workflow that manages research delegation and coordination
supervisor_builder = StateGraph(SupervisorState, config_schema=Configuration)

# Add supervisor nodes for research management
supervisor_builder.add_node("supervisor", supervisor)           # Main supervisor logic
supervisor_builder.add_node("supervisor_tools", supervisor_tools)  # Tool execution handler

# Define supervisor workflow edges
supervisor_builder.add_edge(START, "supervisor")  # Entry point to supervisor

# Compile supervisor subgraph for use in main workflow
supervisor_subgraph = supervisor_builder.compile()

async def researcher(state: ResearcherState, config: RunnableConfig) -> Command[Literal["researcher_tools"]]:
    """Individual researcher that conducts focused research on specific topics.
    
    This researcher is given a specific research topic by the supervisor and uses
    available tools (search, think_tool, MCP tools) to gather comprehensive information.
    It can use think_tool for strategic planning between searches.
    
    Args:
        state: Current researcher state with messages and topic context
        config: Runtime configuration with model settings and tool availability
        
    Returns:
        Command to proceed to researcher_tools for tool execution
    """
    print(f"\n👨‍🔬 RESEARCHER NODE CALLED for topic: {state.get('research_topic', 'Unknown')[:50]}")

    # Step 1: Load configuration and validate tool availability
    configurable = Configuration.from_runnable_config(config)
    researcher_messages = state.get("researcher_messages", [])
    
    # Get all available research tools (search, MCP, think_tool)
    tools = await get_all_tools(config)
    if len(tools) == 0:
        raise ValueError(
            "No tools found to conduct research: Please configure either your "
            "search API or add MCP tools to your configuration."
        )
    
    # Step 2: Configure the researcher model with tools
    research_model_config = {
        "model": configurable.research_model,
        "max_tokens": configurable.research_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.research_model, config),
        "tags": ["langsmith:nostream"]
    }
    
    # Prepare system prompt
    researcher_prompt = research_system_prompt.format(
        date=get_today_str()
    )
    
    # Configure model with tools, retry logic, and settings
    research_model = (
        configurable_model
        .bind_tools(tools)
        .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
        .with_config(research_model_config)
    )
    
    # Step 3: Generate researcher response with system context
    messages = [SystemMessage(content=researcher_prompt)] + researcher_messages
    response = await research_model.ainvoke(messages)
    
    # Step 4: Update state and proceed to tool execution
    # Only increment iteration count for actual search/action tools, not think_tool
    tool_calls = response.tool_calls if hasattr(response, 'tool_calls') else []
    has_non_think_tools = any(call["name"] != "think_tool" for call in tool_calls) if tool_calls else False
    iteration_increment = 1 if has_non_think_tools else 0

    return Command(
        goto="researcher_tools",
        update={
            "researcher_messages": [response],
            "tool_call_iterations": state.get("tool_call_iterations", 0) + iteration_increment
        }
    )

# Tool Execution Helper Function
async def execute_tool_safely(tool, args, config):
    """Safely execute a tool with error handling."""
    try:
        return await tool.ainvoke(args, config)
    except Exception as e:
        return f"Error executing tool: {str(e)}"


async def researcher_tools(state: ResearcherState, config: RunnableConfig) -> Command[Literal["researcher", "compress_research"]]:
    """Execute tools called by the researcher, including search tools and strategic thinking.
    
    This function handles various types of researcher tool calls:
    1. think_tool - Strategic reflection that continues the research conversation
    2. Search tools (tavily_search, web_search) - Information gathering
    3. MCP tools - External tool integrations
    4. ResearchComplete - Signals completion of individual research task
    
    Args:
        state: Current researcher state with messages and iteration count
        config: Runtime configuration with research limits and tool settings
        
    Returns:
        Command to either continue research loop or proceed to compression
    """
    # Step 1: Extract current state and check early exit conditions
    configurable = Configuration.from_runnable_config(config)
    researcher_messages = state.get("researcher_messages", [])
    most_recent_message = researcher_messages[-1]
    
    # Early exit if no tool calls were made (including native web search)
    has_tool_calls = bool(most_recent_message.tool_calls)
    has_native_search = openai_websearch_called(most_recent_message)
    
    if not has_tool_calls and not has_native_search:
        return Command(goto="compress_research")
    
    # Step 2: Handle other tool calls (search, MCP tools, etc.)
    tools = await get_all_tools(config)
    tools_by_name = {
        tool.name if hasattr(tool, "name") else tool.get("name", "web_search"): tool 
        for tool in tools
    }
    
    # Execute all tool calls in parallel
    tool_calls = most_recent_message.tool_calls
    tool_execution_tasks = [
        execute_tool_safely(tools_by_name[tool_call["name"]], tool_call["args"], config) 
        for tool_call in tool_calls
    ]
    observations = await asyncio.gather(*tool_execution_tasks)
    
    # Create tool messages from execution results
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) 
        for observation, tool_call in zip(observations, tool_calls)
    ]
    
    # Step 3: Check late exit conditions (after processing tools)
    exceeded_iterations = state.get("tool_call_iterations", 0) >= configurable.max_react_tool_calls
    research_complete_called = any(
        tool_call["name"] == "ResearchComplete" 
        for tool_call in most_recent_message.tool_calls
    )
    
    if exceeded_iterations or research_complete_called:
        # End research and proceed to compression
        return Command(
            goto="compress_research",
            update={"researcher_messages": tool_outputs}
        )
    
    # Continue research loop with tool results
    return Command(
        goto="researcher",
        update={"researcher_messages": tool_outputs}
    )

async def compress_research(state: ResearcherState, config: RunnableConfig):
    """Compress and synthesize research findings into a concise, structured summary.

    This function takes all the research findings, tool outputs, and AI messages from
    a researcher's work and distills them into a clean, comprehensive summary while
    preserving all important information and findings.

    Args:
        state: Current researcher state with accumulated research messages
        config: Runtime configuration with compression model settings
        
    Returns:
        Dictionary containing compressed research summary and raw notes
    """
    print("\n" + "="*80)
    print("🎯 COMPRESS_RESEARCH CALLED!")
    print("="*80)

    # Step 1: Configure the compression model
    configurable = Configuration.from_runnable_config(config)
    synthesizer_model = configurable_model.with_config({
        "model": configurable.compression_model,
        "max_tokens": configurable.compression_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.compression_model, config),
        "tags": ["langsmith:nostream"]
    })
    
    # Step 2: Prepare messages for compression
    researcher_messages = state.get("researcher_messages", [])
    
    # Add instruction to switch from research mode to compression mode
    researcher_messages.append(HumanMessage(content=compress_research_simple_human_message))
    
    # Step 3: Attempt compression with retry logic for token limit issues
    synthesis_attempts = 0
    max_attempts = 3
    
    while synthesis_attempts < max_attempts:
        try:
            # Create system prompt focused on compression task
            compression_prompt = compress_research_system_prompt.format(date=get_today_str())
            messages = [SystemMessage(content=compression_prompt)] + researcher_messages
            
            # Execute compression
            response = await synthesizer_model.ainvoke(messages)
            
            # Extract raw notes from all tool and AI messages
            raw_notes_content = "\n".join([
                str(message.content)
                for message in filter_messages(researcher_messages, include_types=["tool", "ai"])
            ])

            # Extract sources from tool messages
            from research_compass_core.utils import extract_sources_from_messages
            print(f"\n🔍 COMPRESS_RESEARCH: About to extract sources from {len(researcher_messages)} messages")
            sources = extract_sources_from_messages(researcher_messages)
            print(f"🔍 COMPRESS_RESEARCH: Extracted {len(sources)} sources")

            # Debug logging
            import logging
            logging.info(f"Extracted {len(sources)} sources from researcher messages")
            if sources:
                print(f"🔍 COMPRESS_RESEARCH: First source: {sources[0].title}")
                logging.info(f"First source: {sources[0].title if sources else 'None'}")

            # Return successful compression result
            return {
                "compressed_research": str(response.content),
                "raw_notes": [raw_notes_content],
                "sources": sources
            }
            
        except Exception as e:
            synthesis_attempts += 1
            
            # Handle token limit exceeded by removing older messages
            if is_token_limit_exceeded(e, configurable.research_model):
                researcher_messages = remove_up_to_last_ai_message(researcher_messages)
                continue
            
            # For other errors, continue retrying
            continue
    
    # Step 4: Return error result if all attempts failed
    raw_notes_content = "\n".join([
        str(message.content)
        for message in filter_messages(researcher_messages, include_types=["tool", "ai"])
    ])

    # Extract sources even on error
    from research_compass_core.utils import extract_sources_from_messages
    sources = extract_sources_from_messages(researcher_messages)

    return {
        "compressed_research": "Error synthesizing research report: Maximum retries exceeded",
        "raw_notes": [raw_notes_content],
        "sources": sources
    }

# Researcher Subgraph Construction
# Creates individual researcher workflow for conducting focused research on specific topics
researcher_builder = StateGraph(
    ResearcherState, 
    output=ResearcherOutputState, 
    config_schema=Configuration
)

# Add researcher nodes for research execution and compression
researcher_builder.add_node("researcher", researcher)                 # Main researcher logic
researcher_builder.add_node("researcher_tools", researcher_tools)     # Tool execution handler
researcher_builder.add_node("compress_research", compress_research)   # Research compression

# Define researcher workflow edges
researcher_builder.add_edge(START, "researcher")           # Entry point to researcher
researcher_builder.add_edge("compress_research", END)      # Exit point after compression

# Compile researcher subgraph for parallel execution by supervisor
researcher_subgraph = researcher_builder.compile()

async def analyze_diagrams(state: AgentState, config: RunnableConfig):
    """Analyze research findings and strategically identify where diagrams would enhance understanding.

    The supervisor reviews all compressed research notes and decides where visual diagrams
    (flowcharts, mindmaps, timelines, etc.) would significantly improve comprehension of
    complex concepts, relationships, or processes.

    Args:
        state: Agent state containing research notes and brief
        config: Runtime configuration with model settings

    Returns:
        Dictionary containing diagram specifications for report generation
    """
    print("\n📊 ANALYZE_DIAGRAMS NODE CALLED")

    # Step 1: Extract research context
    notes = state.get("notes", [])
    research_brief = state.get("research_brief", "")

    if not notes:
        print("   No research notes found, skipping diagram analysis")
        return {"diagram_specifications": []}

    # Step 2: Create analysis prompt for the supervisor to identify diagram opportunities
    analysis_prompt = f"""You are reviewing research findings to identify where visual diagrams would enhance understanding.

<Research Brief>
{research_brief}
</Research Brief>

<Research Findings>
{chr(10).join(notes)}
</Research Findings>

<Task>
Analyze the research findings and identify 2-4 strategic locations where visual diagrams would significantly improve comprehension.

For each identified location, determine:

1. **Section/Topic**: Where in the report structure this diagram belongs
2. **Diagram Type**: Choose the most effective type:
   - **flowchart**: For decision processes, algorithms, workflows, step-by-step procedures
   - **mindmap**: For concept relationships, hierarchies, knowledge organization
   - **sequence**: For interactions between entities over time, communication flows
   - **timeline**: For chronological progressions, historical development
   - **hierarchy**: For organizational structures, taxonomies, classification systems

3. **Detailed Specification**: Include:
   - Exact section heading or topic
   - All nodes/concepts that should be included
   - Relationships and connections between elements
   - Flow direction and hierarchy
   - Labels and annotations

<Guidelines>
- Be strategic: Only suggest diagrams where they add genuine value
- Don't suggest diagrams for simple lists or single concepts
- Prefer flowcharts for processes and mindmaps for concept relationships
- Each diagram should visualize at least 3-5 connected concepts
- Focus on complex relationships that are hard to explain in text alone
</Guidelines>

<Output Format>
Return a JSON object with a "diagrams" array. Each diagram should have:
- section: Section heading (e.g., "2. Neural Network Architecture")
- diagram_type: One of: flowchart, mindmap, sequence, timeline, hierarchy
- title: Caption for the diagram (e.g., "Information Flow in Transformer Model")
- description: Detailed description of nodes, relationships, and structure (2-3 sentences)
- concepts: Array of key concepts/nodes to include (5-10 items)

Example:
{{
  "diagrams": [
    {{
      "section": "2. Transformer Architecture",
      "diagram_type": "flowchart",
      "title": "Information Flow in Transformer Model",
      "description": "Show how input tokens flow through the transformer layers. Start with token embedding, add positional encoding, pass through multi-head self-attention mechanism, then through feed-forward network, and finally to the output layer.",
      "concepts": ["Input Tokens", "Token Embedding", "Positional Encoding", "Multi-Head Self-Attention", "Feed Forward Network", "Layer Normalization", "Output Layer"]
    }}
  ]
}}
</Output Format>
</Task>"""

    # Step 3: Configure analysis model
    configurable = Configuration.from_runnable_config(config)
    analysis_model_config = {
        "model": configurable.research_model,
        "max_tokens": 4000,
        "api_key": get_api_key_for_model(configurable.research_model, config),
        "tags": ["langsmith:nostream"],
        "response_format": {"type": "json_object"}
    }

    try:
        # Step 4: Get LLM to analyze and specify diagrams
        print("   Analyzing research findings for diagram opportunities...")
        response = await configurable_model.with_config(analysis_model_config).ainvoke([
            HumanMessage(content=analysis_prompt)
        ])

        # Step 5: Parse diagram specifications with robust error handling
        import json

        if not response.content or not response.content.strip():
            print("   ⚠️  LLM returned empty response, skipping diagrams")
            return {"diagram_specifications": []}

        # Try to parse JSON response
        try:
            parsed_response = json.loads(response.content)
            diagram_specs = parsed_response.get("diagrams", [])
        except json.JSONDecodeError as json_err:
            print(f"   ⚠️  JSON parsing failed: {json_err}")
            print(f"   Response preview: {response.content[:200]}...")
            # Try to extract JSON from response if it's wrapped in text
            import re
            json_match = re.search(r'\{.*"diagrams".*\}', response.content, re.DOTALL)
            if json_match:
                try:
                    parsed_response = json.loads(json_match.group(0))
                    diagram_specs = parsed_response.get("diagrams", [])
                    print("   ✅ Successfully extracted JSON from response")
                except:
                    print("   ❌ Could not extract valid JSON, skipping diagrams")
                    return {"diagram_specifications": []}
            else:
                print("   ❌ No JSON found in response, skipping diagrams")
                return {"diagram_specifications": []}

        if not diagram_specs or len(diagram_specs) == 0:
            print("   📊 No diagrams recommended by analysis")
            return {"diagram_specifications": []}

        print(f"   ✅ Identified {len(diagram_specs)} diagram opportunities")
        for i, spec in enumerate(diagram_specs):
            print(f"      {i+1}. {spec.get('diagram_type', 'unknown')} - {spec.get('title', 'untitled')}")

        return {
            "diagram_specifications": diagram_specs,
            "messages": [response]
        }

    except Exception as e:
        print(f"   ❌ Error analyzing diagrams: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        # Continue without diagrams if analysis fails
        return {"diagram_specifications": []}

async def final_report_generation(state: AgentState, config: RunnableConfig):
    """Generate the final comprehensive research report with retry logic for token limits.
    
    This function takes all collected research findings and synthesizes them into a 
    well-structured, comprehensive final report using the configured report generation model.
    
    Args:
        state: Agent state containing research findings and context
        config: Runtime configuration with model settings and API keys
        
    Returns:
        Dictionary containing the final report and cleared state
    """
    # Step 1: Extract research findings and prepare state cleanup
    notes = state.get("notes", [])
    cleared_state = {"notes": {"type": "override", "value": []}}
    findings = "\n".join(notes)

    # Step 1.5: Extract and format sources for citations
    sources = state.get("sources", [])
    if sources and len(sources) > 0:
        sources_text = "\n\n".join([
            f"**[{i+1}]** {source.get('title', 'Untitled')}\n"
            f"- **Authors**: {', '.join(source.get('authors', [])[:3])}{'...' if len(source.get('authors', [])) > 3 else ''}\n"
            f"- **URL**: {source.get('url', '')}\n"
            f"- **Source**: {source.get('search_api', 'unknown').replace('_', ' ').title()}\n"
            f"- **Published**: {source.get('published_date', 'N/A')}"
            for i, source in enumerate(sources)
        ])
        print(f"\n📚 Including {len(sources)} sources for citations in final report")
    else:
        sources_text = "No structured sources available. Include any sources mentioned in the findings."
        print("\n📚 No structured sources available for final report")

    # Step 1.6: Format diagram specifications for prompt
    diagram_specs = state.get("diagram_specifications", [])
    if diagram_specs and len(diagram_specs) > 0:
        diagram_specs_text = "\n\n".join([
            f"**Diagram {i+1}**: {spec.get('section', 'Unknown section')}\n"
            f"- **Type**: {spec.get('diagram_type', 'unknown')}\n"
            f"- **Title**: {spec.get('title', 'Untitled')}\n"
            f"- **Description**: {spec.get('description', '')}\n"
            f"- **Key Concepts**: {', '.join(spec.get('concepts', []))}"
            for i, spec in enumerate(diagram_specs)
        ])
        print(f"\n📊 Including {len(diagram_specs)} diagrams in final report")
    else:
        diagram_specs_text = "No diagrams specified. Write the report without any diagrams."
        print("\n📊 No diagrams specified for final report")

    # Step 2: Configure the final report generation model
    configurable = Configuration.from_runnable_config(config)
    writer_model_config = {
        "model": configurable.final_report_model,
        "max_tokens": configurable.final_report_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.final_report_model, config),
        "tags": ["langsmith:nostream"]
    }

    # Step 3: Attempt report generation with token limit retry logic
    max_retries = 3
    current_retry = 0
    findings_token_limit = None

    while current_retry <= max_retries:
        try:
            # Create comprehensive prompt with all research context
            final_report_prompt = final_report_generation_prompt.format(
                research_brief=state.get("research_brief", ""),
                messages=get_buffer_string(state.get("messages", [])),
                findings=findings,
                sources=sources_text,
                diagram_specifications=diagram_specs_text,
                date=get_today_str()
            )
            
            # Generate the final report
            final_report = await configurable_model.with_config(writer_model_config).ainvoke([
                HumanMessage(content=final_report_prompt)
            ])
            
            # Return successful report generation
            return {
                "final_report": final_report.content, 
                "messages": [final_report],
                **cleared_state
            }
            
        except Exception as e:
            # Handle token limit exceeded errors with progressive truncation
            if is_token_limit_exceeded(e, configurable.final_report_model):
                current_retry += 1
                
                if current_retry == 1:
                    # First retry: determine initial truncation limit
                    model_token_limit = get_model_token_limit(configurable.final_report_model)
                    if not model_token_limit:
                        return {
                            "final_report": f"Error generating final report: Token limit exceeded, however, we could not determine the model's maximum context length. Please update the model map in deep_researcher/utils.py with this information. {e}",
                            "messages": [AIMessage(content="Report generation failed due to token limits")],
                            **cleared_state
                        }
                    # Use 4x token limit as character approximation for truncation
                    findings_token_limit = model_token_limit * 4
                else:
                    # Subsequent retries: reduce by 10% each time
                    findings_token_limit = int(findings_token_limit * 0.9)
                
                # Truncate findings and retry
                findings = findings[:findings_token_limit]
                continue
            else:
                # Non-token-limit error: return error immediately
                return {
                    "final_report": f"Error generating final report: {e}",
                    "messages": [AIMessage(content="Report generation failed due to an error")],
                    **cleared_state
                }
    
    # Step 4: Return failure result if all retries exhausted
    return {
        "final_report": "Error generating final report: Maximum retries exceeded",
        "messages": [AIMessage(content="Report generation failed after maximum retries")],
        **cleared_state
    }

async def export_reports(state: AgentState, config: RunnableConfig):
    """Export final report to configured formats with timestamp-based versioning.

    This function takes the markdown report and exports it to all configured formats.
    Files are saved with timestamps to prevent overwrites. If no export formats are
    configured, this step is skipped.

    Args:
        state: Agent state containing the final report and research brief
        config: Runtime configuration with export settings

    Returns:
        Dictionary containing paths to all exported files
    """
    # Step 1: Check if export is configured
    configurable = Configuration.from_runnable_config(config)

    if not configurable.export_formats:
        # No export formats configured, skip export
        return {"exported_files": {}}

    # Step 2: Import export functionality
    from research_compass_core.exporters import export_report

    # Step 3: Export to all configured formats
    try:
        final_report = state.get("final_report", "")
        research_brief = state.get("research_brief", "research_report")
        export_formats = [f.value for f in configurable.export_formats]
        export_dir = configurable.export_directory

        print(f"📤 Starting export process...")
        print(f"   Final report length: {len(final_report)} chars")
        print(f"   Research brief: {research_brief}")
        print(f"   Export formats: {export_formats}")
        print(f"   Export directory: {export_dir}")

        exported_files = await export_report(
            markdown_content=final_report,
            research_brief=research_brief,
            export_formats=export_formats,
            export_dir=export_dir
        )

        print(f"✅ Export completed successfully!")
        print(f"   Exported files: {exported_files}")
        print(f"   Number of files: {len(exported_files) if isinstance(exported_files, (list, dict)) else 'N/A'}")

        return {"exported_files": exported_files}

    except Exception as e:
        # Log error but don't fail the entire workflow
        import logging
        import traceback
        logging.error(f"Export failed: {e}")
        print(f"❌ Export failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        print(f"   Export formats requested: {[f.value for f in configurable.export_formats]}")
        print(f"   Export directory: {configurable.export_directory}")
        return {"exported_files": {}}

# Main Deep Researcher Graph Construction
# Creates the complete deep research workflow from user input to final report
deep_researcher_builder = StateGraph(
    AgentState, 
    input=AgentInputState, 
    config_schema=Configuration
)

# Add main workflow nodes for the complete research process
deep_researcher_builder.add_node("clarify_with_user", clarify_with_user)           # User clarification phase
deep_researcher_builder.add_node("write_research_brief", write_research_brief)     # Research planning phase
deep_researcher_builder.add_node("research_supervisor", supervisor_subgraph)       # Research execution phase
deep_researcher_builder.add_node("analyze_diagrams", analyze_diagrams)             # Diagram planning phase
deep_researcher_builder.add_node("final_report_generation", final_report_generation)  # Report generation phase
deep_researcher_builder.add_node("export_reports", export_reports)                 # Export phase

# Define main workflow edges for sequential execution
deep_researcher_builder.add_edge(START, "clarify_with_user")                       # Entry point
deep_researcher_builder.add_edge("research_supervisor", "analyze_diagrams")        # Research to diagram analysis
deep_researcher_builder.add_edge("analyze_diagrams", "final_report_generation")    # Diagrams to report
deep_researcher_builder.add_edge("final_report_generation", "export_reports")      # Report to export
deep_researcher_builder.add_edge("export_reports", END)                            # Final exit point

# Compile the complete deep researcher workflow
deep_researcher = deep_researcher_builder.compile()