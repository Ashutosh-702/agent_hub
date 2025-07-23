#!/usr/bin/env python3
"""
Debug Complex Queries - Single LLM Call Approach
Makes only ONE OpenAI API call, then tests each component separately
"""
import json
import subprocess
import time
import requests
from typing import Dict, Any, Optional

def get_dsl_once(query: str) -> Optional[Dict[str, Any]]:
    """Make ONE LLM call to get DSL, then use it for all tests"""
    
    print(f"🤖 MAKING SINGLE LLM CALL FOR: '{query}'")
    print("=" * 60)
    print("Getting DSL query from LLM (this is the only OpenAI call)...")
    
    llm_start = time.time()
    
    try:
        # Try the /explain endpoint first (doesn't do full search)
        response = requests.post(
            "http://localhost:8001/explain",
            json={"query": query},
            timeout=60
        )
        
        llm_time = time.time() - llm_start
        
        if response.status_code == 200:
            explanation = response.json()
            dsl_query = explanation.get('generated_dsl', {})
            
            print(f"✅ LLM call successful ({llm_time:.2f}s)")
            print(f"📝 Generated DSL:")
            print(json.dumps(dsl_query, indent=2))
            
            if llm_time > 30:
                print(f"⚠️ LLM took {llm_time:.2f}s - this explains timeout issues!")
            
            return dsl_query
            
        else:
            print(f"❌ LLM call failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        llm_time = time.time() - llm_start
        print(f"❌ LLM TIMED OUT after {llm_time:.2f}s")
        print("🔍 This is your bottleneck! LLM is taking too long.")
        return None
    except requests.exceptions.ConnectException:
        print("❌ Server not running. Start with: python3 start_server_simple.py")
        return None
    except Exception as e:
        print(f"❌ LLM error: {str(e)}")
        return None

def test_dsl_direct_coresignal(dsl_query: Dict[str, Any], query_name: str):
    """Test the DSL directly against CoreSignal"""
    
    print(f"\n🌐 TESTING DSL AGAINST CORESIGNAL")
    print("-" * 50)
    
    # Extract components
    query_body = {"query": dsl_query.get("query", {})}
    size = dsl_query.get("size", 5)
    from_offset = dsl_query.get("from_", 0)
    
    print(f"📤 Sending to CoreSignal:")
    print(f"   Size: {size}, From: {from_offset}")
    print(f"   Query: {json.dumps(query_body, indent=2)}")
    
    coresignal_start = time.time()
    
    try:
        curl_cmd = [
            "curl", "-s", "-X", "POST",
            f"https://api.coresignal.com/cdapi/v2/company_multi_source/search/es_dsl?from={from_offset}&items_per_page={size}",
            "-H", "apikey: KeEaNZqGududrVFLip0fhGILV7wQBIDj",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(query_body)
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        coresignal_time = time.time() - coresignal_start
        
        if result.returncode == 0:
            try:
                company_ids = json.loads(result.stdout)
                print(f"✅ CoreSignal responded ({coresignal_time:.2f}s)")
                print(f"📊 Found {len(company_ids)} companies")
                
                if len(company_ids) == 0:
                    print(f"⚠️ ZERO RESULTS - DSL field mapping issue")
                    analyze_zero_results(query_body)
                else:
                    print(f"🎯 Company IDs: {company_ids[:3]}...")
                
                return company_ids
                
            except json.JSONDecodeError:
                print(f"❌ Invalid CoreSignal response: {result.stdout[:200]}")
                return []
        else:
            print(f"❌ CoreSignal API error: {result.stderr}")
            return []
            
    except subprocess.TimeoutExpired:
        print(f"❌ CoreSignal timed out after 30s")
        return []
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

def analyze_zero_results(query_body: Dict[str, Any]):
    """Analyze why we got zero results"""
    
    print(f"\n🔍 ANALYZING ZERO RESULTS")
    print("-" * 30)
    
    query = query_body.get("query", {})
    
    # Check query structure
    if "bool" in query:
        bool_query = query["bool"]
        must_clauses = bool_query.get("must", [])
        print(f"📋 Bool query with {len(must_clauses)} conditions:")
        
        for i, clause in enumerate(must_clauses):
            print(f"   {i+1}. {list(clause.keys())[0]}: {clause}")
            
            # Check for problematic field names
            if "term" in clause:
                term_clause = clause["term"]
                for field, value in term_clause.items():
                    if field in ["hq_city", "hq_state", "hq_country"]:
                        print(f"      ⚠️ Location field '{field}' with value '{value}'")
                        print(f"      💡 Try testing simpler location values")
                    elif field == "company_type":
                        print(f"      ⚠️ Company type '{value}' might not exist in data")
                        
    elif "match" in query:
        match_clause = query["match"]
        print(f"📝 Match query: {match_clause}")
        
    elif "nested" in query:
        nested_clause = query["nested"]
        print(f"🔗 Nested query: {nested_clause}")
        print(f"   ⚠️ Technology searches often return 0 results")
        
    print(f"\n💡 Suggestions:")
    print(f"   • Try a simpler version of the query")
    print(f"   • Test with known working values (e.g., 'Microsoft')")
    print(f"   • Check if CoreSignal has data for these criteria")

def test_company_collection(company_ids: list):
    """Test collecting company details"""
    
    if not company_ids:
        print(f"\n⏩ Skipping collection test - no company IDs")
        return
    
    print(f"\n🏢 TESTING COMPANY COLLECTION")
    print("-" * 40)
    
    company_id = company_ids[0]
    collection_start = time.time()
    
    try:
        curl_cmd = [
            "curl", "-s", "-X", "GET",
            f"https://api.coresignal.com/cdapi/v2/company_multi_source/collect/{company_id}",
            "-H", "apikey: KeEaNZqGududrVFLip0fhGILV7wQBIDj"
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=15)
        collection_time = time.time() - collection_start
        
        if result.returncode == 0:
            try:
                company_data = json.loads(result.stdout)
                company_name = company_data.get('company_name', 'Unknown')
                industry = company_data.get('industry', 'Unknown')
                location = company_data.get('hq_location', 'Unknown')
                
                print(f"✅ Collection successful ({collection_time:.2f}s)")
                print(f"🏢 Company: {company_name}")
                print(f"🏭 Industry: {industry}")
                print(f"📍 Location: {location}")
                
                if collection_time > 3:
                    print(f"⚠️ Collection is slow ({collection_time:.2f}s)")
                    print(f"   💡 With many companies, this could cause timeouts")
                
            except json.JSONDecodeError:
                print(f"❌ Invalid collection response")
        else:
            print(f"❌ Collection failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print(f"❌ Collection timed out")
    except Exception as e:
        print(f"❌ Collection error: {str(e)}")

def test_simpler_version(original_query: str):
    """Test a simpler version without LLM to isolate issues"""
    
    print(f"\n🧪 TESTING SIMPLER VERSION (No LLM)")
    print("-" * 50)
    
    # Create a known working query
    simple_dsl = {
        "query": {
            "match": {
                "company_name": {
                    "query": "Microsoft",
                    "fuzziness": "AUTO"
                }
            }
        },
        "size": 3,
        "from_": 0
    }
    
    print(f"🔄 Testing known working DSL:")
    print(json.dumps(simple_dsl, indent=2))
    
    company_ids = test_dsl_direct_coresignal(simple_dsl, "Simple Microsoft search")
    
    if company_ids:
        print(f"\n✅ Simple query works - issue is with complex DSL generation")
        print(f"💡 Problem is likely in LLM prompt or field mappings")
    else:
        print(f"\n❌ Even simple query fails - check CoreSignal API connection")

def provide_debug_summary(query: str, dsl_query: Optional[Dict], company_ids: list, llm_time: float):
    """Provide debugging summary and recommendations"""
    
    print(f"\n📋 DEBUG SUMMARY FOR: '{query}'")
    print("=" * 60)
    
    if not dsl_query:
        print(f"🚨 PRIMARY ISSUE: LLM Call Failed")
        print(f"   • LLM timeout or error")
        print(f"   • Check OpenAI API key and credits")
        print(f"   • Consider simpler prompts or faster models")
        return
    
    if llm_time > 20:
        print(f"🚨 PRIMARY ISSUE: LLM Too Slow ({llm_time:.2f}s)")
        print(f"   • This explains your timeout issues")
        print(f"   • LLM is the bottleneck in your pipeline")
        print(f"   • Solutions: Optimize prompts, use gpt-3.5-turbo, add timeouts")
    
    if not company_ids:
        print(f"🚨 SECONDARY ISSUE: Zero Results")
        print(f"   • DSL generated correctly but no data returned")
        print(f"   • Field mapping or data availability issue")
        print(f"   • Test with simpler queries to isolate")
    else:
        print(f"✅ DSL AND DATA: Both working correctly")
        print(f"   • Found {len(company_ids)} companies")
        print(f"   • Issue is likely just LLM speed")
    
    print(f"\n💡 NEXT STEPS:")
    if llm_time > 20:
        print(f"   1. Optimize LLM prompts (remove unnecessary examples)")
        print(f"   2. Add timeouts to LLM calls in your code")
        print(f"   3. Consider using gpt-3.5-turbo for faster responses")
    if not company_ids and dsl_query:
        print(f"   1. Test simpler versions of the query")
        print(f"   2. Check field names in LLM prompt")
        print(f"   3. Verify data availability in CoreSignal")

def main():
    """Main debugging function"""
    
    print(f"🔧 SINGLE-CALL DEBUG TOOL")
    print("=" * 60)
    print("This tool makes only ONE LLM call to minimize API costs")
    
    # Get query to debug
    query = input("\n🔍 Enter complex query to debug: ").strip()
    if not query:
        query = "AI startups in San Francisco with 50+ employees"
        print(f"Using default: {query}")
    
    # Step 1: Make single LLM call
    llm_start = time.time()
    dsl_query = get_dsl_once(query)
    llm_time = time.time() - llm_start
    
    if not dsl_query:
        print(f"\n🧪 Testing simpler approach...")
        test_simpler_version(query)
        return
    
    # Step 2: Test DSL against CoreSignal
    company_ids = test_dsl_direct_coresignal(dsl_query, query)
    
    # Step 3: Test company collection
    test_company_collection(company_ids)
    
    # Step 4: Test simpler version for comparison
    if not company_ids:
        test_simpler_version(query)
    
    # Step 5: Provide summary
    provide_debug_summary(query, dsl_query, company_ids, llm_time)
    
    print(f"\n✅ Single-call debug complete!")
    print(f"💰 Total OpenAI calls: 1")

if __name__ == "__main__":
    main() 