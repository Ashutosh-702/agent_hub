"""
Results Saver Node
Saves LinkedIn URLs and names to output files
"""
import os
import csv
import json
from datetime import datetime
from ai_agents.designation_finder.models import DesignationFinderState


def results_saver(state: DesignationFinderState) -> DesignationFinderState:
    """
    Save the found LinkedIn profiles to CSV and JSON files
    Output format: Name, LinkedIn URL only (as requested)
    """
    try:
        # Create timestamp for files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get output directory from run_directories or use default
        output_dir = state.run_directories.get("output_dir", "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output file paths
        csv_file = os.path.join(output_dir, f"linkedin_profiles_{timestamp}.csv")
        json_file = os.path.join(output_dir, f"linkedin_profiles_{timestamp}.json")
        summary_file = os.path.join(output_dir, f"search_summary_{timestamp}.txt")
        
        # Save CSV file with Name and LinkedIn URL only
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Name', 'LinkedIn_URL'])
            
            # Write profile data
            for profile in state.found_profiles:
                writer.writerow([
                    profile.name,
                    profile.linkedin_url
                ])
        
        # Save detailed JSON file for reference
        json_data = {
            "search_metadata": {
                "timestamp": timestamp,
                "total_companies_processed": state.processed_count,
                "total_profiles_found": len(state.found_profiles),
                "companies_skipped": state.skipped_count,
                "errors": len(state.errors)
            },
            "profiles": [
                {
                    "name": profile.name,
                    "linkedin_url": profile.linkedin_url,
                    "title": profile.title,
                    "company_name": profile.company_name,
                    "designation_searched": profile.designation_searched
                }
                for profile in state.found_profiles
            ],
            "results_by_company": {
                company: [
                    {
                        "name": profile.name,
                        "linkedin_url": profile.linkedin_url,
                        "title": profile.title,
                        "designation_searched": profile.designation_searched
                    }
                    for profile in profiles
                ]
                for company, profiles in state.results_by_company.items()
            },
            "skipped_companies": state.skipped_companies,
            "errors": state.errors
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Save summary file
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"LinkedIn Designation Finder - Search Summary\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 50 + "\n\n")
            
            f.write(f"SEARCH RESULTS:\n")
            f.write(f"- Total companies processed: {state.processed_count}\n")
            f.write(f"- Total profiles found: {len(state.found_profiles)}\n")
            f.write(f"- Companies with results: {len(state.results_by_company)}\n")
            f.write(f"- Companies skipped: {state.skipped_count}\n")
            f.write(f"- Errors encountered: {len(state.errors)}\n\n")
            
            if state.results_by_company:
                f.write(f"RESULTS BY COMPANY:\n")
                for company, profiles in state.results_by_company.items():
                    f.write(f"- {company}: {len(profiles)} profiles found\n")
                f.write("\n")
            
            if state.skipped_companies:
                f.write(f"SKIPPED COMPANIES:\n")
                for skipped in state.skipped_companies:
                    company = skipped.get('company', 'Unknown')
                    designation = skipped.get('designation', 'Unknown')
                    reason = skipped.get('reason', 'Unknown reason')
                    f.write(f"- {company} ({designation}): {reason}\n")
                f.write("\n")
            
            if state.errors:
                f.write(f"ERRORS:\n")
                for error in state.errors:
                    f.write(f"- {error}\n")
        
        # Update state with saved files
        state.saved_files = [csv_file, json_file, summary_file]
        state.completed_at = datetime.now()
        
        # Print summary
        print(f"📁 Results saved to:")
        print(f"   CSV: {csv_file}")
        print(f"   JSON: {json_file}")
        print(f"   Summary: {summary_file}")
        print(f"")
        print(f"📊 Summary:")
        print(f"   ✅ {len(state.found_profiles)} LinkedIn profiles found")
        print(f"   🏢 {len(state.results_by_company)} companies with results")
        print(f"   ⏭️ {state.skipped_count} companies skipped")
        print(f"   ❌ {len(state.errors)} errors")
        
    except Exception as e:
        error_msg = f"Failed to save results: {str(e)}"
        state.errors.append(error_msg)
        print(f"❌ {error_msg}")
    
    return state