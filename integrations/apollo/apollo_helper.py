from typing import Dict, Any, List, OrderedDict

from structlog.contextvars import bind_contextvars

from integrations.config.constants import MAX_EMPLOYEES, DOLLAR_TO_INR_RATIO, MILLION_TO_ACTUAL
from integrations.apollo.apollo_api import ApolloAPIClient
from config.logging import logger


class ApolloHelper:
    def __init__(self):
        pass

    def parse_employee_range(self, range_str: str) -> tuple:
        """
        Parse employee range strings like '11-50', '201+' to min/max values
        Returns tuple of (min, max) where max can be None for open-ended ranges
        """
        range_str = range_str.strip()

        if '+' in range_str:
            min_val = int(range_str.replace('+', '')) + 1
            return min_val, None

        elif '-' in range_str:
            parts = range_str.split('-')

            if len(parts) == 2:
                return int(parts[0]), int(parts[1])

        try:
            val = int(range_str)
            return val, val

        except:
            return 1, 10

    def convert_revenue_to_actual(self, revenue_millions: str, currency: str = "USD") -> int:
        """
        Convert revenue from millions to actual numbers
        """
        try:
            if currency == "INR":
                revenue_millions = float(revenue_millions) / DOLLAR_TO_INR_RATIO

            revenue_float = float(revenue_millions)
            actual = int(revenue_float * MILLION_TO_ACTUAL)

            return actual
        except:
            return 0

    def sheets_to_apollo_config(self, sheets_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert sheets configuration to Apollo API configuration
        """
        apollo_config = {
            "per_page": 25  # Default page size
        }

        # Employee ranges
        if sheets_data.get("target", {}).get("employee_count"):
            employee_ranges = [
                range_str for range_str in sheets_data['target']["employee_count"] if range_str
            ]

            if employee_ranges and employee_ranges[0] != "null":
                logger.info(f"employee_ranges: {employee_ranges}")
                org_employee_ranges = []

                for range_str in employee_ranges:
                    logger.info(f"range_value: {range_str}")
                    min_emp, max_emp = self.parse_employee_range(range_str)
                    range_dict = {"min": min_emp}
                    
                    if max_emp:
                        range_dict["max"] = max_emp
                    
                    # Format as "min,max" string for Apollo
                    range_str_formatted = f"{min_emp},{max_emp}" if max_emp else f"{min_emp},"
                    org_employee_ranges.append(range_str_formatted)

                logger.info(f"organization_num_employees_ranges: {org_employee_ranges}")
                apollo_config["organization_num_employees_ranges"] = org_employee_ranges

        # Locations (include)
        if sheets_data.get("target", {}).get("location", {}).get("names"):
            locations = sheets_data['target']["location"]['names']
            apollo_locations = []
            
            for location in locations:
                # Apollo expects location names as-is (e.g., "newyork", "tokyo")
                # Convert to lowercase and remove spaces for consistency
                location_clean = location.lower().replace(" ", "")
                apollo_locations.append(location_clean)

            if apollo_locations:
                apollo_config["organization_locations"] = apollo_locations

        # Revenue range
        revenue_min = sheets_data.get("target", {}).get("revenue_min")
        revenue_max = sheets_data.get("target", {}).get("revenue_max")
        currency = sheets_data.get("target", {}).get("currency")

        logger.info(f"revenue_min_check: {revenue_min}, revenue_max_check: {revenue_max}, currency: {currency}")
        
        if revenue_min and revenue_max:
            try:
                min_value = self._clean_tuple_value(revenue_min) 
                max_value = self._clean_tuple_value(revenue_max) 
                currency_value = self._clean_tuple_value(currency) 
                min_actual = self.convert_revenue_to_actual(min_value, currency_value)
                max_actual = self.convert_revenue_to_actual(max_value, currency_value)
                logger.info(f"min_actual: {min_actual}, max_actual: {max_actual}")

                if min_actual > 0 or max_actual > 0:
                    apollo_config["revenue_range"] = {
                        "min": min_actual if min_actual > 0 else 1,
                        "max": max_actual
                    }

            except Exception as e:
                logger.info(f"⚠️ Error processing revenue: {e}")

        # Keyword tags (from industry or other keywords)
        industry_names = sheets_data.get("segmentation", {}).get("industry", [])
        if industry_names:
            if not isinstance(industry_names, list):
                industry_names = [industry_names]
            
            # Convert industry names to keyword tags (lowercase, no spaces)
            keyword_tags = [name.lower().replace(" ", "") for name in industry_names if name]
            if keyword_tags:
                apollo_config["q_organization_keyword_tags"] = keyword_tags

        apollo_config["campaign_id"] = sheets_data.get("_id")
        logger.info(f"✅ Converted sheets config to Apollo config: {apollo_config}")

        return apollo_config

    async def get_companies_from_apollo(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main function to get companies from Apollo using sheets data
        """
        bind_contextvars(operation="get_companies_from_apollo", component="apollo_helper", event_type="apollo_company_search")
        apollo_config = self.sheets_to_apollo_config(config)
        logger.info(f"Apollo config: {apollo_config}")

        if not apollo_config or len(apollo_config) <= 1:
            logger.warning("❌ No valid Apollo configuration generated")
            return []

        try:
            apollo_api_client = ApolloAPIClient()
            companies = await apollo_api_client.apollo_collect_companies_from_search(apollo_config, config)
            logger.info(f"✅ Retrieved {companies} companies from Apollo")
            return companies

        except Exception as e:
            logger.error(f"❌ Error calling Apollo API: {e}")
            return []

    def _clean_tuple_value(self, value):
        """Clean tuple values from sheets data"""
        if value and isinstance(value, tuple) and len(value) > 0:
            return value[0]
            
        return value

