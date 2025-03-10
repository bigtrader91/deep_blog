report_planner_query_writer_instructions = """You are performing research for a report. 

<Report topic>
{topic}
</Report topic>

<Report organization>
{report_organization}
</Report organization>

<Task>
Your goal is to generate {number_of_queries} web search queries that will help gather information for planning the report sections. 

The queries should:

1. Be related to the Report topic
2. Help satisfy the requirements specified in the report organization
3. Avoid generating queries that might lead to duplicate or generic section headings (e.g., "Sources" or multiple "Conclusion" sections)

Make the queries specific enough to find high-quality, relevant sources while covering the breadth needed for the report structure.
</Task>
"""

report_planner_instructions = """I want a plan for a report that is concise and focused.

<Report topic>
The topic of the report is:
{topic}
</Report topic>

<Report organization>
The report should follow this organization: 
{report_organization}
</Report organization>

<Context>
Here is context to use to plan the sections of the report: 
{context}
</Context>

<Task>
Generate a list of sections for the report. Your plan should be tight and focused with NO overlapping sections or unnecessary filler. 

For example, a good report structure might look like:
1/ intro
2/ overview of topic A
3/ overview of topic B
4/ comparison between A and B
5/ conclusion

Each section should have the fields:

- Name - Name for this section of the report.
- Description - Brief overview of the main topics covered in this section.
- Research - Whether to perform web research for this section of the report.
- Content - The content of the section, which you will leave blank for now.

Integration guidelines:
- Include examples and implementation details within main topic sections, not as separate sections.
- Ensure each section has a distinct purpose with no content overlap.
- Combine related concepts rather than separating them.

Additional Guidelines:
- Ensure that the Table of Contents (TOC) is generated only from the primary report sections (exclude generic headings like "Sources").
- Place the TOC after the report title and introduction (or greeting) and before the main sections (i.e., immediately before the first h2 section).
- Only include one "Conclusion" section at the end of the report.
- Avoid duplicate main titles (e.g., the report title should appear only once).

Before submitting, review your structure to ensure it has no redundant sections and follows a logical flow.
</Task>

<Feedback>
Here is feedback on the report structure from review (if any):
{feedback}
</Feedback>
"""

query_writer_instructions = """You are an expert technical writer crafting targeted web search queries that will gather comprehensive information for writing a technical report section.

<Report topic>
{topic}
</Report topic>

<Section topic>
{section_topic}
</Section topic>

<Task>
Your goal is to generate {number_of_queries} search queries that will help gather comprehensive information above the section topic. 

The queries should:

1. Be related to the topic.
2. Examine different aspects of the topic.
3. Avoid queries that might encourage duplicate or generic sections (e.g., multiple "Sources" or "Conclusion" sections).

Make the queries specific enough to find high-quality, relevant sources.
</Task>
"""

section_writer_instructions = """Write one section of a research report.

<Task>
1. Review the report topic, section name, and section topic carefully.
2. If present, review any existing section content. 
3. Then, look at the provided Source material.
4. Decide the sources that you will use to write a report section.
5. Write the report section and list your sources. 
</Task>

<Writing Guidelines>
- If existing section content is not populated, write from scratch.
- If existing section content is populated, synthesize it with the source material.
- Strict 150-200 word limit.
- Use simple, clear language.
- Use short paragraphs (2-3 sentences max).
- Use ## for section title (Markdown format).
- Ensure that the section title and content are unique and do not duplicate other sections (for example, avoid repeating the report title or creating multiple "Conclusion" sections).
</Writing Guidelines>

<Citation Rules>
- Assign each unique URL a single citation number in your text.
- End with ### Sources that lists each source with corresponding numbers.
- IMPORTANT: Number sources sequentially without gaps (1,2,3,4...) in the final list regardless of which sources you choose.
- Example format:
  [1] Source Title: URL
  [2] Source Title: URL
</Citation Rules>

<Final Check>
1. Verify that EVERY claim is grounded in the provided Source material.
2. Confirm each URL appears ONLY ONCE in the Source list.
3. Verify that sources are numbered sequentially (1,2,3...) without any gaps.
</Final Check>
"""

section_writer_inputs = """ 
<Report topic>
{topic}
</Report topic>

<Section name>
{section_name}
</Section name>

<Section topic>
{section_topic}
</Section topic>

<Existing section content (if populated)>
{section_content}
</Existing section content>

<Source material>
{context}
</Source material>
"""

section_grader_instructions = """Review a report section relative to the specified topic:

<Report topic>
{topic}
</Report topic>

<section topic>
{section_topic}
</section topic>

<section content>
{section}
</section content>

<task>
Evaluate whether the section content adequately addresses the section topic without duplicating content from other sections (e.g., avoid duplicate conclusions or repeated report titles).

If the section content does not adequately address the section topic, generate {number_of_follow_up_queries} follow-up search queries to gather missing information.
</task>

<format>
    grade: Literal["pass","fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: List[SearchQuery] = Field(
        description="List of follow-up search queries.",
    )
</format>
"""

final_section_writer_instructions = """You are an expert technical writer crafting a section that synthesizes information from the rest of the report.

<Report topic>
{topic}
</Report topic>

<Section name>
{section_name}
</Section name>

<Section topic> 
{section_topic}
</Section topic>

<Available report content>
{context}
</Available report content>

<Task>
1. Section-Specific Approach:

For Introduction:
- Use # for report title (Markdown format).
- 50-100 word limit.
- Write in simple and clear language.
- Focus on the core motivation for the report in 1-2 paragraphs.
- Use a clear narrative arc to introduce the report.
- Include NO structural elements (no lists or tables).
- No sources section needed.

For Conclusion/Summary:
- Use ## for section title (Markdown format).
- 100-150 word limit.
- For comparative reports:
    * Must include a focused comparison table using Markdown table syntax.
    * Table should distill insights from the report.
    * Keep table entries clear and concise.
- For non-comparative reports: 
    * Only use ONE structural element IF it helps distill the points made in the report:
    * Either a focused table comparing items present in the report (using Markdown table syntax)
    * Or a short list using proper Markdown list syntax:
      - Use `*` or `-` for unordered lists.
      - Use `1.` for ordered lists.
      - Ensure proper indentation and spacing.
- End with specific next steps or implications.
- No sources section needed.
- Ensure that this section is unique in its role and does not duplicate any previously defined conclusion or summary sections.

3. Writing Approach:
- Use concrete details over general statements.
- Make every word count.
- Focus on your single most important point.
</Task>

<Quality Checks>
- For introduction: 50-100 word limit, # for report title, no structural elements, no sources section.
- For conclusion: 100-150 word limit, ## for section title, only ONE structural element at most, no sources section.
- Markdown format.
- Do not include word count or any preamble in your response.
</Quality Checks>
"""
