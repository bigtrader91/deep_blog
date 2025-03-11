report_planner_query_writer_instructions = """Answer in Korean. You are performing research for a blog post.

<Report topic>
{topic}
</Report topic>

<Report organization>
{report_organization}
</Report organization>

<Task>
Your goal is to generate {number_of_queries} web search queries that will help gather information for planning a 5-step blog post.

The 5-step blog writing process is:

1) Step 1: Write a title (<h1>), a hooking phrase, a greeting of at least 150 characters, and a table of contents with 6 items (each item has an id).
2) Step 2: Write content for table-of-contents items 1 to 3. Each section must have at least 200 characters. The second section includes a table, and the third section includes a list.
3) Step 3: Write content for table-of-contents items 4 to 6. Each section must have at least 200 characters. The fifth section includes a table, and the sixth section includes a list.
4) Step 4: Create an FAQ with 6 questions and answers. Use HTML elements to emphasize the Q&A format.
5) Step 5: Write a finishing statement for the blog.

The queries should:
1. Be related to the blog topic (i.e., the Report topic).
2. Help satisfy the requirements specified in the above 5-step structure.
3. Avoid generating queries that might lead to duplicate or generic headings (e.g., multiple "Conclusion" sections or "Sources").

Make these queries specific enough to find high-quality, relevant sources while covering the breadth needed for the blog post.
</Task>
"""


report_planner_instructions = """Answer in Korean. I want a plan for a blog post that follows a 5-step structure, focusing on clarity and avoiding unnecessary overlap.

<Report topic>
The topic of the blog post is:
{topic}
</Report topic>

<Report organization>
The blog should follow this organization:
{report_organization}
</Report organization>

<Context>
Here is context to use in planning the sections:
{context}
</Context>

<Task>
Generate a plan for a 5-step blog post with the following specific requirements:

1️⃣ STEP 1: Title, hooking phrase, greeting, table of contents
   - Use an <h1> tag for the title.
   - Write a hooking phrase that grabs the reader's attention.
   - Greeting text must be at least 150 characters.
   - The table of contents must have 6 items, each with an id attribute.

2️⃣ STEP 2: Write content for TOC items 1~3
   - Each section must have at least 200 characters.
   - The second section includes a table.
   - The third section includes a list.

3️⃣ STEP 3: Write content for TOC items 4~6
   - Each section must have at least 200 characters.
   - The fifth section includes a table.
   - The sixth section includes a list.

4️⃣ STEP 4: FAQ
   - Provide 6 Q&A pairs.
   - Use HTML-based emphasis for the questions and answers (e.g., <h3>, <p>, etc.).

5️⃣ STEP 5: Final finishing statement
   - Write a concluding remark for the blog post.
   - (Optional) You may also add tags or a brief CTA if relevant.

Your plan should be tight and focused with NO overlapping sections or unnecessary filler.
Each section in your plan must include:
- Name: a short, descriptive title.
- Description: what will be covered in that step/section.
- Research: whether web research is needed for the section.
- Content: leave this blank now; it will be filled in later.

Integration guidelines:
- Ensure each step is clearly distinct and that the final blog post covers all 5 steps.
- Avoid duplicating the blog title or creating multiple finishing sections.
- Double-check there are exactly 6 items in the table of contents for Steps 2 and 3.

Before submitting, review your structure to ensure it follows the above steps and avoids redundant or overlapping content.
</Task>

<Feedback>
Here is feedback on the blog structure from review (if any):
{feedback}
</Feedback>
"""

query_writer_instructions = """Answer in Korean. You are an expert technical writer crafting targeted web search queries to gather comprehensive information for a specific blog section.

<Report topic>
{topic}
</Report topic>

<Section topic>
{section_topic}
</Section topic>

<Task>
Your goal is to generate {number_of_queries} search queries that will help gather comprehensive information on the above section topic. The final blog post follows a 5-step structure, with particular emphasis on tables, lists, and an FAQ section.

The queries should:
1. Be closely related to the topic.
2. Address different aspects of the section topic.
3. Avoid generating duplicate or overly generic queries (e.g., repeating "Conclusion" or "Sources").

Make the queries specific enough to find high-quality, relevant sources for writing this blog section.
</Task>
"""


section_writer_instructions = """Answer in Korean. Write one section of a 5-step blog post.

<Task>
1. Review the blog topic, the section name, and the section description carefully.
2. If present, check any existing content for this section.
3. Examine the provided Source material to support your writing.
4. Write this section's content according to the required guidelines (tables, lists, etc. if needed).
5. Conclude with a ### Sources list referencing the chosen URLs.
</Task>

<Writing Guidelines>
- This blog is structured in 5 major steps with 6 table-of-contents items in Steps 2 and 3.
- Each main section (TOC item) must have at least 200 characters.
- Use simple, clear language and short paragraphs.
- For the section title, use Markdown format (e.g., "## Section 1").
- If this is a special section requiring a table or list, ensure you incorporate it properly in Markdown.
- Do NOT create a new concluding statement for the entire blog. The blog's final finishing statement occurs in Step 5.
</Writing Guidelines>

<Citation Rules>
- Assign each unique URL a single citation number in your text.
- End the section with ### Sources, listing each source with the corresponding number.
- Number sources sequentially without gaps (1,2,3,4...) in the final list.
- Example format:
  [1] Source Title: URL
  [2] Source Title: URL
</Citation Rules>

<Final Check>
1. Verify every claim is grounded in the provided sources.
2. Confirm each URL appears ONLY ONCE in the Sources list.
3. No overlapping or duplicate final statements (the overall blog conclusion is Step 5).
</Final Check>
"""
section_writer_inputs = """Answer in Korean.  
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


section_grader_instructions = """Answer in Korean. Review a blog post section relative to the specified topic:

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
Check whether this section meets the blog's 5-step structure requirements:
- If this section belongs to Steps 2 or 3, ensure at least 200 characters.
- If it's the second or fifth section, confirm a table is included.
- If it's the third or sixth section, confirm a list is included.
- Ensure no duplication of the entire blog's conclusion.

If the content is lacking information, generate {number_of_follow_up_queries} follow-up web search queries.
</task>

<format>
    grade: Literal["pass","fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: List[SearchQuery] = Field(
        description="List of follow-up search queries to address missing details.",
    )
</format>
"""


final_section_writer_instructions = """Answer in Korean.You are an expert technical writer completing the final parts of a 5-step blog post.

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
This blog follows 5 steps. You are now writing either:
1. The FAQ (Step 4), or
2. The final finishing statement (Step 5).

For the FAQ (Step 4):
- Provide exactly 6 Q&A pairs.
- Use HTML to visually emphasize each question and answer (e.g., <h3>Q1</h3><p>A1</p>).
- Keep answers concise yet informative.

For the finishing statement (Step 5):
- Write a final remark wrapping up the blog post (100-150 words).
- You may also include a brief CTA (e.g., "Thank you for reading! Check out more posts on ...").
- If relevant, you may add a short list of tags (up to 10) as #TagName at the very end. 
- Do NOT add any sources section here.

Ensure you do not create overlapping or duplicate concluding sections.
</Task>

<Quality Checks>
- For FAQ: Exactly 6 Q&As, each highlighted with HTML tags.
- For finishing statement: 100-150 words, optional CTA, optional tags (#tag1 #tag2 ...).
- No new tables/lists beyond these guidelines.
</Quality Checks>
"""
