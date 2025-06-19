## Standard Workflow

1. First think through the problem, read the codebase for relevant files, and write a plan to projectplan.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes.
   Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the projectplan.md file with a summary of the changes you made and any other
   relevant information.
8. "Verify all function signatures and dependencies before using them"
9. "Test your code mentally - trace through the execution"
10. "Don't rush - think about architectural implications"
11. "If extracting components from a framework, ensure they can work standalone"
12. "Create new components rather than misusing existing ones outside their context"

# SDR Workflow Execution Flow

The SDR (Sales Development Representative) workflow is a loop-based LangGraph workflow that processes companies
sequentially. Here's how it executes:

## Workflow Nodes and Their Order:

1. **company_retriever** (Entry Point)
    - Retrieves the list of companies to process
    - Conditional: If companies exist → go to streamlined_web_enricher, else → save_results

2. **streamlined_web_enricher**
    - Performs web analysis on the current company
    - Conditional: If relevant → prospect_enricher, else → company_progression

3. **prospect_enricher** (Only if company is relevant)
    - Enriches prospect information via LinkedIn
    - Next: company_linkedin_progress

4. **company_linkedin_progress**
    - Saves LinkedIn progress for the current company
    - Next: hubspot_individual

5. **hubspot_individual**
    - Creates HubSpot contacts for the company's prospects
    - Next: hubspot_progress_saver

6. **hubspot_progress_saver**
    - Saves HubSpot progress for the current company
    - Next: company_progression

7. **company_progression**
    - Moves to the next company in the list
    - Conditional: If more companies → streamlined_web_enricher, else → linkedin_progress_backup

8. **linkedin_progress_backup** (After all companies processed)
    - Backs up all LinkedIn URLs before HubSpot processing
    - Next: final_progress_save

9. **final_progress_save**
    - Saves final workflow results and consolidated data
    - Next: error_summary_export

10. **error_summary_export**
    - Exports categorized error summary
    - Next: save_results

11. **save_results**
    - Saves all final results to files
    - Next: END

## Key Flow Characteristics:

- Loop-based processing: Each company is processed individually through steps 2-7
- Conditional relevance check: Only relevant companies get LinkedIn enrichment
- Sequential progression: Companies are processed one at a time
- Progress tracking: Individual saves after LinkedIn and HubSpot steps
- Final consolidation: All data backed up and saved at the end